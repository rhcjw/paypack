""" 
PayPack Pay Tool — Dify integration core.

AI Agent uses this tool to make payments.
Auto-routes to the correct channel:
- Cloud mode (recommended) → PayPack Cloud API → Alipay/WeChat QR code
- USDC / ETH → Crypto (on-chain)
- CNY + alipay credentials → Alipay (local signing)
- CNY + wechat credentials → WeChat Pay (local signing)
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
        """Execute payment. Auto-routes by currency and available credentials."""
        recipient = tool_parameters.get("recipient", "")
        amount = float(tool_parameters.get("amount", 0))
        currency = tool_parameters.get("currency", "CNY").upper()
        subject = tool_parameters.get("subject", "AI Agent Payment")
        channel = tool_parameters.get("channel", "").lower()

        if amount <= 0:
            return [self.create_text_message("Error: Amount must be greater than 0")]

        credentials = self.runtime.credentials or {}

        try:
            # Priority 1: Cloud mode (simplest — just API Key)
            has_cloud = bool(credentials.get("paypack_api_key"))
            if has_cloud and currency == "CNY":
                return self._pay_cloud(amount, subject, channel or "alipay", credentials)

            # Priority 2: Crypto (on-chain)
            if currency in ("USDC", "ETH"):
                return self._pay_crypto(recipient, amount, currency, credentials)

            # Priority 3: Local Alipay signing
            if currency == "CNY":
                has_alipay = bool(credentials.get("alipay_app_id"))
                has_wechat = bool(credentials.get("wechat_mchid"))
                if has_alipay and not has_wechat:
                    return self._pay_alipay(recipient, amount, subject, credentials)
                elif has_wechat and not has_alipay:
                    return self._pay_wechat(recipient, amount, subject, credentials)
                elif has_alipay and has_wechat:
                    if subject and "wechat" in subject.lower():
                        return self._pay_wechat(recipient, amount, subject, credentials)
                    return self._pay_alipay(recipient, amount, subject, credentials)
                else:
                    return [self.create_text_message(
                        "Error: No payment channel configured. "
                        "Get a free API Key at https://rhcjw.com/pay/dashboard and set paypack_api_key in plugin credentials."
                    )]
            else:
                return [self.create_text_message(f"Unsupported currency '{currency}'. Use USDC, ETH, or CNY.")]
        except Exception as e:
            return [self.create_text_message(f"Payment failed: {str(e)}")]

    # ── Cloud API (recommended) ──────────────────────────

    def _pay_cloud(
        self, amount: float, subject: str, channel: str, creds: Dict[str, Any]
    ) -> list[ToolInvokeMessage]:
        """Call PayPack Cloud API to create payment order. Returns QR code URL."""
        import requests

        cloud_url = (creds.get("paypack_cloud_url") or "https://rhcjw.com/pay").rstrip("/")
        api_key = creds.get("paypack_api_key")

        if not api_key:
            return [self.create_text_message(
                "Error: Cloud API Key not set. Get one at https://rhcjw.com/pay/dashboard"
            )]

        try:
            resp = requests.post(
                f"{cloud_url}/v1/pay",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
                json={
                    "amount": amount,
                    "subject": subject,
                    "channel": channel or "alipay",
                    "currency": "CNY",
                },
                timeout=15,
            )

            if resp.status_code == 402:
                return [self.create_text_message(
                    "Error: Insufficient balance. Please top up at https://rhcjw.com/pay/dashboard"
                )]
            if resp.status_code != 200:
                err = resp.json().get("error", resp.text)
                return [self.create_text_message(f"Error: {err}")]

            data = resp.json()
            return [
                self.create_text_message(json.dumps({
                    "channel": channel or "alipay",
                    "status": "pending",
                    "currency": "CNY",
                    "amount": amount,
                    "subject": subject,
                    "order_id": data.get("order_id"),
                    "pay_url": data.get("pay_url"),
                    "qr_code": data.get("qr_code"),
                    "instruction": "Show the QR code to the user for payment. Use qr_code URL to generate a QR image.",
                }, ensure_ascii=False, indent=2))
            ]
        except requests.ConnectionError:
            return [self.create_text_message(
                f"Error: Cannot connect to PayPack Cloud at {cloud_url}. Is the service running?"
            )]

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
