"""
PayPack LangChain Tool
将 PayPack 封装为 LangChain 工具，供 AI Agent 直接调用。
"""

from typing import Optional, Type
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

# 引用你的 PayPack 核心（确保 paypack.py 在同一目录下）
from paypack import AgentPay


class PaymentInput(BaseModel):
    """支付工具输入参数"""
    to: str = Field(description="收款地址，0x 开头")
    amount: float = Field(description="支付金额，单位由 currency 决定")
    currency: str = Field(default="USDC", description="支付币种，ETH 或 USDC")


class PayPackTool(BaseTool):
    """AI Agent 纳米支付工具"""
    name: str = "paypack_payment"
    description: str = (
        "当 AI 代理需要向某个地址付款时调用此工具。"
        "输入收款地址、金额和币种（ETH 或 USDC）。"
        "自动处理 HTTP 402 响应和链上转账。"
    )
    args_schema: Type[BaseModel] = PaymentInput

    # 钱包配置（由使用者在初始化时注入）
    private_key: str = Field(default="")
    wallet_address: str = Field(default="")
    spend_limit_daily: float = Field(default=10.0)

    def _run(self, to: str, amount: float, currency: str = "USDC") -> str:
        """同步执行支付"""
        if not self.private_key or not self.wallet_address:
            return "错误：未配置钱包私钥或地址"

        pay = AgentPay(
            wallet_config={
                "private_key": self.private_key,
                "address": self.wallet_address
            },
            spend_limit_daily=self.spend_limit_daily
        )

        try:
            receipt = pay.send(to=to, amount=amount, currency=currency)
            return (
                f"支付成功！\n"
                f"币种: {receipt['currency']}\n"
                f"金额: {receipt['amount']}\n"
                f"交易哈希: {receipt['tx_hash']}"
            )
        except Exception as e:
            return f"支付失败: {str(e)}"

    async def _arun(self, to: str, amount: float, currency: str = "USDC") -> str:
        """异步执行支付（暂用同步代替，可后续升级）"""
        return self._run(to, amount, currency)