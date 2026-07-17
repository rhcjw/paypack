"""
测试 LangChain 插件是否正常工作。
支持 Signer 依赖注入。
"""

from langchain_tool import PayPackTool

# 用你的测试钱包配置
tool = PayPackTool(
    private_key="0x你的ETH私钥",
    wallet_address="0x9cbF3Ca5185Ca55C804c2c4b726De212A17734F8",
    spend_limit_daily=0.01
)

# 模拟 AI 调用支付
result = tool._run(
    to="0x9cbF3Ca5185Ca55C804c2c4b726De212A17734F8",
    amount=0.0001,
    currency="ETH"
)
print(result)
