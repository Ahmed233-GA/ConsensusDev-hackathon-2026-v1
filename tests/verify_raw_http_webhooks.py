import hashlib
import hmac
import json
import urllib.request
import urllib.error
import uuid

secret = "test_webhook_secret_key"
url = "http://127.0.0.1:8000/webhook/github"

payload_dict = {
    "action": "opened",
    "number": 999,
    "pull_request": {
        "number": 999,
        "title": "Raw Webhook Test PR",
        "user": {"login": "TestWebhookUser"},
        "head": {"ref": "feature/raw-test", "sha": "11223344556677889900aabbccddeeff11223344"},
        "base": {"ref": "main", "repo": {"full_name": "Ahmed233-GA/ConsensusDev-hackathon-2026-v1"}},
    },
}
body = json.dumps(payload_dict).encode("utf-8")
correct_sig = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
wrong_sig = "sha256=" + "0" * 64
delivery_id = f"del-raw-{uuid.uuid4().hex[:8]}"


def make_request(headers):
    req = urllib.request.Request(url, data=body, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10.0) as resp:
            print(f"HTTP/{resp.version/10:.1f} {resp.status} {resp.reason}")
            data = resp.read().decode("utf-8")
            try:
                print(json.dumps(json.loads(data), indent=2))
            except Exception:
                print(data)
    except urllib.error.HTTPError as e:
        print(f"HTTP/{e.version/10:.1f} {e.code} {e.reason}")
        print(e.read().decode("utf-8"))


print("==================================================")
print("(A) MISSING SIGNATURE:")
print("==================================================")
make_request({"Content-Type": "application/json", "x-github-event": "pull_request"})

print("\n==================================================")
print("(B) WRONG SIGNATURE:")
print("==================================================")
make_request({
    "Content-Type": "application/json",
    "x-github-event": "pull_request",
    "x-hub-signature-256": wrong_sig,
})

print("\n==================================================")
print("(C) CORRECT SIGNATURE (FIRST DELIVERY):")
print("==================================================")
make_request({
    "Content-Type": "application/json",
    "x-github-event": "pull_request",
    "x-hub-signature-256": correct_sig,
    "x-github-delivery": delivery_id,
    "x-consensusdev-sync": "true",
})

print("\n==================================================")
print("(D) DUPLICATE DELIVERY (SAME DELIVERY ID & SHA):")
print("==================================================")
make_request({
    "Content-Type": "application/json",
    "x-github-event": "pull_request",
    "x-hub-signature-256": correct_sig,
    "x-github-delivery": delivery_id,
    "x-consensusdev-sync": "true",
})
