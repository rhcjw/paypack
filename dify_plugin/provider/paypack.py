"""
PayPack Dify Provider — Register PayPack payment tools in Dify tool list.
"""
from typing import Any, Dict

from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError

class PaypackProvider(ToolProvider):

    def _validate_credentials(self, credentials: Dict[str, Any]) -> None:
        """
        Validate user-provided credentials.

        Alipay mode requires: app_id, private_key, alipay_public_key
        Crypto mode requires: private_key (ETH), network
        """
        payment_mode = credentials.get("payment_mode", "crypto")

        if payment_mode == "alipay":
            required = ["app_id", "private_key", "alipay_public_key"]
            for field in required:
                if not credentials.get(field):
                    raise ToolProviderCredentialValidationError(
                        f"Alipay mode missing required parameter: {field}"
                    )
        elif payment_mode == "crypto":
            if not credentials.get("private_key"):
                raise ToolProviderCredentialValidationError(
                    "Crypto payment mode requires private_key"
                )
        else:
            raise ToolProviderCredentialValidationError(
                f"Unsupported payment mode: {payment_mode}"
            )
