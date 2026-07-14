import requests

TOKEN = "YOUR_GITHUB_TOKEN"

# Use the actual IDs from the query
REPO_ID = "R_kgDOIPDwlg"
CATEGORY_ID = "DIC_kwDOIPDwls4CS6Vc"  # Announcements (or try a different one)

# Try creating discussion
mutation = """
mutation($repoId: ID!, $categoryId: ID!, $title: String!, $body: String!) {
  createDiscussion(input: {
    repositoryId: $repoId,
    categoryId: $categoryId,
    title: $title,
    body: $body
  }) {
    discussion {
      url
      number
    }
  }
}
"""

body = """## PayPack - Universal Payment Middleware for LangChain Agents

Hi LangChain community! I built **PayPack** — a LangChain tool that lets AI agents make autonomous on-chain payments.

**The problem:** HTTP 402 "Payment Required" has existed since 1991 but was never usable — humans had to manually pay. Now x402 (Coinbase) and AP2 (Google) protocols enable machine-to-machine payments. PayPack makes them one line of code.

**Quick install:**
```bash
pip install langchain-paypack
```

**Usage:**
```python
from langchain_paypack import PayPackTool

tool = PayPackTool(private_key="0x...", network="base-sepolia")
result = tool._run(to="0x...", amount=0.001, currency="USDC")
```

**Production features (v0.5.0):**
- AWS KMS signing (private key never leaves HSM)
- RPC failover (multi-node auto-switch)
- Transaction retry with Replace-by-Fee
- Persistent limits (Redis/SQLite)
- ERC-4337 batch settlement for gas optimization
- Multi-chain: Base, Ethereum, Polygon, Arbitrum

**Links:**
- PyPI: https://pypi.org/project/langchain-paypack/
- GitHub: https://github.com/rhcjw/paypack

Would love feedback and contributions!"""

variables = {
    "repoId": REPO_ID,
    "categoryId": CATEGORY_ID,
    "title": "PayPack - Universal Payment Middleware for LangChain Agents",
    "body": body
}

r = requests.post("https://api.github.com/graphql",
    headers={"Authorization": f"bearer {TOKEN}"},
    json={"query": mutation, "variables": variables}
)

result = r.json()
print(f"Status: {r.status_code}")
if "data" in result and result["data"]["createDiscussion"]:
    url = result["data"]["createDiscussion"]["discussion"]["url"]
    print(f"DISCUSSION CREATED: {url}")
else:
    print("Response:", result)
    if "errors" in result:
        for err in result["errors"]:
            print(f"  Error: {err.get('message', '')}")
