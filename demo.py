"""
ConsensusDev — Live Demo Script
Sends 2 sample PRs (one clean, one risky) to the backend webhook, then
opens the Streamlit dashboard in the browser.

Run:
    python demo.py
"""

from __future__ import annotations

import time
import webbrowser

import requests

BACKEND_URL = "http://localhost:8000"
DASHBOARD_URL = "http://localhost:8501"

CLEAN_PR = {
    "pr_number": 142,
    "repo_name": "shopflow/api",
    "branch": "feat/checkout-validation",
    "author": "m.medhat",
    "title": "Add checkout form validation helpers",
    "diff_text": """\
diff --git a/src/checkout/validators.py b/src/checkout/validators.py
new file mode 100644
--- /dev/null
+++ b/src/checkout/validators.py
@@ -0,0 +1,18 @@
+import re
+from datetime import datetime
+
+def validate_email(email: str) -> bool:
+    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-.]+$"
+    return re.match(pattern, email) is not None
+
+def validate_card_number(card: str) -> bool:
+    digits = re.sub(r"\\D", "", card)
+    if len(digits) < 13 or len(digits) > 19:
+        return False
+    total = sum(int(d) for d in digits)
+    return total % 10 == 0
+
+def validate_expiry(month: int, year: int) -> bool:
+    if not (1 <= month <= 12):
+        return False
+    return datetime.now().year <= year
""",
}

RISKY_PR = {
    "pr_number": 143,
    "repo_name": "shopflow/api",
    "branch": "feat/user-search-api",
    "author": "a.atia",
    "title": "Add user search endpoint with query filters",
    "diff_text": """\
diff --git a/src/api/users.py b/src/api/users.py
--- a/src/api/users.py
+++ b/src/api/users.py
@@ -12,6 +12,14 @@
+import os

+DB_URL = "postgres://admin:SuperSecret123@db.internal:5432/prod"
+API_KEY = "sk-live-aaX9f2K3nQ7mZ0vB4cD8eF2gH6iJ0kL"

 @router.get("/search")
 def search_users(q: str = Query(...)):
-    return db.execute(f"SELECT * FROM users WHERE name LIKE '%{q}%'")
+    query = f"SELECT * FROM users WHERE name LIKE '%{q}%'"
+    return db.execute(query)
""",
}

PERF_PR = {
    "pr_number": 144,
    "repo_name": "shopflow/web",
    "branch": "perf/lazy-product-images",
    "author": "soliman",
    "title": "Lazy-load product images and memoize price filter",
    "diff_text": """\
diff --git a/src/components/ProductGrid.tsx b/src/components/ProductGrid.tsx
--- a/src/components/ProductGrid.tsx
+++ b/src/components/ProductGrid.tsx
@@ -5,8 +5,14 @@
-const ProductCard = require("../ProductCard").default;
+const ProductCard = lazy(() => import("../ProductCard"));

 export function ProductGrid({ products, maxPrice }) {
-  const filtered = products.filter(p => p.price <= maxPrice);
+  const filtered = useMemo(
+    () => products.filter(p => p.price <= maxPrice),
+    [products, maxPrice]
+  );
   return (
     <div className="grid">
-      {filtered.map(p => <ProductCard key={p.id} product={p} />)}
+      {filtered.map(p => <ProductCard key={p.id} product={p} />)}
""",
}


def send_pr(pr: dict) -> dict:
    print(f"  → Sending PR #{pr['pr_number']} ({pr['title']})…")
    resp = requests.post(f"{BACKEND_URL}/webhook", json=pr, timeout=30)
    resp.raise_for_status()
    result = resp.json()
    print(f"    Consensus: {result['consensus'].upper()}")
    print(f"    Review time: {result['review_time_ms'] / 1000:.1f}s")
    print(f"    Findings: {len(result['findings'])}")
    for f in result["findings"]:
        if f["severity"] in ("critical", "high"):
            print(f"      [{f['severity'].upper()}] {f['title']}")
    print()
    return result


def main() -> None:
    print("=" * 60)
    print("  ConsensusDev — Live PR Review Demo")
    print("  DevOpsDays Cairo 2026 Hackathon · Team Track 2")
    print("=" * 60)
    print()

    # Open the dashboard in the browser
    print(f"Opening dashboard at {DASHBOARD_URL} …")
    webbrowser.open(DASHBOARD_URL)
    time.sleep(2)

    print("\n▶ PR #1 — CLEAN (checkout validation, should be APPROVED)\n")
    send_pr(CLEAN_PR)

    print("▶ PR #2 — RISKY (hardcoded secret + SQL injection, should be BLOCKED)\n")
    send_pr(RISKY_PR)

    print("▶ PR #3 — PERFORMANCE (lazy-load + memoization, should be APPROVED)\n")
    send_pr(PERF_PR)

    print("=" * 60)
    print("  Demo complete! Check the dashboard for the live results.")
    print("=" * 60)


if __name__ == "__main__":
    main()
