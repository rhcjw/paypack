"""
限额持久化。
支持内存（默认）、Redis、SQLite 三种后端。
Agent 重启后日限额不丢失。
"""

import os
import time
import json
import sqlite3
from abc import ABC, abstractmethod
from datetime import date
from typing import Optional


class LimitStore(ABC):
    """限额存储抽象接口"""

    @abstractmethod
    def get_spent_today(self, wallet_address: str) -> float:
        """获取今日已消费金额"""
        ...

    @abstractmethod
    def add_spent(self, wallet_address: str, amount: float):
        """增加今日已消费金额"""
        ...

    @abstractmethod
    def reset_if_new_day(self, wallet_address: str):
        """检查是否跨日，是则重置"""
        ...


class InMemoryStore(LimitStore):
    """内存存储 — 默认实现，重启即丢失"""

    def __init__(self):
        self._data: dict = {}  # key: "address:date" -> float

    def _key(self, wallet_address: str) -> str:
        return f"{wallet_address}:{date.today().isoformat()}"

    def get_spent_today(self, wallet_address: str) -> float:
        return self._data.get(self._key(wallet_address), 0.0)

    def add_spent(self, wallet_address: str, amount: float):
        key = self._key(wallet_address)
        self._data[key] = self._data.get(key, 0.0) + amount

    def reset_if_new_day(self, wallet_address: str):
        pass  # key 自带日期，自动隔离


class RedisStore(LimitStore):
    """
    Redis 存储 — 生产环境推荐。

    前置依赖: pip install redis
    """

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        try:
            import redis
        except ImportError:
            raise ImportError("Redis 存储需要: pip install redis")

        self._client = redis.Redis.from_url(redis_url, decode_responses=True)

    def _key(self, wallet_address: str) -> str:
        return f"paypack:limit:{wallet_address}:{date.today().isoformat()}"

    def get_spent_today(self, wallet_address: str) -> float:
        val = self._client.get(self._key(wallet_address))
        return float(val) if val else 0.0

    def add_spent(self, wallet_address: str, amount: float):
        key = self._key(wallet_address)
        # 设置 48h 过期，确保跨日自动清理
        self._client.incrbyfloat(key, amount)
        self._client.expire(key, 172800)

    def reset_if_new_day(self, wallet_address: str):
        pass  # key 自带日期


class SQLiteStore(LimitStore):
    """
    SQLite 存储 — 零依赖持久化。

    适合不想引入 Redis 的小型部署。
    """

    def __init__(self, db_path: str = "paypack_limits.db"):
        self._db_path = db_path
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS limits ("
            "  wallet TEXT NOT NULL,"
            "  day TEXT NOT NULL,"
            "  spent REAL DEFAULT 0,"
            "  PRIMARY KEY (wallet, day)"
            ")"
        )
        self._conn.commit()

    def _key(self, wallet_address: str) -> str:
        return date.today().isoformat()

    def get_spent_today(self, wallet_address: str) -> float:
        day = self._key(wallet_address)
        row = self._conn.execute(
            "SELECT spent FROM limits WHERE wallet = ? AND day = ?",
            (wallet_address, day),
        ).fetchone()
        return row[0] if row else 0.0

    def add_spent(self, wallet_address: str, amount: float):
        day = self._key(wallet_address)
        self._conn.execute(
            "INSERT INTO limits (wallet, day, spent) VALUES (?, ?, ?) "
            "ON CONFLICT(wallet, day) DO UPDATE SET spent = spent + ?",
            (wallet_address, day, amount, amount),
        )
        self._conn.commit()

    def reset_if_new_day(self, wallet_address: str):
        pass


def create_limit_store(backend: str = "memory", **kwargs) -> LimitStore:
    """
    便捷工厂：根据配置创建限额存储。

    Args:
        backend: "memory" | "redis" | "sqlite"
        **kwargs: 传递给具体后端的参数
            - redis: redis_url="redis://..."
            - sqlite: db_path="limits.db"

    Returns:
        LimitStore 实例
    """
    if backend == "redis":
        return RedisStore(redis_url=kwargs.get("redis_url", "redis://localhost:6379/0"))
    elif backend == "sqlite":
        return SQLiteStore(db_path=kwargs.get("db_path", "paypack_limits.db"))
    else:
        return InMemoryStore()
