# PayPack — AI Agent Payment Plugin

> **🌐 Dual-channel · Neutral · Independent**
>
> PayPack is the **world's only** Agent payment middleware supporting **Alipay AND WeChat Pay** dual-channel in a single integration.
> PayPack stays neutral — not bound to Alipay, not bound to Tencent, not bound to any tech giant ecosystem.
> Private keys remain **local** in Dify's Credential Vault — never transmitted to any third-party cloud.

> Two lines of code, let your Dify AI Agent pay by itself.

PayPack is the first Dify plugin that supports **both on-chain crypto and Chinese fiat payments** in a single integration. Your AI agent can send USDC/ETH on-chain, or create Alipay/WeChat Pay orders for CNY payments — all from within a Dify workflow.

---

## Features

| Tool | Description |
|------|-------------|
| **PayPack Pay** | Send USDC/ETH on-chain or create Alipay CNY payment orders |
| **PayPack Query** | Check transaction status by trade number or transaction hash |
| **PayPack Refund** | Refund Alipay orders (full or partial) |

---

## Installation

1. In Dify, go to **Plugins** → **Upload Local Plugin**
2. Select the `paypack-0.1.0.difypkg` file
3. Wait for installation. The plugin will appear under the **Tools** category.

If Dify has plugin signature verification enabled, you may need to set `FORCE_VERIFYING_SIGNATURE=false` in your `.env` file.

---

## Configuration

After installation, click the PayPack plugin and fill in the credentials. You can choose between two modes:

### Crypto Mode (USDC/ETH on-chain)

| Parameter | Description | Example |
|-----------|-------------|---------|
| `payment_mode` | Set to `crypto` | `crypto` |
| `private_key` | Your ETH wallet private key (stored encrypted by Dify) | `0xabc123...` |
| `network` | Blockchain network to use | `base-sepolia` (test) / `ethereum` (mainnet) |
| `spend_limit_daily` | Maximum daily spend for the AI agent | `10.0` |
| `broadcast` | Actually broadcast to chain, or dry-run only | `true` |

**Supported networks:** Base Sepolia, Base Mainnet, Ethereum Mainnet, Polygon Mainnet, Arbitrum Mainnet.

### Alipay Mode (CNY fiat)

| Parameter | Description | Example |
|-----------|-------------|---------|
| `payment_mode` | Set to `alipay` | `alipay` |
| `app_id` | Alipay application ID (from Alipay Open Platform) | `2021...` |
| `private_key` | Merchant RSA private key (PEM format) | `-----BEGIN RSA PRIVATE KEY-----...` |
| `alipay_public_key` | Alipay production public key (PEM format) | `-----BEGIN PUBLIC KEY-----...` |
| `sandbox` | Use sandbox for testing, or production for real payments | `true` |

> ⚠️ **Security:** `private_key` and `alipay_public_key` are stored as `secret-input` type. Dify encrypts them at rest. They never appear in logs or plugin outputs.

---

## Usage in Dify Workflow

### Simple: Let the LLM decide

In a Chatflow with an Agent node, the LLM will automatically understand payment intent and invoke the right tool:

```
User: "Pay 9.9 USDC to 0x123... for the report"

Agent: → calls paypack_pay(currency="USDC", amount=9.9, recipient="0x123...")
       → returns tx_hash and explorer link
       → "Payment sent! TX: 0xabc..."
```

```
User: "Create an Alipay order for 29.90 CNY — AI consultation fee"

Agent: → calls paypack_pay(currency="CNY", amount=29.90, subject="AI consultation")
       → returns Alipay trade_no
       → "Order created. Trade number: 20260710..."
```

### Advanced: Workflow orchestration

```
[Start]
   │
   ▼
[LLM] Extract amount, currency, recipient from user message
   │
   ▼
[PayPack Pay] Execute payment
   │
   ├── success → [LLM] "Payment complete. TX: {{paypack_pay.tx_hash}}"
   │
   └── failure → [LLM] "Payment failed: {{paypack_pay.error}}"
```

---

## Tool Reference

### PayPack Pay

Creates and executes a payment.

| Input | Type | Required | Description |
|-------|------|----------|-------------|
| `recipient` | string | ✅ | Wallet address (crypto) or Alipay user ID (CNY) |
| `amount` | number | ✅ | Payment amount in the chosen currency |
| `currency` | string | ❌ | `USDC`, `ETH`, or `CNY`. Default: `USDC` |
| `subject` | string | ❌ | Payment description (used for Alipay order title) |

**Example output (crypto):**
```json
{
  "status": "success",
  "currency": "USDC",
  "amount": 9.9,
  "recipient": "0x1234567890abcdef",
  "tx_hash": "0xabcdef1234567890...",
  "explorer_link": "https://sepolia.basescan.org/tx/0xabc...",
  "daily_remaining": 0.1,
  "timestamp": "2026-07-10T08:30:00Z"
}
```

**Example output (Alipay):**
```json
{
  "status": "success",
  "currency": "CNY",
  "amount": 29.90,
  "subject": "AI consultation fee",
  "trade_no": "2026071022001412345678901234",
  "alipay_status": "10000",
  "alipay_message": "Success"
}
```

### PayPack Query

Queries the status of a previous payment.

| Input | Type | Required | Description |
|-------|------|----------|-------------|
| `trade_no` | string | ✅ | Trade number (Alipay) or TX hash (crypto) |
| `currency` | string | ❌ | `CNY`, `USDC`, or `ETH`. Default: `CNY` |

### PayPack Refund

Refunds an Alipay order. Only successful payments can be refunded.

| Input | Type | Required | Description |
|-------|------|----------|-------------|
| `trade_no` | string | ✅ | The Alipay trade number to refund |
| `refund_amount` | number | ❌ | Amount to refund (omit for full refund) |

---

## Prerequisites

- **Dify** 1.0+ (Community Edition or Cloud)
- **Python** 3.12+ (handled by Dify plugin runtime)
- **PayPack SDK** — auto-installed via `paypack-langchain>=0.1.2` dependency
- **Alipay merchant account** — required for CNY payments (sandbox available for testing)

---

## Privacy

This plugin does **not** collect any personal data. All credentials are stored encrypted in Dify's credential vault. See [PRIVACY.md](PRIVACY.md) for details.

---

## Links

- Source: https://github.com/rhcjw/paypack
- Gitee mirror: https://gitee.com/rhcjw_com/paypack
- PyPI SDK: https://pypi.org/project/langchain-paypack/
