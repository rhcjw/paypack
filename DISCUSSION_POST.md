## PayPack — Universal Payment Middleware for AI Agents

Hi LangChain community! 👋

I built **PayPack** — a LangChain tool that lets AI agents make autonomous on-chain payments. Think of it as the "pay" button for your agent.

**What problem it solves:**

The HTTP 402 "Payment Required" status has existed since 1991 but was never usable — humans had to manually pay. Now with x402 (Coinbase) and AP2 (Google) protocols, servers can request payment and AI agents can pay automatically. PayPack handles the entire chain:

```
Server returns 402 → agent.auto_handle_402(response) → payment confirmed
```

**Why this matters for LangChain users:**

- Your agent hits a paid API → PayPack auto-pays → agent continues working
- Agent subscribes to data feeds, buys computation, pays for content
- Micro-payments as small as $0.001 become viable via ERC-4337 batch settlement

**Quick install:**

```bash
pip install langchain-paypack
```

**Code:**

```python
from langchain_paypack import PayPackTool

tool = PayPackTool(
    private_key="0x...",
    network="base-sepolia",
    spend_limit_daily=10.0,
)

# Now your agent can pay
result = tool._run(to="0x...", amount=0.001, currency="USDC")
```

**Production features:**
- ✅ AWS KMS signing (private key never leaves HSM)
- ✅ RPC failover (3-node auto-switch)
- ✅ Transaction retry with Replace-by-Fee
- ✅ Persistent limits (Redis/SQLite)
- ✅ ERC-4337 batch settlement for gas optimization

**Links:**
- PyPI: https://pypi.org/project/langchain-paypack/
- GitHub: https://github.com/rhcjw/paypack

Would love feedback and contributions! 🚀
