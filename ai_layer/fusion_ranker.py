"""
大模型 + 规则式融合推荐排序算法（Fusion Ranker）
核心流程：
  1. 规则式多因子打分（价格匹配 / 场景适配 / 客家特色）
  2. 大模型语义增强打分
  3. 融合排序（加权平均）
  4. Top-3 个性化推荐理由生成
"""

import json
import re
import logging
import time
from dataclasses import dataclass, field
from typing import Optional, Any

from .config import get_config
from .llm_adapter import LLMAdapter, create_adapter
from .exceptions import LLMException

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 数据模型
# ---------------------------------------------------------------------------


@dataclass
class PomeloCandidate:
    """从 MySQL 召回的候选金柚"""
    id: int
    name: str
    category: str = ""
    origin: str = ""
    specification: str = ""
    weight_range: str = ""
    price_range: str = ""                          # 如 "30-80元/箱"
    season_info: str = ""
    taste_description: str = ""
    cultivation_process: str = ""
    hakka_culture_relation: str = ""               # 客家文化关联描述
    identification_tips: str = ""
    preservation_method: str = ""
    edible_pairing: str = ""
    nutritional_value: str = ""
    gift_scene_tags: str = ""                      # 送礼场景标签（逗号分隔）
    tags: str = ""                                 # 通用标签
    price_low: float = 0.0                         # 价格下界（数值，解析自 price_range）
    price_high: float = 0.0                        # 价格上界
    score_requirement_match: float = 5.0           # DB 基础分：需求匹配度
    score_scene_fit: float = 5.0                   # DB 基础分：场景适配度
    score_hakka_feature: float = 5.0               # DB 基础分：客家特色贴合度


@dataclass
class UserDemand:
    """意图识别后提取的用户需求"""
    original_query: str
    intent: str = "QA"
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    recipient: Optional[str] = None
    scene: Optional[str] = None
    spec_preference: Optional[str] = None
    quantity: Optional[int] = None
    culture_tags: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)

    @classmethod
    def from_intent_result(cls, query: str, intent_result) -> "UserDemand":
        """从 IntentResult 构造 UserDemand"""
        c = intent_result.constraints
        return cls(
            original_query=query,
            intent=intent_result.intent,
            budget_min=c.get("budget_min"),
            budget_max=c.get("budget_max"),
            recipient=c.get("recipient"),
            scene=c.get("scene"),
            spec_preference=c.get("spec_preference"),
            quantity=c.get("quantity"),
            culture_tags=intent_result.culture_tags or [],
            keywords=intent_result.keywords or [],
        )


@dataclass
class ScoredCandidate:
    """打分后的候选金柚"""
    candidate: PomeloCandidate
    score_price_match: float = 0.0        # 价格匹配度 (0-10)
    score_scene_fit: float = 0.0          # 场景适配度 (0-10)
    score_hakka_feature: float = 0.0      # 客家特色贴合度 (0-10)
    rule_total: float = 0.0               # 规则式加权总分 (0-10)
    llm_score: float = 0.0                # 大模型语义匹配分 (0-100)
    final_score: float = 0.0              # 融合总分
    reason: str = ""                      # 推荐理由


# ---------------------------------------------------------------------------
# 融合推荐排序引擎
# ---------------------------------------------------------------------------


class FusionRanker:
    """
    大模型 + 规则式融合推荐排序引擎

    使用方式:
        ranker = FusionRanker()
        results = ranker.rank(user_demand, candidates)
        # results 是按 final_score 降序的推荐列表，前3名附带个性化推荐理由
    """

    def __init__(self, adapter: Optional[LLMAdapter] = None):
        self._adapter = adapter or create_adapter()
        self._weights = self._load_weights()

    # ---- 主流程 ----

    def rank(
        self,
        demand: UserDemand,
        candidates: list[PomeloCandidate],
    ) -> list[ScoredCandidate]:
        """
        执行融合推荐排序。

        Args:
            demand: 解析后的用户需求
            candidates: MySQL 召回的候选金柚列表

        Returns:
            按 final_score 降序排列的打分结果列表，前3名包含推荐理由
        """
        if not candidates:
            logger.info("候选列表为空，跳过推荐")
            return []

        logger.info("融合推荐开始: query=%s, candidates=%d", demand.original_query[:60], len(candidates))

        # 1. 规则式多因子打分
        scored = [self._rule_score(c, demand) for c in candidates]

        # 2. 大模型语义增强打分（批量）
        #    超过 TOP_N 时先按规则分预筛，只送头部候选给 LLM 打分
        TOP_N = 10
        t0 = time.perf_counter()
        llm_candidates = [s.candidate for s in scored]
        if len(scored) > TOP_N:
            scored.sort(key=lambda x: x.rule_total, reverse=True)
            llm_candidates = [s.candidate for s in scored[:TOP_N]]
            logger.info("候选过多(%d)，规则预筛Top-%d送LLM", len(candidates), TOP_N)

        try:
            llm_scores = self._llm_semantic_score(demand, llm_candidates)
            llm_map = {id_: score for id_, score in
                       zip([c.id for c in llm_candidates], llm_scores)}
            for s in scored:
                s.llm_score = llm_map.get(s.candidate.id, 50.0)
        except Exception as exc:
            logger.warning("LLM语义打分失败，仅使用规则分数: %s", exc)
            for s in scored:
                s.llm_score = 50.0

        llm_elapsed = int((time.perf_counter() - t0) * 1000)
        logger.info("LLM语义打分完成: %dms", llm_elapsed)

        # 3. 融合总分
        for s in scored:
            s.final_score = self._fuse(s)

        # 4. 降序排序
        scored.sort(key=lambda x: x.final_score, reverse=True)

        # 5. Top-3 推荐理由生成
        top3 = scored[:3]
        if top3:
            try:
                reasons = self._generate_reasons(demand, [s.candidate for s in top3])
                for s, reason in zip(top3, reasons):
                    s.reason = reason
            except Exception as exc:
                logger.warning("推荐理由生成失败: %s", exc)
                for s in top3:
                    s.reason = self._fallback_reason(s, demand)

        logger.info("融合推荐完成: top3=%s", [(s.candidate.name, round(s.final_score, 1)) for s in top3])
        return scored

    # ---- 1. 规则式多因子打分 ----

    def _rule_score(self, c: PomeloCandidate, d: UserDemand) -> ScoredCandidate:
        """对单个候选金柚进行三维度规则打分"""
        s = ScoredCandidate(candidate=c)

        # 维度1：价格匹配度
        s.score_price_match = self._calc_price_match(c, d)

        # 维度2：场景适配度
        s.score_scene_fit = self._calc_scene_fit(c, d)

        # 维度3：客家特色贴合度
        s.score_hakka_feature = self._calc_hakka_feature(c, d)

        # 加权总分
        s.rule_total = (
            self._weights["w_requirement"] * s.score_price_match
            + self._weights["w_scene"] * s.score_scene_fit
            + self._weights["w_hakka"] * s.score_hakka_feature
        )
        return s

    def _calc_price_match(self, c: PomeloCandidate, d: UserDemand) -> float:
        """
        价格匹配度 (0-10)
        - 候选价格在用户预算内 → 高分
        - 候选价格超出预算 → 按超出比例扣分
        - 用户未指定预算 → 取 DB 基础分
        """
        base = c.score_requirement_match
        if d.budget_max is None and d.budget_min is None:
            return base

        low = c.price_low if c.price_low > 0 else (c.price_high * 0.6 if c.price_high > 0 else 0)
        high = c.price_high if c.price_high > 0 else (c.price_low * 1.5 if c.price_low > 0 else 0)

        if low == 0 and high == 0:
            return base

        budget_max = d.budget_max or float("inf")
        budget_min = d.budget_min or 0

        # 价格完全在预算内
        if high <= budget_max and low >= budget_min:
            return min(10.0, base + 2.0)

        # 候选最低价低于预算下限（偏低档）
        if high < budget_min:
            return max(1.0, base - 2.0)

        # 候选最高价超出预算上限
        if high > budget_max:
            over_ratio = (high - budget_max) / budget_max if budget_max > 0 else 1.0
            penalty = min(5.0, over_ratio * 5.0)
            return max(1.0, base - penalty)

        return base

    def _calc_scene_fit(self, c: PomeloCandidate, d: UserDemand) -> float:
        """
        场景适配度 (0-10)
        - 候选 gift_scene_tags / tags 与用户场景关键词匹配 → 加分
        - 无场景信息 → 取 DB 基础分
        """
        base = c.score_scene_fit

        candidate_tags = set()
        if c.gift_scene_tags:
            candidate_tags.update(t.strip() for t in c.gift_scene_tags.replace("，", ",").split(","))
        if c.tags:
            candidate_tags.update(t.strip() for t in c.tags.replace("，", ",").split(","))

        demand_signals = set()
        if d.scene:
            demand_signals.add(d.scene)
        if d.recipient:
            demand_signals.add(d.recipient)
        demand_signals.update(d.culture_tags)
        demand_signals.update(d.keywords)

        if not demand_signals:
            return base

        # 计算标签重合度
        overlap = candidate_tags & demand_signals
        if not overlap:
            # 宽松匹配：子串匹配
            for ct in candidate_tags:
                for ds in demand_signals:
                    if ct in ds or ds in ct:
                        overlap.add(ct)

        if overlap:
            bonus = min(4.0, len(overlap) * 1.0)
            return min(10.0, base + bonus)

        return base

    def _calc_hakka_feature(self, c: PomeloCandidate, d: UserDemand) -> float:
        """
        客家特色贴合度 (0-10)
        - 候选 hakka_culture_relation 与用户 culture_tags 匹配 → 加分
        - 候选产地在梅州核心产区 → 加分
        """
        base = c.score_hakka_feature

        # 客家文化标签匹配
        hakka_core = {"梅州", "客家", "沙田柚", "蜜柚", "金柚", "松口", "梅县", "大埔",
                      "中秋", "春节", "祭祖", "团圆", "送礼", "特产", "非遗"}
        candidate_hakka_signals = set()

        # 从文化关联描述中提取
        text = f"{c.origin} {c.hakka_culture_relation} {c.taste_description} {c.tags} {c.gift_scene_tags}"
        for kw in hakka_core:
            if kw in text:
                candidate_hakka_signals.add(kw)

        # 用户客家标签
        user_hakka = set(d.culture_tags) if d.culture_tags else set()
        # 从 keywords 中提取客家相关
        hakka_context = {"送礼", "团圆", "中秋", "春节", "客家", "梅州", "特产", "祭祖", "亲友"}
        for kw in d.keywords:
            if kw in hakka_context:
                user_hakka.add(kw)

        if user_hakka:
            overlap = candidate_hakka_signals & user_hakka
            bonus = min(3.0, len(overlap) * 0.75)
            return min(10.0, base + bonus)

        return base

    # ---- 权重加载 ----

    def _load_weights(self) -> dict[str, float]:
        """从 algo_rule_params 表或默认值加载三维度权重"""
        defaults = {"w_requirement": 0.40, "w_scene": 0.35, "w_hakka": 0.25}
        try:
            import pymysql
            cfg = get_config()
            conn = pymysql.connect(
                host=cfg.db_host, port=cfg.db_port,
                user=cfg.db_user, password=cfg.db_password,
                database=cfg.db_name, charset="utf8mb4",
                connect_timeout=5,
            )
            try:
                with conn.cursor(pymysql.cursors.DictCursor) as cur:
                    cur.execute(
                        """SELECT param_key, param_value FROM algo_rule_params
                           WHERE param_group IN ('REQUIREMENT_MATCH','SCENE_FIT','HAKKA_FEATURE')
                           AND param_type = 'WEIGHT' AND status = 1"""
                    )
                    rows = cur.fetchall()
                    key_map = {
                        "weight_requirement_match": "w_requirement",
                        "weight_scene_fit": "w_scene",
                        "weight_hakka_feature": "w_hakka",
                    }
                    for r in rows:
                        mapped = key_map.get(r["param_key"])
                        if mapped:
                            defaults[mapped] = float(r["param_value"])
            finally:
                conn.close()
        except Exception as exc:
            logger.warning("从DB加载权重失败，使用默认值: %s", exc)

        total = sum(defaults.values())
        if total > 0 and abs(total - 1.0) > 0.001:
            defaults = {k: v / total for k, v in defaults.items()}
        logger.info("规则打分权重: requirement=%.2f scene=%.2f hakka=%.2f",
                    defaults["w_requirement"], defaults["w_scene"], defaults["w_hakka"])
        return defaults

    # ---- 2. 大模型语义打分 ----

    _SEMANTIC_SCORE_PROMPT = """\
你是客家金柚领域的资深专家。请对以下候选金柚逐一评估其与用户需求的语义匹配度。

用户需求：{user_query}
用户意图：{intent}
约束条件：{constraints}

候选金柚列表：
{candidate_list}

请对每个候选金柚输出一个 0-100 的语义匹配分，综合考量：
- 金柚属性与用户需求的契合度
- 金柚适合用户场景（送礼/自用/宴请）的程度
- 客家文化元素的贴合度

输出严格JSON数组格式（不要包含markdown标记）：
[{{"id": <金柚ID>, "score": <0-100>, "brief": "<10字简评>"}}, ...]"""

    def _llm_semantic_score(self, demand: UserDemand, candidates: list[PomeloCandidate]) -> list[float]:
        """批量调用大模型对候选金柚进行语义打分"""
        if not candidates:
            return []

        constraints_str = ", ".join(
            f"{k}={v}" for k, v in [
                ("预算", f"{demand.budget_min or ''}-{demand.budget_max or ''}元"),
                ("送礼对象", demand.recipient or ""),
                ("场景", demand.scene or ""),
                ("规格偏好", demand.spec_preference or ""),
                ("数量", str(demand.quantity) if demand.quantity else ""),
            ] if v
        ) or "无特殊约束"

        candidate_lines = []
        for i, c in enumerate(candidates):
            desc = (
                f"ID:{c.id} | 品名:{c.name} | 品类:{c.category} | "
                f"产地:{c.origin} | 规格:{c.specification} | "
                f"价格:{c.price_range} | 口感:{c.taste_description} | "
                f"客家文化:{c.hakka_culture_relation[:60]} | "
                f"送礼场景:{c.gift_scene_tags} | 标签:{c.tags}"
            )
            candidate_lines.append(f"  [{i + 1}] {desc}")

        user_prompt = self._SEMANTIC_SCORE_PROMPT.format(
            user_query=demand.original_query,
            intent="选购推荐" if demand.intent == "BUY" else "知识查询",
            constraints=constraints_str,
            candidate_list="\n".join(candidate_lines),
        )

        result = self._adapter.invoke(
            prompt=user_prompt,
            system_prompt="你是客家金柚推荐专家，请严格按照JSON格式输出结果。",
            temperature=0.30,
            max_tokens=1024,
        )

        if not result.get("success"):
            raise LLMException(f"语义打分失败: {result.get('error', '')}")

        return self._parse_semantic_scores(result["content"], [c.id for c in candidates])

    @staticmethod
    def _parse_semantic_scores(raw: str, candidate_ids: list[int]) -> list[float]:
        """解析大模型返回的语义评分JSON"""
        text = raw.strip()
        # 提取 JSON 数组
        arr_match = re.search(r"\[[\s\S]*\]", text)
        if arr_match:
            text = arr_match.group(0)
        try:
            scores = json.loads(text)
        except json.JSONDecodeError:
            # 容错：单引号修复
            try:
                fixed = re.sub(r"(?<!\\)'", '"', text)
                scores = json.loads(fixed)
            except json.JSONDecodeError:
                raise LLMException(f"语义评分JSON解析失败: {raw[:200]}")

        # 映射回候选列表顺序
        score_map = {item["id"]: float(item["score"]) for item in scores}
        return [score_map.get(cid, 50.0) for cid in candidate_ids]

    # ---- 3. 融合公式 ----

    @staticmethod
    def _fuse(s: ScoredCandidate, rule_weight: float = 0.50, llm_weight: float = 0.50) -> float:
        """
        融合公式：final = rule_weight * rule_100 + llm_weight * llm_score
        规则总分 (0-10) 先放大到 0-100 与 LLM 对齐，再按权重加权。
        """
        rule_100 = s.rule_total * 10.0  # 0-10 → 0-100
        return rule_weight * rule_100 + llm_weight * s.llm_score

    # ---- 4. 推荐理由生成 ----

    _REASON_PROMPT = """\
你是梅州客家金柚文化传承人与专业导购。请为以下Top3推荐金柚各生成一段个性化推荐理由。

用户原始需求：{user_query}
用户意图：{intent}

Top3 金柚信息：
{pomelo_list}

要求：
1. 每段理由 40-80 字，温暖亲切，有客家味
2. 结合金柚的产地故事、客家文化内涵
3. 提到与用户需求的契合点
4. 突出客家特色（如"捱兜"客家话元素、客家民俗、梅州山水等）

输出严格JSON数组（不要包含markdown标记）：
[{{"id": <金柚ID>, "reason": "<推荐理由>"}}, ...]"""

    def _generate_reasons(self, demand: UserDemand, top3: list[PomeloCandidate]) -> list[str]:
        """为 Top-3 金柚生成个性化推荐理由"""
        lines = []
        for i, c in enumerate(top3):
            lines.append(
                f"  [{i + 1}] ID:{c.id} 「{c.name}」— {c.origin}，{c.specification}，"
                f"{c.price_range}，{c.taste_description}。"
                f"客家故事：{c.hakka_culture_relation[:80]}"
            )

        user_prompt = self._REASON_PROMPT.format(
            user_query=demand.original_query,
            intent="选购推荐" if demand.intent == "BUY" else "知识推荐",
            pomelo_list="\n".join(lines),
        )

        result = self._adapter.invoke(
            prompt=user_prompt,
            system_prompt="你是梅州客家金柚文化传承人，擅长用温暖亲切的客家风格说话。",
            temperature=0.75,
            max_tokens=1024,
        )

        if not result.get("success"):
            raise LLMException(f"推荐理由生成失败: {result.get('error', '')}")

        return self._parse_reasons(result["content"], [c.id for c in top3])

    @staticmethod
    def _parse_reasons(raw: str, top_ids: list[int]) -> list[str]:
        text = raw.strip()
        arr_match = re.search(r"\[[\s\S]*\]", text)
        if arr_match:
            text = arr_match.group(0)
        try:
            reasons = json.loads(text)
        except json.JSONDecodeError:
            try:
                reasons = json.loads(re.sub(r"(?<!\\)'", '"', text))
            except json.JSONDecodeError:
                raise LLMException(f"推荐理由JSON解析失败: {raw[:200]}")

        reason_map = {item["id"]: item.get("reason", "") for item in reasons}
        return [reason_map.get(cid, "这款金柚非常适合您的需求。") for cid in top_ids]

    @staticmethod
    def _fallback_reason(s: ScoredCandidate, demand: UserDemand) -> str:
        """LLM 不可用时的规则式兜底推荐理由"""
        c = s.candidate
        parts = [f"「{c.name}」产自{c.origin}"]
        if demand.scene:
            parts.append(f"非常适合{demand.scene}场景")
        if c.taste_description:
            parts.append(f"口感{c.taste_description}")
        if c.hakka_culture_relation:
            short = c.hakka_culture_relation[:30].rstrip("，。")
            parts.append(f"承载着{short}的客家文化")
        parts.append("是您品味客家风情的不二之选。")
        return "，".join(parts) + "。"


# ---------------------------------------------------------------------------
# 工具函数：从 MySQL 解析候选数据
# ---------------------------------------------------------------------------


def parse_candidates_from_rows(rows: list[dict]) -> list[PomeloCandidate]:
    """将 pymysql 查询结果转换为 PomeloCandidate 列表"""
    candidates = []
    for r in rows:
        price_low, price_high = _parse_price_range(r.get("price_range", ""))
        candidates.append(PomeloCandidate(
            id=r["id"],
            name=r.get("pomelo_name", ""),
            category=r.get("category", ""),
            origin=r.get("origin", ""),
            specification=r.get("specification", ""),
            weight_range=r.get("weight_range", ""),
            price_range=r.get("price_range", ""),
            season_info=r.get("season_info", ""),
            taste_description=r.get("taste_description", ""),
            cultivation_process=r.get("cultivation_process", ""),
            hakka_culture_relation=r.get("hakka_culture_relation", ""),
            identification_tips=r.get("identification_tips", ""),
            preservation_method=r.get("preservation_method", ""),
            edible_pairing=r.get("edible_pairing", ""),
            nutritional_value=r.get("nutritional_value", ""),
            gift_scene_tags=r.get("gift_scene_tags", ""),
            tags=r.get("tags", ""),
            price_low=price_low,
            price_high=price_high,
            score_requirement_match=float(r.get("score_requirement_match", 5.0)),
            score_scene_fit=float(r.get("score_scene_fit", 5.0)),
            score_hakka_feature=float(r.get("score_hakka_feature", 5.0)),
        ))
    return candidates


def _parse_price_range(text: str) -> tuple[float, float]:
    """解析价格字符串为数值，如 '30-80元/箱' → (30.0, 80.0)"""
    if not text:
        return 0.0, 0.0
    nums = re.findall(r"(\d+(?:\.\d+)?)", text.replace("〜", "-"))
    if len(nums) >= 2:
        return float(nums[0]), float(nums[1])
    if len(nums) == 1:
        return float(nums[0]), float(nums[0])
    return 0.0, 0.0
