"""
本地私钥签名器 —— 开发/测试环境使用。
私钥存储在环境变量或内存中，请勿在生产环境使用。
"""

import os
from typing import Optional

from eth_account import Account
from eth_account.datastructures import SignedTransaction

from paypack.signer.base import Signer


class LocalSigner(Signer):
    """
    使用本地私钥签名交易。

    Usage:
        signer = LocalSigner(private_key="0x...")
        signer = LocalSigner()  # 从环境变量 PRIVATE_KEY 读取
    """

    def __init__(self, private_key: Optional[str] = None):
        self._private_key = private_key or os.getenv("PRIVATE_KEY")
        if not self._private_key:
            raise ValueError(
                "私钥未提供。请传入 private_key 参数或设置环境变量 PRIVATE_KEY"
            )
        self._account = Account.from_key(self._private_key)

    def get_address(self) -> str:
        return self._account.address

    def sign_transaction(self, transaction_dict: dict) -> SignedTransaction:
        return self._account.sign_transaction(transaction_dict)
