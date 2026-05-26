"""
意图识别模块 — 单元测试
覆盖：JSON解析、规则式兜底、IntentResult属性、UserDemand构造
"""

import pytest
from ai_layer.intent_recognizer import (
    IntentRecognizer,
    IntentResult,
)
from ai_layer.fusion_ranker import UserDemand


# ---- IntentResult 属性 ----

class TestIntentResult:
    def test_is_buy(self):
        r = IntentResult(intent="BUY", confidence=0.9)
        assert r.is_buy is True
        assert r.is_qa is False

    def test_is_qa(self):
        r = IntentResult(intent="QA", confidence=0.8)
        assert r.is_buy is False
        assert r.is_qa is True

    def test_is_confident_above_threshold(self):
        r = IntentResult(intent="BUY", confidence=0.9)
        assert r.is_confident is True  # threshold is 0.60

    def test_needs_confirm(self):
        r = IntentResult(intent="BUY", confidence=0.3)
        assert r.is_confident is False
        assert r.needs_confirm is True

    def test_empty(self):
        r = IntentResult.empty()
        assert r.intent == "QA"
        assert r.confidence == 0.0

    def test_to_dict(self):
        r = IntentResult(intent="BUY", confidence=0.85,
                         constraints={"budget_max": 200},
                         culture_tags=["客家"], keywords=["送礼"])
        d = r.to_dict()
        assert d["intent"] == "BUY"
        assert d["confidence"] == 0.85
        assert d["is_confident"] is True


# ---- JSON 解析 ----

class TestJsonParsing:
    def setup_method(self):
        self.recognizer = IntentRecognizer()

    def test_plain_json(self):
        parsed = self.recognizer._extract_json(
            '{"intent":"BUY","confidence":0.9,"constraints":{"budget_max":200}}'
        )
        assert parsed["intent"] == "BUY"
        assert parsed["confidence"] == 0.9

    def test_markdown_code_block(self):
        parsed = self.recognizer._extract_json(
            '```json\n{"intent":"QA","confidence":0.8}\n```'
        )
        assert parsed["intent"] == "QA"

    def test_code_block_without_lang(self):
        parsed = self.recognizer._extract_json(
            '```\n{"intent":"BUY","confidence":0.7}\n```'
        )
        assert parsed["intent"] == "BUY"

    def test_extra_text_around_json(self):
        parsed = self.recognizer._extract_json(
            '以下是意图识别结果：\n{"intent":"QA","confidence":0.75}\n以上请确认。'
        )
        assert parsed["intent"] == "QA"

    def test_single_quotes_fixed(self):
        parsed = self.recognizer._extract_json(
            "{'intent':'BUY','confidence':0.6}"
        )
        assert parsed["intent"] == "BUY"

    def test_trailing_comma_fixed(self):
        parsed = self.recognizer._extract_json(
            '{"intent":"BUY","confidence":0.5,}'
        )
        assert parsed["intent"] == "BUY"


# ---- 规则式兜底 ----

class TestFallback:
    def test_buy_keywords(self):
        r = IntentResult.fallback("我想买金柚送礼200元")
        assert r.intent == "BUY"
        assert r.confidence == 0.30
        assert r.constraints.get("budget_max") == 200

    def test_qa_keywords(self):
        r = IntentResult.fallback("金柚怎么保存比较好")
        assert r.intent == "QA"

    def test_tie_goes_to_qa(self):
        """平局默认 QA"""
        r = IntentResult.fallback("推荐 怎么保存")
        assert r.intent == "QA"

    def test_no_keyword_match(self):
        r = IntentResult.fallback("你好")
        assert r.intent == "QA"

    def test_budget_extraction(self):
        r = IntentResult.fallback("300元预算买金柚")
        assert r.constraints.get("budget_max") == 300


# ---- UserDemand 构造 ----

class TestUserDemand:
    def test_from_buy_intent(self):
        intent = IntentResult(intent="BUY", confidence=0.9,
                             constraints={"budget_max": 200, "scene": "中秋送礼",
                                          "recipient": "亲友", "budget_min": None,
                                          "spec_preference": None, "quantity": None},
                             culture_tags=["客家", "中秋"], keywords=["送礼", "金柚"])
        demand = UserDemand.from_intent_result("200元中秋送礼", intent)
        assert demand.intent == "BUY"
        assert demand.budget_max == 200
        assert demand.scene == "中秋送礼"
        assert demand.recipient == "亲友"

    def test_from_qa_intent(self):
        intent = IntentResult(intent="QA", confidence=0.85,
                             constraints={}, culture_tags=[], keywords=["保存"])
        demand = UserDemand.from_intent_result("金柚怎么保存", intent)
        assert demand.intent == "QA"
        assert demand.budget_max is None


# ---- Prompt模板组装 ----

class TestPromptAssembly:
    def setup_method(self):
        self.recognizer = IntentRecognizer()

    def test_assemble_replaces_user_input(self):
        template = "用户说：{{user_input}}\n请分类。"
        result = self.recognizer._assemble_user_prompt(template, "推荐金柚")
        assert "推荐金柚" in result
        assert "{{user_input}}" not in result

    def test_assemble_replaces_query(self):
        template = "问题：{{query}}"
        result = self.recognizer._assemble_user_prompt(template, "怎么保存")
        assert "怎么保存" in result
        assert "{{query}}" not in result


# ---- 空输入处理 ----

class TestEmptyInput:
    def setup_method(self):
        self.recognizer = IntentRecognizer()

    def test_empty_string(self):
        result = self.recognizer.recognize("")
        assert result.intent == "QA"
        assert result.confidence == 0.0

    def test_whitespace_only(self):
        result = self.recognizer.recognize("   ")
        assert result.intent == "QA"
        assert result.confidence == 0.0
