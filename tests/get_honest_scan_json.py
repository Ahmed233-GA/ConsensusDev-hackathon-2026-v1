import json
import urllib.request

diff_content = """diff --git a/app/db.py b/app/db.py
+++ b/app/db.py
@@ -1,3 +1,3 @@
+query = f"SELECT * FROM users WHERE id = {user_input}"
+api_key = "sk-1234567890abcdef1234567890abcdef"
"""

body = json.dumps({"diff": diff_content}).encode("utf-8")
req = urllib.request.Request(
    "http://127.0.0.1:8002/scan",
    data=body,
    headers={"Content-Type": "application/json"},
)

with urllib.request.urlopen(req) as resp:
    print(json.dumps(json.loads(resp.read().decode("utf-8")), indent=2))
