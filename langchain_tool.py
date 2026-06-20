"""测试 LangChain 插件是否正常工作"""

from langchain_tool import PayPackTool

# 用你的测试钱包配置
tool = PayPackTool(
    private_key="0x6fd8aeba2983ea3eade0f68165376631d285827e74bcb69282c6783d6fb1b356",
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