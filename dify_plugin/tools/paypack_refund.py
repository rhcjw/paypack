"""
PayPack 退款工具。
"""
import json
from typing import Any, Dict, Optional

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
from dify_plugin.runtime.session import Session


class PaypackRefundTool(Tool):

    def _invoke(
        self,
        tool_parameters: Dict[str, Any],
        session: Optional[Session] = None,
    ) -> list[ToolInvokeMessage]:
        trade_no = tool_parameters.get("trade_no", "")
        refund_amount = tool_parameters.get("refund_amount")

        if not trade_no:
            return [self.create_text_message("❌ 缺少交易号/订单号")]

        credentials = self.runtime.credentials or {}

        try:
            from paypack.signer.alipay import AlipaySigner

            app_id = credentials.get("app_id")
            private_key = credentials.get("private_key")
            alipay_public_key = credentials.get("alipay_public_key")
            sandbox = credentials.get("sandbox", "true").lower() == "true"

            if private_key and "BEGIN" in private_key:
                signer = AlipaySigner(
                    app_id=app_id, private_key=private_key,
                    alipay_public_key=alipay_public_key, sandbox=sandbox,
                )
            else:
                signer = AlipaySigner(
                    app_id=app_id, private_key_path=private_key,
                    alipay_public_key=alipay_public_key, sandbox=sandbox,
                )

            amount = float(refund_amount) if refund_amount else None
            result = signer.refund(trade_no, amount) if amount else signer.refund(trade_no, 0.0)
            resp = result.get("alipay_trade_refund_response", result)

            return [
                self.create_text_message(json.dumps({
                    "trade_no": trade_no,
                    "refund_amount": amount,
                    "code": resp.get("code"),
                    "message": resp.get("msg", resp.get("sub_msg", "")),
                    "refund_status": "success" if resp.get("code") == "10000" else "failed",
                }, ensure_ascii=False, indent=2))
            ]

        except Exception as e:
            return [self.create_text_message(f"❌ 退款失败: {str(e)}")]
