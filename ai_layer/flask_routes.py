"""
Flask API 路由模块
- POST /api/recommend    AI智荐推荐
- POST /api/qa           智能问答
- POST /api/intent       意图识别（独立）
- GET  /api/health        健康检查
"""

import traceback
import logging
from flask import Blueprint, request

_log = logging.getLogger(__name__)

from .flask_utils import ok, fail, bad_request, require_fields, log_request
from .intent_recognizer import IntentRecognizer
from .fusion_ranker import (
    FusionRanker,
    PomeloCandidate,
    UserDemand,
    ScoredCandidate,
    parse_candidates_from_rows,
)
from .llm_adapter import create_adapter

# ---------------------------------------------------------------------------
# Blueprint
# ---------------------------------------------------------------------------

api_bp = Blueprint("api", __name__, url_prefix="/api")

# 全局实例（由 app.py 初始化后注入，避免每次请求重复创建）
_intent_recognizer = None
_fusion_ranker = None
_qa_adapter = None


def init_services():
    """初始化 AI 服务实例（在 Flask app 启动时调用）"""
    global _intent_recognizer, _fusion_ranker, _qa_adapter
    _intent_recognizer = IntentRecognizer()
    _fusion_ranker = FusionRanker()
    _qa_adapter = create_adapter()


# ---------------------------------------------------------------------------
# 1. 推荐接口
# ---------------------------------------------------------------------------

@api_bp.route("/recommend", methods=["POST"])
@log_request
@require_fields("user_query")
def recommend():
    """
    AI智荐推荐接口。

    请求体:
        {
            "user_query": "200元中秋送礼客家亲友什么金柚好？",
            "candidates": [ ... ]   // 可选，Spring Boot 从 MySQL 召回的候选金柚列表
        }

    返回:
        {
            "code": 200,
            "data": {
                "intent": {"intent": "BUY", "confidence": 0.95, "constraints": {...}, ...},
                "recommendations": [ {pomelo字段..., score_*, reason, ...}, ... ]
            }
        }
    """
    try:
        body = request.get_json()
        user_query = body["user_query"].strip()
        raw_candidates = body.get("candidates", [])

        # 1. 意图识别
        intent_result = _intent_recognizer.recognize(user_query)
        demand = UserDemand.from_intent_result(user_query, intent_result)

        # 2. 解析候选金柚
        if raw_candidates:
            normalized = [_normalize_candidate_fields(c) for c in raw_candidates]
            candidates = parse_candidates_from_rows(normalized)

            # 3a. 有候选 → 融合推荐排序
            scored_list = _fusion_ranker.rank(demand, candidates)
            recommendations = [_scored_to_dict(s) for s in scored_list]

            return ok({
                "intent": intent_result.to_dict(),
                "recommendations": recommendations,
                "count": len(recommendations),
            })
        else:
            # 3b. 无候选 → LLM 自由对话（结合意图识别结果）
            answer = _free_chat_recommend(user_query, intent_result)
            return ok({
                "intent": intent_result.to_dict(),
                "recommendations": [],
                "count": 0,
                "answer": answer,
            })

    except Exception:
        traceback.print_exc()
        return fail(500, f"推荐服务异常: {traceback.format_exc()[-200:]}")


# ---------------------------------------------------------------------------
# 2. 智能问答接口
# ---------------------------------------------------------------------------

@api_bp.route("/qa", methods=["POST"])
@log_request
@require_fields("question")
def qa():
    """
    智能问答接口。

    请求体:
        {
            "question": "金柚皮怎么制作客家菜？",
            "knowledge_context": "从知识库检索到的相关文本（可选）",
            "session_id": "abc123"
        }

    返回:
        {
            "code": 200,
            "data": {
                "answer": "...",
                "source": "knowledge_base | llm | fallback",
                "session_id": "abc123"
            }
        }
    """
    try:
        body = request.get_json()
        question = body["question"].strip()
        knowledge_context = body.get("knowledge_context", "")
        session_id = body.get("session_id", "")

        # 1. 意图识别
        intent_result = _intent_recognizer.recognize(question)

        # 2. 知识库匹配 → 直接返回
        if knowledge_context and len(knowledge_context.strip()) > 20:
            return ok({
                "answer": _format_knowledge_answer(question, knowledge_context),
                "source": "knowledge_base",
                "intent": intent_result.to_dict(),
                "session_id": session_id,
            })

        # 3. 知识库未命中 → 调用大模型
        llm_answer = _call_llm_for_qa(question, knowledge_context, intent_result)
        return ok({
            "answer": llm_answer,
            "source": "llm",
            "intent": intent_result.to_dict(),
            "session_id": session_id,
        })

    except Exception:
        traceback.print_exc()
        return fail(500, f"问答服务异常: {traceback.format_exc()[-200:]}")


# ---------------------------------------------------------------------------
# 3. 意图识别接口（独立，供调试/预检）
# ---------------------------------------------------------------------------

@api_bp.route("/intent", methods=["POST"])
@log_request
@require_fields("query")
def intent():
    """
    意图识别独立接口。

    请求体: {"query": "200元中秋送礼客家亲友"}
    返回:   {"code": 200, "data": { intent识别结果 }}
    """
    try:
        body = request.get_json()
        query = body["query"].strip()
        result = _intent_recognizer.recognize(query)
        return ok(result.to_dict())
    except Exception:
        traceback.print_exc()
        return fail(500, f"意图识别异常: {traceback.format_exc()[-200:]}")


# ---------------------------------------------------------------------------
# 4. 内容生成接口
# ---------------------------------------------------------------------------

# 内容生成专用 adapter（较高温度，偏创意）
_content_adapter = None


def _get_content_adapter():
    global _content_adapter
    if _content_adapter is None:
        _content_adapter = create_adapter()
    return _content_adapter


CONTENT_PROMPTS = {
    "ecommerce": (
        "你是梅州客家金柚的资深电商文案策划师，擅长撰写吸引人的商品详情页文案。"
        "请用温暖、有客家文化底蕴的语言，突出金柚的产地、口感、营养价值和文化故事。"
        "文案需包含标题、卖点分点（3-4点）和结尾引导语，控制在200字以内。"
    ),
    "social": (
        "你是梅州客家金柚的品牌推广达人，擅长写微信朋友圈/小红书的种草推文。"
        "请用亲切、生活化的语气，配适当emoji，突出金柚的亮点和客家文化特色。"
        "文案需有感染力，适合社交分享，控制在150字以内。"
    ),
}


@api_bp.route("/content", methods=["POST"])
@log_request
@require_fields("scene")
def generate_content():
    """
    内容生成接口 —— 生成金柚电商文案或朋友圈推广语。

    请求体:
        {
            "scene": "ecommerce | social",
            "prompt": "可选，自定义内容要求",
            "pomelo_name": "可选，指定金柚品名",
            "style": "可选，文案风格"
        }
    返回:
        {
            "code": 200,
            "data": {
                "content": "生成的文案...",
                "scene": "ecommerce",
                "pomelo_name": "...",
                "created_at": "2026-05-22 17:00:00"
            }
        }
    """
    try:
        body = request.get_json()
        scene = body.get("scene", "social").strip()
        if scene not in ("ecommerce", "social"):
            return bad_request("scene 参数无效，可选值: ecommerce, social")
        custom_prompt = body.get("prompt", "").strip()
        pomelo_name = body.get("pomelo_name", "客家金柚").strip()
        style = body.get("style", "").strip()

        system_prompt = CONTENT_PROMPTS[scene]

        # 构建 user prompt
        parts = [f"请为「{pomelo_name}」撰写一段{'电商详情页文案' if scene == 'ecommerce' else '朋友圈推广文案'}。"]
        if custom_prompt:
            parts.append(f"额外要求：{custom_prompt}")
        if style:
            parts.append(f"风格：{style}")
        user_prompt = " ".join(parts)

        # 调用大模型
        adapter = _get_content_adapter()
        result = adapter.invoke(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.85,  # 内容生成用较高温度
            max_tokens=512,
        )

        if result.get("success") and result.get("content"):
            content = result["content"].strip()
        else:
            content = _fallback_content(scene, pomelo_name)

        from datetime import datetime
        return ok({
            "content": content,
            "scene": scene,
            "pomelo_name": pomelo_name,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })

    except Exception:
        traceback.print_exc()
        return fail(500, f"内容生成异常: {traceback.format_exc()[-200:]}")


def _fallback_content(scene: str, pomelo_name: str) -> str:
    """LLM 不可用时的兜底文案"""
    if scene == "ecommerce":
        return (
            f"【客家至味】{pomelo_name}\n\n"
            f"产自梅州核心产区，客家传统农法种植，果肉清甜化渣、蜜香浓郁。"
            f"中秋送礼首选，承载千年客家待客之道。\n\n"
            f"立即选购，品味客家风情！"
        )
    return (
        f"中秋团圆时，怎能少了客家{pomelo_name}？🍊\n"
        f"梅州直发，皮薄肉甜，一口下去满是客家人的热情与祝福～\n"
        f"送亲友、送长辈，这份客家味道，暖胃更暖心🫶\n"
        f"#客家金柚 #中秋送礼 #梅州特产"
    )


# ---- 推荐模式下的自由对话（无候选金柚时） ----

def _free_chat_recommend(user_query: str, intent_result) -> str:
    """
    无候选金柚时，直接用 LLM 进行自然语言推荐对话。
    根据用户意图（选购/知识）调整回答风格。
    """
    intent_type = intent_result.intent
    constraints = intent_result.constraints or {}
    culture_tags = intent_result.culture_tags or []

    # 提取约束信息
    budget = constraints.get("budget_max", "")
    scene = constraints.get("scene", "")
    recipient = constraints.get("recipient", "")

    context_parts = []
    if budget:
        context_parts.append(f"预算约{budget}元")
    if scene:
        context_parts.append(f"场景：{scene}")
    if recipient:
        context_parts.append(f"送礼对象：{recipient}")
    if culture_tags:
        context_parts.append(f"客家文化偏好：{', '.join(culture_tags)}")
    context_str = "，".join(context_parts) if context_parts else "无特殊约束"

    if intent_type == "BUY":
        system_prompt = (
            "你是梅州客家金柚的专业导购顾问，精通各产区金柚的特色与客家文化。\n"
            "你的任务是理解用户的选购需求，给出专业、温暖、有客家味的推荐建议。\n"
            "你可以推荐具体的金柚品类（如沙田柚、蜜柚）、产地（梅县松口、大埔、蕉岭等）、"
            "以及适合的规格和价位。回答要具体、实用，融入客家文化元素。\n"
            "控制在200字以内，语气温暖亲切。"
        )
        user_prompt = (
            f"用户需求：{user_query}\n"
            f"已识别的约束条件：{context_str}\n\n"
            "请根据用户需求，推荐合适的客家金柚品类和选购建议。"
            "可以提到具体的产地特色（梅县松口、大埔、蕉岭、五华、平远、丰顺等梅州产区）、"
            "规格选择和价格参考。请直接给出推荐，不要反问用户。"
        )
    else:
        system_prompt = (
            "你是梅州客家金柚领域的资深专家，精通金柚的营养、保存、辨别、食用搭配和客家文化。\n"
            "请用专业、温暖、有客家味的语言回答用户问题。控制在200字以内。"
        )
        user_prompt = f"用户问题：{user_query}\n\n请直接回答，融入客家文化特色。"

    adapter = _get_content_adapter()
    result = adapter.invoke(
        prompt=user_prompt,
        system_prompt=system_prompt,
        temperature=0.70,
        max_tokens=512,
    )

    if result.get("success") and result.get("content"):
        return result["content"].strip()

    # LLM 调用失败时的兜底 — 根据意图给出不同引导
    if intent_type == "BUY":
        return (
            f"抱歉，AI 暂时无法为您精准推荐「{user_query[:20]}」。\n\n"
            "梅州客家金柚品类丰富：沙田柚清甜化渣适合送礼，蜜柚酸甜可口适合自用，"
            "富硒柚适合孝敬长辈。您可以补充预算、送礼对象等信息，我帮您更精准地挑选～"
        )
    return (
        f"关于「{user_query[:20]}」，建议您查阅梅州客家金柚相关资料。\n"
        "也可以试试问我：金柚怎么保存？沙田柚和蜜柚有什么区别？金柚有什么营养价值？"
    )


# ---------------------------------------------------------------------------
# 5. 知识库只读接口（DB 直连 + 静态兜底）
# ---------------------------------------------------------------------------

# 静态兜底数据（MySQL 不可用时使用）
_STATIC_KNOWLEDGE = [
    {"id":1,"pomelo_name":"梅县松口沙田柚·金奖优选","category":"沙田柚","origin":"梅州市梅县区松口镇","price_range":"88-128元/箱","taste_description":"清甜化渣、蜜香浓郁、回甘持久","hakka_culture_relation":"松口是客家人下南洋的起点，中秋赏月必备","gift_scene_tags":"中秋送礼,春节年货,团圆家宴","tags":"金奖,送礼首选,非遗工艺","image_url":"","score_requirement_match":8.5,"score_scene_fit":9.0,"score_hakka_feature":9.5},
    {"id":2,"pomelo_name":"大埔蜜柚·生态红肉","category":"蜜柚","origin":"梅州市大埔县","price_range":"45-68元/箱","taste_description":"果肉绯红、酸甜适口、汁水丰盈","hakka_culture_relation":"大埔是客家香格里拉，红肉蜜柚象征客家人热情好客","gift_scene_tags":"日常送礼,尝鲜自用,家庭分享","tags":"高性价比,红肉,生态种植","image_url":"","score_requirement_match":7.0,"score_scene_fit":6.5,"score_hakka_feature":7.0},
    {"id":3,"pomelo_name":"梅州金柚·客家情礼盒","category":"沙田柚","origin":"梅州市梅江区","price_range":"68-98元/盒","taste_description":"果肉晶莹、蜜甜无渣、香气馥郁","hakka_culture_relation":"以柚待客千年礼仪传统","gift_scene_tags":"商务送礼,中秋送礼,高端伴手礼","tags":"精品,客家礼仪","image_url":"","score_requirement_match":9.0,"score_scene_fit":8.5,"score_hakka_feature":9.0},
    {"id":4,"pomelo_name":"蕉岭富硒柚·长寿之乡","category":"沙田柚","origin":"梅州市蕉岭县","price_range":"78-118元/箱","taste_description":"清甜爽脆、回味悠长","hakka_culture_relation":"蕉岭是世界长寿乡，富硒金柚被客家人视为长寿果","gift_scene_tags":"孝敬长辈,养生送礼","tags":"富硒,长寿乡,养生","image_url":"","score_requirement_match":8.5,"score_scene_fit":8.5,"score_hakka_feature":9.0},
    {"id":5,"pomelo_name":"五华高山柚·有机认证","category":"沙田柚","origin":"梅州市五华县","price_range":"108-168元/箱","taste_description":"高山清泉灌溉、果肉细腻、冰糖甜","hakka_culture_relation":"五华是石匠之乡，高山柚被客家人称为山珍柚","gift_scene_tags":"高端送礼,养生送礼","tags":"有机,高山,送礼","image_url":"","score_requirement_match":8.0,"score_scene_fit":8.0,"score_hakka_feature":8.5},
    {"id":6,"pomelo_name":"平远慈柚·客家福果","category":"沙田柚","origin":"梅州市平远县","price_range":"68-98元/箱","taste_description":"果肉蜜甜、入口即化、柚香绵长","hakka_culture_relation":"客家人称金柚为慈柚，寓意慈母之爱、福运绵长","gift_scene_tags":"孝敬父母,感恩送礼","tags":"慈柚,福果","image_url":"","score_requirement_match":8.0,"score_scene_fit":9.0,"score_hakka_feature":9.5},
]


def _load_knowledge_from_db():
    """尝试从 MySQL 加载金柚知识库，失败则返回静态数据"""
    try:
        import pymysql
        cfg = get_config()
        conn = pymysql.connect(
            host=cfg.db_host, port=cfg.db_port,
            user=cfg.db_user, password=cfg.db_password,
            database=cfg.db_name, charset="utf8mb4",
            connect_timeout=3,
        )
        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cur:
                cur.execute(
                    "SELECT id, pomelo_name, category, origin, specification, "
                    "price_range, taste_description, hakka_culture_relation, "
                    "gift_scene_tags, tags, image_url, "
                    "score_requirement_match, score_scene_fit, score_hakka_feature "
                    "FROM golden_pomelo_knowledge WHERE status=1 AND is_deleted=0 "
                    "ORDER BY view_count DESC LIMIT 20"
                )
                rows = cur.fetchall()
                if rows:
                    _log.info("从MySQL加载知识库: %d条", len(rows))
                    return rows
        finally:
            conn.close()
    except Exception as exc:
        _log.info("MySQL不可用，使用静态知识库数据: %s", exc)
    return _STATIC_KNOWLEDGE


@api_bp.route("/knowledge", methods=["GET"])
def get_knowledge():
    """获取金柚知识库列表（只读，DB/静态数据自动切换）"""
    return ok(_load_knowledge_from_db())


@api_bp.route("/knowledge/<int:kid>", methods=["GET"])
def get_knowledge_by_id(kid):
    """获取单条知识条目"""
    all_data = _load_knowledge_from_db()
    for item in all_data:
        if item.get("id") == kid:
            return ok(item)
    return not_found("知识条目不存在")


# ---------------------------------------------------------------------------
# 6. 健康检查
# ---------------------------------------------------------------------------

@api_bp.route("/health", methods=["GET"])
def health():
    return ok({"status": "running", "service": "pomelo-ai-layer"})


# ---------------------------------------------------------------------------
# 内部辅助
# ---------------------------------------------------------------------------


# Spring Boot (Jackson) → Python (snake_case) 字段名映射
_CAMEL_TO_SNAKE_MAP = {
    "pomeloName": "pomelo_name", "priceRange": "price_range",
    "tasteDescription": "taste_description", "hakkaCultureRelation": "hakka_culture_relation",
    "giftSceneTags": "gift_scene_tags", "scoreRequirementMatch": "score_requirement_match",
    "scoreSceneFit": "score_scene_fit", "scoreHakkaFeature": "score_hakka_feature",
    "weightRange": "weight_range", "seasonInfo": "season_info",
    "cultivationProcess": "cultivation_process", "identificationTips": "identification_tips",
    "preservationMethod": "preservation_method", "ediblePairing": "edible_pairing",
    "nutritionalValue": "nutritional_value", "storyContent": "story_content",
    "imageUrl": "image_url", "viewCount": "view_count", "recCount": "rec_count",
}


def _normalize_candidate_fields(item: dict) -> dict:
    """将 Spring Boot 传来的 camelCase 字段名转为 snake_case，兼容 parse_candidates_from_rows"""
    normalized = {}
    for key, value in item.items():
        snake_key = _CAMEL_TO_SNAKE_MAP.get(key, key)
        normalized[snake_key] = value
    return normalized


def _scored_to_dict(s: ScoredCandidate) -> dict:
    """将 ScoredCandidate 转为前端可消费的字典"""
    c = s.candidate
    return {
        "id": c.id,
        "pomelo_name": c.name,
        "category": c.category,
        "origin": c.origin,
        "specification": c.specification,
        "weight_range": c.weight_range,
        "price_range": c.price_range,
        "taste_description": c.taste_description,
        "hakka_culture_relation": c.hakka_culture_relation,
        "gift_scene_tags": c.gift_scene_tags,
        "tags": c.tags,
        "image_url": getattr(c, "image_url", ""),
        # 打分明细
        "score_price_match": round(s.score_price_match, 2),
        "score_scene_fit": round(s.score_scene_fit, 2),
        "score_hakka_feature": round(s.score_hakka_feature, 2),
        "rule_total": round(s.rule_total, 2),
        "llm_score": round(s.llm_score, 1),
        "final_score": round(s.final_score, 1),
        "reason": s.reason,
    }


def _format_knowledge_answer(question: str, context: str) -> str:
    """将知识库检索结果格式化为自然语言回答"""
    return (
        f"根据客家金柚知识库，关于「{question}」的相关信息如下：\n\n"
        f"{context}\n\n"
        f"如需更多帮助，请进一步描述您的问题。"
    )


def _call_llm_for_qa(question: str, knowledge_context: str, intent_result) -> str:
    """
    调用大模型生成问答答案。
    传入知识库上下文作为参考，让 LLM 结合金柚专业知识作答。
    """
    system_prompt = (
        "你是梅州客家金柚领域的资深专家，精通金柚的营养、保存、辨别、食用搭配、"
        "客家文化典故和种植工艺。请用温暖、专业、有客家味的语言回答用户问题。"
        "如果涉及具体的金柚知识，请融入客家文化元素。回答控制在200字以内。"
    )

    # 构建用户 prompt
    user_prompt_parts = [f"用户问题：{question}"]
    if knowledge_context and len(knowledge_context.strip()) > 10:
        user_prompt_parts.append(f"相关知识参考：{knowledge_context}")
    user_prompt_parts.append("请用专业且亲切的语言回答：")
    user_prompt = "\n\n".join(user_prompt_parts)

    result = _qa_adapter.invoke(
        prompt=user_prompt,
        system_prompt=system_prompt,
        temperature=0.65,
        max_tokens=512,
    )

    if result.get("success") and result.get("content"):
        return result["content"].strip()

    # LLM 调用失败的兜底
    if knowledge_context and len(knowledge_context.strip()) > 10:
        return _format_knowledge_answer(question, knowledge_context)
    return (
        f"关于「{question}」，建议您查阅梅州客家金柚相关资料，"
        f"或换个方式提问，我会尽力为您解答。"
    )
