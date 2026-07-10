# PayPack

**AI Agent Universal Payment Middleware | AI Agent 通用支付中间件**

> 两行代码，让 AI 自己付钱。
> Two lines of code. Let your AI pay for itself.

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![LangChain](https://img.shields.io/badge/LangChain-Integration-green.svg)](https://python.langchain.com/)
[![PyPI](https://img.shields.io/pypi/v/langchain-paypack.svg)](https://pypi.org/project/langchain-paypack/)
[![Gitee](https://img.shields.io/badge/Gitee-Mirror-red.svg)](https://gitee.com/rhcjw_com/paypack)

---

## 为什么是 PayPack？| Why PayPack?

**PayPack is the ONLY payment middleware that supports x402/AP2 crypto payments AND Alipay/WeChat fiat payments.**

| 工具 | 支付方式 | 支持中国用户？ |
|------|---------|---------------|
| **Ampersend** | x402 + USDC | ❌ 不支持支付宝/微信 |
| **GOAT** | 加密货币 | ❌ 不支持支付宝/微信 |
| **Stripe Agent Toolkit** | Stripe（信用卡） | ❌ 仅限外币卡 |
| **Nevermined** | x402 协议 | ❌ 不支持支付宝/微信 |
| **Privy** | 钱包基础设施 | ❌ 不支持支付宝/微信 |
| **PayPack** ✅ | x402/AP2 + USDC/ETH + **支付宝** | ✅ 开源免费 |
| **PayPack WeChat** 🔒 | **微信支付 JSAPI** | ✅ 商业版 |

当所有人在琢磨"怎么让 AI 用 USDC 付钱"时，PayPack 在想"怎么让 AI 用支付宝和微信付钱"。国内 13 亿人用支付宝和微信，不用 USDC。**这个市场，只有 PayPack 在做。**

---

## Quick Start

### 链上支付（ETH / USDC）

```python
from paypack import AgentPay

pay = AgentPay(
    wallet_config={"private_key": "your-key"},
    network="base-sepolia",
    spend_limit_daily=10.0,
)

# AI 自动处理 HTTP 402 支付要求
import requests
response = requests.get("https://api.data-provider.com/premium")
if response.status_code == 402:
    content = pay.auto_handle_402(response)

# 或直接发送支付
receipt = pay.send(to="0xRecipientAddress", amount=0.001, currency="USDC")
print(receipt["tx_hash"])
```

### 支付宝支付（人民币）🏦

```python
from paypack.signer.alipay import AlipaySigner
from paypack import AgentPay

# 两行代码接入支付宝
signer = AlipaySigner(app_id="你的APPID", private_key_path="私钥.pem",
                       alipay_public_key_path="支付宝公钥.pem", sandbox=True)
pay = AgentPay(signer=signer, network="alipay")

# AI 直接付人民币
receipt = pay.send(to="用户支付宝user_id", amount=0.01, currency="CNY",
                   subject="AI 数据订阅费")
```

```python
# 电脑网站支付 — 生成收银台链接，用户扫码即付
pay_url = signer.page_pay(
    out_trade_no="ORDER_20260709_001",
    total_amount=9.90,
    subject="AI Agent API 调用月费",
    body="PayPack 自动生成的支付订单"
)
# 用户打开 pay_url 即可扫码支付
```

### LangChain 集成

```python
from langchain_paypack import PayPackTool

tool = PayPackTool(
    private_key="0x...",
    wallet_address="0x...",
    network="base-sepolia",
    spend_limit_daily=10.0,
)

# AI Agent 直接调用
result = tool._run(to="0x...", amount=0.001, currency="USDC")
```

> 💡 对比一下：自己对接支付宝要读几百页文档、写几百行代码、处理沙箱/RSA2签名/验签/回调。PayPack 两行搞定。

### 微信支付（人民币）💚

```python
# paypack_wechat 为商业模块，需要 License Key
# 开源代码包里包含示例模板: paypack_wechat_run.example.py
from paypack_wechat import WechatSigner
from paypack import AgentPay

signer = WechatSigner(
    mchid="商户号",
    serial_no="证书序列号",
    private_key_path="apiclient_key.pem",
    api_v3_key="APIv3密钥",
    license_key="PAYPACK-WECHAT-v1-...",
    app_id="小程序AppID",
    notify_url="https://你的域名/wechat/notify",
)
pay = AgentPay(signer=signer, network="wechat")

# AI 发起微信支付 → 前端调起 wx.requestPayment()
result = pay.send(
    to="用户openid",
    amount=9.90,
    currency="CNY",
    subject="AI 服务月费",
    app_id="小程序AppID",
)
# result["prepay_params"] 直接传给前端调起支付
```

### Dify 插件

```bash
# 在 Dify 中：插件 → 从 GitHub 安装
# 输入：https://github.com/rhcjw/paypack
```

或直接下载 [paypack-0.1.0.difypkg](https://github.com/rhcjw/paypack/releases/tag/v0.1.0) 上传。

> 详见 [QUICKSTART.md](./QUICKSTART.md) — 5 分钟链上/支付宝/Dify 三路教程。

---

## 当前状态 | Status

| 通道 | 沙箱/测试 | 生产 | 全自动？ |
|------|----------|------|----------|
| **ETH / USDC** (Base/Ethereum/Polygon/Arbitrum) | ✅ 已验证 | ✅ 可用 | ✅ 是 |
| **支付宝 CNY** | ✅ 沙箱已通 | 🚧 开发中 | ⚠️ 需用户扫码 |
| **微信支付 CNY** | ✅ 后端已通 | ✅ 商业版 | ⚠️ 需用户确认 |

---

## 架构 | Architecture

```text
       AI Agent Application
                │
                ▼
         PayPack SDK  ◄── 你在这里
                │
        ┌───────┼───────┐
        │       │       │
  Protocol   Payment   Security
   Parser    Router    Fuse
  (x402/    (USDC/    (Limits/
   AP2)     CNY)       Audit)
        │       │       │
        └───────┼───────┘
                │
                ▼
    Settlement Networks
  (Base / Alipay / More...)
```

PayPack 不发明新协议，而是把零散的能力封装成一个 `agent.pay()`。

---

## 功能 | Features

- **多协议**: x402 + AP2 自动检测和路由
- **三通道**: USDC/ETH 链上 + 支付宝 CNY + 微信支付 CNY
- **签名器抽象**: LocalSigner（开发）/ AWSKMSSigner（生产，私钥不出 HSM）
- **纳米支付优化**: ERC-4337 批量结算，节省 Gas
- **安全熔断**: 日消费限额、余额检查、可审计收据
- **RPC 故障转移**: 多节点自动切换（v0.5）
- **交易重试**: RBF + 指数退避（v0.5）
- **限额持久化**: Redis / SQLite / 内存（v0.5）
- **LangChain 原生**: `PayPackTool` 即插即用
- **Dify 插件**: [paypack-0.1.0.difypkg](https://github.com/rhcjw/paypack/releases/tag/v0.1.0) 三工具（支付/查单/退款）

---

## 支持网络 | Supported Networks

| 网络 | Chain ID | 币种 |
|------|----------|------|
| Base Sepolia (testnet) | 84532 | ETH, USDC |
| Base Mainnet | 8453 | ETH, USDC |
| Ethereum Mainnet | 1 | ETH, USDC |
| Polygon Mainnet | 137 | POL, USDC |
| Arbitrum Mainnet | 42161 | ETH, USDC |
| **支付宝沙箱** | — | **CNY（人民币）** |
| **支付宝生产**（计划中） | — | **CNY（人民币）** |
| **微信支付** | — | **CNY（人民币）** 🔒 商业版 |

---

## 安装 | Installation

```bash
pip install langchain-paypack
```

或从 Gitee 安装（国内更快）：

```bash
pip install https://gitee.com/rhcjw_com/paypack/raw/master/dist/langchain_paypack-0.5.0-py3-none-any.whl
```

---

## 已验证交易 | Verified Transactions

| 币种 | 金额 | 交易哈希 |
|------|------|---------|
| ETH | 0.0001 ETH | `d5f7ec94342c26a132289a9898ffd4885010089d1ddba19951117618a3992127` |
| USDC | 0.001 USDC | `c4c24c4c1c8fd2ae738ed91cd87596ad2c672337b5ebf6d42a392adf61760e27` |
| CNY (支付宝) | 0.63 元 | 沙箱交易号: `2026070922001406640510096995` |

---

## 里程碑 | Milestones

| 版本 | 目标 | 状态 |
|------|------|------|
| v0.1 | Base 测试网 x402 支付闭环 (ETH + USDC) | ✅ |
| v0.2 | AP2 协议支持 | ✅ |
| v0.3 | LangChain 插件发布 | ✅ |
| v0.4 | 签名器抽象 + ERC-4337 批量结算 | ✅ |
| v0.5 | RPC 故障转移 + 重试 + 限额持久化 | ✅ |
| 🔌 Dify 插件 | 支付/查单/退款 | ✅ [v0.1.0](https://github.com/rhcjw/paypack/releases/tag/v0.1.0) |
| v0.6 | 支付宝生产环境上线 | 🚧 |
| v1.0 | PayPack Cloud 托管服务 | 🚧 |

---

## 为什么是现在？| Why Now?

- 稳定币年交易量突破 **$33 万亿**（2025）— 是 PayPal 的 20 倍
- AI Agent 数量预计达 **220 亿**（麦肯锡）
- x402 协议已在 Solana 上处理数千万笔交易
- LangChain/LlamaIndex 支付插件市场**完全空白**
- 支付宝"AI 付"计划 2026 年启动 — PayPack 是首个将其桥接到 x402 的项目

---

## 目标用户：国内 AI 开发者

PayPack 不只是 LangChain 生态的工具。国内数十万开发者在用这些平台——**它们全都没有支付工具**：

| 平台 | 用户量 | 有支付工具吗？ |
|------|--------|---------------|
| **Dify** | 数十万 | ✅ [PayPack 插件](https://github.com/rhcjw/paypack/releases/tag/v0.1.0) |
| **Coze（字节）** | 数百万 | ❌ 没有 |
| **百度千帆** | 数十万 | ❌ 没有 |
| **通义百炼** | 数十万 | ❌ 没有 |

这些平台的开发者，才是 PayPack 真正的用户。

---

## 链接 | Links

| 渠道 | 地址 |
|------|------|
| GitHub | https://github.com/rhcjw/paypack |
| Gitee（国内镜像） | https://gitee.com/rhcjw_com/paypack |
| PyPI | https://pypi.org/project/langchain-paypack/ |
| Dify 插件 | [paypack-0.1.0.difypkg](https://github.com/rhcjw/paypack/releases/tag/v0.1.0) |
| 快速入门 | [QUICKSTART.md](./QUICKSTART.md) |

---

## 贡献 | Contributing

Star、提 Issue、或者在 Dify/Coze 社区里提到 PayPack，都是贡献。

## 许可证 | License

Apache License 2.0. See [LICENSE](LICENSE).
