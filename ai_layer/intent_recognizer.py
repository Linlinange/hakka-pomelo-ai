"""
意图识别模块（Intent Recognizer）
从数据库中读取金柚专属 Prompt 模板，动态拼接后调用大模型，
将返回结果解析为结构化的意图数据。
"""

import json
import re
import logging
import time
from typing import Optional, Any

from .config import get_config
from .llm_adapter import LLMAdapter, create_adapter
from .exceptions import IntentParseException, LLMException

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 默认意图识别 Prompt（数据库无可用模板时的兜底）
# ---------------------------------------------------------------------------

DEFAULT_INTENT_SYSTEM_PROMPT = """\
你是一个意图分类器。只输出JSON，不要解释。

规则：
- BUY：用户想买金柚、求推荐、送礼、有预算（含买/购/送/推荐/预算/哪个好）
- QA：纯知识问题（含怎么保存/营养/做法/区别/历史/怎么吃/种植）

按此JSON格式输出（null表示无此信息）：
{"intent":"BUY","confidence":0.92,"constraints":{"budget_min":null,"budget_max":null,"recipient":null,"scene":null,"spec_preference":null,"quantity":null},"culture_tags":[],"keywords":[]}

字段说明：budget_max=价格数字, recipient=送礼对象, scene=场景, culture_tags=客家文化标签, keywords=3-5个核心词"""

DEFAULT_INTENT_USER_PROMPT_TEMPLATE = """输入：{{user_input}}

JSON输出："""

# ---------------------------------------------------------------------------
# Prompt 加载抽象（方便后续替换为 DB 直连）
# ---------------------------------------------------------------------------


class PromptLoader:
    """Prompt模板加载器，优先读数据库，失败时回退到内置默认模板"""

    def __init__(self):
        self._cache: dict[str, dict] = {}  # scene_category -> template
        self._cache_time: float = 0
        self._cache_ttl: float = 300  # 5 分钟

    def load_intent_prompt(self, scene_category: str = "INTENT") -> dict:
        """
        返回意图识别 Prompt 模板 dict：
        { "system_role_desc": str, "prompt_template": str, "variables_schema": dict, "version": str }
        """
        # 先查缓存
        if scene_category in self._cache and (time.time() - self._cache_time) < self._cache_ttl:
            return self._cache[scene_category]

        # 尝试读数据库
        template = self._load_from_db(scene_category)
        if template is None:
            template = self._get_default(scene_category)

        self._cache[scene_category] = template
        self._cache_time = time.time()
        return template

    def _load_from_db(self, scene_category: str) -> Optional[dict]:
        """从 MySQL pomelo_prompt_library 表加载当前启用版本"""
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
                        """SELECT system_role_desc, prompt_template, variables_schema, version
                           FROM pomelo_prompt_library
                           WHERE scene_category = %s AND is_current = 1 AND status = 1
                           ORDER BY priority DESC LIMIT 1""",
                        (scene_category,),
                    )
                    row = cur.fetchone()
                    if row:
                        return {
                            "system_role_desc": row["system_role_desc"],
                            "prompt_template": row["prompt_template"],
                            "variables_schema": row["variables_schema"],
                            "version": row.get("version", "1.0.0"),
                        }
            finally:
                conn.close()
        except Exception as exc:
            logger.warning("从数据库加载Prompt模板失败，使用默认模板: %s", exc)
        return None

    @staticmethod
    def _get_default(scene_category: str) -> dict:
        return {
            "system_role_desc": DEFAULT_INTENT_SYSTEM_PROMPT,
            "prompt_template": DEFAULT_INTENT_USER_PROMPT_TEMPLATE,
            "variables_schema": {"user_input": "用户原始输入"},
            "version": "default-1.0.0",
        }


# ---------------------------------------------------------------------------
# 意图识别引擎
# ---------------------------------------------------------------------------


class IntentRecognizer:
    """
    金柚意图识别引擎

    使用方式:
        recognizer = IntentRecognizer()
        result = recognizer.recognize("200元预算中秋送客家亲友什么金柚好")
        # result.intent  -> "BUY"
        # result.constraints -> {...}
    """

    def __init__(self, adapter: Optional[LLMAdapter] = None, prompt_loader: Optional[PromptLoader] = None):
        self._adapter = adapter or create_adapter()
        self._prompt_loader = prompt_loader or PromptLoader()

    # ---- 核心入口 ----

    def recognize(self, user_input: str) -> "IntentResult":
        """
        识别用户输入的意图。

        Args:
            user_input: 用户在微信小程序中输入的文本

        Returns:
            IntentResult 对象
        """
        if not user_input or not user_input.strip():
            return IntentResult.empty()

        user_input = user_input.strip()
        logger.info("意图识别开始: input=%s...", user_input[:80])

        # 1. 加载 Prompt 模板
        template = self._prompt_loader.load_intent_prompt("INTENT")
        system_prompt = template["system_role_desc"]
        user_prompt = self._assemble_user_prompt(template["prompt_template"], user_input)

        # 2. 调用大模型
        invoke_result = self._adapter.invoke(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.10,  # 意图识别用极低温度，保证输出稳定
            max_tokens=512,
        )

        raw_content = invoke_result.get("content", "")
        if not invoke_result.get("success") or not raw_content:
            logger.warning("大模型调用失败，回退到默认意图: error=%s", invoke_result.get("error", ""))
            return IntentResult.fallback(user_input, error=invoke_result.get("error", "LLM返回为空"))

        # 3. 解析 JSON
        try:
            parsed = self._extract_json(raw_content)
            return IntentResult.from_parsed(parsed, raw=raw_content, version=template.get("version", ""),
                                            response_time_ms=invoke_result.get("response_time_ms", 0))
        except IntentParseException as exc:
            logger.warning("意图JSON解析失败: %s, raw=%s...", exc, raw_content[:200])
            return IntentResult.fallback(user_input, error=str(exc))

    # ---- 内部方法 ----

    def _assemble_user_prompt(self, template_str: str, user_input: str) -> str:
        """将用户输入填入 Prompt 模板的 {{user_input}} 占位符"""
        prompt = template_str.replace("{{user_input}}", user_input)
        # 兼容其他可能的占位符
        prompt = prompt.replace("{{query}}", user_input)
        return prompt

    @staticmethod
    def _extract_json(raw: str) -> dict:
        """从大模型返回文本中提取 JSON，兼容带 markdown 代码块的情况"""
        text = raw.strip()

        # 尝试匹配 ```json ... ``` 代码块
        code_block = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if code_block:
            text = code_block.group(1).strip()

        # 尝试找到最外层的 { }
        brace_start = text.find("{")
        brace_end = text.rfind("}")
        if brace_start != -1 and brace_end > brace_start:
            text = text[brace_start:brace_end + 1]

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # 最后的容错：尝试修复常见格式问题（单引号、尾逗号、无引号key）
        try:
            fixed = re.sub(r"(?<!\\)'", '"', text)  # 单引号 → 双引号
            fixed = re.sub(r",\s*}", "}", fixed)     # 移除尾部逗号
            fixed = re.sub(r",\s*]", "]", fixed)
            return json.loads(fixed)
        except json.JSONDecodeError:
            raise IntentParseException("无法解析大模型返回为JSON", raw_response=raw)


# ---------------------------------------------------------------------------
# 意图识别结果
# ---------------------------------------------------------------------------


class IntentResult:
    """意图识别结果数据对象"""

    __slots__ = (
        "intent", "confidence", "constraints", "culture_tags", "keywords",
        "raw_response", "prompt_version", "response_time_ms", "error",
    )

    def __init__(
        self,
        intent: str = "QA",
        confidence: float = 0.0,
        constraints: Optional[dict] = None,
        culture_tags: Optional[list] = None,
        keywords: Optional[list] = None,
        raw_response: str = "",
        prompt_version: str = "",
        response_time_ms: int = 0,
        error: str = "",
    ):
        self.intent = intent
        self.confidence = float(confidence)
        self.constraints = constraints or {}
        self.culture_tags = culture_tags or []
        self.keywords = keywords or []
        self.raw_response = raw_response
        self.prompt_version = prompt_version
        self.response_time_ms = response_time_ms
        self.error = error

    def __repr__(self) -> str:
        return (
            f"IntentResult(intent={self.intent!r}, confidence={self.confidence:.2f}, "
            f"constraints={self.constraints}, culture_tags={self.culture_tags}, "
            f"keywords={self.keywords})"
        )

    # ---- 属性快捷方法 ----

    @property
    def is_buy(self) -> bool:
        return self.intent.upper() == "BUY"

    @property
    def is_qa(self) -> bool:
        return self.intent.upper() == "QA"

    @property
    def is_confident(self) -> bool:
        threshold = get_config().intent_confidence_threshold
        return self.confidence >= threshold

    @property
    def needs_confirm(self) -> bool:
        """是否需要二次确认（置信度不足）"""
        return not self.is_confident

    # ---- 工厂方法 ----

    @classmethod
    def from_parsed(cls, parsed: dict, raw: str = "", version: str = "", response_time_ms: int = 0) -> "IntentResult":
        constraints = parsed.get("constraints", {}) or {}
        # 规范化约束字段
        normalized = {}
        normalized["budget_min"] = constraints.get("budget_min")
        normalized["budget_max"] = constraints.get("budget_max")
        normalized["recipient"] = constraints.get("recipient")
        normalized["scene"] = constraints.get("scene")
        normalized["spec_preference"] = constraints.get("spec_preference")
        normalized["quantity"] = constraints.get("quantity")
        # 保留大模型返回的其他字段
        for k, v in constraints.items():
            if k not in normalized:
                normalized[k] = v

        return cls(
            intent=parsed.get("intent", "QA").upper(),
            confidence=float(parsed.get("confidence", 0.5)),
            constraints=normalized,
            culture_tags=parsed.get("culture_tags", []),
            keywords=parsed.get("keywords", []),
            raw_response=raw,
            prompt_version=version,
            response_time_ms=response_time_ms,
        )

    @classmethod
    def empty(cls) -> "IntentResult":
        return cls(intent="QA", confidence=0.0)

    @classmethod
    def fallback(cls, user_input: str, error: str = "") -> "IntentResult":
        """大模型不可用时的规则式兜底（关键词加权匹配）"""
        buy_keywords = ["买", "选", "推荐", "送礼", "多少钱", "预算", "哪个", "哪款", "怎么选", "帮挑", "送"]
        qa_keywords = ["怎么", "如何", "什么", "保存", "保鲜", "辨别", "营养", "做法", "工艺", "好处", "区别",
                       "是什么", "能不能"]

        buy_score = sum(1 for w in buy_keywords if w in user_input)
        qa_score = sum(1 for w in qa_keywords if w in user_input)

        if buy_score > qa_score:
            intent = "BUY"
        elif qa_score > buy_score:
            intent = "QA"
        else:
            intent = "QA"  # 平局默认问答
        # 简单提取约束
        constraints = {}
        budget_match = re.search(r"(\d+)\s*元", user_input)
        if budget_match:
            budget = int(budget_match.group(1))
            constraints["budget_max"] = budget

        return cls(
            intent=intent,
            confidence=0.30,  # 规则兜底的置信度较低
            constraints=constraints,
            keywords=[w for w in user_input[:30].split() if len(w) > 1][:5],
            error=error,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "intent": self.intent,
            "confidence": self.confidence,
            "constraints": self.constraints,
            "culture_tags": self.culture_tags,
            "keywords": self.keywords,
            "prompt_version": self.prompt_version,
            "response_time_ms": self.response_time_ms,
            "is_confident": self.is_confident,
            "needs_confirm": self.needs_confirm,
        }
