"""
ERC-4337 Bundler 客户端。
与 Bundler RPC 交互，提交 UserOperation 到链上。
"""

from typing import Optional

import requests


class BundlerClient:
    """
    ERC-4337 Bundler 客户端。

    与以太坊 Bundler 节点通信，提交 UserOperation 并查询状态。

    参考: ERC-4337 Bundler JSON-RPC API
    """

    def __init__(self, bundler_rpc_url: str, timeout: int = 30):
        """
        Args:
            bundler_rpc_url: Bundler RPC 节点地址
            timeout: 请求超时（秒）
        """
        self.rpc_url = bundler_rpc_url
        self.timeout = timeout
        self._next_id = 1

    def _rpc_call(self, method: str, params: list) -> dict:
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": self._next_id,
        }
        self._next_id += 1

        response = requests.post(
            self.rpc_url,
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        result = response.json()

        if "error" in result:
            raise RuntimeError(f"Bundler RPC error: {result['error']}")

        return result.get("result")

    def send_user_operation(self, user_op: dict, entry_point: str) -> str:
        """
        提交 UserOperation 到 Bundler。

        Args:
            user_op: UserOperation 字典
            entry_point: EntryPoint 合约地址

        Returns:
            userOpHash: UserOperation 哈希
        """
        return self._rpc_call("eth_sendUserOperation", [user_op, entry_point])

    def get_user_operation_receipt(self, user_op_hash: str) -> Optional[dict]:
        """
        查询 UserOperation 收据。

        Args:
            user_op_hash: UserOperation 哈希

        Returns:
            收据字典，如果尚未上链则返回 None
        """
        return self._rpc_call("eth_getUserOperationReceipt", [user_op_hash])

    def estimate_user_operation_gas(
        self, user_op: dict, entry_point: str
    ) -> dict:
        """
        估算 UserOperation 的 Gas 消耗。

        Returns:
            {"callGasLimit": "...", "verificationGasLimit": "...", "preVerificationGas": "..."}
        """
        return self._rpc_call(
            "eth_estimateUserOperationGas", [user_op, entry_point]
        )
