
PayPack 不发明新协议，而是把散落在各处的底层能力**封装成一个 `agent.pay()`**。

---

## 功能特性

- **多协议兼容**：同时支持 x402 和 AP2，自动识别并切换
- **纳米支付优化**：专为 0.01 美元以下交易设计，内置 Gas 费估算和批量结算
- **安全熔断**：可设置单笔上限、日支出上限、收款地址白名单
- **完整审计日志**：每一笔支付都有可查询的 JSON 收据
- **框架原生插件**：LangChain / LlamaIndex 等主流 AI 框架的支付工具
- **双轨合规**：同时对接海外稳定币通道（USDC）和国内合规通道（支付宝 AI 付）

---

## 快速预览（开发中）

```python
from paypack import AgentPay

# 初始化
pay = AgentPay(
    wallet_config={"private_key": "your-key", "chain": "base"},
    spend_limit_daily=10.0,   # 日限额 10 美元
    spend_limit_per_tx=0.5    # 单笔上限 0.5 美元
)

# 场景一：自动处理 HTTP 402
response = requests.get("https://api.data-provider.com/premium")
if response.status_code == 402:
    content = pay.auto_handle_402(response)
    # 付款完成，content 里就是付费内容

# 场景二：直接发起纳米支付
receipt = pay.send(
    to="0x接收地址",
    amount=0.001,
    currency="USDC"
)
print(receipt.tx_hash)  # 链上交易哈希
print(receipt.fee)      # 实际手续费