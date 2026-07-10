# PayPack Quick Start — Let AI Pay for Itself in 5 Minutes | 5 分钟让 AI 自己付钱

> Hands-on tutorial for Dify / Coze / LangChain developers | 给 Dify / Coze / LangChain 开发者的实战教程

---

## What You Need | 你要准备什么

| Required | On-Chain (USDC/ETH) | Alipay (CNY) | WeChat Pay (CNY) |
|----------|--------------------|--------------|-------------------|
| Wallet private key | ✅ ETH key | ✅ Merchant key | ✅ Merchant key |
| Base Sepolia test ETH | ✅ Get from faucet | — | — |
| Alipay sandbox APPID | — | ✅ | — |
| WeChat merchant/cert | — | — | ✅ Commercial License |
| Python 3.9+ | ✅ | ✅ | ✅ |
| Install PayPack | ✅ | ✅ | ✅ |

---

## 5 min: On-Chain Payment (ETH/USDC) | 5 分钟跑通链上支付

### Step 1: Install | 第 1 步：安装

```bash
pip install langchain-paypack
```

### Step 2: Create `ai_pay_demo.py` | 第 2 步：创建文件

```python
from paypack import AgentPay

# Put your ETH private key here | 把你的 ETH 私钥填在这里
# Get test ETH: https://www.alchemy.com/faucets/base-sepolia
PRIVATE_KEY = "0x_your_private_key"

pay = AgentPay(
    wallet_config={"private_key": PRIVATE_KEY},
    network="base-sepolia",       # testnet, safe | 测试网，安全
    spend_limit_daily=10.0,       # AI can spend max $10/day | AI 每天最多花 10 美元
    broadcast=True,               # True = actually goes on-chain | True = 真的上链
)

# Send ETH | 付 ETH
receipt = pay.send(
    to="0x9cbF3Ca5185Ca55C804c2c4b726De212A17734F8",
    amount=0.0001,
    currency="ETH",
)
print(f"ETH payment done! TX hash: {receipt['tx_hash']}")

# Send USDC | 付 USDC
receipt = pay.send(
    to="0x9cbF3Ca5185Ca55C804c2c4b726De212A17734F8",
    amount=0.001,
    currency="USDC",
)
print(f"USDC payment done! TX hash: {receipt['tx_hash']}")

# Batch payment (ERC-4337, saves gas) | 批量支付（省 Gas）
receipt = pay.batch_pay([
    {"to": "0x_addr_A", "amount": 0.0001, "currency": "ETH"},
    {"to": "0x_addr_B", "amount": 0.0002, "currency": "USDC"},
])
print(f"Batch done! {receipt['batch_size']} txs, total {receipt['total_amount']}")
```

### Step 3: Run | 第 3 步：跑起来

```bash
python ai_pay_demo.py
```

Output | 输出：

```
ETH payment done! TX hash: 0xd5f7ec94342c26a132289a9898ffd488...
USDC payment done! TX hash: 0xc4c24c4c1c8fd2ae738ed91cd87596a...
```

**That's it. Your AI just paid real money. | 这就通了。你刚刚让 AI 自己付了钱。**

---

## 5 min: Alipay Integration | 5 分钟接入支付宝

### Prerequisites (one-time, 5 min) | 准备工作（一次性，5分钟）

1. Sign up at [Alipay Open Platform](https://open.alipay.com/) | 去支付宝开放平台入驻开发者
2. Enter "Sandbox" → get your sandbox APPID | 进入"沙箱环境" → 获取沙箱 APPID
3. Generate RSA2 key pair, upload public key | 生成 RSA2 密钥对，上传公钥到沙箱
4. Download Alipay sandbox public key | 下载支付宝沙箱公钥

### Code (2 lines) | 代码（2行）

```python
from paypack.signer.alipay import AlipaySigner
from paypack import AgentPay

signer = AlipaySigner(
    app_id="your_sandbox_appid",
    private_key_path="your_private_key.pem",
    alipay_public_key_path="alipay_sandbox_public_key.pem",
    sandbox=True,                 # sandbox mode, no real money | 沙箱模式，不真扣钱
)

pay = AgentPay(signer=signer, network="alipay")

# Generate cashier page → user scans QR to pay | 生成收银台链接 → 用户扫码即付
pay_url = signer.page_pay(
    out_trade_no="ORDER_20260710_001",
    total_amount=9.90,
    subject="AI API Monthly Subscription | AI API 调用月费",
)
print(f"Open to pay: {pay_url}")
```

Compare: doing Alipay yourself means hundreds of pages of docs, hundreds of lines of code. PayPack: **2 lines.** | 自己对接支付宝要读几百页文档、写几百行代码。用 PayPack：**2行。**

---

## 10 min: Dify Integration | 10 分钟接入 Dify

> Your AI chatbot can now accept payments. | 你的 AI 聊天机器人能直接收钱了

### Quick Install | 快速安装

```bash
# In Dify: Plugins → Install from GitHub | 在 Dify 中：插件 → 从 GitHub 安装
# Enter: https://github.com/rhcjw/paypack
```

Or download [paypack-0.1.0.difypkg](https://github.com/rhcjw/paypack/releases/tag/v0.1.0) and upload locally. | 或下载 `.difypkg` 本地上传。

### Configure Credentials | 配置凭据

**Crypto Mode | 链上支付模式：**

| Field | Value |
|-------|-------|
| payment_mode | `crypto` |
| private_key | `0x_your_eth_key` |
| network | `base-sepolia` |
| spend_limit_daily | `10.0` |
| broadcast | `true` |

**Alipay Mode | 支付宝模式：**

| Field | Value |
|-------|-------|
| payment_mode | `alipay` |
| app_id | `your_sandbox_appid` |
| private_key | `paste PEM content` |
| alipay_public_key | `paste alipay public key PEM` |
| sandbox | `true` |

### Use in Workflow | 在工作流里用

Add PayPack node in Dify Chatflow / Workflow:

```
User Input → LLM → PayPack Pay → Result
```

The LLM automatically understands payment intent and calls the tool. | AI 会自动理解用户意图并调用支付。

---

## Real-World Scenarios | 实战场景

### Scenario 1: AI Auto-Purchases Data | AI 自动买数据

```python
import requests
from paypack import AgentPay

pay = AgentPay(
    wallet_config={"private_key": "0x..."},
    network="base-sepolia",
)

# AI accesses a paid API | AI 访问付费 API
response = requests.get("https://api.premium-weather.com/v2/tokyo")

if response.status_code == 402:  # ← payment required | 要求付费
    # AI pays and retries | AI 自己付钱，然后重试
    pay.auto_handle_402(response)
    response = requests.get("https://api.premium-weather.com/v2/tokyo")
    data = response.json()
    print(f"AI auto-paid and got data: {data}")
```

### Scenario 2: Paid Consulting Bot in Dify | Dify 里的付费咨询机器人

```
User: "Analyze this stock for me"
AI:   "I can use the Premium model for 0.01 USDC. Analyze?"
User: "Yes"
AI:   → calls PayPack for 0.01 USDC
     → fetches analysis
     → "BUY rating, target price..."
```

### Scenario 3: Agent-to-Agent Economy | Agent 经济

```
Agent A (your AI): "I need a competitor analysis report"
Agent B (data agent): → HTTP 402 requires 0.005 ETH
Agent A: → auto_handle_402 → pays 0.005 ETH
Agent B: → returns report
Agent A: "Received, thanks."
```

**Zero human intervention. | 全程无人干预。**

---

## Supported Chains | 支持的链

| Network | Currency | Best For |
|---------|----------|----------|
| Base Sepolia (testnet) | ETH, USDC | Development / 开发测试 |
| Base Mainnet | ETH, USDC | Production, lowest gas / 生产（Gas最低） |
| Ethereum Mainnet | ETH, USDC | Production, most secure / 生产（最安全） |
| Polygon Mainnet | POL, USDC | Production, low gas / 生产（低Gas） |
| Arbitrum Mainnet | ETH, USDC | Production, L2 / 生产（L2） |

---

## Built-in Security | 安全机制（已内置）

| Mechanism | Description |
|-----------|-------------|
| Daily spend limit | `spend_limit_daily=10.0` — AI can spend at most $10/day |
| Balance check | Auto-checks before paying, errors if insufficient |
| Limit persistence | SQLite / Redis, survives restarts |
| RPC failover | Multi-node auto-switch, no lost transactions |
| Tx retry | Exponential backoff + Replace-by-Fee |
| AWS KMS signer | Private key never leaves HSM in production |

---

## FAQ | 常见问题

**Q: Is it free?** | **要钱吗？**
A: On-chain (ETH/USDC): free & open-source. WeChat Pay: commercial license required. Alipay: free.

**Q: Mainnet support?** | **支持主网吗？**
A: On-chain: Base/Ethereum/Polygon/Arbitrum mainnet live. Alipay production (v0.6) in progress.

**Q: Works on Coze?** | **能用在 Coze 上吗？**
A: Coze plugin coming. For now, use Python SDK + Coze code nodes.

**Q: Is my private key safe?** | **私钥安全吗？**
A: Use AWS KMS Signer in production — key never leaves HSM. Use testnet keys for development.

---

## Links | 下一步

- GitHub: https://github.com/rhcjw/paypack
- Gitee (China): https://gitee.com/rhcjw_com/paypack
- PyPI: https://pypi.org/project/langchain-paypack/
- Dify Plugin: [paypack-0.1.0.difypkg](https://github.com/rhcjw/paypack/releases/tag/v0.1.0)
- Verified TXs: ETH `d5f7ec...2127` | USDC `c4c24c...27e` | CNY `20260709...995`

**Star ⭐ — let more developers know AI can pay in yuan. | 让更多开发者知道 AI 也能付人民币了。**
