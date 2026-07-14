import requests

TOKEN = "YOUR_GITHUB_TOKEN"

# Test token
r = requests.get("https://api.github.com/user", headers={"Authorization": f"token {TOKEN}"})
if r.status_code == 200:
    user = r.json().get("login", "unknown")
    print(f"Token valid — logged in as: {user}")
    
    # Remove all package labels from issue #38727, keep only external + feature request
    # Get current labels
    r2 = requests.get(
        "https://api.github.com/repos/langchain-ai/langchain/issues/38727/labels",
        headers={"Authorization": f"token {TOKEN}"}
    )
    if r2.status_code == 200:
        labels = [l["name"] for l in r2.json()]
        print(f"Current labels ({len(labels)}): {labels}")
        
        # Labels to remove (all package-specific ones)
        remove = [l for l in labels if l not in ("external", "feature request")]
        print(f"Removing: {remove}")
        
        for label in remove:
            r3 = requests.delete(
                f"https://api.github.com/repos/langchain-ai/langchain/issues/38727/labels/{label}",
                headers={"Authorization": f"token {TOKEN}"}
            )
            if r3.status_code == 200:
                print(f"  Removed: {label}")
            else:
                print(f"  Failed: {label} ({r3.status_code})")
        
        print("Done cleaning labels")
    else:
        print(f"Get labels error: {r2.status_code} {r2.text[:200]}")
else:
    print(f"Token invalid: {r.status_code} — need new token")
    print("Go to: https://github.com/settings/tokens and create a new classic token")
