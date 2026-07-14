import requests

TOKEN = "YOUR_GITHUB_TOKEN"
HEADERS = {"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github.v3+json"}

body = """## PayPack - Universal Payment Middleware for LangChain Agents

Hi LangChain team! I built **PayPack** — a LangChain tool that lets AI agents make autonomous on-chain payments. Published on PyPI as `langchain-paypack`.

### What it solves

The HTTP 402 "Payment Required" status has existed since 1991 but was never usable — humans had to manually pay. x402 (Coinbase) and AP2 (Google) protocols change that. PayPack handles the entire loop:

```
Server returns 402 → agent.auto_handle_402(response) → payment confirmed
```

### Quick Start

```bash
pip install langchain-paypack
```

```python
from langchain_paypack import PayPackTool

tool = PayPackTool(private_key="0x...", network="base-sepolia")
result = tool._run(to="0x...", amount=0.001, currency="USDC")
```

### Features (v0.5.0)
- **Signer abstraction**: LocalSigner for dev, AWSKMSSigner for production
- **ERC-4337 batch settlement**: Bundle micropayments to save gas
- **RPC failover**: Multi-node auto-switch with health checks
- **Transaction retry**: Exponential backoff + Replace-by-Fee
- **Persistent limits**: Redis / SQLite backends
- **Multi-chain**: Base, Ethereum, Polygon, Arbitrum

### Links
- **PyPI**: https://pypi.org/project/langchain-paypack/
- **GitHub**: https://github.com/rhcjw/paypack

Would love to get this listed as a community integration. Happy to make any changes needed!"""

data = {
    "title": "[Integration] PayPack - AI Agent Payment Tool for LangChain",
    "body": body,
    "labels": ["community", "integration"]
}

r = requests.post(
    "https://api.github.com/repos/langchain-ai/langchain/issues",
    headers=HEADERS, json=data
)
result = r.json()
if r.status_code == 201:
    print(f"ISSUE CREATED: {result['html_url']}")
else:
    print(f"Status {r.status_code}: {result.get('message', result)}")
