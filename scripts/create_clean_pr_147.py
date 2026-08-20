import json
import urllib.request

def main():
    diff_code = """diff --git a/services/rate_limiter.py b/services/rate_limiter.py
+import time
+
+class TokenBucketRateLimiter:
+    def __init__(self, capacity: int = 100, refill_rate_per_sec: float = 10.0):
+        self.capacity = float(capacity)
+        self.tokens = float(capacity)
+        self.refill_rate = refill_rate_per_sec
+        self.last_update = time.time()
+
+    def allow_request(self, cost: float = 1.0) -> bool:
+        now = time.time()
+        elapsed = now - self.last_update
+        self.last_update = now
+        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
+        if self.tokens >= cost:
+            self.tokens -= cost
+            return True
+        return False
+
+def test_rate_limiter():
+    limiter = TokenBucketRateLimiter(capacity=5, refill_rate_per_sec=1.0)
+    for _ in range(5):
+        assert limiter.allow_request() is True
+    assert limiter.allow_request() is False
"""

    data = {
        "diff": diff_code,
        "pr_number": 147,
        "title": "feat(rate-limit): implement token bucket rate limiter with sliding window refills",
        "author": "Youssef",
        "branch": "feature/rate-limiter"
    }

    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/reviews/trigger",
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )

    with urllib.request.urlopen(req, timeout=30.0) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        pr = res["review"]
        print("=== NEW CLEAN PR CREATED AND PERSISTED ON TOP ===")
        print(f"PR #: #{pr['meta']['prNumber']}")
        print(f"Title: {pr['meta']['title']}")
        print(f"Author: {pr['meta']['author']['name']}")
        print(f"Decision: {pr['consensus']['decision'].upper()}")
        print(f"Score: {pr['consensus']['score']}/100")
        print(f"Gates: {pr['consensus']['gates']}")
        print(f"Status: {pr['status']}")

if __name__ == "__main__":
    main()
