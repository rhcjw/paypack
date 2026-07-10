"""
PayPack 支付工具 — Dify 集成核心。

AI Agent 通过此工具发起支付：
- 链上：USDC/ETH 转账（Base/Ethereum/Polygon/Arbitrum）
- 法币：支付宝人民币支付
"""
import json
import os
import tempfile
from typing import Any, Dict, Optional

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
from dify_plugin.runtime.session import Session


class PaypackPayTool(Tool):

    def _invoke(
        self,
        tool_parameters: Dict[str, Any],
        session: Optional[Session] = None,
    ) -> list[ToolInvokeMessage]:
        """
        执行支付。
        """
        recipient = tool_parameters.get("recipient", "")
        amount = float(tool_parameters.get("amount", 0))
        currency = tool_parameters.get("currency", "USDC").upper()
        subject = tool_parameters.get("subject", "AI Agent Payment")

        if amount <= 0:
            return [self.create_text_message("❌ 金额必须大于 0")]

        credentials = self.runtime.credentials or {}
        payment_mode = credentials.get("payment_mode", "crypto")

        try:
            if currency == "CNY" or payment_mode == "alipay":
                return self._pay_alipay(recipient, amount, subject, credentials)
            else:
                return self._pay_crypto(recipient, amount, currency, credentials)
        except Exception as e:
            return [self.create_text_message(f"❌ 支付失败: {str(e)}")]

    def _pay_crypto(
        self, to: str, amount: float, currency: str, creds: Dict[str, Any]
    ) -> list[ToolInvokeMessage]:
        """链上支付"""
        from paypack import AgentPay

        private_key = creds.get("private_key") or os.getenv("PRIVATE_KEY")
        if not private_key:
            return [self.create_text_message("❌ 未配置私钥。请在 Dify 插件设置中提供 private_key")]

        network = creds.get("network", "base-sepolia")
        limit = float(creds.get("spend_limit_daily", 10.0))
        broadcast = creds.get("broadcast", "false").lower() == "true"

        pay = AgentPay(
            wallet_config={"private_key": private_key},
            network=network,
            spend_limit_daily=limit,
            broadcast=broadcast,
        )

        receipt = pay.send(to=to, amount=amount, currency=currency)

        return [
            self.create_text_message(json.dumps({
                "status": "success",
                "currency": currency,
                "amount": amount,
                "recipient": to,
                "tx_hash": receipt.get("tx_hash"),
                "explorer_link": receipt.get("explorer_link"),
                "daily_remaining": receipt.get("daily_remaining"),
                "timestamp": receipt.get("timestamp"),
            }, ensure_ascii=False, indent=2))
        ]

    def _pay_alipay(
        self, buyer_id: str, amount: float, subject: str, creds: Dict[str, Any]
    ) -> list[ToolInvokeMessage]:
        """支付宝支付"""
        from paypack.signer.alipay import AlipaySigner
        from paypack import AgentPay

        app_id = creds.get("app_id")
        private_key = creds.get("private_key")
        alipay_public_key = creds.get("alipay_public_key")
        sandbox = creds.get("sandbox", "true").lower() == "true"

        # 处理私钥 —— 可能是文件路径，也可能是直接传入的 PEM 内容
        if private_key and ("BEGIN" in private_key or "PRIVATE KEY" in private_key):
            # 直接传入的 PEM 字符串
            signer = AlipaySigner(
                app_id=app_id,
                private_key=private_key,
                alipay_public_key=alipay_public_key,
                sandbox=sandbox,
            )
        else:
            # 文件路径
            signer = AlipaySigner(
                app_id=app_id,
                private_key_path=private_key,
                alipay_public_key=alipay_public_key,
                sandbox=sandbox,
            )

        pay = AgentPay(signer=signer, network="alipay")
        receipt = pay.send(
            to=buyer_id,
            amount=amount,
            currency="CNY",
            subject=subject,
        )

        alipay_resp = receipt.get("alipay_response", receipt)

        return [
            self.create_text_message(json.dumps({
                "status": "success",
                "currency": "CNY",
                "amount": amount,
                "subject": subject,
                "trade_no": receipt.get("trade_no"),
                "alipay_status": alipay_resp.get("code"),
                "alipay_message": alipay_resp.get("msg", alipay_resp.get("sub_msg", "")),
            }, ensure_ascii=False, indent=2))
        ]
