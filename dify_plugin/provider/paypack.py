"""
PayPack Dify Provider — 注册 PayPack 支付工具到 Dify 工具列表。
"""
from typing import Any, Dict

from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError

class PaypackProvider(ToolProvider):

    def _validate_credentials(self, credentials: Dict[str, Any]) -> None:
        """
        验证用户提供的凭据是否有效。

        支付宝模式需要: app_id, private_key, alipay_public_key
        链上模式需要: private_key (ETH), network
        """
        payment_mode = credentials.get("payment_mode", "crypto")

        if payment_mode == "alipay":
            required = ["app_id", "private_key", "alipay_public_key"]
            for field in required:
                if not credentials.get(field):
                    raise ToolProviderCredentialValidationError(
                        f"支付宝模式缺少必要参数: {field}"
                    )
        elif payment_mode == "crypto":
            if not credentials.get("private_key"):
                raise ToolProviderCredentialValidationError(
                    "链上支付模式需要提供 private_key"
                )
        else:
            raise ToolProviderCredentialValidationError(
                f"不支持的支付模式: {payment_mode}"
            )
