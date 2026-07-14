import requests, json, base64

TOKEN = "YOUR_GITHUB_TOKEN"
HEADERS = {"Authorization": f"token {TOKEN}"}

# 1. Get README
r = requests.get("https://api.github.com/repos/kyrolabs/awesome-langchain/readme", headers=HEADERS)
d = r.json()
content = base64.b64decode(d["content"]).decode()
sha = d["sha"]

# Find sections
lines = content.split("\n")
for i, line in enumerate(lines):
    if line.startswith("##") and "LangChain" in line:
        print(f"L{i}: {line.strip()}")
    if line.startswith("##") and ("Tool" in line or "Agent" in line or "Payment" in line):
        print(f"L{i}: {line.strip()}")

# Find Tools section more broadly
print("\n--- All ## headers ---")
for i, line in enumerate(lines):
    if line.startswith("## "):
        print(f"L{i}: {line.strip()}")
