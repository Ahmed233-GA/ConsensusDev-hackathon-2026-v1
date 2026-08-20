import json
import os
import subprocess
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path
from sqlalchemy import create_engine, text

ROOT_DIR = Path(__file__).resolve().parent.parent
PYTHON_EXE = sys.executable
DB_PATH = ROOT_DIR / "consensusdev.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

def clean_database():
    print("[*] Cleaning SQLite database (preserving users table)...")
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM findings;"))
        conn.execute(text("DELETE FROM approval_events;"))
        conn.execute(text("DELETE FROM audit_logs;"))
        conn.execute(text("DELETE FROM reviews;"))
        conn.commit()
    print("[+] Database cleaned successfully.")

def trigger_review(diff: str, pr_number: int, title: str, author: str, branch: str) -> dict:
    url = "http://127.0.0.1:8000/api/reviews/trigger"
    data = {
        "diff": diff,
        "pr_number": pr_number,
        "title": title,
        "author": author,
        "branch": branch
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=10.0) as resp:
        return json.loads(resp.read().decode("utf-8"))

def main():
    print("=" * 60)
    print(" 🧹 RESETTING CONSENSUS DEV DEMO DATA (4 REAL REVIEWS)")
    print("=" * 60)

    # 1. Clean Database
    clean_database()

    # 2. Restart Gateway to clear in-memory cache
    print("\n[*] Waiting for Gateway to be ready...")
    time.sleep(1.0)

    # Review 1: Clean PR -> APPROVED (Author: Soliman)
    print("\n[1/4] Generating Review 1: Clean PR -> APPROVED (Author: Soliman)")
    diff_clean = """diff --git a/services/auth.py b/services/auth.py
+def validate_session_token(token: str) -> bool:
+    if not token or len(token) < 32:
+        return False
+    return True
+
+def test_validate_session():
+    assert validate_session_token("a" * 32) is True
+    assert validate_session_token("") is False
"""
    res1 = trigger_review(
        diff=diff_clean,
        pr_number=142,
        title="feat(auth): add JWT session validation with tests",
        author="Soliman",
        branch="feature/jwt-auth"
    )
    rev1 = res1["review"]
    print(f"  -> Decision: {rev1['consensus']['decision'].upper()} | Score: {rev1['consensus']['score']}/100 | Findings: {len(rev1['findings'])}")

    # Review 2: Security Vulnerability -> REJECTED (Author: Shahd)
    print("\n[2/4] Generating Review 2: Security Vulnerability -> REJECTED (Author: Shahd)")
    diff_sec = """diff --git a/services/profile.py b/services/profile.py
+aws_secret = "AKIA1234567890EXAMPLE"
+def get_user_profile(user_id: str):
+    query = f"SELECT * FROM users WHERE id = '{user_id}'"
+    return db.execute(query)
"""
    res2 = trigger_review(
        diff=diff_sec,
        pr_number=143,
        title="feat(profile): expose user profile endpoint",
        author="Shahd",
        branch="feature/user-profile"
    )
    rev2 = res2["review"]
    tools = [f.get("tool") for f in rev2["findings"]]
    print(f"  -> Decision: {rev2['consensus']['decision'].upper()} | Score: {rev2['consensus']['score']}/100 | Findings: {len(rev2['findings'])} ({tools})")

    # Review 3: QA Failure -> REJECTED (Author: Nourhan)
    print("\n[3/4] Generating Review 3: QA Failure -> REJECTED (Author: Nourhan)")
    diff_qa = """diff --git a/services/billing.py b/services/billing.py
+def calculate_invoice_total(items: list) -> float:
+    total = sum(i['price'] * i['qty'] for i in items)
+    assert False, "Regression: invoice formula broken"
+    return total
+
+def test_invoice_calculation():
+    assert False
"""
    res3 = trigger_review(
        diff=diff_qa,
        pr_number=144,
        title="refactor(billing): update invoice calculation",
        author="Nourhan",
        branch="refactor/billing-calc"
    )
    rev3 = res3["review"]
    print(f"  -> Decision: {rev3['consensus']['decision'].upper()} | Score: {rev3['consensus']['score']}/100 | QA Status: {rev3['qaStats']['status']} | Blockers: {rev3['consensus']['blocking_reasons']}")

    print("\n[+] First 3 reviews successfully processed.")

if __name__ == "__main__":
    main()
