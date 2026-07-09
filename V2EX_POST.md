# V2EX 帖子草稿 — 创造者/分享创造 节点

---

**标题：我做了个开源项目，让 AI Agent 两行代码就能用支付宝付钱**

---

说出来你可能不信——HTTP 402 "Payment Required" 这个状态码在协议规范里躺了 34 年（1991 年就有了），但从来没人用过。

原因很简单：返回 402 的时候，得有个活人在屏幕前掏信用卡。

但现在情况变了。AI Agent 可以自动调 API、自动买数据、自动订阅服务——一次可能就花 $0.001。传统支付体系根本处理不了这种纳米支付。

Coinbase 提了 x402 协议，Google 提了 AP2 协议，都在解决"机器自动付钱"这个问题。但我去翻了所有开源项目：

| 工具 | 支付方式 | 国内用户能用吗？ |
|------|---------|----------------|
| Ampersend | x402 + USDC | ❌ |
| GOAT | 加密货币 | ❌ |
| Stripe Agent Toolkit | 信用卡 | ❌（谁有外币卡？） |
| Nevermined | x402 | ❌ |
| Privy | 钱包基建 | ❌ |

**全都不支持支付宝和微信支付。**

所以我自己写了一个——[PayPack](https://github.com/rhcjw/paypack)。

---

## 它做什么？

两行代码，让 AI Agent 付人民币：

```python
from paypack.signer.alipay import AlipaySigner
from paypack import AgentPay

signer = AlipaySigner(app_id="你的APPID", private_key_path="私钥.pem",
                       alipay_public_key_path="支付宝公钥.pem", sandbox=True)
pay = AgentPay(signer=signer, network="alipay")

# AI 直接付人民币
pay.send(to="用户支付宝user_id", amount=0.01, currency="CNY",
         subject="AI 数据订阅费")
```

同时也支持链上 USDC/ETH 支付（x402/AP2 协议），ERC-4337 批量结算，AWS KMS 签名这些生产特性都已经做完了。

---

## 坐标图

如果你把现在的 AI 支付工具画成三个圈：

```
x402/AP2 协议  →  Ampersend、Nevermined、PayPack
USDC/ETH 链上  →  GOAT、PayPack
支付宝/微信法币 →  PayPack（唯一）
```

**PayPack 是唯一一个同时出现在三个圈里的项目。**

---

## 为什么做这个？

国内 AI 开发者想让 Agent 自动付人民币，现在有什么选择？

- ❌ 自己对接支付宝：几百页文档，RSA2 签名，沙箱调试，验签回调...
- ❌ 用 Ampersend：只支持 USDC
- ❌ 用 Stripe：国内用户没信用卡

✅ **PayPack：两行代码，开源，免费。**

Dify、Coze、百度千帆、通义百炼——这些平台加起来几百万开发者，没有一个有支付工具。PayPack 是给这些人用的。

---

## 链接

- GitHub: https://github.com/rhcjw/paypack
- Gitee（国内更快）: https://gitee.com/rhcjw_com/paypack
- PyPI: `pip install langchain-paypack`

---

欢迎 star、试用、拍砖。也欢迎讨论：AI Agent 支付这个方向，你觉得有戏吗？
