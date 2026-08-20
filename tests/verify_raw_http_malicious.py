import json
import urllib.request
import urllib.error

# Malicious PR payload with SQLi & Hardcoded API Key
payload = {
    "diff": "diff --git a/auth.py b/auth.py\n+api_key = 'sk-1234567890abcdef1234567890abcdef'\n+query = f'SELECT * FROM users WHERE id={user_input}'",
    "pr_number": 778,
    "pr_title": "feat: malicious auth patch with SQLi and secret",
    "author": "Attacker",
    "branch": "feature/hack",
}

data = json.dumps(payload).encode("utf-8")
req = urllib.request.Request(
    "http://127.0.0.1:8000/api/reviews/trigger",
    data=data,
    headers={"Content-Type": "application/json", "User-Agent": "MaliciousVerifier"},
)

try:
    with urllib.request.urlopen(req, timeout=15.0) as resp:
        print(f"HTTP/{resp.version/10:.1f} {resp.status} {resp.reason}")
        for k, v in resp.headers.items():
            print(f"{k}: {v}")
        print()
        body = json.loads(resp.read().decode("utf-8"))
        print(json.dumps(body, indent=2))
except urllib.error.HTTPError as e:
    print(f"HTTP/{e.version/10:.1f} {e.code} {e.reason}")
    print(e.read().decode("utf-8"))
