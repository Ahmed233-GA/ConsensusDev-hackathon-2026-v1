import json
import urllib.request

def main():
    diff_code = """diff --git a/services/payment_gateway.py b/services/payment_gateway.py
+import hmac
+import hashlib
+import time
+
+def verify_stripe_webhook_signature(payload: bytes, signature_header: str, secret: str) -> bool:
+    if not signature_header or not secret:
+        return False
+    try:
+        parts = dict(x.split('=', 1) for x in signature_header.split(','))
+        timestamp = parts.get('t')
+        v1_sig = parts.get('v1')
+        if not timestamp or not v1_sig:
+            return False
+        # Prevent replay attacks (> 5 minutes old)
+        if abs(time.time() - int(timestamp)) > 300:
+            return False
+        signed_payload = f"{timestamp}.".encode('utf-8') + payload
+        expected_sig = hmac.new(secret.encode('utf-8'), signed_payload, hashlib.sha256).hexdigest()
+        return hmac.compare_digest(expected_sig, v1_sig)
+    except Exception:
+        return False
+
+def test_webhook_verification():
+    secret = "whsec_test_secret_key_1234567890"
+    payload = b'{"event": "payment_intent.succeeded"}'
+    ts = str(int(time.time()))
+    sig = hmac.new(secret.encode('utf-8'), f"{ts}.".encode('utf-8') + payload, hashlib.sha256).hexdigest()
+    header = f"t={ts},v1={sig}"
+    assert verify_stripe_webhook_signature(payload, header, secret) is True
+    assert verify_stripe_webhook_signature(payload, "t=123,v1=invalid", secret) is False
"""

    data = {
        "diff": diff_code,
        "pr_number": 146,
        "title": "feat(payments): add Stripe webhook HMAC signature verification & replay protection",
        "author": "Omar",
        "branch": "feature/stripe-webhook-hmac"
    }

    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/reviews/trigger",
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )

    with urllib.request.urlopen(req, timeout=30.0) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        pr = res["review"]
        print("=== NEW PULL REQUEST PROCESSED AND PERSISTED ===")
        print(f"PR #: #{pr['meta']['prNumber']}")
        print(f"Title: {pr['meta']['title']}")
        print(f"Author: {pr['meta']['author']['name']}")
        print(f"Decision: {pr['consensus']['decision'].upper()}")
        print(f"Score: {pr['consensus']['score']}/100")
        print(f"Gates: {pr['consensus']['gates']}")
        print(f"Status: {pr['status']}")

if __name__ == "__main__":
    main()
