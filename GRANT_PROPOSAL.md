# PayPack — Grant Proposal

> **AI Agent Universal Payment Middleware**
>
> One line of code. Let your AI pay for itself.

---

## Executive Summary

**PayPack** is the thinnest, most reliable payment middleware layer for autonomous AI agents. It wraps x402 (Coinbase), AP2 (Google), and mainstream payment protocols into a single `agent.pay()` call — supporting both crypto (ETH/USDC on Base) and fiat (Alipay) channels.

**Status**: Production-ready v0.5.0. Published on PyPI, GitHub, Gitee. Alipay sandbox payment loop verified end-to-end (2026-07-09).

**Ask**: $25,000–$50,000 to complete v0.6 (Alipay production launch), v1.0 (PayPack Cloud).

---

## The Problem

HTTP 402 "Payment Required" has existed since 1991 — but never used, because a human must pull out a credit card. AI agents change this. An autonomous agent can make hundreds of micro-transactions per hour ($0.001 each), and traditional payment rails cannot handle this.

x402 and AP2 define the protocol. **But there is no unified, pluggable middleware to implement them across all chains and payment channels.** Every developer rebuilds the same payment integration from scratch.

---

## What PayPack Does

```
AI Agent Application
       │
       ▼
   PayPack SDK        ◄── One `agent.pay()` call
       │
   ┌───┼───┐
   │   │   │
Protocol  Payment  Security
Parser    Router   Fuse
(x402/    (USDC/   (Limits/
 AP2)      Fiat)    Audit)
   │   │   │
   └───┼───┘
       │
   Settlement Networks
(Base / Alipay / More)
```

- **Protocol Parsing**: Auto-detect x402/AP2 headers and route payments
- **Payment Channels**: USDC on Base (ETH, USDC, ERC-4337 batch); Alipay AI Pay (CNY fiat)
- **Security Fuse**: Daily spend limits, balance checks, auditable receipts
- **LangChain Native**: `PayPackTool` — AI agents call payments directly

---

## Technical Achievements (v0.1–v0.5)

| Version | Feature | Status |
|---------|---------|--------|
| v0.1 | x402 protocol + ETH/USDC on Base Sepolia | Verified |
| v0.2 | AP2 protocol parser | Verified |
| v0.3 | LangChain plugin + multi-chain | Published on PyPI |
| v0.4 | Signer abstraction (LocalSigner + AWSKMSSigner) + ERC-4337 batch settlement | Verified |
| v0.5 | RPC failover, transaction retry (RBF), limit persistence (Redis/SQLite) | Verified |
| v0.6 | Alipay AI Pay — RSA2 signing, page_pay, query, refund | Sandbox verified 2026-07-09 |

### Verified Transactions

| Currency | Amount | TX Hash |
|----------|--------|---------|
| ETH | 0.0001 ETH | `d5f7ec94342c26a132289a9898ffd4885010089d1ddba19951117618a3992127` |
| USDC | 0.001 USDC | `c4c24c4c1c8fd2ae738ed91cd87596ad2c672337b5ebf6d42a392adf61760e27` |
| CNY (Alipay) | 0.63 CNY | Sandbox Trade: `2026070922001406640510096995` |

### Live Assets

| Asset | URL |
|-------|-----|
| GitHub | https://github.com/rhcjw/paypack |
| PyPI | https://pypi.org/project/langchain-paypack/ |
| Gitee (China) | https://gitee.com/rhcjw_com/paypack |
| LangChain PR | https://github.com/kyrolabs/awesome-langchain/pull/448 |
| LangChain Issue | https://github.com/langchain-ai/langchain/issues/38725 |

---

## Why Base?

PayPack is built **on Base** as its primary settlement network:

1. **x402 protocol** was proposed by Coinbase (Base's parent company)
2. **Base's low gas fees** enable sub-$0.01 nano-payments
3. **ERC-4337 bundler** integration uses Base's account abstraction infrastructure
4. **USDC on Base** is the canonical stablecoin for AI-to-AI payments
5. **RPC failover** (v0.5) supports multiple Base endpoints for production reliability

PayPack and Base share the same vision: **making on-chain payments invisible to end users.**

---

## Market Context

- Stablecoin annual transaction volume surpassed **$33 trillion** (2025) — 20x PayPal
- AI agent count projected to reach **22 billion** (McKinsey)
- x402 already processes tens of millions of transactions on Solana
- LangChain/LlamaIndex payment plugin market is **completely vacant**
- Alipay's "AI Pay" initiative launched 2026 — PayPack is first to bridge it with x402

---

## Roadmap & Funding Use

### Phase 1: Production Launch ($15K)

- Alipay production app approval + live transaction verification
- Base mainnet deployment with real USDC liquidity
- CI/CD pipeline with automated test suite
- Security audit (external firm)

### Phase 2: PayPack Cloud v1.0 ($20K)

- Hosted API endpoint — no wallet management needed
- Dashboard with spend analytics and receipt tracking
- Multi-tenant support with organization-level limits
- SDK for Python, JavaScript, Rust

### Phase 3: Ecosystem Growth ($15K)

- LangChain/LlamaIndex official plugin listing
- Developer documentation and tutorial series
- Community grants for integrators
- Base Grants retroactive funding eligibility

---

## Team

- **Ronghua** — Full-stack developer. Built the entire PayPack codebase (Python, Solidity, Alipay Open Platform integration). Active in LangChain community.

---

## Contact

- Email: szkj89@163.com
- GitHub: https://github.com/rhcjw
- Website: https://rhcjw.com

---

*PayPack: One line of code. Let your AI pay for itself.*
