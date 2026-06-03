"""
演示脚本：验证融合推荐排序全流程（无 API Key 时走纯规则打分）
使用方式：在 Desktop/123/ 目录下执行 `python -m ai_layer.demo_fusion`
"""
from __future__ import annotations
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

from ai_layer.intent_recognizer import IntentRecognizer
from ai_layer.fusion_ranker import (
    FusionRanker, ProductCandidate, UserDemand, parse_candidates_from_rows,
)


def build_mock_candidates() -> list[ProductCandidate]:
    """构造包含多品类水果的模拟数据（金柚 + 苹果 + 香蕉 + 西瓜）"""
    rows = [
        # --- 金柚（pomelo）4 款 ---
        {"id": 1, "product_type": "pomelo", "pomelo_name": "梅县松口沙田柚·金奖优选", "category": "沙田柚",
         "origin": "梅州市梅县区松口镇", "specification": "6粒装礼盒/约7.5kg",
         "weight_range": "1.2kg-1.5kg/颗", "price_range": "88-128元/箱",
         "taste_description": "清甜化渣、蜜香浓郁、回甘持久",
         "hakka_culture_relation": "松口是客家人下南洋的起点，沙田柚随客家人远渡重洋名扬海外，中秋赏月必备",
         "gift_scene_tags": "中秋送礼,春节年货,团圆家宴,探亲访友",
         "tags": "金奖,送礼首选,非遗工艺,松口古镇",
         "score_requirement_match": 8.5, "score_scene_fit": 9.0, "score_hakka_feature": 9.5, "score_product_feature": 5.0},

        {"id": 2, "product_type": "pomelo", "pomelo_name": "大埔蜜柚·生态红肉", "category": "蜜柚",
         "origin": "梅州市大埔县", "specification": "4粒装/约5kg",
         "weight_range": "1.0kg-1.4kg/颗", "price_range": "45-68元/箱",
         "taste_description": "果肉绯红、酸甜适口、汁水丰盈",
         "hakka_culture_relation": "大埔是客家香格里拉，红肉蜜柚象征客家人热情好客的红心",
         "gift_scene_tags": "日常送礼,尝鲜自用,家庭分享",
         "tags": "高性价比,红肉,生态种植,大埔",
         "score_requirement_match": 7.0, "score_scene_fit": 6.5, "score_hakka_feature": 7.0, "score_product_feature": 5.0},

        {"id": 3, "product_type": "pomelo", "pomelo_name": "梅州金柚·客家情礼盒", "category": "沙田柚",
         "origin": "梅州市梅江区", "specification": "2粒精品装/约2.8kg",
         "weight_range": "1.3kg-1.6kg/颗", "price_range": "68-98元/盒",
         "taste_description": "果肉晶莹、蜜甜无渣、香气馥郁",
         "hakka_culture_relation": "梅江是客家文化发祥地，金柚承载客家人'以柚待客'的千年礼仪传统",
         "gift_scene_tags": "商务送礼,中秋送礼,高端伴手礼",
         "tags": "精品,客家礼仪,商务,梅江",
         "score_requirement_match": 9.0, "score_scene_fit": 8.5, "score_hakka_feature": 9.0, "score_product_feature": 5.0},

        {"id": 4, "product_type": "pomelo", "pomelo_name": "平远慈柚·客家福果", "category": "沙田柚",
         "origin": "梅州市平远县", "specification": "4粒福运装/约5kg",
         "weight_range": "1.2kg-1.5kg/颗", "price_range": "68-98元/箱",
         "taste_description": "果肉蜜甜、入口即化、柚香绵长",
         "hakka_culture_relation": "平远客家人称金柚为'慈柚'，寓意慈母之爱、福运绵长",
         "gift_scene_tags": "孝敬父母,感恩送礼,家庭团聚,中秋",
         "tags": "慈柚,福果,感恩,平远",
         "score_requirement_match": 8.0, "score_scene_fit": 9.0, "score_hakka_feature": 9.5, "score_product_feature": 5.0},

        # --- 苹果（apple）2 款 ---
        {"id": 5, "product_type": "apple", "pomelo_name": "洛川红富士·冰糖心", "category": "红富士",
         "origin": "陕西洛川", "specification": "12粒装/约5kg",
         "weight_range": "0.3kg-0.5kg/颗", "price_range": "59-89元/箱",
         "taste_description": "果肉黄白、细脆多汁、冰糖心蜜甜、香气浓郁",
         "product_description": "洛川红富士苹果，国家地理标志产品，海拔1100米高原种植，昼夜温差大造就冰糖心",
         "gift_scene_tags": "送礼佳品,年货,看望长辈",
         "tags": "冰糖心,地理标志,红富士,陕西特产",
         "score_requirement_match": 8.0, "score_scene_fit": 7.5, "score_hakka_feature": 1.0, "score_product_feature": 9.0},

        {"id": 6, "product_type": "apple", "pomelo_name": "阿克苏苹果·天山雪水", "category": "红富士",
         "origin": "新疆阿克苏", "specification": "10粒装/约5kg",
         "weight_range": "0.4kg-0.6kg/颗", "price_range": "78-118元/箱",
         "taste_description": "果面光滑、果肉细腻、甜酸适口、汁多酥脆",
         "product_description": "阿克苏苹果生长于天山南麓，引用天山雪水灌溉，光照充足，果实着色好、糖分高",
         "gift_scene_tags": "高端送礼,中秋送礼,年货",
         "tags": "新疆,天山雪水,冰糖心,高端",
         "score_requirement_match": 7.5, "score_scene_fit": 8.0, "score_hakka_feature": 1.0, "score_product_feature": 8.5},

        # --- 香蕉（banana）2 款 ---
        {"id": 7, "product_type": "banana", "pomelo_name": "海南贵妃蕉·树上熟", "category": "贵妃蕉",
         "origin": "海南三亚", "specification": "5把装/约3kg",
         "weight_range": "0.1kg-0.2kg/根", "price_range": "29-49元/箱",
         "taste_description": "果皮薄如纸、果肉软糯香甜、略带淡淡果酸",
         "product_description": "海南贵妃蕉，树上自然成熟，皮薄肉厚，甜度高，口感细腻柔滑，营养丰富",
         "gift_scene_tags": "日常自用,家庭分享,早餐水果",
         "tags": "海南,树上熟,贵妃蕉,软糯香甜",
         "score_requirement_match": 6.5, "score_scene_fit": 6.0, "score_hakka_feature": 1.0, "score_product_feature": 8.0},

        {"id": 8, "product_type": "banana", "pomelo_name": "广西小米蕉·有机种植", "category": "小米蕉",
         "origin": "广西南宁", "specification": "6把装/约3.5kg",
         "weight_range": "0.08kg-0.15kg/根", "price_range": "25-45元/箱",
         "taste_description": "果型小巧、果肉细腻、甜度极高、入口即化",
         "product_description": "广西小米蕉，有机种植认证，果型小巧玲珑，皮薄肉厚，甜度比普通香蕉高出30%",
         "gift_scene_tags": "儿童水果,日常自用,健康零食",
         "tags": "有机,小米蕉,广西特产,高甜",
         "score_requirement_match": 7.0, "score_scene_fit": 6.5, "score_hakka_feature": 1.0, "score_product_feature": 7.5},

        # --- 西瓜（watermelon）2 款 ---
        {"id": 9, "product_type": "watermelon", "pomelo_name": "宁夏硒砂瓜·石头缝里长出的瓜", "category": "硒砂瓜",
         "origin": "宁夏中卫", "specification": "1个装/约8-12kg",
         "weight_range": "8kg-12kg/个", "price_range": "38-68元/个",
         "taste_description": "果肉鲜红、汁多味甜、沙脆爽口、富含硒元素",
         "product_description": "宁夏硒砂瓜生长于砂石覆盖的旱地，独特的气候和土壤条件使其富含硒元素，有'戈壁西瓜'美誉",
         "gift_scene_tags": "消暑佳品,夏至送礼,家庭分享",
         "tags": "硒砂瓜,宁夏,富硒,消暑",
         "score_requirement_match": 7.5, "score_scene_fit": 8.5, "score_hakka_feature": 1.0, "score_product_feature": 8.5},

        {"id": 10, "product_type": "watermelon", "pomelo_name": "海南麒麟瓜·早春红玉", "category": "麒麟瓜",
         "origin": "海南文昌", "specification": "2个装/约5-7kg",
         "weight_range": "2.5kg-3.5kg/个", "price_range": "45-79元/箱",
         "taste_description": "皮薄肉厚、瓤红汁多、清甜爽口、口感酥脆",
         "product_description": "海南麒麟瓜，大棚早春种植，皮薄可食用率高，肉质酥脆，是夏季消暑水果的首选",
         "gift_scene_tags": "消暑必备,夏季送礼,野餐聚会",
         "tags": "麒麟瓜,海南,早春红玉,皮薄多汁",
         "score_requirement_match": 8.0, "score_scene_fit": 9.0, "score_hakka_feature": 1.0, "score_product_feature": 8.0},
    ]
    return parse_candidates_from_rows(rows)


def demo():
    print("=" * 66)
    print("客家金柚AI智荐系统 — 融合推荐排序算法演示（V2.0 多品类）")
    print("=" * 66)

    # 构造数据
    candidates = build_mock_candidates()
    print(f"\n候选产品: {len(candidates)} 款（多品类混合）")
    for c in candidates:
        type_label = {"pomelo": "金柚", "apple": "苹果", "banana": "香蕉", "watermelon": "西瓜"}
        print(f"  [{type_label.get(c.product_type, c.product_type):>4}] {c.name}")

    # 测试1：金柚推荐
    query1 = "200元预算中秋送客家亲友什么好？"
    recognizer = IntentRecognizer()
    intent_result = recognizer.recognize(query1)
    demand1 = UserDemand.from_intent_result(query1, intent_result)

    print(f"\n{'=' * 66}")
    print(f"测试场景1: 金柚推荐")
    print(f"Query: {query1}")
    print(f"意图: {demand1.intent}")
    print(f"=" * 66)

    ranker = FusionRanker()
    results1 = ranker.rank(demand1, candidates)

    print(f"\n{'排名':<4} {'品类':<6} {'品名':<24} {'规则分':<7} {'融合分':<7} {'产地'}")
    print("-" * 70)
    for i, s in enumerate(results1, 1):
        c = s.candidate
        t = {"pomelo": "金柚", "apple": "苹果", "banana": "香蕉", "watermelon": "西瓜"}
        print(f"{i:<4} {t.get(c.product_type, c.product_type):<6} {c.name:<24} "
              f"{s.rule_total:<7.2f} {s.final_score:<7.1f} {c.origin}")

    print(f"\nTop-3 推荐理由:")
    for i, s in enumerate(results1[:3], 1):
        c = s.candidate
        dim_label = "客家特色" if c.product_type == "pomelo" else "产品特色"
        print(f"  [{i}] {c.name}")
        print(f"      规则: 价格{s.score_price_match:.1f}  场景{s.score_scene_fit:.1f}  {dim_label}{s.score_third_dimension:.1f}")
        if s.reason:
            print(f"      理由: {s.reason}")
        else:
            print(f"      理由: (LLM未生成)")

    # 测试2：夏季消暑推荐（应该优先推西瓜）
    query2 = "夏天消暑解渴的水果推荐"
    intent_result2 = recognizer.recognize(query2)
    demand2 = UserDemand.from_intent_result(query2, intent_result2)

    print(f"\n{'=' * 66}")
    print(f"测试场景2: 夏季消暑推荐")
    print(f"Query: {query2}")
    print(f"意图: {demand2.intent}")
    print(f"=" * 66)

    results2 = ranker.rank(demand2, candidates)

    print(f"\n{'排名':<4} {'品类':<6} {'品名':<24} {'规则分':<7} {'融合分':<7} {'产地'}")
    print("-" * 70)
    for i, s in enumerate(results2, 1):
        c = s.candidate
        t = {"pomelo": "金柚", "apple": "苹果", "banana": "香蕉", "watermelon": "西瓜"}
        print(f"{i:<4} {t.get(c.product_type, c.product_type):<6} {c.name:<24} "
              f"{s.rule_total:<7.2f} {s.final_score:<7.1f} {c.origin}")

    # 测试3：送礼推荐（混合品类）
    query3 = "100元左右送礼推荐什么水果？"
    intent_result3 = recognizer.recognize(query3)
    demand3 = UserDemand.from_intent_result(query3, intent_result3)

    print(f"\n{'=' * 66}")
    print(f"测试场景3: 混合品类送礼推荐")
    print(f"Query: {query3}")
    print(f"意图: {demand3.intent}")
    print(f"=" * 66)

    results3 = ranker.rank(demand3, candidates)

    print(f"\n{'排名':<4} {'品类':<6} {'品名':<24} {'规则分':<7} {'融合分':<7} {'产地'}")
    print("-" * 70)
    for i, s in enumerate(results3, 1):
        c = s.candidate
        t = {"pomelo": "金柚", "apple": "苹果", "banana": "香蕉", "watermelon": "西瓜"}
        print(f"{i:<4} {t.get(c.product_type, c.product_type):<6} {c.name:<24} "
              f"{s.rule_total:<7.2f} {s.final_score:<7.1f} {c.origin}")

    print(f"\n{'=' * 66}")
    print("演示完成。设置 DEEPSEEK_API_KEY 后可走完整大模型增强链路。")
    print("=" * 66)


if __name__ == "__main__":
    demo()
