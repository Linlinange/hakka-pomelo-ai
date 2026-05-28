"""
大模型调用适配层（LLM Adapter）
统一封装 ChatGLM-4 / 讯飞星火 的调用接口，提供：
- 统一的 invoke() 请求发送 & 结果解析
- 指数退避重试
- 超时、限流、网络异常的自动降级
"""

import json
import time
import logging
import threading
from abc import ABC, abstractmethod
from typing import Optional, Any

import requests

from .config import get_config, LLMConfig, RetryConfig
from .exceptions import (
    LLMException,
    LLMTimeoutException,
    LLMRateLimitException,
    LLMAuthException,
    LLMNetworkException,
    LLMResponseException,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 抽象基类
# ---------------------------------------------------------------------------


class LLMAdapter(ABC):
    """大模型调用适配器抽象基类"""

    def __init__(self, model_name: str, llm_config: LLMConfig, retry_config: Optional[RetryConfig] = None):
        self._model_name = model_name
        self._llm_config = llm_config
        self._retry_config = retry_config or get_config().retry
        # 非线程安全，单次请求够用
        self._lock = threading.Lock()

    # ---- 公共接口 ----

    def invoke(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> dict[str, Any]:
        """
        统一调用入口：发送请求 → 解析结果 → 返回标准化字典。

        Returns:
            {
                "success": bool,
                "content": str,          # 大模型返回的文本
                "model": str,            # 实际调用的模型名
                "token_input": int,
                "token_output": int,
                "response_time_ms": int,
                "raw": dict,             # 原始响应（调试用）
            }
        """
        t0 = time.perf_counter()
        temperature = temperature if temperature is not None else self._llm_config.temperature
        max_tokens = max_tokens if max_tokens is not None else self._llm_config.max_tokens

        last_exception: Optional[LLMException] = None
        for attempt in range(self._retry_config.max_retries + 1):
            try:
                raw = self._send(prompt, system_prompt, temperature, max_tokens)
                parsed = self._parse_response(raw)
                parsed["response_time_ms"] = int((time.perf_counter() - t0) * 1000)
                parsed["success"] = True
                parsed["raw"] = raw
                return parsed
            except LLMException as exc:
                last_exception = exc
                if not exc.retryable or attempt >= self._retry_config.max_retries:
                    break
                delay = self._calc_backoff(attempt)
                logger.warning(
                    "LLM调用失败 (attempt %d/%d, model=%s): %s — %s秒后重试",
                    attempt + 1, self._retry_config.max_retries, self._model_name, exc, round(delay, 1),
                )
                time.sleep(delay)

        # 所有重试耗尽
        response_time_ms = int((time.perf_counter() - t0) * 1000)
        logger.error("LLM调用最终失败 model=%s retries=%d", self._model_name, self._retry_config.max_retries)
        return {
            "success": False,
            "content": "",
            "model": self._model_name,
            "token_input": 0,
            "token_output": 0,
            "response_time_ms": response_time_ms,
            "error": str(last_exception),
            "raw": {},
        }

    # ---- 子类需实现 ----

    @abstractmethod
    def _send(self, prompt: str, system_prompt: Optional[str], temperature: float, max_tokens: int) -> dict:
        """发送请求到具体大模型平台，返回平台原始响应 JSON"""
        ...

    @abstractmethod
    def _parse_response(self, raw: dict) -> dict:
        """解析平台原始响应为标准化字段 dict"""
        ...

    # ---- 内部工具 ----

    
    def invoke_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ):
        """
        流式调用入口：返回一个生成器，逐 token yield 文本块。
        子类可选实现，默认降级为非流式（一次返回全部内容）。
        """
        result = self.invoke(prompt, system_prompt, temperature, max_tokens)
        if result.get("success"):
            yield result["content"]

    def _calc_backoff(self, attempt: int) -> float:
        delay = self._retry_config.base_delay_seconds * (self._retry_config.backoff_multiplier ** attempt)
        return min(delay, self._retry_config.max_delay_seconds)


# ---------------------------------------------------------------------------
# ChatGLM-4 适配器
# ---------------------------------------------------------------------------

class ChatGLM4Adapter(LLMAdapter):
    """智谱 ChatGLM-4 API 适配器"""

    def __init__(self, llm_config: Optional[LLMConfig] = None):
        cfg = llm_config or get_config().chatglm
        super().__init__("chatglm-4-lite", cfg)

    def _send(self, prompt: str, system_prompt: Optional[str], temperature: float, max_tokens: int) -> dict:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self._model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        headers = {
            "Authorization": f"Bearer {self._llm_config.api_key}",
            "Content-Type": "application/json",
        }
        try:
            resp = requests.post(
                self._llm_config.endpoint,
                json=payload,
                headers=headers,
                timeout=self._llm_config.timeout_seconds,
            )
        except requests.exceptions.Timeout:
            raise LLMTimeoutException(model_name=self._model_name)
        except requests.exceptions.ConnectionError as e:
            raise LLMNetworkException(str(e), model_name=self._model_name)

        return self._handle_http_status(resp)


    def invoke_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ):
        """DeepSeek 流式调用：逐 token yield 文本块"""
        temperature = temperature if temperature is not None else self._llm_config.temperature
        max_tokens = max_tokens if max_tokens is not None else self._llm_config.max_tokens

        try:
            for chunk in self._send_stream(prompt, system_prompt, temperature, max_tokens):
                yield chunk
        except LLMException:
            # 流式失败时降级到非流式
            result = self.invoke(prompt, system_prompt, temperature, max_tokens)
            if result.get("success"):
                yield result["content"]

    def _send_stream(self, prompt: str, system_prompt: Optional[str], temperature: float, max_tokens: int):
        """逐 token 从 DeepSeek 流式 API 读取 SSE 数据"""
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": system_prompt or ""},
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        headers = {
            "Authorization": f"Bearer {self._llm_config.api_key}",
            "Content-Type": "application/json",
        }
        endpoint = self._llm_config.endpoint or "https://api.deepseek.com/chat/completions"

        try:
            resp = requests.post(
                endpoint, json=payload, headers=headers,
                timeout=self._llm_config.timeout_seconds,
                stream=True,
            )
        except requests.exceptions.Timeout:
            raise LLMTimeoutException(model_name=self._model_name)
        except requests.exceptions.ConnectionError as e:
            raise LLMNetworkException(str(e), model_name=self._model_name)

        if resp.status_code != 200:
            msg = ""
            try:
                msg = resp.json().get("error", {}).get("message", resp.text)
            except Exception:
                msg = resp.text
            if resp.status_code == 401:
                raise LLMAuthException(msg, model_name=self._model_name)
            if resp.status_code == 429:
                raise LLMRateLimitException(msg, model_name=self._model_name)
            raise LLMException(f"HTTP {resp.status_code}: {msg}", model_name=self._model_name, retryable=True)

        # 逐行读取 SSE
        for line in resp.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data: "):
                continue
            data_str = line[6:]
            if data_str == "[DONE]":
                break
            try:
                data = json.loads(data_str)
                delta = data.get("choices", [{}])[0].get("delta", {})
                content = delta.get("content", "")
                if content:
                    yield content
            except json.JSONDecodeError:
                continue

    def _handle_http_status(self, resp: requests.Response) -> dict:
        if resp.status_code == 200:
            return resp.json()
        body = {}
        try:
            body = resp.json()
        except Exception:
            pass
        msg = body.get("error", {}).get("message", resp.text)
        if resp.status_code == 401 or resp.status_code == 403:
            raise LLMAuthException(msg, model_name=self._model_name)
        if resp.status_code == 429:
            raise LLMRateLimitException(msg, model_name=self._model_name)
        raise LLMException(f"HTTP {resp.status_code}: {msg}", model_name=self._model_name, retryable=True)

    def _parse_response(self, raw: dict) -> dict:
        try:
            choices = raw.get("choices", [])
            content = choices[0]["message"]["content"] if choices else ""
        except (KeyError, IndexError, TypeError):
            raise LLMResponseException("ChatGLM响应缺少 choices[0].message.content", model_name=self._model_name)

        usage = raw.get("usage", {})
        return {
            "content": content,
            "model": raw.get("model", self._model_name),
            "token_input": usage.get("prompt_tokens", 0),
            "token_output": usage.get("completion_tokens", 0),
        }


# ---------------------------------------------------------------------------
# DeepSeek 适配器（OpenAI 兼容协议，继承 ChatGLM4Adapter）
# ---------------------------------------------------------------------------

class DeepSeekAdapter(ChatGLM4Adapter):
    """DeepSeek API 适配器，协议与 OpenAI 兼容，直接复用 ChatGLM 的收发逻辑"""

    def __init__(self, llm_config: Optional[LLMConfig] = None):
        cfg = llm_config or get_config().deepseek
        super().__init__(cfg)
        self._model_name = "deepseek-chat"

    def _handle_http_status(self, resp: requests.Response) -> dict:
        if resp.status_code == 200:
            return resp.json()
        body = {}
        try:
            body = resp.json()
        except Exception:
            pass
        # DeepSeek 错误格式: {"error": {"message": "...", "type": "..."}}
        msg = body.get("error", {}).get("message", resp.text)
        if resp.status_code == 401 or resp.status_code == 403:
            raise LLMAuthException(msg, model_name=self._model_name)
        if resp.status_code == 429:
            raise LLMRateLimitException(msg, model_name=self._model_name)
        if resp.status_code == 402:
            raise LLMException(f"DeepSeek 账户余额不足: {msg}", model_name=self._model_name, retryable=False)
        raise LLMException(f"HTTP {resp.status_code}: {msg}", model_name=self._model_name, retryable=True)


# ---------------------------------------------------------------------------
# 讯飞星火适配器
# ---------------------------------------------------------------------------

class SparkAdapter(LLMAdapter):
    """讯飞星火大模型 API 适配器（HTTP 协议，星火 4.0）"""

    def __init__(self, llm_config: Optional[LLMConfig] = None):
        cfg = llm_config or get_config().spark
        super().__init__("spark-lite", cfg)

    def _send(self, prompt: str, system_prompt: Optional[str], temperature: float, max_tokens: int) -> dict:
        # 讯飞星火需要先通过 API Key + Secret 获取临时鉴权 URL 上可用的 domain 参数，
        # 这里使用其 HTTP 接口（而非 WebSocket），路径因版本略有差异。
        # 如果环境配置的是 wss 地址，自动转为 http。
        endpoint = self._llm_config.endpoint.replace("wss://", "https://")
        payload = {
            "model": "generalv4.0",
            "messages": [
                {"role": "system", "content": system_prompt or ""},
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        headers = {
            "Authorization": f"Bearer {self._llm_config.api_key}:{self._llm_config.api_secret}",
            "Content-Type": "application/json",
        }
        try:
            resp = requests.post(endpoint, json=payload, headers=headers,
                                 timeout=self._llm_config.timeout_seconds)
        except requests.exceptions.Timeout:
            raise LLMTimeoutException(model_name=self._model_name)
        except requests.exceptions.ConnectionError as e:
            raise LLMNetworkException(str(e), model_name=self._model_name)

        return self._handle_http_status(resp)

    def _handle_http_status(self, resp: requests.Response) -> dict:
        if resp.status_code == 200:
            return resp.json()
        body = {}
        try:
            body = resp.json()
        except Exception:
            pass
        code = body.get("header", {}).get("code", resp.status_code)
        msg = body.get("header", {}).get("message", resp.text)
        if code in (10002, 10004, 10013):
            raise LLMAuthException(msg, model_name=self._model_name)
        if code == 10019:
            raise LLMRateLimitException(msg, model_name=self._model_name)
        raise LLMException(f"Spark code={code}: {msg}", model_name=self._model_name, retryable=True)

    def _parse_response(self, raw: dict) -> dict:
        try:
            # 星火返回结构: payload.choices.text[0].content
            choices = raw.get("payload", {}).get("choices", {}).get("text", [])
            content = choices[0]["content"] if choices else ""
        except (KeyError, IndexError, TypeError):
            try:
                # 兜底：尝试通用 OpenAI 格式
                content = raw["choices"][0]["message"]["content"]
            except (KeyError, IndexError, TypeError):
                raise LLMResponseException("Spark响应解析失败", model_name=self._model_name)

        usage = raw.get("payload", {}).get("usage", {}).get("text", {})
        return {
            "content": content,
            "model": raw.get("header", {}).get("model", self._model_name),
            "token_input": usage.get("prompt_tokens", 0),
            "token_output": usage.get("completion_tokens", 0),
        }


# ---------------------------------------------------------------------------
# 工厂函数
# ---------------------------------------------------------------------------

def create_adapter(model_name: str = "", llm_config: Optional[LLMConfig] = None) -> LLMAdapter:
    """
    根据模型名创建对应的适配器实例。

    Args:
        model_name: "chatglm" / "spark" / "deepseek" / "chatglm-4-lite" / "spark-lite" / "deepseek-chat"，
                    默认取 config.default_model
        llm_config: 覆盖全局配置中的模型参数
    """
    name = (model_name or get_config().default_model).lower()
    if "spark" in name:
        return SparkAdapter(llm_config)
    if "deepseek" in name:
        return DeepSeekAdapter(llm_config)
    return ChatGLM4Adapter(llm_config)
