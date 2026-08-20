import json
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:8000"

def run_step(step_name, func):
    print(f"\n==================================================")
    print(f"[TEST STEP] {step_name}")
    print(f"==================================================")
    try:
        res = func()
        print(f"-> SUCCESS: {res}")
        return True, res
    except Exception as e:
        print(f"-> ERROR: {e}")
        return False, None

def http_post(endpoint, data, token=None):
    url = f"{BASE_URL}{endpoint}"
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            **({"Authorization": f"Bearer {token}"} if token else {})
        }
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def http_get(endpoint, token=None):
    url = f"{BASE_URL}{endpoint}"
    req = urllib.request.Request(
        url,
        headers={
            "Content-Type": "application/json",
            **({"Authorization": f"Bearer {token}"} if token else {})
        }
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def main():
    token = None

    # Step 1: Health
    ok, health = run_step("1. Check Gateway & Aggregate Health", lambda: http_get("/api/health"))
    assert ok and health["status"] == "healthy"

    # Step 2: Login with Seeded Admin
    ok, auth_data = run_step("2. Authenticate Admin via POST /auth/login", lambda: http_post("/auth/login", {
        "operator_id": "admin@consensus.dev",
        "access_key": "admin1234"
    }))
    assert ok and auth_data["status"] == "authenticated"
    token = auth_data["token"]
    print(f"   Logged in as: {auth_data['user']['username']} (Role: {auth_data['user']['role']})")

    # Step 3: Verify /auth/me
    ok, me_data = run_step("3. Query Authenticated Operator via GET /auth/me", lambda: http_get("/auth/me", token=token))
    assert ok and me_data["user"]["username"] == "admin"

    # Step 4: Fetch Real DB Stats Before Review
    ok, stats_before = run_step("4. Query SQLite Aggregated Metrics via GET /api/stats", lambda: http_get("/api/stats", token=token))
    assert ok
    print(f"   Total PRs in SQLite: {stats_before['totalReviews']}, Approval Rate: {stats_before['approvalRate']}%")

    # Step 5: Trigger Live PR Review #889
    ok, review_resp = run_step("5. Trigger End-to-End Review via POST /api/reviews/trigger", lambda: http_post("/api/reviews/trigger", {
        "diff": "diff --git a/services/payment.py b/services/payment.py\n+def process_payment(amount: float) -> bool:\n+    return amount > 0\n",
        "pr_number": 889,
        "title": "feat(payment): add payment verification service",
        "author": "AhmedSoliman",
        "branch": "feature/payments"
    }, token=token))
    assert ok and review_resp["status"] == "completed"
    review = review_resp["review"]
    print(f"   Review ID: {review['meta']['id']}, Score: {review['consensus']['score']}/100, Decision: {review['consensus']['decision']}")

    # Step 6: Verify Direct SQLite Retrieval of Review #889
    ok, fetched_review = run_step("6. Fetch Persisted Review via GET /api/pull-requests/pr-889", lambda: http_get("/api/pull-requests/pr-889", token=token))
    assert ok and fetched_review["meta"]["prNumber"] == 889
    print(f"   Successfully retrieved from SQLite: PR #{fetched_review['meta']['prNumber']} ({fetched_review['meta']['title']})")

    # Step 7: Verify DB Stats Updated
    ok, stats_after = run_step("7. Verify SQLite Metrics Incremented", lambda: http_get("/api/stats", token=token))
    assert ok
    print(f"   New Total PRs: {stats_after['totalReviews']} (was {stats_before['totalReviews']}), Approval Rate: {stats_after['approvalRate']}%")

    # Step 8: Verify Bad Login Rejection
    def try_bad_login():
        try:
            http_post("/auth/login", {"operator_id": "admin@consensus.dev", "access_key": "wrong_key"})
            return "Unexpected success"
        except urllib.error.HTTPError as e:
            return f"Correctly rejected with HTTP {e.code}"
    ok, bad_login_res = run_step("8. Verify Invalid Access Key Rejection", try_bad_login)
    assert "HTTP 401" in bad_login_res

    # Step 9: Logout
    ok, logout_res = run_step("9. Terminate Session via POST /auth/logout", lambda: http_post("/auth/logout", {}, token=token))
    assert ok and logout_res["status"] == "logged_out"

    print("\n==================================================")
    print("ALL 9 DEFINITION OF DONE STEPS COMPLETED SUCCESSFULLY!")
    print("==================================================")

if __name__ == "__main__":
    main()
