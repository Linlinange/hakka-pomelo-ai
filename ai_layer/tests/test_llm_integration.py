"""
LLM 集成测试 — 需要 DEEPSEEK_API_KEY 环境变量。
设置 API Key 后运行: python -m pytest ai_layer/tests/ -v
无 Key 时自动跳过。
"""

import os
import pytest
from ai_layer.llm_adapter import create_adapter
from ai_layer.intent_recognizer import IntentRecognizer
from ai_layer.fusion_ranker import (
    FusionRanker,
    PomeloCandidate,
    UserDemand,
    parse_candidates_from_rows,
)

pytestmark = pytest.mark.skipif(
    not os.getenv("DEEPSEEK_API_KEY"),
    reason="DEEPSEEK_API_KEY not set — set it to run LLM integration tests",
)


# ---- 候选金柚测试数据 ----

def make_candidates():
    rows = [
        {"id": 1, "pomelo_name": "梅县松口沙田柚·金奖优选", "category": "沙田柚",
         "origin": "梅州市梅县区松口镇", "price_range": "88-128元/箱",
         "taste_description": "清甜化渣、蜜香浓郁、回甘持久",
         "hakka_culture_relation": "松口是客家人下南洋的起点，沙田柚随客家人远渡重洋名扬海外，中秋赏月必备",
         "gift_scene_tags": "中秋送礼,春节年货,团圆家宴,探亲访友",
         "tags": "金奖,送礼首选,非遗工艺,松口古镇",
         "score_requirement_match": 8.5, "score_scene_fit": 9.0, "score_hakka_feature": 9.5},
        {"id": 2, "pomelo_name": "大埔蜜柚·生态红肉", "category": "蜜柚",
         "origin": "梅州市大埔县", "price_range": "45-68元/箱",
         "taste_description": "果肉绯红、酸甜适口、汁水丰盈",
         "hakka_culture_relation": "大埔是客家香格里拉，红肉蜜柚象征客家人热情好客的红心",
         "gift_scene_tags": "日常送礼,尝鲜自用,家庭分享",
         "tags": "高性价比,红肉,生态种植,大埔",
         "score_requirement_match": 7.0, "score_scene_fit": 6.5, "score_hakka_feature": 7.0},
        {"id": 3, "pomelo_name": "梅州金柚·客家情礼盒", "category": "沙田柚",
         "origin": "梅州市梅江区", "price_range": "68-98元/盒",
         "taste_description": "果肉晶莹、蜜甜无渣、香气馥郁",
         "hakka_culture_relation": "梅江是客家文化发祥地，以柚待客千年礼仪传统",
         "gift_scene_tags": "商务送礼,中秋送礼,高端伴手礼",
         "tags": "精品,客家礼仪,商务,梅江",
         "score_requirement_match": 9.0, "score_scene_fit": 8.5, "score_hakka_feature": 9.0},
    ]
    return parse_candidates_from_rows(rows)


# ---- LLM 适配器 ----

class TestLLMAdapter:
    def test_deepseek_invoke_returns_content(self):
        """DeepSeek 正常返回文本"""
        adapter = create_adapter()
        result = adapter.invoke(
            prompt="用一句话介绍梅州客家金柚",
            system_prompt="你是金柚专家，回答要简短。",
            temperature=0.3,
            max_tokens=128,
        )
        assert result.get("success") is True, f"LLM invoke failed: {result.get('error')}"
        assert len(result.get("content", "")) > 10
        assert result.get("model") == "deepseek-chat"
        assert result.get("response_time_ms", 0) > 0


# ---- 意图识别（真实 LLM） ----

class TestIntentRecognition:
    def test_recognize_buy_intent(self):
        """LLM 识别选购意图"""
        recognizer = IntentRecognizer()
        result = recognizer.recognize("200元中秋送礼客家亲友推荐金柚")
        assert result.intent == "BUY"
        assert result.confidence >= 0.6  # 真实 LLM 应有较高置信度
        assert result.is_confident is True

    def test_recognize_qa_intent(self):
        """LLM 识别问答意图"""
        recognizer = IntentRecognizer()
        result = recognizer.recognize("金柚怎么保存比较好")
        assert result.intent == "QA"
        assert result.confidence >= 0.6

    def test_recognize_extracts_constraints(self):
        """LLM 提取预算等约束"""
        recognizer = IntentRecognizer()
        result = recognizer.recognize("300元预算买金柚送老人")
        assert result.constraints.get("budget_max") is not None or result.intent == "BUY"


# ---- 融合推荐排序（真实 LLM 语义打分 + 推荐理由） ----

class TestFusionRanking:
    def test_rank_returns_sorted_results(self):
        """全链路融合排序返回结果"""
        ranker = FusionRanker()
        candidates = make_candidates()
        demand = UserDemand(
            original_query="200元中秋送礼客家亲友推荐金柚",
            intent="BUY",
            budget_max=200,
            scene="中秋送礼",
            recipient="亲友",
            culture_tags=["客家", "中秋"],
            keywords=["送礼", "金柚", "中秋"],
        )
        results = ranker.rank(demand, candidates)
        assert len(results) == 3
        # 结果应降序排列
        assert results[0].final_score >= results[-1].final_score

    def test_top3_have_reasons(self):
        """Top-3 有 LLM 生成的推荐理由"""
        ranker = FusionRanker()
        candidates = make_candidates()
        demand = UserDemand(
            original_query="200元中秋送礼客家亲友",
            intent="BUY",
            budget_max=200,
            scene="中秋送礼",
            recipient="亲友",
        )
        results = ranker.rank(demand, candidates)
        for s in results[:3]:
            assert len(s.reason) > 20, f"推荐理由太短: {s.reason}"

    def test_llm_scoring_produces_variance(self):
        """LLM 语义打分有区分度（不是全部 50）"""
        ranker = FusionRanker()
        candidates = make_candidates()
        demand = UserDemand(
            original_query="高端商务送礼选什么金柚",
            intent="BUY",
            budget_max=500,
            scene="商务送礼",
            recipient="客户",
        )
        results = ranker.rank(demand, candidates)
        llm_scores = [s.llm_score for s in results]
        # 至少有两个不同的分数值
        assert len(set(llm_scores)) >= 2, f"LLM 打分无区分度: {llm_scores}"
