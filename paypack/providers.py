"""
RPC 故障转移 Provider。
支持多 RPC URL 自动切换、健康检查。
"""

import time
import threading
from typing import List, Optional, Dict
from urllib.parse import urlparse

from web3 import Web3
from web3.providers.rpc import HTTPProvider


class FailoverProvider(HTTPProvider):
    """
    多 RPC 故障转移 Provider。

    按顺序尝试 RPC 列表中的节点，自动跳过不可用节点。
    支持可选的健康检查，定期标记不健康节点。

    Usage:
        provider = FailoverProvider([
            "https://sepolia.base.org",
            "https://base-sepolia.publicnode.com",
            "https://base-sepolia-rpc.publicnode.com",
        ])
        w3 = Web3(provider)
    """

    def __init__(
        self,
        rpc_urls: List[str],
        health_check_interval: int = 30,
        request_kwargs: Optional[dict] = None,
    ):
        if not rpc_urls:
            raise ValueError("至少需要一个 RPC URL")

        self._rpc_urls = rpc_urls
        self._active_index = 0
        self._health_check_interval = health_check_interval
        self._unhealthy: Dict[int, float] = {}  # index -> unhealthy_since
        self._lock = threading.Lock()

        # 用第一个 URL 初始化父类
        super().__init__(endpoint_uri=rpc_urls[0], request_kwargs=request_kwargs)

    @property
    def active_url(self) -> str:
        with self._lock:
            return self._rpc_urls[self._active_index]

    @property
    def url_count(self) -> int:
        return len(self._rpc_urls)

    def make_request(self, method: str, params: list) -> dict:
        """发起 RPC 请求，失败时自动切换到下一个节点。"""
        errors = []

        with self._lock:
            urls_to_try = self._get_ordered_urls()

        for idx, url in urls_to_try:
            try:
                self.endpoint_uri = url
                result = super().make_request(method, params)

                # 请求成功，标记为健康
                with self._lock:
                    self._unhealthy.pop(idx, None)
                    self._active_index = idx
                return result

            except Exception as e:
                errors.append(f"{urlparse(url).netloc}: {e}")
                with self._lock:
                    if idx not in self._unhealthy:
                        self._unhealthy[idx] = time.time()

        raise RuntimeError(
            f"所有 RPC 节点均不可用，已尝试 {len(urls_to_try)} 个节点:\n"
            + "\n".join(f"  - {err}" for err in errors)
        )

    def _get_ordered_urls(self) -> List[tuple]:
        """获取排序后的 URL 列表：健康的在前，不健康的在后。"""
        healthy = []
        unhealthy = []

        for i in range(len(self._rpc_urls)):
            if i in self._unhealthy:
                # 检查是否过了隔离期
                if time.time() - self._unhealthy[i] > self._health_check_interval:
                    self._unhealthy.pop(i)
                    healthy.append(i)
                else:
                    unhealthy.append(i)
            else:
                healthy.append(i)

        # 健康节点按当前 active_index 优先
        if self._active_index in healthy:
            healthy.remove(self._active_index)
            healthy.insert(0, self._active_index)

        ordered = healthy + unhealthy
        return [(i, self._rpc_urls[i]) for i in ordered]

    def is_connected(self, show_traceback: bool = False) -> bool:
        """检查是否有任何可用节点。"""
        for _ in range(len(self._rpc_urls)):
            try:
                return super().is_connected(show_traceback)
            except Exception:
                with self._lock:
                    self._unhealthy[self._active_index] = time.time()
                    # 尝试下一个
                    self._active_index = (self._active_index + 1) % len(self._rpc_urls)
                    self.endpoint_uri = self._rpc_urls[self._active_index]
        return False


def create_failover_w3(
    rpc_urls: List[str],
    health_check_interval: int = 30,
    request_kwargs: Optional[dict] = None,
) -> Web3:
    """
    便捷工厂：创建带故障转移的 Web3 实例。

    Usage:
        w3 = create_failover_w3([
            "https://sepolia.base.org",
            "https://base-sepolia.publicnode.com",
        ])
    """
    if len(rpc_urls) == 1:
        return Web3(HTTPProvider(endpoint_uri=rpc_urls[0], request_kwargs=request_kwargs))
    return Web3(FailoverProvider(rpc_urls, health_check_interval, request_kwargs))
