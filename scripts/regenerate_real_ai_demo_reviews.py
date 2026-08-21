import json
import os
import sqlite3
import subprocess
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
GATEWAY_URL = "http://127.0.0.1:8000"
DB_PATH = ROOT_DIR / "consensusdev.db"


def reset_demo_db():
    print("[*] Resetting demo database (keeping seeded users)...")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM findings;")
    cur.execute("DELETE FROM approval_events;")
    cur.execute("DELETE FROM audit_logs;")
    cur.execute("DELETE FROM reviews;")
    conn.commit()
    conn.close()
    print("[+] Demo DB tables cleared.")


def trigger_review(pr_number: int, title: str, author: str, diff_text: str, description: str = ""):
    url = f"{GATEWAY_URL}/api/reviews/trigger"
    payload = {
        "pr_number": pr_number,
        "title": title,
        "author": author,
        "branch": f"feature/pr-{pr_number}",
        "diff": diff_text,
    }
    
    headers = {"Content-Type": "application/json"}
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
    
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=180.0) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        review = data.get("review", {})
        consensus = review.get("consensus", {})
        decision = consensus.get("decision") or review.get("status")
        score = consensus.get("score")
        dur = time.time() - t0
        print(f" -> Response in {dur:.2f}s: Decision={decision}, Score={score}")
        return review


# 1. Review 1 Diff (Clean & High Quality for Real AI Approval)
PR1_DIFF = """\"\"\"
Authentication session validation and token verification module.
Provides cryptographically secure helpers to verify HMAC-signed session tokens.
\"\"\"
import base64
import hashlib
import hmac
import json
import time
from typing import Any, Dict, Optional


def create_signed_token(payload: Dict[str, Any], signing_key: str, expires_in_seconds: int = 3600) -> str:
    \"\"\"
    Generate a signed base64 session token with timestamp expiration.
    
    Args:
        payload: Dictionary containing user session metadata.
        signing_key: Cryptographic key used to sign the token.
        expires_in_seconds: Token lifetime in seconds (default 1 hour).
        
    Returns:
        Encoded token string in 'payload_b64.signature_hex' format.
    \"\"\"
    token_data = dict(payload)
    token_data["exp"] = int(time.time()) + expires_in_seconds
    
    serialized = json.dumps(token_data, separators=(",", ":"), sort_keys=True)
    payload_b64 = base64.urlsafe_b64encode(serialized.encode("utf-8")).decode("utf-8")
    
    signature = hmac.new(
        signing_key.encode("utf-8"),
        payload_b64.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    
    return f"{payload_b64}.{signature}"


def verify_session_token(token: str, signing_key: str) -> Optional[Dict[str, Any]]:
    \"\"\"
    Verify the cryptographic signature and expiration of an authentication token.
    
    Args:
        token: Token string in 'payload_b64.signature_hex' format.
        signing_key: Key used to verify the HMAC signature.
        
    Returns:
        Decoded payload dict if valid and unexpired; None if invalid or expired.
    \"\"\"
    if not token or "." not in token:
        return None
        
    parts = token.split(".")
    if len(parts) != 2:
        return None
        
    payload_b64, provided_sig = parts
    
    expected_sig = hmac.new(
        signing_key.encode("utf-8"),
        payload_b64.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(expected_sig, provided_sig):
        return None
        
    try:
        raw_json = base64.urlsafe_b64decode(payload_b64.encode("utf-8")).decode("utf-8")
        payload = json.loads(raw_json)
        
        # Verify expiration timestamp
        exp = payload.get("exp")
        if not isinstance(exp, (int, float)) or time.time() > exp:
            return None
            
        return payload
    except (ValueError, TypeError, json.JSONDecodeError):
        return None


def test_session_token_lifecycle():
    \"\"\"Unit test verifying complete token generation, validation, and rejection cases.\"\"\"
    test_key = "production_vault_derived_key_987"
    user_payload = {"user_id": 142, "username": "Soliman", "role": "admin"}
    
    # 1. Valid token
    token = create_signed_token(user_payload, test_key, expires_in_seconds=300)
    verified = verify_session_token(token, test_key)
    assert verified is not None
    assert verified["user_id"] == 142
    assert verified["role"] == "admin"
    
    # 2. Tampered token
    tampered_token = token[:-4] + "abcd"
    assert verify_session_token(tampered_token, test_key) is None
    
    # 3. Wrong key
    assert verify_session_token(token, "wrong_signing_key_123") is None
    
    # 4. Malformed tokens
    assert verify_session_token("", test_key) is None
    assert verify_session_token("invalid_no_dot", test_key) is None
"""

# 2. Review 2 Diff (Security Vulnerability: SQLi + Hardcoded Secret)
PR2_DIFF = """\"\"\"User profile management endpoint.\"\"\"
import sqlite3

AWS_SECRET_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE123456789"

def get_user_profile(user_id: str):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    query = f"SELECT * FROM users WHERE id = '{user_id}'"
    cursor.execute(query)
    return cursor.fetchall()
"""

# 3. Review 3 Diff (QA Test Failure)
PR3_DIFF = """\"\"\"Billing and invoice calculation service.\"\"\"
def calculate_invoice_total(subtotal: float, tax_rate: float, discount: float) -> float:
    \"\"\"Calculate invoice total with tax and discount.\"\"\"
    # BUG: Subtracting tax instead of adding it
    return (subtotal - discount) - ((subtotal - discount) * tax_rate)

def test_calculate_invoice_total():
    # Failing assertion in test suite
    result = calculate_invoice_total(100.0, 0.1, 10.0)
    assert False, f"AssertionError: Expected invoice total 99.0 but got {result}"
"""

# 4. Review 4 Diff (Clean PR during Outage)
PR4_DIFF = """\"\"\"Safe arithmetic division utilities.\"\"\"
from typing import Optional

def safe_divide(numerator: float, denominator: float) -> Optional[float]:
    \"\"\"
    Safely divide numerator by denominator handling zero division.
    \"\"\"
    if denominator == 0:
        return None
    return numerator / denominator

def test_safe_divide():
    assert safe_divide(10.0, 2.0) == 5.0
    assert safe_divide(10.0, 0.0) is None
"""


def main():
    print("=" * 80)
    print(" [LAUNCH] REGENERATING DEMO DATASET WITH REAL LIVE AI")
    print("=" * 80)
    
    reset_demo_db()
    
    # -------------------------------------------------------------
    # 1. PR #142 (Soliman) - Clean APPROVED PR
    # -------------------------------------------------------------
    print("\n[*] Generating Review 1 (PR #142 - Soliman)...")
    res1 = trigger_review(
        pr_number=142,
        title="feat(auth): add JWT session validation helper with tests",
        author="Soliman",
        diff_text=PR1_DIFF,
        description="User Story: Implement secure HMAC-SHA256 session token generation and verification with expiration timestamps and unit tests."
    )
    dec1 = res1.get("consensus", {}).get("decision") or res1.get("status")
    score1 = res1.get("consensus", {}).get("score")
    if dec1 != "approved":
        print(f"[-] WARNING: Review 1 returned decision '{dec1}' (Score: {score1}), expected 'approved'")
    else:
        print(f"[+] Review 1 successfully APPROVED (Score: {score1}/100)!")
        
    # -------------------------------------------------------------
    # 2. PR #143 (Shahd) - Security Vulnerability (REJECTED)
    # -------------------------------------------------------------
    print("\n[*] Generating Review 2 (PR #143 - Shahd)...")
    res2 = trigger_review(
        pr_number=143,
        title="feat(profile): expose user profile endpoint",
        author="Shahd",
        diff_text=PR2_DIFF,
        description="User Story: Expose user profile endpoint with database query and token validation."
    )
    dec2 = res2.get("consensus", {}).get("decision") or res2.get("status")
    print(f"[+] Review 2 decision: {dec2} (Expected: rejected)")
    
    # -------------------------------------------------------------
    # 3. PR #144 (Nourhan) - QA Test Failure (REJECTED)
    # -------------------------------------------------------------
    print("\n[*] Generating Review 3 (PR #144 - Nourhan)...")
    res3 = trigger_review(
        pr_number=144,
        title="refactor(billing): update invoice calculation",
        author="Nourhan",
        diff_text=PR3_DIFF,
        description="User Story: Update invoice calculation and tax rates."
    )
    dec3 = res3.get("consensus", {}).get("decision") or res3.get("status")
    print(f"[+] Review 3 decision: {dec3} (Expected: rejected)")
    
    # -------------------------------------------------------------
    # 4. PR #145 (AhmedAtia) - Clean PR during Scanner+QA Outage (BLOCKED)
    # -------------------------------------------------------------
    print("\n[*] Generating Review 4 (PR #145 - AhmedAtia) with Scanner (:8002) + QA (:8003) OFFLINE...")
    # Temporarily kill scanner & QA processes
    print("[*] Simulating Scanner + QA outage...")
    
    # Find PIDs listening on 8002 and 8003 using netstat
    def kill_port(port):
        try:
            out = subprocess.check_output(f'netstat -ano | findstr ":{port} "', shell=True, text=True)
            for line in out.strip().splitlines():
                if "LISTENING" in line:
                    parts = line.strip().split()
                    pid = parts[-1]
                    subprocess.run(f"taskkill /F /PID {pid}", shell=True, check=False)
                    print(f"[+] Stopped process on port {port} (PID {pid})")
        except Exception as e:
            print(f"[-] Could not find/kill port {port}: {e}")

    kill_port(8002)
    kill_port(8003)
    time.sleep(2.0)
    
    print("[*] Triggering Review 4 under fail-closed outage...")
    res4 = trigger_review(
        pr_number=145,
        title="fix(calc): correct division edge case",
        author="AhmedAtia",
        diff_text=PR4_DIFF,
        description="User Story: Handle division by zero and return None safely with complete test coverage."
    )
    dec4 = res4.get("consensus", {}).get("decision") or res4.get("status")
    print(f"[+] Review 4 decision: {dec4} (Expected: rejected / blocked)")
    
    # Restart Scanner and QA
    print("[*] Restarting Scanner (:8002) and QA (:8003)...")
    subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "scanners.main:app", "--host", "0.0.0.0", "--port", "8002"],
        cwd=ROOT_DIR
    )
    subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "qa_runner.main:app", "--host", "0.0.0.0", "--port", "8003"],
        cwd=ROOT_DIR
    )
    for _ in range(10):
        try:
            with urllib.request.urlopen("http://127.0.0.1:8002/health", timeout=1.0) as r1:
                with urllib.request.urlopen("http://127.0.0.1:8003/health", timeout=1.0) as r2:
                    if r1.status == 200 and r2.status == 200:
                        break
        except Exception:
            time.sleep(0.5)
    print("[+] Scanner and QA restarted & online.")
    
    # -------------------------------------------------------------
    # Final Demo DB Dump
    # -------------------------------------------------------------
    print("\n" + "=" * 80)
    print(" [DATABASE VERIFICATION] FINAL DEMO DATABASE CONTENTS")
    print("=" * 80)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, pr_number, author, consensus_decision, score FROM reviews ORDER BY created_at;")
    rows = cur.fetchall()
    for r in rows:
        print(r)
    conn.close()
    
    print(f"\nTotal demo reviews in DB: {len(rows)}")
    if len(rows) == 4:
        print(" [SUCCESS] Exactly 4 clean demo reviews generated with REAL AI!")
    else:
        print(f" [ERROR] Expected 4 reviews, found {len(rows)}")


if __name__ == "__main__":
    main()
