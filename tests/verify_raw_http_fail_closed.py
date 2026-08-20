import json
import urllib.request
import urllib.error

# PR payload sent to Gateway
payload = {
    "diff": "diff --git a/calc.py b/calc.py\n+def add(a, b): return a + b",
    "pr_number": 777,
    "pr_title": "feat: clean calculation PR but scanner/qa offline",
    "author": "AhmedDev",
    "branch": "feature/calc",
}

data = json.dumps(payload).encode("utf-8")
req = urllib.request.Request(
    "http://127.0.0.1:8000/api/reviews/trigger",
    data=data,
    headers={"Content-Type": "application/json", "User-Agent": "FailClosedVerifier"},
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
