"""
PayPack - AI Agent 通用支付中间件
v0.3.0 - 支持多链、环境变量私钥、余额检查、真实广播
"""

import os
import json
from datetime import datetime, date, timezone
from typing import Optional, Dict, Any, Union
from web3 import Web3

# ======== 多链网络配置 ========
DEFAULT_NETWORKS = {
    "base-sepolia": {
        "chain_id": 84532,
        "rpc_url": "https://sepolia.base.org",
        "usdc_address": "0x036CbD53842c5426634e7929541eC2318f3dCF7e",
        "native_currency": "ETH",
        "explorer": "https://sepolia.basescan.org"
    },
    "base-mainnet": {
        "chain_id": 8453,
        "rpc_url": "https://mainnet.base.org",
        "usdc_address": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        "native_currency": "ETH",
        "explorer": "https://basescan.org"
    },
    "ethereum-mainnet": {
        "chain_id": 1,
        "rpc_url": "https://mainnet.infura.io/v3/YOUR_INFURA_KEY",  # 需替换
        "usdc_address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "native_currency": "ETH",
        "explorer": "https://etherscan.io"
    },
    "polygon-mainnet": {
        "chain_id": 137,
        "rpc_url": "https://polygon-rpc.com",
        "usdc_address": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
        "native_currency": "POL",
        "explorer": "https://polygonscan.com"
    },
    "arbitrum-mainnet": {
        "chain_id": 42161,
        "rpc_url": "https://arb1.arbitrum.io/rpc",
        "usdc_address": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
        "native_currency": "ETH",
        "explorer": "https://arbiscan.io"
    },
}

# ======== USDC 完整 ABI ========
USDC_ABI = [
    {
        "constant": False,
        "inputs": [
            {"name": "to", "type": "address"},
            {"name": "value", "type": "uint256"}
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [{"name": "owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    }
]


class InsufficientFundsError(Exception):
    """余额不足"""
    pass


class DailyLimitExceededError(Exception):
    """日限额超限"""
    pass


class NetworkConfigError(Exception):
    """网络配置错误"""
    pass


class AgentPay:
    """AI 代理支付客户端（支持多链、环境变量、余额检查）"""

    def __init__(
        self,
        wallet_config: Optional[dict] = None,
        spend_limit_daily: float = 10.0,
        broadcast: bool = False,
        network: Union[str, Dict[str, Any]] = "base-sepolia",
    ):
        self.wallet_config = wallet_config or {}
        self.spend_limit_daily = spend_limit_daily
        self.broadcast = broadcast
        self._today = date.today()
        self._spent_today = 0.0

        self.private_key = self.wallet_config.get("private_key") or os.getenv("PRIVATE_KEY")
        self.address = self.wallet_config.get("address")
        if not self.private_key:
            raise ValueError("私钥未提供，请传入 wallet_config 或设置环境变量 PRIVATE_KEY")

        self._init_network(network)

        if not self.address:
            self.address = self.w3.eth.account.from_key(self.private_key).address

        self.usdc_contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(self.usdc_address),
            abi=USDC_ABI
        )
        self.usdc_decimals = self.usdc_contract.functions.decimals().call()

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
                raise NetworkConfigError("自定义网络必须提供 chain_id, rpc_url, usdc_address")
        else:
            raise NetworkConfigError("network 参数必须是字符串或字典")

        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        if not self.w3.is_connected():
            raise NetworkConfigError(f"无法连接到 RPC: {self.rpc_url}")

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
            "network": headers.get("X-402-Network", self.network_name)
        }

    def _parse_ap2_headers(self, headers):
        return {
            "payee": headers.get("X-AP2-Payee", ""),
            "amount": headers.get("X-AP2-Amount", "0"),
            "currency": headers.get("X-AP2-Currency", "USDC"),
            "network": headers.get("X-AP2-Network", self.network_name)
        }

    def _execute_eth_transfer(self, to_address, amount_eth):
        if not self.private_key or not self.address:
            raise ValueError("请提供私钥和地址")

        to_address = Web3.to_checksum_address(to_address)
        nonce = self.w3.eth.get_transaction_count(self.address)

        txn = {
            "from": self.address,
            "to": to_address,
            "value": self.w3.to_wei(amount_eth, "ether"),
            "gas": 21000,
            "nonce": nonce,
            "chainId": self.chain_id,
        }

        try:
            fee_data = self.w3.eth.fee_history(1, 'latest')
            max_priority = self.w3.eth.max_priority_fee
            base_fee = fee_data['baseFeePerGas'][0]
            txn['maxPriorityFeePerGas'] = max_priority
            txn['maxFeePerGas'] = base_fee + max_priority
        except Exception:
            txn['gasPrice'] = self.w3.eth.gas_price

        signed_txn = self.w3.eth.account.sign_transaction(txn, self.private_key)

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
            "to": to_address,
            "amount": amount_eth,
            "currency": "ETH",
            "network": self.network_name,
            "explorer_link": f"{self.explorer}/tx/{tx_hash_hex}" if self.explorer else None
        }

    def _execute_usdc_transfer(self, to_address, amount_usdc):
        if not self.private_key or not self.address:
            raise ValueError("请提供私钥和地址")

        to_address = Web3.to_checksum_address(to_address)
        amount_raw = int(amount_usdc * (10 ** self.usdc_decimals))
        nonce = self.w3.eth.get_transaction_count(self.address)

        txn = self.usdc_contract.functions.transfer(
            to_address,
            amount_raw
        ).build_transaction({
            "from": self.address,
            "chainId": self.chain_id,
            "gas": 100000,
            "nonce": nonce,
        })

        try:
            fee_data = self.w3.eth.fee_history(1, 'latest')
            max_priority = self.w3.eth.max_priority_fee
            base_fee = fee_data['baseFeePerGas'][0]
            txn['maxPriorityFeePerGas'] = max_priority
            txn['maxFeePerGas'] = base_fee + max_priority
        except Exception:
            txn['gasPrice'] = self.w3.eth.gas_price

        signed_txn = self.w3.eth.account.sign_transaction(txn, self.private_key)

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
            "to": to_address,
            "amount": amount_usdc,
            "currency": "USDC",
            "network": self.network_name,
            "explorer_link": f"{self.explorer}/tx/{tx_hash_hex}" if self.explorer else None
        }

    def send(self, to, amount, currency="ETH"):
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
            "daily_remaining": round(self.spend_limit_daily - self._spent_today, 6)
        }


def create_agent_pay(
    private_key: Optional[str] = None,
    wallet_address: Optional[str] = None,
    network: str = "base-sepolia",
    spend_limit_daily: float = 10.0,
    broadcast: bool = False,
) -> AgentPay:
    """便捷创建 AgentPay 实例"""
    return AgentPay(
        wallet_config={"private_key": private_key, "address": wallet_address},
        network=network,
        spend_limit_daily=spend_limit_daily,
        broadcast=broadcast
    )


if __name__ == "__main__":
    print("请设置环境变量 PRIVATE_KEY，然后运行测试。")