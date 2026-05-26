"""
客家金柚AI智荐系统 - AI算法层
提供大模型调用适配、意图识别、融合推荐排序、智能问答解析等核心AI能力。
"""

from .llm_adapter import LLMAdapter, create_adapter
from .intent_recognizer import IntentRecognizer, IntentResult
from .fusion_ranker import (
    FusionRanker,
    PomeloCandidate,
    UserDemand,
    ScoredCandidate,
    parse_candidates_from_rows,
)
from .config import Config
from .exceptions import (
    LLMException,
    LLMTimeoutException,
    LLMRateLimitException,
    LLMAuthException,
    IntentParseException,
)
