"""
SSE (Server-Sent Events) 工具模块
用于流式传输 LLM token 到前端
"""

import json
from typing import Generator


def sse_event(data: str, event: str = "token") -> str:
    """格式化一条 SSE 事件"""
    payload = json.dumps({"token": data, "event": event}, ensure_ascii=False)
    return f"data: {payload}\n\n"


def sse_done(data: dict = None) -> str:
    """发送 SSE 结束事件，附带最终结构化数据"""
    payload = json.dumps({
        "event": "done",
        "data": data or {},
    }, ensure_ascii=False)
    return f"data: {payload}\n\n"


def sse_error(message: str) -> str:
    """发送 SSE 错误事件"""
    payload = json.dumps({
        "event": "error",
        "data": {"message": message},
    }, ensure_ascii=False)
    return f"data: {payload}\n\n"


def sse_stream(generator: Generator[str, None, None]):
    """
    将生成器包装为 Flask SSE Response。
    用法:
        return Response(sse_stream(my_generator), mimetype='text/event-stream')
    """
    for chunk in generator:
        yield chunk
