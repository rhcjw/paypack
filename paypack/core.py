"""
PayPack Core - AI Agent 通用支付中间件 v0.5.0
支持 Signer 依赖注入、ERC-4337 批量结算、RPC 故障转移、交易重试、限额持久化
"""

import os
import time
import json
import threading
import urllib.request
from datetime import datetime, date, timezone
from typing import Optional, Dict, Any, Union, List

from web3 import Web3

from paypack.signer.base import Signer
from paypack.signer.local import LocalSigner
from paypack.providers import FailoverProvider, create_failover_w3
from paypack.retry import RetryConfig, broadcast_with_retry, rbf_resend
from paypack.limits import LimitStore, InMemoryStore, create_limit_store


# ======== 多链网络配置（含故障转移 URL 列表）========
DEFAULT_NETWORKS = {
    "base-sepolia": {
        "chain_id": 84532,
        "rpc_url": "https://sepolia.base.org",
        "rpc_urls": [
            "https://sepolia.base.org",
            "https://base-sepolia.publicnode.com",
            "https://base-sepolia-rpc.publicnode.com",
        ],
        "usdc_address": "0x036CbD53842c5426634e7929541eC2318f3dCF7e",
        "usdt_address": "0x036CbD53842c5426634e7929541eC2318f3dCF7e",  # sepolia testnet USDT 同地址
        "native_currency": "ETH",
        "explorer": "https://sepolia.basescan.org",
    },
    "base-mainnet": {
        "chain_id": 8453,
        "rpc_url": "https://mainnet.base.org",
        "rpc_urls": [
            "https://mainnet.base.org",
            "https://base.publicnode.com",
            "https://base-rpc.publicnode.com",
        ],
        "usdc_address": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        "usdt_address": "0xfde4C96c8593536E31F229EA8f37b2ADa2699bb2",
        "native_currency": "ETH",
        "explorer": "https://basescan.org",
    },
    "ethereum-mainnet": {
        "chain_id": 1,
        "rpc_url": "https://mainnet.infura.io/v3/YOUR_INFURA_KEY",
        "rpc_urls": [],
        "usdc_address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "usdt_address": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
        "native_currency": "ETH",
        "explorer": "https://etherscan.io",
    },
    "polygon-mainnet": {
        "chain_id": 137,
        "rpc_url": "https://polygon-rpc.com",
        "rpc_urls": [
            "https://polygon-rpc.com",
            "https://polygon-bor.publicnode.com",
        ],
        "usdc_address": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
        "usdt_address": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
        "native_currency": "POL",
        "explorer": "https://polygonscan.com",
    },
    "arbitrum-mainnet": {
        "chain_id": 42161,
        "rpc_url": "https://arb1.arbitrum.io/rpc",
        "rpc_urls": [
            "https://arb1.arbitrum.io/rpc",
            "https://arbitrum-one.publicnode.com",
        ],
        "usdc_address": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
        "usdt_address": "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9",
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

ENTRY_POINT_ADDRESS = "0x5FF137D4b0FDCD49DcA30c7CF57E578a026d2789"

# ======== 匿名使用统计 ========
# 仅上报链上公开数据（网络、币种、金额范围），绝不触碰私钥或地址
# 可通过 AgentPay(telemetry=False) 关闭
TELEMETRY_ENDPOINT = os.getenv("PAYPACK_TELEMETRY_URL", "https://rhcjw.com/pay/api/telemetry")
TELEMETRY_ENABLED_DEFAULT = True


class InsufficientFundsError(Exception):
    pass


class DailyLimitExceededError(Exception):
    pass


class NetworkConfigError(Exception):
    pass


class AgentPay:
    """
    AI Agent 纳米支付客户端 v0.5.0。

    支持:
    - x402 / AP2 协议自动解析
    - ETH / USDC 转账 + ERC-4337 批量结算
    - Signer 依赖注入（本地 / AWS KMS）
    - RPC 故障转移（多节点自动切换）
    - 交易重试 + Replace-by-Fee
    - 限额持久化（Redis / SQLite / 内存）

    Usage:
        # 开发环境
        signer = LocalSigner(private_key="0x...")
        pay = AgentPay(signer=signer, network="base-sepolia")

        # 生产环境（全功能）
        signer = AWSKMSSigner(key_id="alias/paypack-eth-key")
        pay = AgentPay(
            signer=signer,
            network="base-mainnet",
            limit_store=create_limit_store("redis"),
            max_retries=3,
        )
    """

    def __init__(
        self,
        signer: Optional[Signer] = None,
        wallet_config: Optional[dict] = None,
        spend_limit_daily: float = 10.0,
        broadcast: bool = False,
        network: Union[str, Dict[str, Any]] = "base-sepolia",
        bundler_rpc_url: Optional[str] = None,
        # ---- v0.5 新增 ----
        rpc_urls: Optional[List[str]] = None,
        limit_store: Optional[LimitStore] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        tx_timeout: int = 120,
        # ---- v0.5.1 遥测 ----
        telemetry: bool = TELEMETRY_ENABLED_DEFAULT,
    ):
        # ---- Signer ----
        if signer is not None:
            self.signer = signer
        else:
            wallet_cfg = wallet_config or {}
            private_key = wallet_cfg.get("private_key") or os.getenv("PRIVATE_KEY")
            if not private_key:
                raise ValueError(
                    "私钥未提供。请传入 signer 参数，或 wallet_config['private_key']，或设置 PRIVATE_KEY"
                )
            self.signer = LocalSigner(private_key=private_key)

        # ---- 限额持久化 ----
        self._limit_store = limit_store or InMemoryStore()
        self.spend_limit_daily = spend_limit_daily

        self.broadcast = broadcast
        self.address = self.signer.get_address()
        self.telemetry = telemetry  # 匿名使用统计

        # ---- 重试配置 ----
        self.retry_config = RetryConfig(
            max_retries=max_retries,
            retry_delay=retry_delay,
            tx_timeout=tx_timeout,
        )

        self._init_network(network, rpc_urls)

        if not getattr(self, '_offchain_mode', False):
            try:
                self.usdc_contract = self.w3.eth.contract(
                    address=Web3.to_checksum_address(self.usdc_address),
                    abi=USDC_ABI,
                )
                self.usdc_decimals = self.usdc_contract.functions.decimals().call()
            except Exception:
                self.usdc_contract = None
                self.usdc_decimals = 6
            try:
                self.usdt_contract = self.w3.eth.contract(
                    address=Web3.to_checksum_address(self.usdt_address),
                    abi=USDC_ABI,  # USDT 也是 ERC-20，ABI 通用
                )
                self.usdt_decimals = self.usdt_contract.functions.decimals().call()
            except Exception:
                self.usdt_contract = None
                self.usdt_decimals = 6
        else:
            self.usdc_contract = None
            self.usdc_decimals = 6
            self.usdt_contract = None
            self.usdt_decimals = 6
        self._bundler_url = bundler_rpc_url

    def _init_network(self, network, rpc_urls=None):
        # ---- 支付宝 / 微信支付等非链上网络，跳过 Web3 初始化 ----
        if isinstance(network, str) and network.lower() in ("alipay", "wechat"):
            self.network_name = network
            self.chain_id = 0
            self.rpc_url = ""
            self.usdc_address = "0x0000000000000000000000000000000000000000"
            self.usdt_address = "0x0000000000000000000000000000000000000000"
            self.native_currency = "CNY"
            self.explorer = ""
            self.w3 = None
            self._offchain_mode = True
            return

        if isinstance(network, str):
            config = DEFAULT_NETWORKS.get(network)
            if not config:
                raise NetworkConfigError(f"未知网络: {network}")
            self.network_name = network
            self.chain_id = config["chain_id"]
            self.rpc_url = config["rpc_url"]
            self.usdc_address = config["usdc_address"]
            self.usdt_address = config.get("usdt_address", config.get("usdc_address"))
            self.native_currency = config.get("native_currency", "ETH")
            self.explorer = config.get("explorer", "")
            fallback_urls = rpc_urls or config.get("rpc_urls", [])
            if not fallback_urls:
                fallback_urls = [config["rpc_url"]]
        elif isinstance(network, dict):
            self.network_name = network.get("name", "custom")
            self.chain_id = network.get("chain_id")
            self.rpc_url = network.get("rpc_url")
            self.usdc_address = network.get("usdc_address")
            self.usdt_address = network.get("usdt_address", network.get("usdc_address"))
            self.native_currency = network.get("native_currency", "ETH")
            self.explorer = network.get("explorer", "")
            fallback_urls = rpc_urls or network.get("rpc_urls", [self.rpc_url])
        else:
            raise NetworkConfigError("network 参数必须是字符串或字典")

        self._offchain_mode = False

        if len(fallback_urls) > 1:
            self.w3 = create_failover_w3(fallback_urls, request_kwargs={"timeout": 10})
        else:
            self.w3 = Web3(Web3.HTTPProvider(fallback_urls[0], request_kwargs={"timeout": 10}))

        if not self.w3.is_connected():
            raise NetworkConfigError(f"无法连接到任何 RPC 节点: {fallback_urls}")

    # ======== 限额持久化 ========

    def _reset_daily_limit_if_new_day(self):
        self._limit_store.reset_if_new_day(self.address)

    def _get_spent_today(self) -> float:
        return self._limit_store.get_spent_today(self.address)

    def _add_spent(self, amount: float):
        self._limit_store.add_spent(self.address, amount)

    # ======== 余额检查 ========

    def _ensure_sufficient_balance(self, currency: str, amount: float):
        if currency.upper() == "CNY":
            return  # 支付宝自身保证余额
        if currency.upper() in ("USDC", "USDT"):
            contract = self.usdt_contract if currency.upper() == "USDT" else self.usdc_contract
            decimals = self.usdt_decimals if currency.upper() == "USDT" else self.usdc_decimals
            balance_raw = contract.functions.balanceOf(self.address).call()
            balance = balance_raw / (10 ** decimals)
        else:
            balance_raw = self.w3.eth.get_balance(self.address)
            balance = self.w3.from_wei(balance_raw, "ether")

        if balance < amount:
            raise InsufficientFundsError(
                f"余额不足: 当前 {balance:.6f} {currency}, 需要 {amount:.6f} {currency}"
            )

    # ======== 协议解析 ========

    def auto_handle_402(self, response):
        if response.status_code != 402:
            raise ValueError("仅支持处理 402 状态码")
        headers = response.headers
        if "X-402-Payee" in headers:
            info = self._parse_x402_headers(headers)
        elif "X-AP2-Payee" in headers:
            info = self._parse_ap2_headers(headers)
        else:
            raise ValueError("无法识别的支付协议头，仅支持 x402 和 AP2")
        return self.send(to=info["payee"], amount=float(info.get("amount", 0)), currency=info.get("currency", "ETH"))

    def _parse_x402_headers(self, h):
        return {"payee": h.get("X-402-Payee", ""), "amount": h.get("X-402-Amount", "0"),
                "currency": h.get("X-402-Currency", "ETH"), "network": h.get("X-402-Network", self.network_name)}

    def _parse_ap2_headers(self, h):
        return {"payee": h.get("X-AP2-Payee", ""), "amount": h.get("X-AP2-Amount", "0"),
                "currency": h.get("X-AP2-Currency", "USDC"), "network": h.get("X-AP2-Network", self.network_name)}

    # ======== 交易构建与广播（带重试）========

    def _build_transaction(self, to_address, value=0, data="0x", gas=21000):
        to_address = Web3.to_checksum_address(to_address)
        txn = {
            "from": self.address,
            "to": to_address,
            "value": value,
            "gas": gas,
            "nonce": self.w3.eth.get_transaction_count(self.address),
            "chainId": self.chain_id,
        }
        if data and data != "0x":
            txn["data"] = data
        try:
            fee_data = self.w3.eth.fee_history(1, "latest")
            txn["maxPriorityFeePerGas"] = self.w3.eth.max_priority_fee
            txn["maxFeePerGas"] = fee_data["baseFeePerGas"][0] + txn["maxPriorityFeePerGas"]
        except Exception:
            txn["gasPrice"] = self.w3.eth.gas_price
        return txn

    def _sign_and_broadcast(self, txn):
        signed = self.signer.sign_transaction(txn)
        if self.broadcast:
            def send_fn(): return self.w3.eth.send_raw_transaction(signed.raw_transaction)
            def wait_fn(h, **kwargs): return self.w3.eth.wait_for_transaction_receipt(h, **kwargs)
            def nonce_fn(): return self.w3.eth.get_transaction_count(self.address)
            return broadcast_with_retry(send_fn, wait_fn, nonce_fn, self.retry_config)
        return {"tx_hash": signed.hash.hex(), "block_number": None, "status": "signed (not broadcasted)", "attempts": 1}

    def _execute_eth_transfer(self, to_address, amount_eth):
        txn = self._build_transaction(to_address, self.w3.to_wei(amount_eth, "ether"), gas=21000)
        r = self._sign_and_broadcast(txn)
        r.update({"to": to_address, "amount": amount_eth, "currency": "ETH",
                   "network": self.network_name,
                   "explorer_link": f"{self.explorer}/tx/{r['tx_hash']}" if self.explorer else None})
        return r

    def _execute_erc20_transfer(self, to_address, amount, currency="USDC"):
        """执行 ERC-20 转账，支持 USDC 和 USDT"""
        to_address = Web3.to_checksum_address(to_address)
        contract = self.usdt_contract if currency == "USDT" else self.usdc_contract
        decimals = self.usdt_decimals if currency == "USDT" else self.usdc_decimals
        amount_raw = int(amount * (10 ** decimals))
        txn = contract.functions.transfer(to_address, amount_raw).build_transaction({
            "from": self.address, "chainId": self.chain_id, "gas": 100000,
            "nonce": self.w3.eth.get_transaction_count(self.address),
        })
        try:
            fee_data = self.w3.eth.fee_history(1, "latest")
            txn["maxPriorityFeePerGas"] = self.w3.eth.max_priority_fee
            txn["maxFeePerGas"] = fee_data["baseFeePerGas"][0] + txn["maxPriorityFeePerGas"]
        except Exception:
            txn["gasPrice"] = self.w3.eth.gas_price
        r = self._sign_and_broadcast(txn)
        r.update({"to": to_address, "amount": amount, "currency": currency,
                   "network": self.network_name,
                   "explorer_link": f"{self.explorer}/tx/{r['tx_hash']}" if self.explorer else None})
        return r

    # ======== 遥测（匿名使用统计）========

    @staticmethod
    def _classify_amount(amount: float) -> str:
        """将金额归入范围，不暴露精确值"""
        if amount <= 0.001:
            return "micro"
        elif amount <= 0.1:
            return "small"
        elif amount <= 1:
            return "medium"
        elif amount <= 100:
            return "large"
        else:
            return "xlarge"

    def _report_telemetry(self, event_type: str, payload: dict):
        """
        异步上报匿名统计。
        - 仅上报链上公开数据，绝不触碰私钥或完整地址
        - 异步非阻塞，上报失败不影响支付
        - 可通过 AgentPay(telemetry=False) 关闭
        """
        if not self.telemetry:
            return

        safe = {
            "event": event_type,
            "network": getattr(self, "network_name", "unknown"),
            "currency": payload.get("currency", ""),
            "amount_range": self._classify_amount(payload.get("amount", 0)),
            "success": payload.get("success", False),
            "broadcast": getattr(self, "broadcast", False),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        def _send():
            try:
                data = json.dumps(safe).encode("utf-8")
                req = urllib.request.Request(
                    TELEMETRY_ENDPOINT,
                    data=data,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                urllib.request.urlopen(req, timeout=3)
            except Exception:
                pass  # 上报失败绝不抛异常，不影响支付

        t = threading.Thread(target=_send, daemon=True)
        t.start()

    # ======== 单笔支付 ========

    def send(self, to, amount, currency="ETH", **kwargs):
        self._reset_daily_limit_if_new_day()
        spent = self._get_spent_today()
        if spent + amount > self.spend_limit_daily:
            raise DailyLimitExceededError(f"日限额超限: 今日已消费 {spent:.6f}, 本次需 {amount:.6f}")
        self._ensure_sufficient_balance(currency, amount)

        if currency.upper() == "CNY":
            # duck typing: detect WechatSigner without importing it
            if hasattr(self.signer, 'create_jsapi_order'):
                tx = self._execute_wechat_transfer(to, amount, **kwargs)
            else:
                tx = self._execute_alipay_transfer(to, amount, **kwargs)
        elif currency.upper() in ("USDC", "USDT"):
            tx = self._execute_erc20_transfer(to, amount, currency.upper())
        else:
            tx = self._execute_eth_transfer(to, amount)

        self._add_spent(amount)
        new_spent = self._get_spent_today()

        result = {
            "to": to, "amount": amount, "currency": currency,
            "tx_hash": tx.get("tx_hash", tx.get("trade_no")),
            "status": tx["status"],
            "attempts": tx.get("attempts", 1),
            "explorer_link": tx.get("explorer_link"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "daily_remaining": round(self.spend_limit_daily - new_spent, 6),
        }

        # 匿名遥测：支付成功后上报（异步，不影响主流程）
        self._report_telemetry("payment_success", {
            "currency": currency, "amount": amount, "success": True
        })
        return result

    def _execute_alipay_transfer(self, to, amount, **kwargs):
        """执行支付宝支付"""
        import uuid
        trade_no = kwargs.pop("out_trade_no", f"PAYPACK_{int(time.time())}_{uuid.uuid4().hex[:8]}")
        subject = kwargs.pop("subject", "AI Agent Payment")
        buyer_id = kwargs.pop("buyer_id", to)

        result = self.signer.create_payment(
            out_trade_no=trade_no,
            total_amount=amount,
            subject=subject,
            buyer_id=buyer_id,
            **kwargs,
        )

        alipay_resp = result.get("alipay_trade_create_response", result)
        return {
            "trade_no": alipay_resp.get("trade_no", trade_no),
            "status": "pending" if alipay_resp.get("code") == "10000" else "failed",
            "alipay_response": alipay_resp,
        }

    def _execute_wechat_transfer(self, to, amount, **kwargs):
        """
        执行微信支付（JSAPI）。

        开源的 AgentPay 不包含微信支付实现。此方法通过 duck typing
        检测 signer 是否实现了 create_jsapi_order，
        具体实现在闭源的 paypack-wechat 包中。

        Usage (需要安装 paypack-wechat):
            from paypack_wechat import WechatSigner
            signer = WechatSigner(mchid="...", private_key="...", ...)
            pay = AgentPay(signer=signer, network="wechat")
            pay.send(to="用户openid", amount=9.90, currency="CNY",
                     subject="AI 服务订阅", app_id="公众号APPID")
        """
        trade_no = kwargs.pop("out_trade_no", None)
        subject = kwargs.pop("subject", "AI Agent Payment")
        app_id = kwargs.pop("app_id", "")

        # WechatSigner.create_jsapi_order() 返回 prepay 参数
        # （请求 JSAPI 下单 → 返回前端调起微信支付所需的参数）
        result = self.signer.create_jsapi_order(
            openid=to,
            amount=amount,
            description=subject,
            out_trade_no=trade_no,
            app_id=app_id,
            **kwargs,
        )

        return {
            "trade_no": result.get("out_trade_no", result.get("trade_no")),
            "status": "pending" if result.get("prepay_id") else "failed",
            "wechat_response": result,
        }

    # ======== ERC-4337 批量支付 ========

    def batch_pay(self, payments: List[dict]) -> dict:
        if len(payments) == 0:
            raise ValueError("payments 不能为空")
        if len(payments) == 1:
            p = payments[0]
            return self.send(to=p["to"], amount=p["amount"], currency=p.get("currency", "ETH"))

        self._reset_daily_limit_if_new_day()
        spent = self._get_spent_today()
        total = sum(p["amount"] for p in payments)
        if spent + total > self.spend_limit_daily:
            raise DailyLimitExceededError(f"日限额超限: 今日已消费 {spent:.6f}, 批量需 {total:.6f}")
        for p in payments:
            self._ensure_sufficient_balance(p.get("currency", "ETH"), p["amount"])

        calls = []
        for p in payments:
            cur = p.get("currency", "ETH")
            to_addr = Web3.to_checksum_address(p["to"])
            if cur.upper() == "USDC":
                raw = int(p["amount"] * (10 ** self.usdc_decimals))
                calls.append({"to": self.usdc_address, "value": 0,
                              "data": self.usdc_contract.encode_abi("transfer", args=[to_addr, raw])})
            else:
                calls.append({"to": to_addr, "value": self.w3.to_wei(p["amount"], "ether"), "data": "0x"})

        from paypack.nanopay import ERC4337Batcher
        batcher = ERC4337Batcher(entry_point_address=ENTRY_POINT_ADDRESS, chain_id=self.chain_id)
        uo = batcher.build_user_operation(sender=self.address, calls=calls, nonce=self.w3.eth.get_transaction_count(self.address))
        signed_uo = self.signer.sign_user_operation(uo)

        bundler_result = None
        if self._bundler_url:
            from paypack.nanopay import BundlerClient
            bundler_result = {"user_op_hash": BundlerClient(self._bundler_url).send_user_operation(signed_uo, ENTRY_POINT_ADDRESS)}

        self._add_spent(total)
        return {
            "batch_size": len(payments), "total_amount": total, "payments": payments,
            "user_operation": signed_uo, "bundler_result": bundler_result,
            "status": "bundled" if bundler_result else "signed (no bundler)",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "daily_remaining": round(self.spend_limit_daily - self._get_spent_today(), 6),
        }


def create_agent_pay(
    private_key=None, wallet_address=None, network="base-sepolia",
    spend_limit_daily=10.0, broadcast=False, signer=None,
    limit_backend="memory", max_retries=3, **kwargs,
) -> AgentPay:
    limit_store = create_limit_store(limit_backend, **kwargs)
    if signer is not None:
        return AgentPay(signer=signer, network=network, spend_limit_daily=spend_limit_daily,
                        broadcast=broadcast, limit_store=limit_store, max_retries=max_retries)
    return AgentPay(
        wallet_config={"private_key": private_key, "address": wallet_address},
        network=network, spend_limit_daily=spend_limit_daily,
        broadcast=broadcast, limit_store=limit_store, max_retries=max_retries,
    )


if __name__ == "__main__":
    print("请设置环境变量 PRIVATE_KEY，然后运行测试。")
