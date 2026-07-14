# 【首发】PayPack —— 让 AI Agent 自己付钱，支持支付宝 / 微信 / USDC / ETH

**一句话：给你的 AI Agent 装上一个钱包，它能自己决定用支付宝还是链上加密币付款。**

---

## 为什么做这个

过去半年我一直在用 LangChain 搭 Agent，遇到一个很尴尬的问题——**Agent 不会付钱**。

想让它买 API 数据 → 卡住。
想让它订个订阅服务 → 卡住。
想让它跨平台比价后下单 → 卡住。

现有的支付工具要么只支持 Stripe/信用卡（国内没法用），要么只走加密货币（跟日常消费脱节）。而国内 13 亿人每天在用的支付宝和微信支付，在 AI Agent 生态里是**完全空白**的。

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
| USDC / ETH | ✅ 已支持 | Base, Ethereum, Polygon, Arbitrum |
| 支付宝 (CNY) | ✅ 生产环境已验证 | 成功支付并退款 ¥0.10 |
| 微信支付 (CNY) | ✅ 生产环境已验证 | 成功支付 ¥0.05 |
| LangChain | ✅ 已集成 | PayPackTool 即插即用 |
| Dify | ✅ 插件已提交 | 等待官方合并 PR |

## 架构很简单

```
Agent Pay 入口 → 判断用 crypto / 支付宝 / 微信 → 调用对应的支付接口
```

## 开源地址

代码完全开源，Apache 2.0 协议：

**GitHub:** https://github.com/rhcjw/paypack
**PyPI:** `pip install langchain-paypack`

欢迎 star、提 issue、或者直接拿去用。

---

折腾了一个月，终于搞出来了。希望能帮到和我有同样困扰的开发者。
