"""
PayPack Pay Tool — Dify integration core.

AI Agent uses this tool to make payments.
Auto-routes to the correct channel based on currency:
- USDC / ETH  → Crypto (on-chain)
- CNY + alipay credentials → Alipay
- CNY + wechat credentials  → WeChat Pay
All channels can be configured at once in a single plugin instance.
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
        """Execute payment. Auto-routes by currency."""
        recipient = tool_parameters.get("recipient", "")
        amount = float(tool_parameters.get("amount", 0))
        currency = tool_parameters.get("currency", "USDC").upper()
        subject = tool_parameters.get("subject", "AI Agent Payment")

        if amount <= 0:
            return [self.create_text_message("Error: Amount must be greater than 0")]

        credentials = self.runtime.credentials or {}

        try:
            if currency in ("USDC", "ETH"):
                return self._pay_crypto(recipient, amount, currency, credentials)
            elif currency == "CNY":
                has_alipay = bool(credentials.get("alipay_app_id"))
                has_wechat = bool(credentials.get("wechat_mchid"))
                if has_alipay and not has_wechat:
                    return self._pay_alipay(recipient, amount, subject, credentials)
                elif has_wechat and not has_alipay:
                    return self._pay_wechat(recipient, amount, subject, credentials)
                elif has_alipay and has_wechat:
                    # Both configured — check subject for hint
                    if subject and "wechat" in subject.lower():
                        return self._pay_wechat(recipient, amount, subject, credentials)
                    return self._pay_alipay(recipient, amount, subject, credentials)
                else:
                    return [self.create_text_message(
                        "Error: CNY selected but neither Alipay nor WeChat Pay configured. "
                        "Set up Alipay or WeChat Pay in plugin settings."
                    )]
            else:
                return [self.create_text_message(f"Unsupported currency '{currency}'. Use USDC, ETH, or CNY.")]
        except Exception as e:
            return [self.create_text_message(f"Payment failed: {str(e)}")]

    # ── Crypto ──────────────────────────────────────────

    def _pay_crypto(
        self, to: str, amount: float, currency: str, creds: Dict[str, Any]
    ) -> list[ToolInvokeMessage]:
        """On-chain USDC/ETH payment."""
        from paypack import AgentPay

        private_key = creds.get("crypto_private_key") or os.getenv("PRIVATE_KEY")
        if not private_key:
            return [self.create_text_message(
                "Error: Crypto private key not configured. Set crypto_private_key in plugin settings."
            )]

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
                "channel": "crypto",
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

    # ── Alipay ──────────────────────────────────────────

    def _pay_alipay(
        self, buyer_id: str, amount: float, subject: str, creds: Dict[str, Any]
    ) -> list[ToolInvokeMessage]:
        """Alipay CNY payment."""
        from paypack.signer.alipay import AlipaySigner
        from paypack import AgentPay

        app_id = creds.get("alipay_app_id")
        private_key = creds.get("alipay_private_key")
        alipay_public_key = creds.get("alipay_public_key")
        sandbox = creds.get("alipay_sandbox", "true").lower() == "true"

        if private_key and ("BEGIN" in private_key or "PRIVATE KEY" in private_key):
            signer = AlipaySigner(
                app_id=app_id,
                private_key=private_key,
                alipay_public_key=alipay_public_key,
                sandbox=sandbox,
            )
        else:
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
                "channel": "alipay",
                "status": "success",
                "currency": "CNY",
                "amount": amount,
                "subject": subject,
                "trade_no": receipt.get("trade_no"),
                "alipay_status": alipay_resp.get("code"),
                "alipay_message": alipay_resp.get("msg", alipay_resp.get("sub_msg", "")),
            }, ensure_ascii=False, indent=2))
        ]

    # ── WeChat Pay ──────────────────────────────────────

    def _pay_wechat(
        self, openid: str, amount: float, subject: str, creds: Dict[str, Any]
    ) -> list[ToolInvokeMessage]:
        """WeChat Pay CNY payment."""
        from paypack import AgentPay
        from paypack_wechat import WechatSigner

        signer = WechatSigner(
            mchid=creds.get("wechat_mchid"),
            serial_no=creds.get("wechat_serial_no"),
            private_key_path=creds.get("wechat_private_key"),
            api_v3_key=creds.get("wechat_api_v3_key"),
            license_key=creds.get("wechat_license_key"),
            app_id=creds.get("wechat_app_id"),
            notify_url=creds.get("wechat_notify_url"),
        )

        pay = AgentPay(signer=signer, network="wechat")
        result = pay.send(
            to=openid,
            amount=amount,
            currency="CNY",
            subject=subject,
            app_id=creds.get("wechat_app_id"),
        )

        return [
            self.create_text_message(json.dumps({
                "channel": "wechat",
                "status": "success",
                "currency": "CNY",
                "amount": amount,
                "subject": subject,
                "prepay_params": result.get("prepay_params"),
            }, ensure_ascii=False, indent=2))
        ]
