"""
演示脚本：验证意图识别全流程（无需真实 API Key 也可运行，会走兜底逻辑）
使用方式：在 ai_layer 目录下执行 `python demo.py`
"""

import os
import sys

# 将父目录加入路径，使 ai_layer 能作为包导入
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

from ai_layer.llm_adapter import create_adapter
from ai_layer.intent_recognizer import IntentRecognizer


def demo():
    print("=" * 60)
    print("客家金柚AI智荐系统 — 意图识别模块演示")
    print("=" * 60)

    # 创建适配器（无有效 API Key 时，invoke 会失败 → 走 rule-based fallback）
    adapter = create_adapter("chatglm")
    recognizer = IntentRecognizer(adapter=adapter)

    test_cases = [
        "200元预算中秋送客家亲友什么金柚好？",
        "梅州沙田柚和蜜柚有什么区别？",
        "金柚皮怎么制作客家菜？",
        "想买两箱金柚送领导，1000以内，包装要好",
        "冬天金柚怎么保存不容易坏？",
        "帮我推荐一款适合团圆饭吃的金柚",
    ]

    for i, query in enumerate(test_cases, 1):
        print(f"\n--- 测试 {i}: {query}")
        result = recognizer.recognize(query)
        print(f"    意图: {result.intent}  置信度: {result.confidence:.2f}")
        print(f"    约束: {result.constraints}")
        print(f"    客家标签: {result.culture_tags}")
        print(f"    关键词: {result.keywords}")
        print(f"    需二次确认: {result.needs_confirm}")
        print(f"    耗时: {result.response_time_ms}ms")
        if result.error:
            print(f"    [fallback原因] {result.error}")

    print("\n" + "=" * 60)
    print("演示完成。设置环境变量 CHATGLM_API_KEY 后可走真实大模型链路。")
    print("=" * 60)


if __name__ == "__main__":
    demo()
