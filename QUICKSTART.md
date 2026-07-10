# PayPack 快速入门 — 5 分钟让 AI 自己付钱

> 给 Dify / Coze / LangChain 开发者的实战教程

---

## 你要准备什么

| 你需要的 | 链上支付(USDC/ETH) | 支付宝(CNY) | 微信支付(CNY) |
|----------|-------------------|-------------|--------------|
| 钱包私钥 | ✅ ETH私钥 | ✅ 商户私钥 | ✅ 商户私钥 |
| Base Sepolia测试币 | ✅ 去水龙头领 | — | — |
| 支付宝沙箱APPID | — | ✅ | — |
| 微信商户号/证书 | — | — | ✅ 商业License |
| Python 3.9+ | ✅ | ✅ | ✅ |
| 安装 PayPack | ✅ | ✅ | ✅ |

---

## 5 分钟跑通链上支付（ETH/USDC）

### 第 1 步：安装

```bash
pip install langchain-paypack
```

### 第 2 步：创建一个文件 `ai_pay_demo.py`

```python
from paypack import AgentPay

# ============================================
# 配置：把你的 ETH 私钥填在这里
# 去 https://www.alchemy.com/faucets/base-sepolia 领测试币
# ============================================
PRIVATE_KEY = "0x你的私钥"

pay = AgentPay(
    wallet_config={"private_key": PRIVATE_KEY},
    network="base-sepolia",       # 测试网，安全
    spend_limit_daily=10.0,       # AI 每天最多花 10 美元
    broadcast=True,               # True = 真的上链
)

# ============================================
# AI 付钱！三种币随便选
# ============================================

# 付 ETH
receipt = pay.send(
    to="0x9cbF3Ca5185Ca55C804c2c4b726De212A17734F8",
    amount=0.0001,
    currency="ETH",
)
print(f"ETH 支付完成! 交易哈希: {receipt['tx_hash']}")

# 付 USDC
receipt = pay.send(
    to="0x9cbF3Ca5185Ca55C804c2c4b726De212A17734F8",
    amount=0.001,
    currency="USDC",
)
print(f"USDC 支付完成! 交易哈希: {receipt['tx_hash']}")

# 批量支付（ERC-4337，省 Gas）
receipt = pay.batch_pay([
    {"to": "0x地址A", "amount": 0.0001, "currency": "ETH"},
    {"to": "0x地址B", "amount": 0.0002, "currency": "USDC"},
])
print(f"批量支付完成! {receipt['batch_size']} 笔, 总计 {receipt['total_amount']}")
```

### 第 3 步：跑起来

```bash
python ai_pay_demo.py
```

输出示例：

```
ETH 支付完成! 交易哈希: 0xd5f7ec94342c26a132289a9898ffd488...
USDC 支付完成! 交易哈希: 0xc4c24c4c1c8fd2ae738ed91cd87596a...
```

**这就通了。你刚刚让 AI 自己付了钱。**

---

## 5 分钟接入支付宝

### 准备工作（一次性，5分钟）

1. 去 [支付宝开放平台](https://open.alipay.com/) 入驻开发者
2. 进入"沙箱环境" → 获取沙箱 APPID
3. 生成 RSA2 密钥对，上传公钥到沙箱
4. 下载支付宝沙箱公钥

### 代码（2行）

```python
from paypack.signer.alipay import AlipaySigner
from paypack import AgentPay

signer = AlipaySigner(
    app_id="你的沙箱APPID",
    private_key_path="你的私钥.pem",
    alipay_public_key_path="支付宝沙箱公钥.pem",
    sandbox=True,                 # 沙箱模式，不真扣钱
)

pay = AgentPay(signer=signer, network="alipay")

# 生成收银台链接 → 用户扫码即付
pay_url = signer.page_pay(
    out_trade_no="ORDER_20260710_001",
    total_amount=9.90,
    subject="AI API 调用月费",
)
print(f"打开链接付款: {pay_url}")
```

对比一下：自己对接支付宝要读几百页文档、写几百行代码。用 PayPack：**2行。**

---

## 10 分钟接入 Dify

> 你的 AI 聊天机器人能直接收钱了

### 目录结构（已写好的）

```
dify_plugin/
├── manifest.yaml           # 插件声明
├── main.py                 # 入口
├── openapi.json            # API 定义
├── .env.example            # 配置示例
├── provider/
│   ├── paypack.py          # 凭据验证
│   └── paypack.yaml        # Provider 声明
└── tools/
    ├── paypack_pay.py      #   支付工具
    ├── paypack_pay.yaml
    ├── paypack_query.py    #   查单工具
    ├── paypack_query.yaml
    ├── paypack_refund.py   #   退款工具
    └── paypack_refund.yaml
```

### 接入步骤

#### 第 1 步：安装 Dify Plugin CLI

```bash
pip install dify-plugin
```

#### 第 2 步：本地调试

```bash
cd dify_plugin

# 复制配置
cp .env.example .env
# 编辑 .env 填入你的私钥/APPID

# 启动本地调试
dify-plugin run
```

#### 第 3 步：配置凭据

在 Dify 中打开 PayPack 插件，填入凭据：

**链上支付模式：**

| 字段 | 值 |
|------|-----|
| payment_mode | `crypto` |
| private_key | `0x你的ETH私钥` |
| network | `base-sepolia` |
| spend_limit_daily | `10.0` |
| broadcast | `true` |

**支付宝模式：**

| 字段 | 值 |
|------|-----|
| payment_mode | `alipay` |
| app_id | `你的沙箱APPID` |
| private_key | `粘贴私钥PEM内容` |
| alipay_public_key | `粘贴支付宝公钥PEM内容` |
| sandbox | `true` |

#### 第 4 步：在 Dify 工作流里用

在 Dify 的 Chatflow / Workflow 中添加 PayPack 节点：

```
用户输入 → LLM → PayPack 支付 → 返回结果
```

AI 会自动理解用户意图并调用支付。比如用户说"帮我付 0.001 ETH 给 0x...", Dify 的 LLM 会自动调用 PayPack 工具完成支付。

#### 第 5 步：打包发布

```bash
dify-plugin package
```

生成 `.difypkg` 文件，可以直接上传到 Dify 插件市场。

---

## 实战场景

### 场景 1：AI 自动买数据

```python
import requests
from paypack import AgentPay

pay = AgentPay(
    wallet_config={"private_key": "0x..."},
    network="base-sepolia",
)

# AI 访问付费 API
response = requests.get("https://api.premium-weather.com/v2/tokyo")

if response.status_code == 402:  # ← 要求付费
    # AI 自己付钱，然后重试
    pay.auto_handle_402(response)
    response = requests.get("https://api.premium-weather.com/v2/tokyo")
    data = response.json()
    print(f"AI 已自动支付并获取数据: {data}")
```

### 场景 2：Dify 里的付费咨询机器人

```
用户: "帮我分析一下这支股票"
AI:   "我可以用 Premium 分析模型，费用 0.01 USDC/次，要分析吗？"
用户:  "好"
AI:   → 调用 PayPack 支付 0.01 USDC
     → 获取分析结果
     → "XXX股票建议买入，目标价..." 
```

### 场景 3：Agent-to-Agent 经济

```
Agent A (你的AI): "我需要一份竞品分析报告"
Agent B (数据Agent): → HTTP 402 要求 0.005 ETH
Agent A: → auto_handle_402 → 自动付 0.005 ETH
Agent B: → 返回分析报告
Agent A: "收到，谢谢"
```

**全程无人干预。**

---

## 支持的链

| 网络 | 币种 | 适合 |
|------|------|------|
| Base Sepolia (测试) | ETH, USDC | 开发测试 |
| Base Mainnet | ETH, USDC | 生产（Gas最低） |
| Ethereum Mainnet | ETH, USDC | 生产（最安全） |
| Polygon Mainnet | POL, USDC | 生产（低Gas） |
| Arbitrum Mainnet | ETH, USDC | 生产（L2） |

---

## 安全机制（已内置）

| 机制 | 说明 |
|------|------|
| 日消费限额 | `spend_limit_daily=10.0` — AI每天最多花10美元 |
| 余额检查 | 付款前自动检查，余额不足直接报错 |
| 限额持久化 | SQLite / Redis，重启不丢失 |
| RPC故障转移 | 多节点自动切换，不丢交易 |
| 交易重试 | 指数退避 + RBF提价 |
| AWS KMS签名 | 生产环境私钥不出HSM |

---

## 常见问题

**Q: 要钱吗？**
A: 链上支付（ETH/USDC）：开源免费。微信支付：需要商业 License。支付宝：免费。

**Q: 支持主网吗？**
A: 链上支付支持 Base/Ethereum/Polygon/Arbitrum 主网。支付宝生产环境（v0.6）开发中。

**Q: 能用在 Coze 上吗？**
A: Coze 插件开发中。现在可以直接用 Python SDK + Coze 的代码节点。

**Q: 私钥安全吗？**
A: 生产环境可以用 AWS KMS Signer，私钥不出 HSM。开发环境请用测试网 + 测试私钥。

---

## 下一步

- GitHub: https://github.com/rhcjw/paypack
- Gitee（国内）: https://gitee.com/rhcjw_com/paypack
- PyPI: https://pypi.org/project/langchain-paypack/
- 已验证交易: ETH `d5f7ec...2127` | USDC `c4c24c...27e` | CNY `20260709...995`

**Star ⭐ 一下，让更多国内开发者知道 AI 也能付人民币了。**
