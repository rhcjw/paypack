"""
PayPack Core - AI Agent 通用支付中间件 v0.4.0
支持 Signer 依赖注入、ERC-4337 批量结算
"""

import os
import json
from datetime import datetime, date, timezone
from typing import Optional, Dict, Any, Union, List

from web3 import Web3

from paypack.signer.base import Signer
from paypack.signer.local import LocalSigner


# ======== 多链网络配置 ========
DEFAULT_NETWORKS = {
    "base-sepolia": {
        "chain_id": 84532,
        "rpc_url": "https://sepolia.base.org",
        "usdc_address": "0x036CbD53842c5426634e7929541eC2318f3dCF7e",
        "native_currency": "ETH",
        "explorer": "https://sepolia.basescan.org",
    },
    "base-mainnet": {
        "chain_id": 8453,
        "rpc_url": "https://mainnet.base.org",
        "usdc_address": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        "native_currency": "ETH",
        "explorer": "https://basescan.org",
    },
    "ethereum-mainnet": {
        "chain_id": 1,
        "rpc_url": "https://mainnet.infura.io/v3/YOUR_INFURA_KEY",
        "usdc_address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "native_currency": "ETH",
        "explorer": "https://etherscan.io",
    },
    "polygon-mainnet": {
        "chain_id": 137,
        "rpc_url": "https://polygon-rpc.com",
        "usdc_address": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
        "native_currency": "POL",
        "explorer": "https://polygonscan.com",
    },
    "arbitrum-mainnet": {
        "chain_id": 42161,
        "rpc_url": "https://arb1.arbitrum.io/rpc",
        "usdc_address": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
        "native_currency": "ETH",
        "explorer": "https://arbiscan.io",
    },
}

USDC_ABI = [
    {
        "constant": False,
        "inputs": [
            {"name": "to", "type": "address"},
            {"name": "value", "type": "uint256"},
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [{"name": "owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function",
    },
]

# ERC-4337 EntryPoint 合约地址（各链通用 v0.6）
ENTRY_POINT_ADDRESS = "0x5FF137D4b0FDCD49DcA30c7CF57E578a026d2789"


class InsufficientFundsError(Exception):
    pass


class DailyLimitExceededError(Exception):
    pass


class NetworkConfigError(Exception):
    pass


class AgentPay:
    """
    AI Agent 纳米支付客户端。

    支持 x402 / AP2 协议自动解析，ETH / USDC 转账，
    Signer 依赖注入（本地私钥 / AWS KMS / Azure Key Vault），
    ERC-4337 批量结算。

    Usage:
        # 开发环境
        signer = LocalSigner(private_key="0x...")
        pay = AgentPay(signer=signer, network="base-sepolia")

        # 生产环境 (AWS KMS)
        signer = AWSKMSSigner(key_id="alias/paypack-eth-key")
        pay = AgentPay(signer=signer, network="base-mainnet")
    """

    def __init__(
        self,
        signer: Optional[Signer] = None,
        wallet_config: Optional[dict] = None,
        spend_limit_daily: float = 10.0,
        broadcast: bool = False,
        network: Union[str, Dict[str, Any]] = "base-sepolia",
        bundler_rpc_url: Optional[str] = None,
    ):
        # ---- Signer: 优先级 signer > wallet_config > 环境变量 ----
        if signer is not None:
            self.signer = signer
        else:
            # 向后兼容：旧的 wallet_config / PRIVATE_KEY 方式
            wallet_cfg = wallet_config or {}
            private_key = wallet_cfg.get("private_key") or os.getenv("PRIVATE_KEY")
            if not private_key:
                raise ValueError(
                    "私钥未提供。请传入 signer 参数，或 wallet_config['private_key']，或设置环境变量 PRIVATE_KEY"
                )
            self.signer = LocalSigner(private_key=private_key)

        self.spend_limit_daily = spend_limit_daily
        self.broadcast = broadcast
        self._today = date.today()
        self._spent_today = 0.0
        self.address = self.signer.get_address()

        self._init_network(network)

        self.usdc_contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(self.usdc_address),
            abi=USDC_ABI,
        )
        self.usdc_decimals = self.usdc_contract.functions.decimals().call()

        # ---- ERC-4337 可选 ----
        self._bundler_url = bundler_rpc_url

    def _init_network(self, network: Union[str, Dict[str, Any]]):
        if isinstance(network, str):
            config = DEFAULT_NETWORKS.get(network)
            if not config:
                raise NetworkConfigError(f"未知网络: {network}")
            self.network_name = network
            self.chain_id = config["chain_id"]
            self.rpc_url = config["rpc_url"]
            self.usdc_address = config["usdc_address"]
            self.native_currency = config.get("native_currency", "ETH")
            self.explorer = config.get("explorer", "")
        elif isinstance(network, dict):
            self.network_name = network.get("name", "custom")
            self.chain_id = network.get("chain_id")
            self.rpc_url = network.get("rpc_url")
            self.usdc_address = network.get("usdc_address")
            self.native_currency = network.get("native_currency", "ETH")
            self.explorer = network.get("explorer", "")
            if not self.chain_id or not self.rpc_url or not self.usdc_address:
                raise NetworkConfigError(
                    "自定义网络必须提供 chain_id, rpc_url, usdc_address"
                )
        else:
            raise NetworkConfigError("network 参数必须是字符串或字典")

        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        if not self.w3.is_connected():
            raise NetworkConfigError(f"无法连接到 RPC: {self.rpc_url}")

    # ======== 余额 & 限额 ========

    def _ensure_sufficient_balance(self, currency: str, amount: float):
        if currency.upper() == "USDC":
            balance_raw = self.usdc_contract.functions.balanceOf(self.address).call()
            balance = balance_raw / (10 ** self.usdc_decimals)
        else:
            balance_raw = self.w3.eth.get_balance(self.address)
            balance = self.w3.from_wei(balance_raw, "ether")

        if balance < amount:
            raise InsufficientFundsError(
                f"余额不足: 当前 {balance:.6f} {currency}, 需要 {amount:.6f} {currency}"
            )

    def _reset_daily_limit_if_new_day(self):
        if date.today() != self._today:
            self._today = date.today()
            self._spent_today = 0.0

    # ======== 协议解析 ========

    def auto_handle_402(self, response):
        if response.status_code != 402:
            raise ValueError("仅支持处理 402 状态码")

        headers = response.headers
        if "X-402-Payee" in headers:
            payment_info = self._parse_x402_headers(headers)
        elif "X-AP2-Payee" in headers:
            payment_info = self._parse_ap2_headers(headers)
        else:
            raise ValueError("无法识别的支付协议头，仅支持 x402 和 AP2")

        payee = payment_info.get("payee")
        amount = float(payment_info.get("amount", 0))
        currency = payment_info.get("currency", "ETH")

        return self.send(to=payee, amount=amount, currency=currency)

    def _parse_x402_headers(self, headers):
        return {
            "payee": headers.get("X-402-Payee", ""),
            "amount": headers.get("X-402-Amount", "0"),
            "currency": headers.get("X-402-Currency", "ETH"),
            "network": headers.get("X-402-Network", self.network_name),
        }

    def _parse_ap2_headers(self, headers):
        return {
            "payee": headers.get("X-AP2-Payee", ""),
            "amount": headers.get("X-AP2-Amount", "0"),
            "currency": headers.get("X-AP2-Currency", "USDC"),
            "network": headers.get("X-AP2-Network", self.network_name),
        }

    # ======== 交易构建与签名 ========

    def _build_transaction(self, to_address: str, value: int = 0, data: str = "0x", gas: int = 21000):
        """构建未签名交易字典"""
        to_address = Web3.to_checksum_address(to_address)
        nonce = self.w3.eth.get_transaction_count(self.address)

        txn = {
            "from": self.address,
            "to": to_address,
            "value": value,
            "gas": gas,
            "nonce": nonce,
            "chainId": self.chain_id,
        }

        if data and data != "0x":
            txn["data"] = data

        try:
            fee_data = self.w3.eth.fee_history(1, "latest")
            max_priority = self.w3.eth.max_priority_fee
            base_fee = fee_data["baseFeePerGas"][0]
            txn["maxPriorityFeePerGas"] = max_priority
            txn["maxFeePerGas"] = base_fee + max_priority
        except Exception:
            txn["gasPrice"] = self.w3.eth.gas_price

        return txn

    def _sign_and_broadcast(self, txn: dict) -> dict:
        """通过 Signer 签名，可选广播"""
        signed_txn = self.signer.sign_transaction(txn)

        if self.broadcast:
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            tx_hash_hex = receipt.transactionHash.hex()
            block = receipt.blockNumber
            status = "success" if receipt.status == 1 else "failed"
        else:
            tx_hash_hex = signed_txn.hash.hex()
            block = None
            status = "signed (not broadcasted)"

        return {
            "tx_hash": tx_hash_hex,
            "block_number": block,
            "status": status,
            "from": self.address,
        }

    def _execute_eth_transfer(self, to_address, amount_eth):
        txn = self._build_transaction(
            to_address=to_address,
            value=self.w3.to_wei(amount_eth, "ether"),
            gas=21000,
        )
        result = self._sign_and_broadcast(txn)
        result.update({
            "to": to_address,
            "amount": amount_eth,
            "currency": "ETH",
            "network": self.network_name,
            "explorer_link": f"{self.explorer}/tx/{result['tx_hash']}" if self.explorer else None,
        })
        return result

    def _execute_usdc_transfer(self, to_address, amount_usdc):
        to_address = Web3.to_checksum_address(to_address)
        amount_raw = int(amount_usdc * (10 ** self.usdc_decimals))

        txn = self.usdc_contract.functions.transfer(
            to_address, amount_raw
        ).build_transaction({
            "from": self.address,
            "chainId": self.chain_id,
            "gas": 100000,
            "nonce": self.w3.eth.get_transaction_count(self.address),
        })

        # 补充 gas 费用字段
        try:
            fee_data = self.w3.eth.fee_history(1, "latest")
            max_priority = self.w3.eth.max_priority_fee
            base_fee = fee_data["baseFeePerGas"][0]
            txn["maxPriorityFeePerGas"] = max_priority
            txn["maxFeePerGas"] = base_fee + max_priority
        except Exception:
            txn["gasPrice"] = self.w3.eth.gas_price

        result = self._sign_and_broadcast(txn)
        result.update({
            "to": to_address,
            "amount": amount_usdc,
            "currency": "USDC",
            "network": self.network_name,
            "explorer_link": f"{self.explorer}/tx/{result['tx_hash']}" if self.explorer else None,
        })
        return result

    # ======== 单笔支付 ========

    def send(self, to, amount, currency="ETH"):
        """单笔支付（ETH 或 USDC）"""
        self._reset_daily_limit_if_new_day()
        if self._spent_today + amount > self.spend_limit_daily:
            raise DailyLimitExceededError(
                f"日限额超限: 今日已消费 {self._spent_today:.6f}, 本次需 {amount:.6f}"
            )

        self._ensure_sufficient_balance(currency, amount)

        if currency.upper() == "USDC":
            tx_receipt = self._execute_usdc_transfer(to, amount)
        else:
            tx_receipt = self._execute_eth_transfer(to, amount)

        self._spent_today += amount
        return {
            "to": to,
            "amount": amount,
            "currency": currency,
            "tx_hash": tx_receipt["tx_hash"],
            "status": tx_receipt["status"],
            "explorer_link": tx_receipt.get("explorer_link"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "daily_remaining": round(self.spend_limit_daily - self._spent_today, 6),
        }

    # ======== ERC-4337 批量支付 ========

    def batch_pay(self, payments: List[dict]) -> dict:
        """
        批量支付 —— 将多笔小额支付打包成一个 ERC-4337 UserOperation。

        Args:
            payments: 支付列表
                [{"to": "0x...", "amount": 0.001, "currency": "USDC"}, ...]

        Returns:
            批量支付收据

        注意:
            - 需要账户是 ERC-4337 智能合约钱包（如 SimpleAccount）
            - 需要部署 Bundler 或使用第三方 Bundler 服务
        """
        if len(payments) == 0:
            raise ValueError("payments 不能为空")
        if len(payments) == 1:
            p = payments[0]
            return self.send(to=p["to"], amount=p["amount"], currency=p.get("currency", "ETH"))

        self._reset_daily_limit_if_new_day()
        total_amount = sum(p["amount"] for p in payments)
        if self._spent_today + total_amount > self.spend_limit_daily:
            raise DailyLimitExceededError(
                f"日限额超限: 今日已消费 {self._spent_today:.6f}, 批量需 {total_amount:.6f}"
            )

        # 检查每笔余额
        for p in payments:
            self._ensure_sufficient_balance(p.get("currency", "ETH"), p["amount"])

        # 构建批量调用
        calls = []
        for p in payments:
            currency = p.get("currency", "ETH")
            to_addr = Web3.to_checksum_address(p["to"])
            if currency.upper() == "USDC":
                amount_raw = int(p["amount"] * (10 ** self.usdc_decimals))
                data = self.usdc_contract.encode_abi("transfer", args=[to_addr, amount_raw])
                calls.append({"to": self.usdc_address, "value": 0, "data": data})
            else:
                value_wei = self.w3.to_wei(p["amount"], "ether")
                calls.append({"to": to_addr, "value": value_wei, "data": "0x"})

        from paypack.nanopay import ERC4337Batcher
        batcher = ERC4337Batcher(
            entry_point_address=ENTRY_POINT_ADDRESS,
            chain_id=self.chain_id,
        )

        nonce = self.w3.eth.get_transaction_count(self.address)
        user_op = batcher.build_user_operation(
            sender=self.address,
            calls=calls,
            nonce=nonce,
        )

        # 签名 UserOperation
        signed_op = self.signer.sign_user_operation(user_op)

        # 如果配置了 Bundler RPC，提交
        bundler_result = None
        if self._bundler_url:
            from paypack.nanopay import BundlerClient
            bundler = BundlerClient(self._bundler_url)
            user_op_hash = bundler.send_user_operation(signed_op, ENTRY_POINT_ADDRESS)
            bundler_result = {"user_op_hash": user_op_hash}

        self._spent_today += total_amount
        return {
            "batch_size": len(payments),
            "total_amount": total_amount,
            "payments": payments,
            "user_operation": signed_op,
            "bundler_result": bundler_result,
            "status": "bundled" if bundler_result else "signed (no bundler)",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "daily_remaining": round(self.spend_limit_daily - self._spent_today, 6),
        }


# ======== 便捷工厂函数 ========

def create_agent_pay(
    private_key: Optional[str] = None,
    wallet_address: Optional[str] = None,
    network: str = "base-sepolia",
    spend_limit_daily: float = 10.0,
    broadcast: bool = False,
    signer: Optional[Signer] = None,
) -> AgentPay:
    """
    快速创建 AgentPay 实例。

    支持两种方式：
    1. signer 参数（推荐）—— 传入 Signer 实例
    2. private_key 参数（向后兼容）—— 自动创建 LocalSigner
    """
    if signer is not None:
        return AgentPay(signer=signer, network=network, spend_limit_daily=spend_limit_daily, broadcast=broadcast)

    wallet_config = {"private_key": private_key, "address": wallet_address}
    return AgentPay(
        wallet_config=wallet_config,
        network=network,
        spend_limit_daily=spend_limit_daily,
        broadcast=broadcast,
    )


if __name__ == "__main__":
    print("请设置环境变量 PRIVATE_KEY，然后运行测试。")
