"""
PayPack LangChain Tool
将 PayPack 封装为 LangChain 工具，供 AI Agent 直接调用。
"""

import os
from typing import Optional, Type
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

from paypack import AgentPay, create_agent_pay


class PaymentInput(BaseModel):
    """支付工具输入参数"""
    to: str = Field(description="收款地址，0x 开头")
    amount: float = Field(description="支付金额，单位由 currency 决定")
    currency: str = Field(default="USDC", description="支付币种，ETH 或 USDC")


class PayPackTool(BaseTool):
    """AI Agent 纳米支付工具（支持多链和广播模式）"""
    name: str = "paypack_payment"
    description: str = (
        "当 AI 代理需要向某个地址付款时调用此工具。"
        "输入收款地址、金额和币种（ETH 或 USDC）。"
        "自动处理 HTTP 402 响应和链上转账。"
    )
    args_schema: Type[BaseModel] = PaymentInput

    private_key: str = Field(default="", description="钱包私钥（0x 开头），留空则从环境变量 PRIVATE_KEY 读取")
    wallet_address: str = Field(default="", description="钱包地址（0x 开头）")
    spend_limit_daily: float = Field(default=10.0, description="每日支付上限（单位同币种）")
    network: str = Field(default="base-sepolia", description="网络名称，如 base-mainnet, ethereum-mainnet")
    broadcast: bool = Field(default=False, description="是否真实广播上链（False=仅签名）")

    def _run(self, to: str, amount: float, currency: str = "USDC") -> str:
        """同步执行支付（返回友好文本给 AI）"""
        effective_private_key = self.private_key or os.getenv("PRIVATE_KEY")
        if not effective_private_key:
            return "错误：未配置钱包私钥，请设置 private_key 或环境变量 PRIVATE_KEY"

        pay = AgentPay(
            wallet_config={
                "private_key": effective_private_key,
                "address": self.wallet_address or None
            },
            spend_limit_daily=self.spend_limit_daily,
            broadcast=self.broadcast,
            network=self.network
        )

        try:
            receipt = pay.send(to=to, amount=amount, currency=currency)
            tx_hash = receipt["tx_hash"]
            explorer_link = receipt.get("explorer_link", "")
            status = receipt.get("status", "unknown")
            daily_remaining = receipt.get("daily_remaining", 0)

            result_msg = (
                f"✅ 支付成功！\n"
                f"币种: {receipt['currency']}\n"
                f"金额: {receipt['amount']}\n"
                f"交易哈希: {tx_hash}\n"
                f"状态: {status}\n"
                f"今日剩余额度: {daily_remaining:.6f}\n"
            )
            if explorer_link:
                result_msg += f"区块浏览器: {explorer_link}"
            return result_msg

        except Exception as e:
            return f"❌ 支付失败: {type(e).__name__} - {str(e)}"

    async def _arun(self, to: str, amount: float, currency: str = "USDC") -> str:
        """异步执行支付（暂用同步代替）"""
        return self._run(to, amount, currency)


def create_paypack_tool(
    private_key: Optional[str] = None,
    wallet_address: Optional[str] = None,
    network: str = "base-sepolia",
    spend_limit_daily: float = 10.0,
    broadcast: bool = False,
) -> PayPackTool:
    """快速创建 PayPackTool 实例"""
    return PayPackTool(
        private_key=private_key,
        wallet_address=wallet_address,
        network=network,
        spend_limit_daily=spend_limit_daily,
        broadcast=broadcast
    )


# ========== 使用示例 ==========
if __name__ == "__main__":
    # 优先读取环境变量，否则使用测试私钥
    test_key = os.getenv(
        "PRIVATE_KEY",
        "0x6fd8aeba2983ea3eade0f68165376631d285827e74bcb69282c6783d6fb1b356"
    )
    tool = create_paypack_tool(
        private_key=test_key,
        wallet_address="0x9cbF3Ca5185Ca55C804c2c4b726De212A17734F8",
        network="base-sepolia",
        spend_limit_daily=0.01,
        broadcast=False
    )
    # 测试 ETH 支付
    result = tool._run(
        to="0x9cbF3Ca5185Ca55C804c2c4b726De212A17734F8",
        amount=0.0001,
        currency="ETH"
    )
    print(result)
