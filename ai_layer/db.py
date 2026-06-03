"""
数据库直连工具模块

AI 算法层通过 pymysql 直连 MySQL 读取 Prompt 模板、权重参数和知识库。
提供统一的连接管理和查询封装，避免各模块重复连接逻辑。
"""

from __future__ import annotations
import pymysql
from typing import Optional

from .config import get_config

logger = logging.getLogger(__name__)


def get_connection(connect_timeout: int = 5):
    """创建 MySQL 连接，参数来自全局 Config"""
    cfg = get_config()
    return pymysql.connect(
        host=cfg.db_host,
        port=cfg.db_port,
        user=cfg.db_user,
        password=cfg.db_password,
        database=cfg.db_name,
        charset="utf8mb4",
        connect_timeout=connect_timeout,
    )


def query_all(sql: str, params=None, connect_timeout: int = 5) -> list[dict]:
    """执行查询，返回所有行（DictCursor）"""
    conn = get_connection(connect_timeout=connect_timeout)
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute(sql, params)
            return cur.fetchall()
    finally:
        conn.close()


def query_one(sql: str, params=None, connect_timeout: int = 5) -> Optional[dict]:
    """执行查询，返回第一行或 None"""
    rows = query_all(sql, params, connect_timeout=connect_timeout)
    return rows[0] if rows else None
