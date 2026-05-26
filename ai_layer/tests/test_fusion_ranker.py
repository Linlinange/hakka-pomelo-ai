"""
融合推荐排序算法 — 单元测试
覆盖：规则打分、融合公式、LLM降级、空候选、权重归一化
"""

import pytest
from ai_layer.fusion_ranker import (
    FusionRanker,
    PomeloCandidate,
    UserDemand,
    ScoredCandidate,
    parse_candidates_from_rows,
    _parse_price_range,
)


# ---- 测试数据构造 ----

def make_candidate(**overrides):
    """快速构造候选金柚，自动解析 price_range → price_low/price_high"""
    defaults = {
        "id": 1, "name": "测试金柚", "category": "沙田柚",
        "origin": "梅州市梅县区", "specification": "6粒装",
        "price_range": "88-128元/箱", "taste_description": "清甜化渣",
        "hakka_culture_relation": "客家中秋必备", "gift_scene_tags": "中秋送礼,春节年货",
        "tags": "金奖,送礼", "score_requirement_match": 7.0,
        "score_scene_fit": 7.0, "score_hakka_feature": 7.0,
    }
    defaults.update(overrides)
    c = PomeloCandidate(**defaults)
    # 自动补全 price_low/price_high（正常流程由 parse_candidates_from_rows 完成）
    if c.price_low == 0.0 and c.price_high == 0.0 and c.price_range:
        c.price_low, c.price_high = _parse_price_range(c.price_range)
    return c


def make_demand(**overrides):
    """快速构造用户需求"""
    defaults = {
        "original_query": "200元中秋送礼",
        "intent": "BUY",
        "budget_max": 200,
        "scene": "中秋送礼",
        "recipient": "亲友",
        "culture_tags": ["客家", "中秋"],
        "keywords": ["送礼", "金柚", "中秋"],
    }
    defaults.update(overrides)
    return UserDemand(**defaults)


# ---- 价格解析 ----

class TestParsePriceRange:
    def test_standard_range(self):
        assert _parse_price_range("88-128元/箱") == (88.0, 128.0)

    def test_single_price(self):
        assert _parse_price_range("68元/箱") == (68.0, 68.0)

    def test_empty(self):
        assert _parse_price_range("") == (0.0, 0.0)

    def test_none(self):
        assert _parse_price_range(None) == (0.0, 0.0)

    def test_decimal(self):
        assert _parse_price_range("10.5-20.8") == (10.5, 20.8)


# ---- 候选解析 ----

class TestParseCandidates:
    def test_from_rows(self):
        rows = [{
            "id": 1, "pomelo_name": "梅县沙田柚", "category": "沙田柚",
            "origin": "梅县", "price_range": "88-128元/箱",
            "score_requirement_match": 8.5, "score_scene_fit": 9.0,
            "score_hakka_feature": 9.5,
        }]
        candidates = parse_candidates_from_rows(rows)
        assert len(candidates) == 1
        assert candidates[0].name == "梅县沙田柚"
        assert candidates[0].price_low == 88.0
        assert candidates[0].price_high == 128.0

    def test_missing_fields_default(self):
        rows = [{"id": 5, "pomelo_name": "未知柚"}]
        candidates = parse_candidates_from_rows(rows)
        assert candidates[0].score_requirement_match == 5.0
        assert candidates[0].price_low == 0.0


# ---- 规则打分 ----

class TestRuleScoring:
    def setup_method(self):
        self.ranker = FusionRanker()

    def test_price_match_within_budget(self):
        c = make_candidate(price_range="50-100元/箱")
        d = make_demand(budget_max=200)
        s = self.ranker._rule_score(c, d)
        # 价格在预算内，应该在基础分上有加分
        assert s.score_price_match >= 7.0

    def test_price_match_over_budget(self):
        c = make_candidate(price_range="300-500元/箱")
        d = make_demand(budget_max=200)
        s = self.ranker._rule_score(c, d)
        # 价格超出预算，应该扣分
        assert s.score_price_match < 7.0

    def test_price_match_no_budget(self):
        """无预算约束时返回DB基础分"""
        c = make_candidate(score_requirement_match=8.0)
        d = make_demand(budget_max=None, budget_min=None)
        s = self.ranker._rule_score(c, d)
        assert s.score_price_match == 8.0

    def test_scene_fit_with_match(self):
        """场景标签匹配时加分"""
        c = make_candidate(gift_scene_tags="中秋送礼,春节年货")
        d = make_demand(scene="中秋送礼")
        s = self.ranker._rule_score(c, d)
        assert s.score_scene_fit > 7.0

    def test_scene_fit_no_match(self):
        """场景标签和用户需求无交集时保持基础分"""
        c = make_candidate(gift_scene_tags="春节年货,日常自用", tags="实惠,家庭")
        d = make_demand(scene="商务送礼", keywords=["高端", "正式"])
        s = self.ranker._rule_score(c, d)
        # 无匹配应该不额外加分
        assert s.score_scene_fit == 7.0

    def test_hakka_feature_bonus(self):
        c = make_candidate(hakka_culture_relation="客家中秋祭祖必备")
        d = make_demand(culture_tags=["中秋", "客家"])
        s = self.ranker._rule_score(c, d)
        assert s.score_hakka_feature > 7.0

    def test_hakka_no_user_tags(self):
        """用户无客家标签时返回基础分"""
        c = make_candidate()
        d = make_demand(culture_tags=[], keywords=[])
        s = self.ranker._rule_score(c, d)
        assert s.score_hakka_feature == 7.0


# ---- 融合公式 ----

class TestFusionFormula:
    def setup_method(self):
        self.ranker = FusionRanker()

    def test_fusion_with_default_weights(self):
        c = make_candidate()
        s = ScoredCandidate(candidate=c, rule_total=8.0, llm_score=60.0)
        result = self.ranker._fuse(s)
        # rule: 8.0 * 10 = 80, llm: 60; 0.5*80 + 0.5*60 = 70
        assert result == 70.0


# ---- 排名流程 ----

class TestRankPipeline:
    def test_empty_candidates(self):
        ranker = FusionRanker()
        demand = make_demand()
        results = ranker.rank(demand, [])
        assert results == []

    def test_single_candidate_ranked(self):
        ranker = FusionRanker()
        demand = make_demand()
        candidates = [make_candidate(id=1, name="梅县沙田柚")]
        results = ranker.rank(demand, candidates)
        assert len(results) == 1
        assert results[0].candidate.name == "梅县沙田柚"
        assert results[0].final_score >= 0

    def test_multiple_candidates_sorted(self):
        """确认结果按 fusion 分降序排列"""
        ranker = FusionRanker()
        demand = make_demand()

        # 构造两个候选：一个完全匹配预算，一个超出预算
        good = make_candidate(id=1, name="好柚", price_range="50-100元/箱",
                              score_requirement_match=9.0, score_scene_fit=9.0,
                              score_hakka_feature=9.0)
        bad = make_candidate(id=2, name="贵柚", price_range="500-800元/箱",
                             score_requirement_match=3.0, score_scene_fit=3.0,
                             score_hakka_feature=3.0)
        results = ranker.rank(demand, [good, bad])
        assert results[0].candidate.id == 1  # 更好的排前面

    def test_top3_get_reasons(self):
        """Top-3 应有推荐理由（即使 LLM 不可用也有兜底）"""
        ranker = FusionRanker()
        demand = make_demand()
        candidates = [make_candidate(id=i, name=f"金柚{i}") for i in range(1, 6)]
        results = ranker.rank(demand, candidates)
        # 前3名应该有理由（规则兜底）
        for s in results[:3]:
            assert len(s.reason) > 0

    def test_fallback_reason(self):
        """兜底推荐理由包含关键字段"""
        ranker = FusionRanker()
        c = make_candidate(name="梅县沙田柚", origin="梅县松口")
        s = ScoredCandidate(candidate=c, rule_total=8.0)
        reason = ranker._fallback_reason(s, make_demand())
        assert "梅县沙田柚" in reason
        assert "梅县松口" in reason


# ---- 权重加载与归一化 ----

class TestWeightLoading:
    def test_default_weights_exist(self):
        ranker = FusionRanker()
        w = ranker._weights
        assert "w_requirement" in w
        assert "w_scene" in w
        assert "w_hakka" in w
        assert "w_fusion_rule" in w
        assert "w_fusion_llm" in w

    def test_dimension_weights_sum_to_one(self):
        ranker = FusionRanker()
        dim_sum = ranker._weights["w_requirement"] + \
                  ranker._weights["w_scene"] + \
                  ranker._weights["w_hakka"]
        assert abs(dim_sum - 1.0) < 0.01

    def test_fusion_weights_sum_to_one(self):
        ranker = FusionRanker()
        fusion_sum = ranker._weights["w_fusion_rule"] + \
                     ranker._weights["w_fusion_llm"]
        assert abs(fusion_sum - 1.0) < 0.01
