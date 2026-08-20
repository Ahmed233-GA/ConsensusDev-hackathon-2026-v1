import json
import os
import re
import subprocess
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path
from sqlalchemy import create_engine, text

ROOT_DIR = Path(__file__).resolve().parent.parent
PYTHON_EXE = str(ROOT_DIR / ".venv" / "Scripts" / "python.exe")
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


def kill_port_process(port: int):
    try:
        cmd = f"netstat -ano | findstr :{port}"
        out = subprocess.check_output(cmd, shell=True).decode("utf-8")
        pids = set()
        for line in out.splitlines():
            line = line.strip()
            if f":{port}" in line and "LISTENING" in line:
                parts = line.split()
                if len(parts) >= 5:
                    pids.add(parts[-1])
        for pid in pids:
            print(f"[*] Terminating process on port {port} (PID: {pid})...")
            subprocess.run(f"taskkill /PID {pid} /F /T", shell=True, check=False)
    except Exception as e:
        print(f"[-] No listening process found on port {port} ({e})")


def start_service(cmd_list, port: int):
    print(f"[*] Starting service on port {port}: {' '.join(cmd_list)}")
    p = subprocess.Popen(cmd_list, cwd=ROOT_DIR)
    for _ in range(10):
        time.sleep(0.5)
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=1.0) as resp:
                if resp.status == 200:
                    print(f"[+] Service on port {port} is ONLINE.")
                    return p
        except Exception:
            pass
    return p


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
    with urllib.request.urlopen(req, timeout=25.0) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    print("=" * 70)
    print(" [LAUNCH] GENERATING REALISTIC 4-REVIEW DEMO STORY DATASET")
    print("=" * 70)

    # 1. Clean Database
    clean_database()

    # -------------------------------------------------------------
    # Review 1: Clean PR -> APPROVED (Author: Soliman)
    # -------------------------------------------------------------
    print("\n[1/4] Review 1: Clean, Well-Written PR -> APPROVED (Author: Soliman)")
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
    print(f"  -> PR #{rev1['meta']['prNumber']} ({rev1['meta']['author']['name']})")
    print(f"     Decision: {rev1['consensus']['decision'].upper()} | Score: {rev1['consensus']['score']}/100 | Findings: {len(rev1['findings'])}")

    # -------------------------------------------------------------
    # Review 2: Security Vulnerability -> REJECTED (Author: Shahd)
    # -------------------------------------------------------------
    print("\n[2/4] Review 2: Real Security Vulnerability -> REJECTED (Author: Shahd)")
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
    tool_names = [f.get("tool") for f in rev2["findings"]]
    print(f"  -> PR #{rev2['meta']['prNumber']} ({rev2['meta']['author']['name']})")
    print(f"     Decision: {rev2['consensus']['decision'].upper()} | Score: {rev2['consensus']['score']}/100 | Findings: {len(rev2['findings'])} {tool_names}")

    # -------------------------------------------------------------
    # Review 3: QA Failure -> REJECTED (Author: Nourhan)
    # -------------------------------------------------------------
    print("\n[3/4] Review 3: QA Test Failure -> REJECTED (Author: Nourhan)")
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
    print(f"  -> PR #{rev3['meta']['prNumber']} ({rev3['meta']['author']['name']})")
    print(f"     Decision: {rev3['consensus']['decision'].upper()} | Score: {rev3['consensus']['score']}/100 | QA Status: {rev3['qaStats']['status']} | Blockers: {rev3['consensus']['blocking_reasons']}")

    # -------------------------------------------------------------
    # Review 4: Scanner + QA Offline -> BLOCKED Fail-Closed (Author: AhmedAtia)
    # -------------------------------------------------------------
    print("\n[4/4] Review 4: Clean PR during Scanner & QA Outage -> BLOCKED Fail-Closed (Author: AhmedAtia)")
    print("  [*] Temporarily terminating Scanner (:8002) and QA Runner (:8003)...")
    kill_port_process(8002)
    kill_port_process(8003)
    time.sleep(1.5)

    diff_failclosed = """diff --git a/services/calc.py b/services/calc.py
+def safe_divide(a: float, b: float) -> float:
+    if b == 0.0:
+        return 0.0
+    return a / b
"""
    res4 = trigger_review(
        diff=diff_failclosed,
        pr_number=145,
        title="fix(calc): correct division edge case",
        author="AhmedAtia",
        branch="fix/div-zero"
    )
    rev4 = res4["review"]
    print(f"  -> PR #{rev4['meta']['prNumber']} ({rev4['meta']['author']['name']})")
    print(f"     Decision: {rev4['consensus']['decision'].upper()} | Status: {rev4['status']}")
    print(f"     Gates: {rev4['consensus']['gates']}")
    print(f"     Honest Blockers: {rev4['consensus']['blocking_reasons']}")
    print(f"     Findings Count: {len(rev4['findings'])} (Must be 0, no fake findings)")

    # -------------------------------------------------------------
    # Restart Scanner and QA Runner
    # -------------------------------------------------------------
    print("\n[*] Restarting Scanner (:8002) and QA Runner (:8003)...")
    start_service([PYTHON_EXE, "-m", "uvicorn", "scanners.main:app", "--port", "8002", "--host", "0.0.0.0"], 8002)
    start_service([PYTHON_EXE, "-m", "uvicorn", "qa_runner.main:app", "--port", "8003", "--host", "0.0.0.0"], 8003)

    print("\n" + "=" * 70)
    print(" [SUCCESS] DEMO DATASET GENERATION COMPLETE!")
    print("=" * 70)


if __name__ == "__main__":
    main()
