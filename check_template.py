import requests

# Try to find LangChain issue templates
urls = [
    "https://raw.githubusercontent.com/langchain-ai/langchain/master/.github/ISSUE_TEMPLATE/integration.yml",
    "https://raw.githubusercontent.com/langchain-ai/langchain/master/.github/ISSUE_TEMPLATE/feature-request.yml",
    "https://raw.githubusercontent.com/langchain-ai/langchain/master/.github/ISSUE_TEMPLATE/config.yml",
]

for url in urls:
    r = requests.get(url)
    print(f"{url.split('/')[-1]}: {r.status_code}")
    if r.status_code == 200:
        print(r.text[:1500])
    print("---")
