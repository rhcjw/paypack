"""
PayPack Dify Provider — Register PayPack payment tools in Dify tool list.
"""
from typing import Any, Dict

from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError


class PaypackProvider(ToolProvider):

    def _validate_credentials(self, credentials: Dict[str, Any]) -> None:
        """
        Validate user-provided credentials. Supports all channels in one config.
        At least one payment channel must be configured.
        """
        has_cloud = bool(credentials.get("paypack_api_key"))
        has_crypto = bool(credentials.get("crypto_private_key"))
        has_alipay = bool(credentials.get("alipay_app_id") and credentials.get("alipay_private_key"))
        has_wechat = bool(credentials.get("wechat_mchid") and credentials.get("wechat_private_key"))

        if not has_cloud and not has_crypto and not has_alipay and not has_wechat:
            raise ToolProviderCredentialValidationError(
                "At least one payment channel must be configured. "
                "Easiest: fill in Cloud API Key (get it at rhcjw.com/pay/dashboard)."
            )

        if has_alipay:
            if not credentials.get("alipay_public_key"):
                raise ToolProviderCredentialValidationError(
                    "Alipay mode requires: alipay_public_key"
                )

        if has_wechat:
            missing_wx = []
            for f in ["wechat_serial_no", "wechat_api_v3_key", "wechat_app_id", "wechat_license_key"]:
                if not credentials.get(f):
                    missing_wx.append(f)
            if missing_wx:
                raise ToolProviderCredentialValidationError(
                    f"WeChat Pay missing: {', '.join(missing_wx)}"
                )
