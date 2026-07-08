"""
Signer 抽象接口 —— 所有签名器的基类。
支持本地私钥、AWS KMS、Azure Key Vault 等多种实现。
"""

from abc import ABC, abstractmethod
from eth_account.datastructures import SignedTransaction


class Signer(ABC):
    """所有签名器的抽象基类"""

    @abstractmethod
    def get_address(self) -> str:
        """获取签名对应的钱包地址"""
        ...

    @abstractmethod
    def sign_transaction(self, transaction_dict: dict) -> SignedTransaction:
        """
        签名交易，返回可广播的 SignedTransaction。

        Args:
            transaction_dict: web3 交易字典，包含 from, to, value, gas, nonce, chainId 等字段

        Returns:
            SignedTransaction: 包含 raw_transaction 的已签名交易对象
        """
        ...

    def sign_user_operation(self, user_operation: dict) -> dict:
        """
        签名 ERC-4337 UserOperation（可选实现）。

        默认实现将 userOpHash 当作普通交易摘要签名。
        子类可覆盖以提供原生 UserOp 签名支持。
        """
        raise NotImplementedError("sign_user_operation not implemented for this signer")
