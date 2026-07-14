import requests
TOKEN = "YOUR_GITHUB_TOKEN"
r = requests.post(
    "https://api.github.com/repos/langchain-ai/langchain/issues",
    headers={"Authorization": f"token {TOKEN}"},
    json={
        "title": "[Integration] PayPack - AI Agent Payment Tool for LangChain",
        "body": "pip install langchain-paypack\n\nUniversal payment middleware for AI agents.\n\nhttps://github.com/rhcjw/paypack\nhttps://pypi.org/project/langchain-paypack/"
    }
)
print(r.status_code, r.json().get("html_url", r.json().get("message", "")))
