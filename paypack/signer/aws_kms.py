"""
AWS KMS 签名器 —— 生产环境使用。
私钥永不离开 AWS KMS 基础设施，所有签名操作在 HSM 内完成。
"""

from typing import Optional

from eth_account.datastructures import SignedTransaction

from paypack.signer.base import Signer


class AWSKMSSigner(Signer):
    """
    通过 AWS KMS 签名交易，私钥永远不会暴露在内存中。

    前置条件:
        pip install boto3 ethereum-kms-signer

    Usage:
        signer = AWSKMSSigner(key_id="alias/paypack-eth-key", region="us-east-1")
    """

    def __init__(self, key_id: str, region: str = "us-east-1"):
        self.key_id = key_id
        self.region = region

        try:
            import boto3
            from ethereum_kms_signer import get_eth_address
        except ImportError as e:
            raise ImportError(
                "AWS KMS 签名器需要额外依赖: pip install boto3 ethereum-kms-signer"
            ) from e

        self._kms_client = boto3.client("kms", region_name=region)
        self._address = get_eth_address(key_id)

    def get_address(self) -> str:
        return self._address

    def sign_transaction(self, transaction_dict: dict) -> SignedTransaction:
        from ethereum_kms_signer import sign_transaction as kms_sign

        return kms_sign(transaction_dict, self.key_id)
