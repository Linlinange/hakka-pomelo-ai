"""
演示脚本：验证融合推荐排序全流程（无 API Key 时走纯规则打分）
使用方式：在 Desktop/123/ 目录下执行 `python -m ai_layer.demo_fusion`
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

from ai_layer.intent_recognizer import IntentRecognizer
from ai_layer.fusion_ranker import (
    FusionRanker, PomeloCandidate, UserDemand, parse_candidates_from_rows,
)


def build_mock_candidates() -> list[PomeloCandidate]:
    """构造 8 款梅州客家金柚模拟数据"""
    rows = [
        {"id": 1, "pomelo_name": "梅县松口沙田柚·金奖优选", "category": "沙田柚",
         "origin": "梅州市梅县区松口镇", "specification": "6粒装礼盒/约7.5kg",
         "weight_range": "1.2kg-1.5kg/颗", "price_range": "88-128元/箱",
         "taste_description": "清甜化渣、蜜香浓郁、回甘持久",
         "hakka_culture_relation": "松口是客家人下南洋的起点，沙田柚随客家人远渡重洋名扬海外，中秋赏月必备",
         "gift_scene_tags": "中秋送礼,春节年货,团圆家宴,探亲访友",
         "tags": "金奖,送礼首选,非遗工艺,松口古镇",
         "score_requirement_match": 8.5, "score_scene_fit": 9.0, "score_hakka_feature": 9.5},

        {"id": 2, "pomelo_name": "大埔蜜柚·生态红肉", "category": "蜜柚",
         "origin": "梅州市大埔县", "specification": "4粒装/约5kg",
         "weight_range": "1.0kg-1.4kg/颗", "price_range": "45-68元/箱",
         "taste_description": "果肉绯红、酸甜适口、汁水丰盈",
         "hakka_culture_relation": "大埔是客家香格里拉，红肉蜜柚象征客家人热情好客的红心",
         "gift_scene_tags": "日常送礼,尝鲜自用,家庭分享",
         "tags": "高性价比,红肉,生态种植,大埔",
         "score_requirement_match": 7.0, "score_scene_fit": 6.5, "score_hakka_feature": 7.0},

        {"id": 3, "pomelo_name": "梅州金柚·客家情礼盒", "category": "沙田柚",
         "origin": "梅州市梅江区", "specification": "2粒精品装/约2.8kg",
         "weight_range": "1.3kg-1.6kg/颗", "price_range": "68-98元/盒",
         "taste_description": "果肉晶莹、蜜甜无渣、香气馥郁",
         "hakka_culture_relation": "梅江是客家文化发祥地，金柚承载客家人'以柚待客'的千年礼仪传统",
         "gift_scene_tags": "商务送礼,中秋送礼,高端伴手礼",
         "tags": "精品,客家礼仪,商务,梅江",
         "score_requirement_match": 9.0, "score_scene_fit": 8.5, "score_hakka_feature": 9.0},

        {"id": 4, "pomelo_name": "兴宁金柚·客家手信", "category": "沙田柚",
         "origin": "梅州市兴宁市", "specification": "8粒家庭装/约10kg",
         "weight_range": "1.1kg-1.4kg/颗", "price_range": "99-158元/箱",
         "taste_description": "果肉紧实、甜中带微酸、柚香持久",
         "hakka_culture_relation": "兴宁素有'文化之乡'美誉，金柚是客家人围龙屋里待客必备的手信",
         "gift_scene_tags": "家庭分享,春节年货,探亲访友",
         "tags": "家庭装,手信,实惠,兴宁围龙屋",
         "score_requirement_match": 7.5, "score_scene_fit": 7.0, "score_hakka_feature": 8.0},

        {"id": 5, "pomelo_name": "五华高山柚·有机认证", "category": "沙田柚",
         "origin": "梅州市五华县", "specification": "4粒装/约5.2kg",
         "weight_range": "1.2kg-1.5kg/颗", "price_range": "108-168元/箱",
         "taste_description": "高山清泉灌溉、果肉细腻、冰糖甜",
         "hakka_culture_relation": "五华是石匠之乡，高山柚吸收云雾精华，客家人称其为'山珍柚'",
         "gift_scene_tags": "高端送礼,养生送礼,中秋送礼",
         "tags": "有机,高山,送礼,五华",
         "score_requirement_match": 8.0, "score_scene_fit": 8.0, "score_hakka_feature": 8.5},

        {"id": 6, "pomelo_name": "丰顺温泉柚·温润佳品", "category": "蜜柚",
         "origin": "梅州市丰顺县", "specification": "6粒装/约6.5kg",
         "weight_range": "1.0kg-1.3kg/颗", "price_range": "58-88元/箱",
         "taste_description": "温泉滋养、果肉柔嫩、清甜温润",
         "hakka_culture_relation": "丰顺温泉闻名粤东，柚树得温泉地热滋养，客家人认为此柚有'暖身养气'之效",
         "gift_scene_tags": "养生送礼,日常自用,孝敬长辈",
         "tags": "温泉,养生,孝敬,丰顺",
         "score_requirement_match": 7.0, "score_scene_fit": 7.5, "score_hakka_feature": 7.5},

        {"id": 7, "pomelo_name": "蕉岭富硒柚·长寿之乡", "category": "沙田柚",
         "origin": "梅州市蕉岭县", "specification": "6粒精品装/约7kg",
         "weight_range": "1.1kg-1.4kg/颗", "price_range": "78-118元/箱",
         "taste_description": "富硒土壤培育、清甜爽脆、回味悠长",
         "hakka_culture_relation": "蕉岭是世界长寿乡，富硒水土养育的金柚被客家人视为'长寿果'",
         "gift_scene_tags": "孝敬长辈,养生送礼,中秋送礼,春节年货",
         "tags": "富硒,长寿乡,养生,蕉岭",
         "score_requirement_match": 8.5, "score_scene_fit": 8.5, "score_hakka_feature": 9.0},

        {"id": 8, "pomelo_name": "平远慈柚·客家福果", "category": "沙田柚",
         "origin": "梅州市平远县", "specification": "4粒福运装/约5kg",
         "weight_range": "1.2kg-1.5kg/颗", "price_range": "68-98元/箱",
         "taste_description": "果肉蜜甜、入口即化、柚香绵长",
         "hakka_culture_relation": "平远客家人称金柚为'慈柚'，寓意慈母之爱、福运绵长，是客家人表达感恩的佳品",
         "gift_scene_tags": "孝敬父母,感恩送礼,家庭团聚,中秋",
         "tags": "慈柚,福果,感恩,平远",
         "score_requirement_match": 8.0, "score_scene_fit": 9.0, "score_hakka_feature": 9.5},
    ]
    return parse_candidates_from_rows(rows)


def demo():
    print("=" * 66)
    print("客家金柚AI智荐系统 — 融合推荐排序算法演示")
    print("=" * 66)

    # 构造数据
    candidates = build_mock_candidates()
    print(f"\n候选金柚: {len(candidates)} 款")

    # 模拟意图识别
    query = "200元预算中秋送客家亲友什么金柚好？"
    recognizer = IntentRecognizer()
    intent_result = recognizer.recognize(query)
    demand = UserDemand.from_intent_result(query, intent_result)

    print(f"用户Query: {query}")
    print(f"意图: {demand.intent}  预算: {demand.budget_min}-{demand.budget_max}")
    print(f"场景: {demand.scene}  对象: {demand.recipient}")
    print(f"客家标签: {demand.culture_tags}  关键词: {demand.keywords}")

    # 执行融合推荐
    ranker = FusionRanker()
    results = ranker.rank(demand, candidates)

    # 输出结果
    print(f"\n{'排名':<4} {'品名':<22} {'价格':<12} {'规则分':<7} {'LLM分':<7} {'融合分':<7} {'产地'}")
    print("-" * 85)
    for i, s in enumerate(results, 1):
        c = s.candidate
        print(f"{i:<4} {c.name:<22} {c.price_range:<12} "
              f"{s.rule_total:<7.2f} {s.llm_score:<7.1f} {s.final_score:<7.1f} {c.origin}")

    # Top-3 推荐理由
    print(f"\n{'=' * 66}")
    print("Top-3 个性化推荐理由")
    print("=" * 66)
    top3 = results[:3]
    for i, s in enumerate(top3, 1):
        print(f"\n  [{i}] {s.candidate.name}  (融合分: {s.final_score:.1f})")
        print(f"      规则得分: 价格{s.score_price_match:.1f}  场景{s.score_scene_fit:.1f}  客家{s.score_hakka_feature:.1f}")
        if s.reason:
            print(f"      推荐理由: {s.reason}")
        else:
            print(f"      推荐理由: (LLM未生成，需配置API Key)")

    print(f"\n{'=' * 66}")
    print("演示完成。设置 DEEPSEEK_API_KEY 后可走完整大模型增强链路。")
    print("=" * 66)


if __name__ == "__main__":
    demo()
