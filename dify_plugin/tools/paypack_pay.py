"""
PayPack Pay Tool — Dify integration core.

AI Agent uses this tool to make payments:
- On-chain: USDC/ETH transfers (Base/Ethereum/Polygon/Arbitrum)
- Fiat: Alipay CNY payments
"""
import json
import os
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
        Execute payment.
        """
        recipient = tool_parameters.get("recipient", "")
        amount = float(tool_parameters.get("amount", 0))
        currency = tool_parameters.get("currency", "USDC").upper()
        subject = tool_parameters.get("subject", "AI Agent Payment")

        if amount <= 0:
            return [self.create_text_message("Error: Amount must be greater than 0")]

        credentials = self.runtime.credentials or {}
        payment_mode = credentials.get("payment_mode", "crypto")

        try:
            if currency == "CNY" or payment_mode == "alipay":
                return self._pay_alipay(recipient, amount, subject, credentials)
            else:
                return self._pay_crypto(recipient, amount, currency, credentials)
        except Exception as e:
            return [self.create_text_message(f"Payment failed: {str(e)}")]

    def _pay_crypto(
        self, to: str, amount: float, currency: str, creds: Dict[str, Any]
    ) -> list[ToolInvokeMessage]:
        """On-chain payment"""
        from paypack import AgentPay

        private_key = creds.get("private_key") or os.getenv("PRIVATE_KEY")
        if not private_key:
            return [self.create_text_message("Error: Private key not configured. Please set private_key in Dify plugin settings.")]

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
        """Alipay payment"""
        from paypack.signer.alipay import AlipaySigner
        from paypack import AgentPay

        app_id = creds.get("app_id")
        private_key = creds.get("private_key")
        alipay_public_key = creds.get("alipay_public_key")
        sandbox = creds.get("sandbox", "true").lower() == "true"

        # Handle private key — may be a file path or direct PEM content
        if private_key and ("BEGIN" in private_key or "PRIVATE KEY" in private_key):
            # Direct PEM string
            signer = AlipaySigner(
                app_id=app_id,
                private_key=private_key,
                alipay_public_key=alipay_public_key,
                sandbox=sandbox,
            )
        else:
            # File path
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
