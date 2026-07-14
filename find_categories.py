import requests

TOKEN = "YOUR_GITHUB_TOKEN"

query = """
query {
  repository(owner: "langchain-ai", name: "langchain") {
    discussionCategories(first: 20) {
      nodes {
        id
        name
        description
        isAnswerable
      }
    }
  }
}
"""

r = requests.post("https://api.github.com/graphql",
    headers={"Authorization": f"bearer {TOKEN}"},
    json={"query": query}
)

data = r.json()
if "data" in data and data["data"]["repository"]:
    for cat in data["data"]["repository"]["discussionCategories"]["nodes"]:
        print(f"  {cat['name']:30s} -> {cat['id']}")
else:
    print(data)
