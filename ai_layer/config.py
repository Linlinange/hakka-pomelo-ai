"""AI算法层全局配置，支持环境变量与代码内默认值"""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class LLMConfig:
    """单个大模型接入配置"""
    api_key: str = ""
    api_secret: str = ""
    app_id: str = ""
    endpoint: str = ""
    max_tokens: int = 2048
    temperature: float = 0.70
    timeout_seconds: int = 30


@dataclass
class RetryConfig:
    """重试策略配置"""
    max_retries: int = 3
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 30.0
    backoff_multiplier: float = 2.0


@dataclass
class Config:
    """全局配置"""
    # --- 默认模型选择 ---
    default_model: str = "deepseek"  # "chatglm" | "spark" | "deepseek"

    # --- 各模型配置 ---
    chatglm: LLMConfig = field(default_factory=lambda: LLMConfig(
        api_key=os.getenv("CHATGLM_API_KEY", ""),
        endpoint=os.getenv("CHATGLM_ENDPOINT", "https://open.bigmodel.cn/api/paas/v4/chat/completions"),
        max_tokens=2048,
        temperature=0.70,
        timeout_seconds=30,
    ))

    spark: LLMConfig = field(default_factory=lambda: LLMConfig(
        app_id=os.getenv("SPARK_APP_ID", ""),
        api_key=os.getenv("SPARK_API_KEY", ""),
        api_secret=os.getenv("SPARK_API_SECRET", ""),
        endpoint=os.getenv("SPARK_ENDPOINT", "wss://spark-api.xf-yun.com/v4.0/chat"),
        max_tokens=2048,
        temperature=0.70,
        timeout_seconds=30,
    ))

    deepseek: LLMConfig = field(default_factory=lambda: LLMConfig(
        api_key=os.getenv("DEEPSEEK_API_KEY", ""),
        endpoint=os.getenv("DEEPSEEK_ENDPOINT", "https://api.deepseek.com/chat/completions"),
        max_tokens=2048,
        temperature=0.70,
        timeout_seconds=30,
    ))

    # --- 重试策略 ---
    retry: RetryConfig = field(default_factory=RetryConfig)

    # --- 意图识别 ---
    intent_confidence_threshold: float = float(os.getenv("INTENT_CONFIDENCE_THRESHOLD", "0.60"))

    # --- 数据库（供AI层直连读取Prompt库/知识库）---
    db_host: str = os.getenv("DB_HOST", "127.0.0.1")
    db_port: int = int(os.getenv("DB_PORT", "3306"))
    db_user: str = os.getenv("DB_USER", "root")
    db_password: str = os.getenv("DB_PASSWORD", "")
    db_name: str = os.getenv("DB_NAME", "golden_pomelo_ai")

    @classmethod
    def from_env(cls) -> "Config":
        """全部从环境变量读取，适合容器化部署"""
        return Config()

    def get_llm_config(self, model_name: str) -> LLMConfig:
        name = model_name.lower()
        if "spark" in name:
            return self.spark
        if "deepseek" in name:
            return self.deepseek
        return self.chatglm


# 全局单例
_config: Optional[Config] = None


def get_config() -> Config:
    global _config
    if _config is None:
        _config = Config()
    return _config


def set_config(cfg: Config) -> None:
    global _config
    _config = cfg
