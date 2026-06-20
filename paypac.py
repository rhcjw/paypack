"""
PayPack - AI Agent 通用支付中间件
v0.1.0
"""

import json
from datetime import datetime, date


class InsufficientFundsError(Exception):
    """余额不足"""
    pass


class DailyLimitExceededError(Exception):
    """日限额超限"""
    pass


class AgentPay:
    """AI 代理支付客户端"""

    def __init__(self, wallet_config=None, spend_limit_daily=10.0):
        self.wallet_config = wallet_config or {}
        self.spend_limit_daily = spend_limit_daily
        self._today = date.today()
        self._spent_today = 0.0

    def _reset_daily_limit_if_new_day(self):
        """跨天自动重置日消费额度"""
        if date.today() != self._today:
            self._today = date.today()
            self._spent_today = 0.0

    def auto_handle_402(self, response):
        """
        自动处理 HTTP 402 响应。
        解析响应头中的付款信息，校验限额，返回支付后的响应体。
        
        参数:
            response: 一个模拟的 HTTP 响应对象，需包含 status_code 和 headers
        
        返回:
            包含交易信息的字典
        """
        if response.status_code != 402:
            raise ValueError("仅支持处理 402 状态码")

        # 1. 解析 x402 协议头
        payment_info = self._parse_x402_headers(response.headers)

        # 2. 提取收款地址和金额
        payee = payment_info.get("payee")
        amount = float(payment_info.get("amount", 0))
        currency = payment_info.get("currency", "USDC")
        network = payment_info.get("network", "base")

        # 3. 日限额校验
        self._reset_daily_limit_if_new_day()
        if self._spent_today + amount > self.spend_limit_daily:
            raise DailyLimitExceededError(
                f"今日已消费 ${self._spent_today:.4f}，"
                f"本次需支付 ${amount:.4f}，超出日限额 ${self.spend_limit_daily:.2f}"
            )

        # 4. 执行支付（当前为模拟，后续接入真实链上转账）
        tx_receipt = self._execute_payment(payee, amount, currency, network)

        # 5. 扣减今日额度
        self._spent_today += amount

        return {
            "status": "paid",
            "payee": payee,
            "amount": amount,
            "currency": currency,
            "network": network,
            "tx_hash": tx_receipt.get("tx_hash"),
            "timestamp": datetime.utcnow().isoformat(),
            "daily_remaining": round(self.spend_limit_daily - self._spent_today, 4)
        }

    def _parse_x402_headers(self, headers):
        """
        解析 x402 协议响应头。
        x402 标准头示例:
            X-402-Payee: 0x收款地址
            X-402-Amount: 0.01
            X-402-Currency: USDC
            X-402-Network: base
        """
        return {
            "payee": headers.get("X-402-Payee", ""),
            "amount": headers.get("X-402-Amount", "0"),
            "currency": headers.get("X-402-Currency", "USDC"),
            "network": headers.get("X-402-Network", "base")
        }

    def _execute_payment(self, payee, amount, currency, network):
        """
        执行实际支付（当前为模拟，后续对接 web3.py 链上转账）。
        """
        # TODO: 接入真实链上支付
        return {
            "tx_hash": f"mock_tx_{datetime.utcnow().timestamp()}",
            "status": "success"
        }

    def send(self, to, amount, currency="USDC"):
        """
        直接发起一笔纳米支付。
        """
        self._reset_daily_limit_if_new_day()
        if self._spent_today + amount > self.spend_limit_daily:
            raise DailyLimitExceededError("日限额超限")

        tx_receipt = self._execute_payment(to, amount, currency, "base")
        self._spent_today += amount

        return {
            "to": to,
            "amount": amount,
            "currency": currency,
            "tx_hash": tx_receipt.get("tx_hash"),
            "timestamp": datetime.utcnow().isoformat()
        }


# ========== 自测代码（不会影响 SDK 被引用） ==========
if __name__ == "__main__":
    # 模拟一个 HTTP 402 响应对象
    class MockResponse:
        status_code = 402
        headers = {
            "X-402-Payee": "0xABCDEF1234567890",
            "X-402-Amount": "0.01",
            "X-402-Currency": "USDC",
            "X-402-Network": "base"
        }

    # 初始化 AgentPay，设置日限额 1 美元
    pay = AgentPay(spend_limit_daily=1.0)

    # 处理模拟的 402 响应
    mock_resp = MockResponse()
    receipt = pay.auto_handle_402(mock_resp)

    print("✅ 支付成功！收据如下：")
    print(json.dumps(receipt, indent=2, ensure_ascii=False))