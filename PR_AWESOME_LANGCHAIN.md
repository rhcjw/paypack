# PayPack - AI Agent Payment Middleware

## One-liner
`pip install langchain-paypack` → `agent.pay()` → Done.

## What is PayPack?

PayPack is the **universal payment middleware for AI agents** — the missing "pay" button for autonomous agents. It wraps on-chain payments (ETH, USDC via x402/AP2 protocols + ERC-4337 batch settlement) into a **single LangChain Tool**.

The HTTP 402 status code has existed since 1991 but was never usable — because when a server says "Payment Required," a human has to pull out a credit card. AI agents change that. x402 (Coinbase) and AP2 (Google) protocols enable machine-to-machine payments. PayPack makes them **one line of code**.

## Key Features

- **LangChain Native**: Drop-in `PayPackTool` for any LangChain agent
- **Signer Abstraction**: `LocalSigner` for dev, `AWSKMSSigner` for production (private key never leaves HSM)
- **ERC-4337 Batch Settlement**: Bundle micro-payments to save gas
- **RPC Failover**: Multi-node auto-switch with health checks
- **Transaction Retry**: Exponential backoff + Replace-by-Fee
- **Limit Persistence**: Redis / SQLite backends, survives agent restarts
- **Multi-chain**: Base, Ethereum, Polygon, Arbitrum

## Quick Start

```python
from paypack import AgentPay, LocalSigner

signer = LocalSigner(private_key="0x...")
pay = AgentPay(signer=signer, network="base-sepolia")

# Single payment
pay.send(to="0xRecipient", amount=0.001, currency="USDC")

# Auto-handle HTTP 402
pay.auto_handle_402(response)

# Batch 100 micropayments in one tx
pay.batch_pay([
    {"to": "0x...", "amount": 0.001, "currency": "USDC"},
    {"to": "0x...", "amount": 0.002, "currency": "ETH"},
])
```

## Links

- **PyPI**: https://pypi.org/project/langchain-paypack/
- **GitHub**: https://github.com/rhcjw/paypack
- **Gitee**: https://gitee.com/rhcjw_com/paypack

## Version

v0.5.0 — Production-ready: RPC failover, retry, KMS signing, persistent limits.
