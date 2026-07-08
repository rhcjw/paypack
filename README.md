# PayPack

**Universal Payment Middleware for AI Agents**

> One line of code. Let your AI pay for itself.

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![LangChain](https://img.shields.io/badge/LangChain-Integration-green.svg)](https://python.langchain.com/)

---

## The Problem

The HTTP 402 status code has existed in the protocol specification since **1991**. For over three decades, it has never been used in practice.

Why? Because when a server returns "Payment Required," there must be a human on the other end of the screen to pull out a credit card.

**AI Agents change everything.**

An autonomous AI agent can make hundreds of API calls, data purchases, and content subscriptions per hour — with individual amounts as small as **$0.001**. Traditional payment systems collapse under micro-transaction fees and the need for manual approval.

**x402** (proposed by Coinbase) and **AP2** (proposed by Google) are solving this: the server returns 402 with a payee address and amount, and the AI agent completes the on-chain payment automatically — all within a single HTTP round trip. No human intervention required.

**PayPack's mission**: to be the **thinnest, most reliable, most indispensable middleware layer** in the AI payment stack.

---

## Architecture

```text
       AI Agent Application
                │
                ▼
         PayPack SDK  ◄── You are here
                │
        ┌───────┼───────┐
        │       │       │
  Protocol   Payment   Security
   Parser    Router    Fuse
  (x402/    (USDC/    (Limits/
   AP2)      Fiat)     Audit)
        │       │       │
        └───────┼───────┘
                │
                ▼
    Settlement Networks
  (Base / Solana / Alipay+)
```

PayPack doesn't invent new protocols. It wraps scattered capabilities into a single `agent.pay()`.

---

## Features

- **Multi-Protocol**: Supports both x402 and AP2 with automatic detection
- **Signer Abstraction**: Pluggable signing — LocalSigner for dev, AWSKMSSigner for production (private key never leaves HSM)
- **Nano-Payment Optimized**: Built for sub-$0.01 transactions with ERC-4337 batch settlement to save gas
- **Security Fuse**: Daily spend limits, balance checks, auditable receipts
- **Full Audit Trail**: Every payment generates a queryable JSON receipt
- **LangChain Native**: Drop-in `PayPackTool` for LangChain agents
- **Dual Compliance Track**: USDC on-chain + Alipay AI Pay (planned)

---

## Installation

```bash
pip install https://gitee.com/rhcjw_com/paypack/raw/master/dist/langchain_paypack-0.4.0-py3-none-any.whl
```

> **Note**: Includes the full `paypack` SDK (core + signer + nanopay).

---

## Quick Start

```python
from paypack import AgentPay

# Initialize
pay = AgentPay(
    wallet_config={"private_key": "your-key"},
    network="base-sepolia",
    spend_limit_daily=10.0,
    broadcast=False
)

# Scenario 1: Auto-handle HTTP 402
import requests
response = requests.get("https://api.data-provider.com/premium")
if response.status_code == 402:
    content = pay.auto_handle_402(response)

# Scenario 2: Direct nano-payment
receipt = pay.send(
    to="0xRecipientAddress",
    amount=0.001,
    currency="USDC"
)
print(receipt["tx_hash"])
```

### LangChain Integration

```python
from langchain_paypack import PayPackTool

tool = PayPackTool(
    private_key="0x...",
    wallet_address="0x...",
    network="base-sepolia",
    spend_limit_daily=10.0,
    broadcast=False
)

# AI agent calls this directly
result = tool._run(to="0x...", amount=0.001, currency="USDC")
print(result)
```

---

## Supported Networks

| Network | Chain ID | Currency |
|---------|----------|----------|
| Base Sepolia (testnet) | 84532 | ETH, USDC |
| Base Mainnet | 8453 | ETH, USDC |
| Ethereum Mainnet | 1 | ETH, USDC |
| Polygon Mainnet | 137 | POL, USDC |
| Arbitrum Mainnet | 42161 | ETH, USDC |

---

## Milestones

✅ **v0.1.0 (2026-06-20)** — ETH + USDC offline signing verified on Base Sepolia testnet

✅ **v0.2.0** — AP2 protocol parser completed

✅ **v0.3.0 (2026-06-21)** — LangChain tool plugin tested, multi-chain support, balance checks, environment variable key support

| Currency | Amount | Offline-Signed TX Hash |
|----------|--------|------------------------|
| ETH | 0.0001 ETH | `d5f7ec94342c26a132289a9898ffd4885010089d1ddba19951117618a3992127` |
| USDC | 0.001 USDC | `c4c24c4c1c8fd2ae738ed91cd87596ad2c672337b5ebf6d42a392adf61760e27` |

> 📌 **Ready for mainnet broadcast**: `broadcast=True` parameter is in place. Sepolia testnet holds 0.531 ETH for verification.

## Roadmap

| Phase | Goal | Status |
|-------|------|--------|
| v0.1 | Base testnet x402 payment loop (ETH + USDC) | ✅ Done |
| v0.2 | AP2 protocol support | ✅ Done |
| v0.3 | LangChain plugin release | ✅ Done |
| v0.4 | Alipay AI Pay integration | 🚧 Planned |
| v1.0 | PayPack Cloud (hosted service) | 🚧 Planned |

---

## Why Now?

- Stablecoin annual transaction volume surpassed **$33 trillion** (2025) — 20x PayPal
- AI agent count projected to reach **22 billion** (McKinsey)
- x402 protocol already processes tens of millions of transactions on Solana
- LangChain/LlamaIndex payment plugin market is **completely vacant**

Infrastructure is ready. Demand is exploding. The payment layer lacks a standard answer.

---

## Contributing

Star this repo, open an issue, or reach out if you're building in the agent economy.

## License

Apache License 2.0. See [LICENSE](LICENSE).
