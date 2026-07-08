"""
ERC-4337 批量交易打包器。
将多笔小额支付合并为一个 UserOperation，节省 Gas 费。
"""

from typing import List, Optional


class ERC4337Batcher:
    """
    ERC-4337 UserOperation 构建器。

    将多个链上调用打包成一个 UserOperation，
    由 Bundler 批量执行，实现 Gas 费分摊。

    参考: ERC-4337 Account Abstraction 规范
    """

    def __init__(self, entry_point_address: str, chain_id: int):
        """
        Args:
            entry_point_address: ERC-4337 EntryPoint 合约地址
            chain_id: 链 ID
        """
        self.entry_point = entry_point_address
        self.chain_id = chain_id

    def build_user_operation(
        self,
        sender: str,
        calls: List[dict],
        nonce: int,
        max_fee_per_gas: int = 50_000_000_000,
        max_priority_fee_per_gas: int = 1_000_000_000,
        paymaster_and_data: str = "0x",
    ) -> dict:
        """
        构建 UserOperation 对象。

        Args:
            sender: 智能合约账户地址
            calls: 批量调用列表 [{"to": "0x...", "value": 0, "data": "0x..."}]
            nonce: 账户 nonce（从 EntryPoint 获取）
            max_fee_per_gas: 最大 Gas 单价 (wei)
            max_priority_fee_per_gas: 优先费 (wei)
            paymaster_and_data: Paymaster 地址与数据（可选代付 Gas）

        Returns:
            UserOperation dict，符合 ERC-4337 规范
        """
        call_data = self._encode_batch_calls(calls)

        return {
            "sender": sender,
            "nonce": hex(nonce),
            "initCode": "0x",
            "callData": call_data,
            "callGasLimit": hex(self._estimate_call_gas(calls)),
            "verificationGasLimit": hex(200_000),
            "preVerificationGas": hex(50_000),
            "maxFeePerGas": hex(max_fee_per_gas),
            "maxPriorityFeePerGas": hex(max_priority_fee_per_gas),
            "paymasterAndData": paymaster_and_data,
            "signature": "0x",
        }

    def _encode_batch_calls(self, calls: List[dict]) -> str:
        """
        将多个调用编码为批量 callData。

        使用 MultiSend 风格编码（基于 Gnosis Safe 的 multiSend 合约）：
        - 每个调用编码为: operation(1B) + to(20B) + value(32B) + dataLength(32B) + data(variable)
        - 整体打包为 bytes

        简化实现：拼接 ABI 编码的 executeBatch 调用。
        """
        if len(calls) == 1:
            call = calls[0]
            return self._encode_single_call(call["to"], call.get("value", 0), call["data"])

        # 批量调用: executeBatch(address[], uint256[], bytes[])
        from eth_abi import encode
        targets = [c["to"] for c in calls]
        values = [c.get("value", 0) for c in calls]
        datas = [bytes.fromhex(c["data"][2:]) if c["data"].startswith("0x") else c["data"] for c in calls]

        # executeBatch 函数选择器
        selector = bytes.fromhex("47e1da2a")  # keccak("executeBatch(address[],uint256[],bytes[])")[:4]
        encoded_params = encode(
            ["address[]", "uint256[]", "bytes[]"],
            [targets, values, datas],
        )
        return "0x" + (selector + encoded_params).hex()

    def _encode_single_call(self, to: str, value: int, data: str) -> str:
        """编码单次调用为 execute() 选择器 + 参数"""
        from eth_abi import encode
        selector = bytes.fromhex("b61d27f6")  # keccak("execute(address,uint256,bytes)")[:4]
        data_bytes = bytes.fromhex(data[2:]) if data.startswith("0x") else data
        encoded_params = encode(
            ["address", "uint256", "bytes"],
            [to, value, data_bytes],
        )
        return "0x" + (selector + encoded_params).hex()

    def _estimate_call_gas(self, calls: List[dict]) -> int:
        """估算批量调用的 Gas 量"""
        base_gas = 50_000
        per_call_gas = 150_000
        return base_gas + per_call_gas * len(calls)
