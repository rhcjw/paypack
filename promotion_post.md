# 【首发】PayPack —— 让 AI Agent 自己付钱，支持支付宝 / 微信 / USDC / ETH

**一句话：给你的 AI Agent 装上一个钱包，它能自己决定用支付宝还是链上加密币付款。**

---

## 为什么做这个

过去半年我一直在用 LangChain 搭 Agent，遇到一个很尴尬的问题——**Agent 不会付钱**。

想让它买 API 数据 → 卡住。
想让它订个订阅服务 → 卡住。
想让它跨平台比价后下单 → 卡住。

现有的支付工具要么只支持 Stripe/信用卡（国内没法用），要么只走加密货币（跟日常消费脱节）。而国内 13 亿人每天在用的 **支付宝和微信支付**，在 AI Agent 生态里是真空地带。

所以我写了 **PayPack**。

## PayPack 是什么

一个通用支付 SDK，专为 AI Agent 设计。核心就一行：

```python
receipt = pay.send(to="0x...", amount=0.01, currency="USDC")
```

或者：

```python
receipt = pay.send(to="user_alipay_id", amount=9.90, currency="CNY")
```

Agent 根据场景自动切换支付渠道。

## 目前已支持

| 渠道 | 状态 | 说明 |
|------|------|------|
| **USDC / ETH** | ✅ 生产可用 | Base / Ethereum / Polygon / Arbitrum |
| **支付宝 CNY** | ✅ 生产可用 | ¥0.10 真实支付验证通过 |
| **微信支付 CNY** | ✅ 生产可用 | ¥0.05 真实支付验证通过 |
| **Dify 插件** | ⏳ PR 审核中 | 安装即用 |

## 快速体验

```bash
pip install langchain-paypack
```

```python
from langchain_paypack import PayPackTool

tool = PayPackTool(
    private_key="0x...",
    network="base-sepolia",
    spend_limit_daily=10.0,
)

# AI 发起支付
result = tool._run(to="0xRecipient", amount=0.001, currency="USDC")
print(result["tx_hash"])
```

## 设计理念

- **一个 API 打通三个生态**：crypto、支付宝、微信，Agent 无需关心底层
- **安全熔断**：日限额、余额检查、交易可审计
- **开源可信**：Apache 2.0，代码全公开

## 链接

- GitHub：https://github.com/rhcjw/paypack
- PyPI：`pip install langchain-paypack`
- 文档：README 里有完整的中英文说明
- Dify 插件 PR：https://github.com/langgenius/dify-plugins/pull/2693

---

欢迎 star、fork、提 issue。有任何问题直接回帖，我在线回复。

**PayPack —— 让 AI 自己买单。**
