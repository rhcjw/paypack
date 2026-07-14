# PayPack — Gitee 中文 README

**AI Agent 通用支付中间件**

> 两行代码，让 AI 自己付钱。

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Gitee Star](https://gitee.com/rhcjw_com/paypack/badge/star.svg)](https://gitee.com/rhcjw_com/paypack)

---

## 一句话说清楚 PayPack 是什么

**PayPack 是目前唯一一个同时支持链上支付（USDC/ETH）和支付宝/微信人民币支付的 AI Agent 支付中间件。**

国内 AI 开发者想让 Agent 自动付钱？两行代码，PayPack 搞定。

---

## 为什么你需要它？

### 现状：所有官方生态的支付工具都不管中国用户

| 工具 | 支付方式 | 国内用户能用吗？ |
|------|---------|----------------|
| Ampersend | x402 + USDC | ❌ |
| GOAT | 加密货币 | ❌ |
| Stripe Agent Toolkit | 信用卡 | ❌ |
| Nevermined | x402 协议 | ❌ |
| Privy | 钱包基建 | ❌ |
| **PayPack** ✅ | x402/AP2 + USDC/ETH + **支付宝** + **微信** | ✅ **唯一** |
| **PayPack Cloud** ☁️ | **云托管 API — 支付宝 + 微信支付** | ✅ **已上线** [rhcjw.com/pay](https://rhcjw.com/pay) |

### 如果你自己对接支付宝

- 读几百页开放平台文档
- 写几十行 RSA2 签名代码
- 处理沙箱、验签、回调通知
- 搞几天才能跑通

**用 PayPack：两行代码。**

---

## 快速开始

### 安装

```bash
pip install https://gitee.com/rhcjw_com/paypack/raw/master/dist/langchain_paypack-0.5.0-py3-none-any.whl
```

### 支付宝支付

```python
from paypack.signer.alipay import AlipaySigner
from paypack import AgentPay

# 初始化支付宝签名器
signer = AlipaySigner(
    app_id="你的APPID",
    private_key_path="私钥.pem",
    alipay_public_key_path="支付宝公钥.pem",
    sandbox=True,  # 沙箱模式
)

pay = AgentPay(signer=signer, network="alipay")

# AI 付人民币！
receipt = pay.send(
    to="用户支付宝user_id",
    amount=0.01,
    currency="CNY",
    subject="AI 数据订阅费"
)
```

### 链上支付（USDC / ETH）

```python
from paypack import AgentPay

pay = AgentPay(
    wallet_config={"private_key": "你的私钥"},
    network="base-sepolia",
)

# 发送 USDC
receipt = pay.send(to="0x...", amount=0.001, currency="USDC")
```

### 不想管密钥？直接用 PayPack Cloud ☁️

```bash
# 注册获取 API Key
curl -X POST https://rhcjw.com/pay/v1/register \
  -H "Content-Type: application/json" \
  -d '{"name": "myapp"}'

# 支付宝支付
curl -X POST https://rhcjw.com/pay/v1/pay \
  -H "Authorization: Bearer ppk_xxx" \
  -d '{"amount": 0.01, "subject": "AI 服务", "channel": "alipay"}'

# 微信支付
curl -X POST https://rhcjw.com/pay/v1/pay \
  -H "Authorization: Bearer ppk_xxx" \
  -d '{"amount": 0.01, "subject": "AI 服务", "channel": "wechat"}'
```

---

## 坐标图

三个圈的交集，只有 PayPack：

```
x402/AP2 协议  →  Ampersend、Nevermined、PayPack
USDC/ETH 链上  →  GOAT、PayPack
支付宝/微信   →  PayPack（唯一）
```

---

## 谁在用？谁能用？

这些平台上的开发者，**全都没有支付工具可用**：

| 平台 | 用户量 | 有支付工具吗？ |
|------|--------|---------------|
| Dify | 数十万 | ✅ [PayPack 插件](https://github.com/rhcjw/paypack/releases/tag/v0.1.0) |
| Coze（字节跳动） | 数百万 | ❌ 没有 |
| 百度千帆 | 数十万 | ❌ 没有 |
| 通义百炼 | 数十万 | ❌ 没有 |

PayPack 就是给这些人用的。

---

## 功能

- ✅ x402 协议解析（Coinbase 提出）
- ✅ AP2 协议解析（Google 提出）
- ✅ ETH / USDC 链上转账（Base、以太坊、Polygon、Arbitrum）
- ✅ **支付宝人民币支付**（沙箱 + 生产已验证 ¥0.10）
- ✅ **微信支付**（生产已验证 ¥0.05 Native 扫码）
- ✅ **PayPack Cloud 云托管**（已上线 https://rhcjw.com/pay）
- ✅ ERC-4337 批量结算（省 Gas）
- ✅ AWS KMS 签名（生产环境私钥不出 HSM）
- ✅ RPC 故障转移（多节点自动切换）
- ✅ 交易重试 + Replace-by-Fee
- ✅ 日消费限额 + 持久化
- ✅ LangChain 插件
- ✅ Dify 插件 — [v0.1.0](https://github.com/rhcjw/paypack/releases/tag/v0.1.0) 支付/查单/退款

---

## 已验证交易

| 币种 | 金额 | 交易凭证 |
|------|------|---------|
| ETH | 0.0001 ETH | `d5f7ec94342c26a132289a9898ffd4885010089d1ddba19951117618a3992127` |
| USDC | 0.001 USDC | `c4c24c4c1c8fd2ae738ed91cd87596ad2c672337b5ebf6d42a392adf61760e27` |
| CNY (支付宝) | 0.63 元 | `2026070922001406640510096995` |
| CNY (支付宝) | **¥0.10** | **生产环境** ✅ `2026071122001479581453918172`（已支付 + 已退款） |
| CNY (微信) | **¥0.05** | **生产环境** ✅ Native 扫码支付 |

---

## 路线图

| 版本 | 内容 | 状态 |
|------|------|------|
| v0.5 | 链上支付 + LangChain + 生产特性 | ✅ 已发布 |
| 🔌 Dify 插件 | 支付/查单/退款 | ✅ [v0.1.0](https://github.com/rhcjw/paypack/releases/tag/v0.1.0) |
| v0.6 | 支付宝生产环境 | ✅ 已发布（¥0.10 真实支付） |
| v0.7 | 微信支付生产环境 | ✅ 已发布（¥0.05 Native 扫码） |
| v1.0 | PayPack Cloud 托管服务 | ✅ **已上线** https://rhcjw.com/pay |

---

## 链接

| 渠道 | 地址 |
|------|------|
| GitHub | https://github.com/rhcjw/paypack |
| Gitee（国内） | https://gitee.com/rhcjw_com/paypack |
| PyPI | https://pypi.org/project/langchain-paypack/ |
| PayPack Cloud | https://rhcjw.com/pay |

---

## 参与贡献

Star ⭐、提 Issue、在 Dify/Coze 社区里提一嘴 PayPack，都是贡献。

## 许可证

Apache License 2.0
