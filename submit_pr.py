import requests, json, base64

TOKEN = "YOUR_GITHUB_TOKEN"
HEADERS = {"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github.v3+json"}

# 1. Get README
r = requests.get("https://api.github.com/repos/rhcjw/awesome-langchain/contents/README.md", headers=HEADERS)
d = r.json()
content = base64.b64decode(d["content"]).decode()
sha = d["sha"]

# 2. Find insertion point (after ## Tools section, before first ## Open Source Projects)
lines = content.split("\n")
tools_start = None
tools_end = None
for i, line in enumerate(lines):
    if line.startswith("## Tools"):
        tools_start = i
    if tools_start and line.startswith("## Open Source Projects") and tools_end is None:
        tools_end = i
        break

# Find the last actual entry in Tools (look for last line starting with "- [")
last_entry = tools_start
for i in range(tools_start + 1, tools_end):
    if lines[i].strip().startswith("- [") or lines[i].strip().startswith("- **[") or lines[i].strip().startswith("- ["):
        last_entry = i

print(f"Tools: L{tools_start} - L{tools_end}, last entry at L{last_entry}")
print(f"Last entry: {lines[last_entry][:80]}")

# 3. Insert PayPack entry after last entry
paypack_entry = "- [PayPack](https://github.com/rhcjw/paypack) - Universal payment middleware for AI agents. x402/AP2 protocols, ETH/USDC, ERC-4337 batch settlement, AWS KMS signing."

lines.insert(last_entry + 1, paypack_entry)
new_content = "\n".join(lines)

# 4. Commit to fork
commit_data = {
    "message": "Add PayPack - AI agent payment middleware",
    "content": base64.b64encode(new_content.encode()).decode(),
    "sha": sha,
    "branch": "main"
}
r = requests.put(
    f"https://api.github.com/repos/rhcjw/awesome-langchain/contents/README.md",
    headers=HEADERS, json=commit_data
)
print(f"Commit: {r.status_code} {r.json().get('commit', {}).get('sha', '')}")

# 5. Create PR to kyrolabs/awesome-langchain
pr_data = {
    "title": "Add PayPack - AI Agent Payment Middleware for LangChain",
    "head": "rhcjw:main",
    "base": "main",
    "body": """## PayPack - Universal Payment Middleware for AI Agents

**pip install langchain-paypack** → agent.pay() → Done.

PayPack is the missing "pay" button for autonomous AI agents. It wraps on-chain payments into a single LangChain Tool.

### What it does:
- Auto-handles HTTP 402 responses (x402/AP2 protocols)
- ETH & USDC transfers on Base/Ethereum/Polygon/Arbitrum
- ERC-4337 batch settlement for gas optimization
- AWS KMS signing for production security

### Quick example:
```python
from paypack import AgentPay, LocalSigner
pay = AgentPay(signer=LocalSigner(private_key="0x..."), network="base-sepolia")
pay.send(to="0xRecipient", amount=0.001, currency="USDC")
```

- **PyPI**: https://pypi.org/project/langchain-paypack/
- **GitHub**: https://github.com/rhcjw/paypack
- **Version**: v0.5.0 (production-ready: RPC failover, retry, KMS, persistent limits)
"""
}
r = requests.post(
    "https://api.github.com/repos/kyrolabs/awesome-langchain/pulls",
    headers=HEADERS, json=pr_data
)
result = r.json()
if r.status_code == 201:
    print(f"PR CREATED: {result['html_url']}")
else:
    print(f"PR Error {r.status_code}: {result}")
