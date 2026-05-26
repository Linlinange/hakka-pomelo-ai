"""AI算法层自定义异常类"""


class LLMException(Exception):
    """大模型调用基础异常"""

    def __init__(self, message: str, model_name: str = "", retryable: bool = False):
        self.model_name = model_name
        self.retryable = retryable
        super().__init__(f"[{model_name}] {message}" if model_name else message)


class LLMTimeoutException(LLMException):
    """大模型调用超时异常（可重试）"""

    def __init__(self, message: str = "LLM request timeout", model_name: str = ""):
        super().__init__(message, model_name, retryable=True)


class LLMRateLimitException(LLMException):
    """大模型调用限流异常（可重试）"""

    def __init__(self, message: str = "LLM rate limit exceeded", model_name: str = ""):
        super().__init__(message, model_name, retryable=True)


class LLMAuthException(LLMException):
    """大模型认证失败异常（不可重试）"""

    def __init__(self, message: str = "LLM authentication failed", model_name: str = ""):
        super().__init__(message, model_name, retryable=False)


class LLMNetworkException(LLMException):
    """大模型网络异常（可重试）"""

    def __init__(self, message: str = "LLM network error", model_name: str = ""):
        super().__init__(message, model_name, retryable=True)


class LLMResponseException(LLMException):
    """大模型返回结果解析异常"""

    def __init__(self, message: str = "LLM response parse error", model_name: str = ""):
        super().__init__(message, model_name, retryable=False)


class IntentParseException(Exception):
    """意图识别解析异常"""

    def __init__(self, message: str, raw_response: str = ""):
        self.raw_response = raw_response
        super().__init__(f"Intent parse failed: {message}")
