"""
Flask API 路由模块
- POST /api/recommend    AI智荐推荐
- POST /api/qa           智能问答
- POST /api/intent       意图识别（独立）
- GET  /api/health        健康检查
"""

import json
import traceback
import logging
from flask import Blueprint, request

_log = logging.getLogger(__name__)

from .flask_utils import ok, fail, bad_request, require_fields, log_request
from .intent_recognizer import IntentRecognizer
from .fusion_ranker import (
    FusionRanker,
    ProductCandidate,
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

        # 2. 解析候选金柚（Spring Boot 全局 SNAKE_CASE，字段名已统一）
        if raw_candidates:
            candidates = parse_candidates_from_rows(raw_candidates)

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
        return fail(500, "推荐服务暂时不可用，请稍后重试")


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
        return fail(500, "问答服务暂时不可用，请稍后重试")


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
        return fail(500, "意图识别服务暂时不可用，请稍后重试")


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
        "你是资深农产品电商文案策划师，擅长撰写吸引人的商品详情页文案。"
        "请用温暖的语言，突出产品产地、口感、营养价值和文化故事。"
        "文案需包含标题、卖点分点（3-4点）和结尾引导语，控制在200字以内。"
    ),
    "social": (
        "你是农产品品牌推广达人，擅长写微信朋友圈/小红书的种草推文。"
        "请用亲切、生活化的语气，配适当emoji，突出产品亮点。"
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
        return fail(500, "内容生成服务暂时不可用，请稍后重试")


def _fallback_content(scene: str, pomelo_name: str) -> str:
    """LLM 不可用时的兜底文案"""
    if scene == "ecommerce":
        return (
            f"【精选好物】{pomelo_name}\n\n"
            f"源自优质产区，精心种植采摘，品质上乘。"
            f"自用送礼皆宜，品味自然馈赠。\n\n"
            f"立即选购！"
        )
    return (
        f"分享今日份好物：{pomelo_name} 🛒\n"
        f"产地直发，品质新鲜，每一口都是自然的味道～\n"
        f"送亲友、送长辈，这份心意，甜到心里🫶\n"
        f"#好物分享 #产地直供"
    )


# ---- 推荐模式下的自由对话（无候选金柚时） ----

def _free_chat_recommend(user_query: str, intent_result) -> str:
    """
    无候选产品时，直接用 LLM 进行自然语言推荐对话。
    根据用户意图（选购/知识）和检测到的产品类型调整回答风格。
    """
    intent_type = intent_result.intent
    constraints = intent_result.constraints or {}
    culture_tags = intent_result.culture_tags or []
    product_type = constraints.get("product_type", "")

    # 检测用户是否提到特定水果
    fruit_keywords = {"苹果": "apple", "香蕉": "banana", "西瓜": "watermelon",
                      "橙子": "orange", "葡萄": "grape", "草莓": "strawberry",
                      "金柚": "pomelo", "柚子": "pomelo", "沙田柚": "pomelo", "蜜柚": "pomelo"}
    detected_type = product_type
    for kw, pt in fruit_keywords.items():
        if kw in user_query:
            detected_type = pt
            break

    is_pomelo = detected_type in ("pomelo", "") or "金柚" in user_query or "柚子" in user_query or "梅州" in user_query or "客家" in user_query

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
        context_parts.append(f"文化偏好：{', '.join(culture_tags)}")
    context_str = "，".join(context_parts) if context_parts else "无特殊约束"

    if is_pomelo:
        # 金柚专属风格
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
    else:
        # 通用水果风格
        if intent_type == "BUY":
            system_prompt = (
                "你是农产品推荐专家，精通各类水果的产地特色、品质鉴别和选购技巧。\n"
                "你的任务是理解用户的选购需求，给出专业、实用的推荐建议。\n"
                "你可以推荐具体的品种、产地以及适合的规格和价位。回答要具体、实用。\n"
                "控制在200字以内，语气温暖亲切。"
            )
            user_prompt = (
                f"用户需求：{user_query}\n"
                f"已识别的约束条件：{context_str}\n\n"
                "请根据用户需求，推荐合适的水果品类和选购建议。"
                "可以提到具体的产地特色、品种选择和价格参考。请直接给出推荐，不要反问用户。"
            )
        else:
            system_prompt = (
                "你是农产品领域的资深专家，精通各类水果的营养、保存、辨别和食用搭配。\n"
                "请用专业、温暖的语言回答用户问题。控制在200字以内。"
            )
            user_prompt = f"用户问题：{user_query}\n\n请直接用中文回答。注意：知识库涉及金柚时标明是梅州特产即可。"

    adapter = _get_content_adapter()
    result = adapter.invoke(
        prompt=user_prompt,
        system_prompt=system_prompt,
        temperature=0.70,
        max_tokens=512,
    )

    if result.get("success") and result.get("content"):
        return result["content"].strip()

    # LLM 调用失败时的兜底
    return (
        f"抱歉，AI 暂时无法为您解答「{user_query[:20]}」。\n\n"
        "请换个方式提问，我会尽力为您解答。"
    )


# ---------------------------------------------------------------------------
# 5. 知识库只读接口
# ---------------------------------------------------------------------------


def _load_knowledge_from_db(product_type: str = None):
    """从 MySQL 加载知识库，可选按 product_type 筛选，失败返回空列表"""
    try:
        from .db import query_all
        sql = (
            "SELECT id, product_type, pomelo_name, category, origin, specification, "
            "price_range, taste_description, hakka_culture_relation, product_description, "
            "gift_scene_tags, tags, image_url, "
            "score_requirement_match, score_scene_fit, score_hakka_feature, score_product_feature "
            "FROM golden_pomelo_knowledge WHERE status=1 AND is_deleted=0"
        )
        params = None
        if product_type:
            sql += " AND product_type = %s"
            params = (product_type,)
        sql += " ORDER BY view_count DESC LIMIT 20"
        rows = query_all(sql, params, connect_timeout=3)
        if rows:
            _log.info("从MySQL加载知识库: %d条", len(rows))
            return rows
    except Exception as exc:
        _log.warning("MySQL不可用，知识库返回空列表: %s", exc)
    return []


@api_bp.route("/knowledge", methods=["GET"])
def get_knowledge():
    """获取知识库列表，支持可选参数 ?product_type=apple 筛选"""
    pt = request.args.get("product_type")
    return ok(_load_knowledge_from_db(product_type=pt))


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


# ---------------------------------------------------------------------------
# 8. 中文分词接口
# ---------------------------------------------------------------------------

@api_bp.route("/text/segment", methods=["POST"])
@require_fields("text")
def text_segment():
    """
    中文分词 + 关键词提取。
    请求体: { "text": "沙田柚和蜜柚有什么区别" }
    返回: { "keywords": [...], "words": [...] }
    """
    try:
        from .text_utils import segment, extract_keywords
        body = request.get_json()
        text = body["text"].strip()

        words = segment(text)
        keywords = extract_keywords(text, topk=5)

        return ok({
            "keywords": keywords,
            "words": words,
        })
    except ImportError:
        return ok({"keywords": [], "words": [], "error": "jieba not installed"})
    except Exception:
        _log.exception("分词接口异常")
        return fail(500, "分词服务暂时不可用")


@api_bp.route("/health", methods=["GET"])
def health():
    return ok({"status": "running", "service": "pomelo-ai-layer"})



# ---------------------------------------------------------------------------
# 7. 流式端点（SSE）
# ---------------------------------------------------------------------------

@api_bp.route("/recommend/stream", methods=["POST"])
@require_fields("user_query")
def recommend_stream():
    """
    流式推荐接口 — 通过 SSE 逐 token 返回 LLM 的推荐理由。
    流程：意图识别 → 规则打分 → LLM 流式理由 → SSE 逐 token 推送
    """
    from flask import Response
    from .sse_utils import sse_event, sse_done, sse_error

    try:
        body = request.get_json()
        user_query = body["user_query"].strip()
        raw_candidates = body.get("candidates", [])

        intent_result = _intent_recognizer.recognize(user_query)
        demand = UserDemand.from_intent_result(user_query, intent_result)

        if raw_candidates:
            candidates = parse_candidates_from_rows(raw_candidates)
            scored_list = _fusion_ranker.rank(demand, candidates)
            recommendations = [_scored_to_dict(s) for s in scored_list]

            # 尝试流式生成推荐理由
            top3 = [s.candidate for s in scored_list[:3]]

            def generate():
                # 先发意图
                yield sse_event(json.dumps({
                    "type": "intent",
                    "intent": intent_result.to_dict(),
                }, ensure_ascii=False), event="meta")

                # 流式推荐理由
                try:
                    reason_gen = _fusion_ranker._generate_reasons_stream(demand, top3)
                    full_reason = ""
                    for chunk in reason_gen:
                        full_reason += chunk
                        yield sse_event(chunk)
                    # 附加完整结构化数据
                    yield sse_done({
                        "intent": intent_result.to_dict(),
                        "recommendations": recommendations,
                        "count": len(recommendations),
                        "reason": full_reason,
                    })
                except Exception:
                    # 降级：直接返回完整结果
                    yield sse_done({
                        "intent": intent_result.to_dict(),
                        "recommendations": recommendations,
                        "count": len(recommendations),
                    })

            return Response(generate(), mimetype='text/event-stream',
                          headers={
                              'Cache-Control': 'no-cache',
                              'X-Accel-Buffering': 'no',
                          })
        else:
            # 无候选人 → LLM 自由对话
            answer = _free_chat_recommend(user_query, intent_result)
            resp_data = {
                "intent": intent_result.to_dict(),
                "recommendations": [],
                "count": 0,
                "answer": answer,
            }
            return ok(resp_data)

    except Exception:
        _log.exception("流式推荐异常")
        return fail(500, "推荐服务暂时不可用，请稍后重试")


@api_bp.route("/qa/stream", methods=["POST"])
@require_fields("question")
def qa_stream():
    """
    流式问答接口 — 通过 SSE 逐 token 返回 LLM 的回答。
    """
    from flask import Response
    from .sse_utils import sse_event, sse_done, sse_error

    try:
        body = request.get_json()
        question = body["question"].strip()
        knowledge_context = body.get("knowledge_context", "")
        session_id = body.get("session_id", "")

        intent_result = _intent_recognizer.recognize(question)

        # 知识库命中 → 非流式直接返回
        if knowledge_context and len(knowledge_context.strip()) > 50:
            answer = _format_knowledge_answer(question, knowledge_context)
            return ok({
                "answer": answer,
                "source": "knowledge_base",
                "intent": intent_result.to_dict(),
                "session_id": session_id,
            })

        # 构建 LLM prompt（动态检测产品类型）
        system_prompt = _build_qa_system_prompt(question)
        user_prompt_parts = [f"用户问题：{question}"]
        if knowledge_context and len(knowledge_context.strip()) > 10:
            user_prompt_parts.append(f"相关知识参考：{knowledge_context}")
        user_prompt_parts.append("请用专业且亲切的语言回答：")
        user_prompt = "\n\n".join(user_prompt_parts)

        def generate():
            try:
                for chunk in _qa_adapter.invoke_stream(
                    prompt=user_prompt,
                    system_prompt=system_prompt,
                    temperature=0.65,
                    max_tokens=512,
                ):
                    yield sse_event(chunk)
                yield sse_done({
                    "source": "llm",
                    "intent": intent_result.to_dict(),
                    "session_id": session_id,
                })
            except Exception:
                yield sse_error("问答生成失败，请稍后重试")

        return Response(generate(), mimetype='text/event-stream',
                      headers={
                          'Cache-Control': 'no-cache',
                          'X-Accel-Buffering': 'no',
                      })

    except Exception:
        _log.exception("流式问答异常")
        return fail(500, "问答服务暂时不可用，请稍后重试")


# ---------------------------------------------------------------------------
# 内部辅助
# ---------------------------------------------------------------------------


def _scored_to_dict(s: ScoredCandidate) -> dict:
    """将 ScoredCandidate 转为前端可消费的字典"""
    c = s.candidate
    return {
        "id": c.id,
        "product_type": c.product_type,
        "pomelo_name": c.name,
        "category": c.category,
        "origin": c.origin,
        "specification": c.specification,
        "weight_range": c.weight_range,
        "price_range": c.price_range,
        "taste_description": c.taste_description,
        "hakka_culture_relation": c.hakka_culture_relation,
        "product_description": c.product_description,
        "gift_scene_tags": c.gift_scene_tags,
        "tags": c.tags,
        "image_url": getattr(c, "image_url", ""),
        # 打分明细
        "score_price_match": round(s.score_price_match, 2),
        "score_scene_fit": round(s.score_scene_fit, 2),
        "score_hakka_feature": round(s.score_third_dimension, 2),    # 兼容旧字段名
        "score_product_feature": round(s.score_third_dimension, 2),  # 新字段名
        "rule_total": round(s.rule_total, 2),
        "llm_score": round(s.llm_score, 1),
        "final_score": round(s.final_score, 1),
        "reason": s.reason,
    }


def _format_knowledge_answer(question: str, context: str) -> str:
    """将知识库检索结果格式化为自然语言回答"""
    return (
        f"关于「{question}」的相关信息如下：\n\n"
        f"{context}\n\n"
        f"如需更多帮助，请进一步描述您的问题。"
    )


def _detect_product_type(text: str) -> str:
    """从文本中检测提到的产品类型"""
    fruit_map = {
        "苹果": "apple", "香蕉": "banana", "西瓜": "watermelon",
        "橙子": "orange", "葡萄": "grape", "草莓": "strawberry",
        "金柚": "pomelo", "柚子": "pomelo", "沙田柚": "pomelo", "蜜柚": "pomelo",
        "梅州": "pomelo", "客家": "pomelo",
    }
    for kw, pt in fruit_map.items():
        if kw in text:
            return pt
    return "pomelo"  # 默认金柚


def _build_qa_system_prompt(question: str) -> str:
    """根据问题内容动态构建 QA system prompt"""
    pt = _detect_product_type(question)
    if pt == "pomelo":
        return (
            "你是梅州客家金柚领域的资深专家，精通金柚的营养、保存、辨别、食用搭配、"
            "客家文化典故和种植工艺。请用温暖、专业、有客家味的语言回答用户问题。"
            "如果涉及具体的金柚知识，请融入客家文化元素。回答控制在200字以内。"
        )
    else:
        return (
            "你是农产品领域的资深专家，精通各类水果的营养、保存、辨别、食用搭配常识。"
            "请用温暖、专业的语言回答用户问题。回答控制在200字以内。"
        )


def _call_llm_for_qa(question: str, knowledge_context: str, intent_result) -> str:
    """
    调用大模型生成问答答案。
    传入知识库上下文作为参考，让 LLM 结合专业知识作答。
    """
    system_prompt = _build_qa_system_prompt(question)

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
        f"关于「{question}」，建议您查阅相关资料，"
        f"或换个方式提问，我会尽力为您解答。"
    )
