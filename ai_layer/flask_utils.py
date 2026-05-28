"""
Flask API 工具模块
- 统一响应格式
- 请求参数校验
- 日志记录装饰器
"""

import time
import logging
from functools import wraps
from flask import jsonify, request

logger = logging.getLogger("pomelo_api")

# ---------------------------------------------------------------------------
# 统一响应
# ---------------------------------------------------------------------------


def ok(data=None, message="success"):
    """成功响应"""
    return jsonify({"code": 200, "data": data, "message": message})


def fail(code=500, message="server error", data=None):
    """失败响应"""
    return jsonify({"code": code, "data": data, "message": message})


def bad_request(message="参数错误"):
    return fail(400, message)


def not_found(message="资源不存在"):
    return fail(404, message)


# ---------------------------------------------------------------------------
# 参数校验
# ---------------------------------------------------------------------------


def require_fields(*fields):
    """
    装饰器：校验请求 JSON body 中必须包含指定字段。

    用法:
        @require_fields("user_query")
        def my_route():
            ...
    """

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            body = request.get_json(silent=True)
            if body is None:
                return bad_request("请求体不能为空或非JSON格式")
            for field in fields:
                value = body.get(field)
                if value is None or (isinstance(value, str) and not value.strip()):
                    return bad_request(f"缺少必要参数: {field}")
                # 长度校验：防止滥用
                if isinstance(value, str) and len(value) > 2000:
                    return bad_request(f"参数 {field} 超过最大长度限制(2000字符)")
            return fn(*args, **kwargs)

        return wrapper

    return decorator


# ---------------------------------------------------------------------------
# 请求日志
# ---------------------------------------------------------------------------


def log_request(fn):
    """装饰器：记录请求时间、参数、响应耗时"""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        t0 = time.perf_counter()
        body = request.get_json(silent=True) or {}
        # 截断长文本用于日志
        query = str(body.get("user_query", body.get("question", "")))[:80]
        logger.info("→ %s %s query=%s", request.method, request.path, query)

        try:
            resp = fn(*args, **kwargs)
            elapsed = int((time.perf_counter() - t0) * 1000)
            logger.info("← %s %s %dms", request.method, request.path, elapsed)
            return resp
        except Exception:
            elapsed = int((time.perf_counter() - t0) * 1000)
            logger.exception("✗ %s %s %dms", request.method, request.path, elapsed)
            raise

    return wrapper
