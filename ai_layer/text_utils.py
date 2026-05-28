"""
中文文本处理工具模块
基于 jieba 分词 + TF-IDF 进行关键词提取和分词
"""

import logging
import jieba
import jieba.analyse

logger = logging.getLogger(__name__)

# 中文停用词表
_STOP_WORDS = set([
    "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一",
    "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着",
    "没有", "看", "好", "自己", "这", "他", "她", "它", "们", "那", "些",
    "什么", "怎么", "如何", "为什么", "哪", "吗", "呢", "吧", "啊", "哦",
    "可以", "这个", "那个", "还是", "只是", "但是", "而且", "所以", "因为",
    "如果", "虽然", "不过", "然后", "已经", "正在", "将", "把", "被", "让",
    "从", "对", "与", "或", "及", "向", "为", "以", "之", "其", "于",
    "请问", "帮忙", "推荐", "谢谢", "麻烦", "需要", "想要", "希望",
])

def segment(text: str) -> list[str]:
    """对中文文本进行分词，去除停用词和单字"""
    if not text or not text.strip():
        return []
    words = jieba.cut(text.strip())
    return [
        w.strip() for w in words
        if w.strip() and len(w.strip()) >= 2 and w.strip() not in _STOP_WORDS
    ]


def extract_keywords(text: str, topk: int = 5) -> list[str]:
    """
    提取中文文本的关键词。
    优先使用 TF-IDF，若结果不足则回退到 TextRank。
    """
    if not text or not text.strip():
        return []

    try:
        # TF-IDF 提取
        keywords = jieba.analyse.extract_tags(text, topK=topk, withWeight=False)
        # 过滤停用词
        keywords = [k for k in keywords if k not in _STOP_WORDS and len(k) >= 2]
        if keywords:
            return keywords[:topk]
    except Exception as e:
        logger.warning("TF-IDF关键词提取失败: %s，尝试TextRank", e)

    try:
        # TextRank 降级
        keywords = jieba.analyse.textrank(text, topK=topk, withWeight=False)
        keywords = [k for k in keywords if k not in _STOP_WORDS and len(k) >= 2]
        return keywords[:topk]
    except Exception as e:
        logger.warning("TextRank关键词提取也失败: %s，返回分词结果", e)
        return segment(text)[:topk]
