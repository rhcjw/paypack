"""
PayPack - AI Agent 通用支付中间件
v0.2.0 - 支持 x402 + AP2 双协议自动识别，可配置是否广播上链
"""

import json
from datetime import datetime, date, timezone
from typing import Optional
from web3 import Web3

# ========== 连接 Base Sepolia 测试网 ==========
RPC_URL = "https://sepolia.base.org"
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# ========== 测试网 USDC 合约地址 (Base Sepolia) ==========
USDC_CONTRACT_ADDRESS = "0x036CbD53842c5426634e7929541eC2318f3dCF7e"
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
    }
]


class InsufficientFundsError(Exception):
    """余额不足"""
    pass


class DailyLimitExceededError(Exception):
    """日限额超限"""
    pass


class AgentPay:
    """AI 代理支付客户端"""

    def __init__(
        self,
        wallet_config: Optional[dict] = None,
        spend_limit_daily: float = 10.0,
        broadcast: bool = False          # 新增：是否真实广播上链
    ):
        self.wallet_config = wallet_config or {}
        self.spend_limit_daily = spend_limit_daily
        self.broadcast = broadcast        # 保存广播开关
        self._today = date.today()
        self._spent_today = 0.0

        # 从配置中加载私钥和地址
        self.private_key = self.wallet_config.get("private_key")
        self.address = self.wallet_config.get("address")

        # 初始化 USDC 合约
        self.usdc_contract = w3.eth.contract(
            address=Web3.to_checksum_address(USDC_CONTRACT_ADDRESS),
            abi=USDC_ABI
        )

    def _reset_daily_limit_if_new_day(self):
        """跨天自动重置日消费额度"""
        if date.today() != self._today:
            self._today = date.today()
            self._spent_today = 0.0

    def auto_handle_402(self, response):
        """
        自动处理 HTTP 402 响应。
        自动识别 x402 或 AP2 协议头，校验限额，根据币种选择 ETH 或 USDC 转账。
        """
        if response.status_code != 402:
            raise ValueError("仅支持处理 402 状态码")

        # 1. 自动识别协议头（x402 或 AP2）
        headers = response.headers
        if "X-402-Payee" in headers:
            payment_info = self._parse_x402_headers(headers)
        elif "X-AP2-Payee" in headers:
            payment_info = self._parse_ap2_headers(headers)
        else:
            raise ValueError("无法识别的支付协议头，仅支持 x402 和 AP2")

        # 2. 提取付款信息
        payee = payment_info.get("payee")
        amount = float(payment_info.get("amount", 0))
        currency = payment_info.get("currency", "ETH")

        # 3. 日限额校验
        self._reset_daily_limit_if_new_day()
        if self._spent_today + amount > self.spend_limit_daily:
            raise DailyLimitExceededError(
                f"今日已消费 {self._spent_today:.6f} {currency}，"
                f"本次需支付 {amount:.6f} {currency}，超出日限额 {self.spend_limit_daily} {currency}"
            )

        # 4. 根据币种执行转账
        if currency.upper() == "USDC":
            tx_receipt = self._execute_usdc_transfer(payee, amount)
        else:
            tx_receipt = self._execute_eth_transfer(payee, amount)

        # 5. 扣减今日额度
        self._spent_today += amount

        return {
            "status": "paid",
            "payee": payee,
            "amount": amount,
            "currency": currency,
            "network": "base-sepolia",
            "tx_hash": tx_receipt["tx_hash"],
            "signature_status": tx_receipt.get("status", "unknown"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "daily_remaining": round(self.spend_limit_daily - self._spent_today, 6)
        }

    def _parse_x402_headers(self, headers):
        """解析 x402 协议响应头"""
        return {
            "payee": headers.get("X-402-Payee", ""),
            "amount": headers.get("X-402-Amount", "0"),
            "currency": headers.get("X-402-Currency", "ETH"),
            "network": headers.get("X-402-Network", "base-sepolia")
        }

    def _parse_ap2_headers(self, headers):
        """解析 AP2 协议响应头"""
        return {
            "payee": headers.get("X-AP2-Payee", ""),
            "amount": headers.get("X-AP2-Amount", "0"),
            "currency": headers.get("X-AP2-Currency", "USDC"),
            "network": headers.get("X-AP2-Network", "base-sepolia")
        }

    def _execute_eth_transfer(self, to_address, amount_eth):
        """
        构造并签名 ETH 转账交易。
        根据 self.broadcast 决定是否广播上链。
        """
        if not self.private_key or not self.address:
            raise ValueError("请提供私钥和地址")

        txn = {
            "from": self.address,
            "to": Web3.to_checksum_address(to_address),
            "value": w3.to_wei(amount_eth, "ether"),
            "gas": 21000,
            "nonce": w3.eth.get_transaction_count(self.address),
            "chainId": w3.eth.chain_id,
        }

        # 动态获取 gas 价格
        try:
            fee_data = w3.eth.fee_history(1, 'latest')
            max_priority = w3.eth.max_priority_fee
            base_fee = fee_data['baseFeePerGas'][0]
            txn['maxPriorityFeePerGas'] = max_priority
            txn['maxFeePerGas'] = base_fee + max_priority
        except Exception:
            txn['gasPrice'] = w3.eth.gas_price

        # 签名
        signed_txn = w3.eth.account.sign_transaction(txn, self.private_key)

        # 根据 broadcast 决定是否广播
        if self.broadcast:
            tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            return {
                "tx_hash": receipt.transactionHash.hex(),
                "block_number": receipt.blockNumber,
                "status": "success" if receipt.status == 1 else "failed"
            }
        else:
            return {
                "tx_hash": signed_txn.hash.hex(),
                "status": "signed (not broadcasted)"
            }

    def _execute_usdc_transfer(self, to_address, amount_usdc):
        """
        构造并签名 USDC 转账交易。
        根据 self.broadcast 决定是否广播上链。
        """
        if not self.private_key or not self.address:
            raise ValueError("请提供私钥和地址")

        amount_raw = int(amount_usdc * 1_000_000)

        txn = self.usdc_contract.functions.transfer(
            Web3.to_checksum_address(to_address),
            amount_raw
        ).build_transaction({
            "from": self.address,
            "chainId": w3.eth.chain_id,
            "gas": 100000,
            "nonce": w3.eth.get_transaction_count(self.address),
        })

        try:
            fee_data = w3.eth.fee_history(1, 'latest')
            max_priority = w3.eth.max_priority_fee
            base_fee = fee_data['baseFeePerGas'][0]
            txn['maxPriorityFeePerGas'] = max_priority
            txn['maxFeePerGas'] = base_fee + max_priority
        except Exception:
            txn['gasPrice'] = w3.eth.gas_price

        signed_txn = w3.eth.account.sign_transaction(txn, self.private_key)

        if self.broadcast:
            tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            return {
                "tx_hash": receipt.transactionHash.hex(),
                "block_number": receipt.blockNumber,
                "status": "success" if receipt.status == 1 else "failed"
            }
        else:
            return {
                "tx_hash": signed_txn.hash.hex(),
                "status": "signed (not broadcasted)"
            }

    def send(self, to, amount, currency="ETH"):
        """直接发起一笔纳米支付"""
        self._reset_daily_limit_if_new_day()
        if self._spent_today + amount > self.spend_limit_daily:
            raise DailyLimitExceededError("日限额超限")

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
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# ========== 自测代码 ==========
if __name__ == "__main__":
    # ===== 测试配置 =====
    TEST_PRIVATE_KEY = "0x6fd8aeba2983ea3eade0f68165376631d285827e74bcb69282c6783d6fb1b356"
    TEST_ADDRESS = "0x9cbF3Ca5185Ca55C804c2c4b726De212A17734F8"

    # ----- 模拟模式（不广播） -----
    print("===== 模拟模式（broadcast=False） =====")
    pay_sim = AgentPay(
        wallet_config={"private_key": TEST_PRIVATE_KEY, "address": TEST_ADDRESS},
        spend_limit_daily=0.001,
        broadcast=False
    )

    class MockResponseETH:
        status_code = 402
        headers = {
            "X-402-Payee": TEST_ADDRESS,
            "X-402-Amount": "0.0001",
            "X-402-Currency": "ETH",
            "X-402-Network": "base-sepolia"
        }

    receipt_eth_sim = pay_sim.auto_handle_402(MockResponseETH())
    print("✅ ETH 签名（模拟）:", json.dumps(receipt_eth_sim, indent=2, ensure_ascii=False))

    # ----- 如果测试币就绪，可以打开广播 -----
    # print("===== 真实广播（broadcast=True） =====")
    # pay_real = AgentPay(
    #     wallet_config={"private_key": TEST_PRIVATE_KEY, "address": TEST_ADDRESS},
    #     spend_limit_daily=0.001,
    #     broadcast=True
    # )
    # receipt_eth_real = pay_real.auto_handle_402(MockResponseETH())
    # print("✅ ETH 上链:", json.dumps(receipt_eth_real, indent=2, ensure_ascii=False))