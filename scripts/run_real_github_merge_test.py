import asyncio
import json
import logging
import os
import subprocess
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path
import httpx

# Ensure project root is in path and use test database
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

os.environ["DATABASE_URL"] = f"sqlite:///{ROOT_DIR / 'test_consensusdev.db'}"

from gateway.database import configure_db, init_db
configure_db(os.environ["DATABASE_URL"])
init_db()

from gateway.github_client import GitHubClient
from gateway.orchestrator import PipelineOrchestrator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("RealMergeTest")


def get_github_token() -> str:
    # Check env var first
    token = os.getenv("GITHUB_TOKEN")
    if token and not token.startswith("ghp_your_"):
        return token

    # Retrieve from git credential helper
    p = subprocess.Popen(
        ["git", "credential", "fill"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    out, _ = p.communicate(input="protocol=https\nhost=github.com\n\n")
    for line in out.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1].strip()
    return ""


async def github_api_request(method: str, endpoint: str, token: str, payload: dict = None) -> dict:
    url = f"https://api.github.com{endpoint}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "ConsensusDev-RealMergeTest",
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        if method.upper() == "GET":
            resp = await client.get(url, headers=headers)
        elif method.upper() == "POST":
            resp = await client.post(url, headers=headers, json=payload)
        elif method.upper() == "PUT":
            resp = await client.put(url, headers=headers, json=payload)
        elif method.upper() == "DELETE":
            resp = await client.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported method {method}")

        if resp.status_code in [200, 201, 204]:
            if resp.content:
                return resp.json()
            return {}
        else:
            raise RuntimeError(f"GitHub API {method} {endpoint} failed: HTTP {resp.status_code} {resp.text}")


async def main():
    print("=" * 80)
    print(" [LAUNCH] CONSENSUSDEV REAL GITHUB MERGE VERIFICATION TEST")
    print("=" * 80)

    token = get_github_token()
    if not token:
        print("[-] ERROR: No GitHub token found in environment or git credentials.")
        sys.exit(1)

    print("[+] GitHub Token successfully loaded.")

    # 1. Get authenticated user
    user_data = await github_api_request("GET", "/user", token)
    owner = user_data["login"]
    repo_name = "consensusdev-merge-test"
    repo_full_name = f"{owner}/{repo_name}"
    print(f"[+] Authenticated User: {owner} (Full Repo Target: {repo_full_name})")

    # 2. Create or verify throwaway repo
    try:
        repo_info = await github_api_request("GET", f"/repos/{owner}/{repo_name}", token)
        print(f"[+] Repository '{repo_full_name}' already exists.")
    except Exception:
        print(f"[*] Creating new public repository '{repo_full_name}'...")
        repo_info = await github_api_request(
            "POST",
            "/user/repos",
            token,
            {"name": repo_name, "description": "Throwaway repository for ConsensusDev real merge testing", "auto_init": True, "private": False}
        )
        print(f"[+] Repository created: {repo_info['html_url']}")
        await asyncio.sleep(2.0)

    # 3. Ensure base branch has initial calc.py
    base_file_content = 'def add(a: int, b: int) -> int:\n    return a + b\n'
    import base64
    b64_content = base64.b64encode(base_file_content.encode('utf-8')).decode('utf-8')

    sha_file = None
    try:
        f_info = await github_api_request("GET", f"/repos/{owner}/{repo_name}/contents/calc.py", token)
        sha_file = f_info.get("sha")
    except Exception:
        pass

    put_payload = {
        "message": "init: add base calc.py",
        "content": b64_content,
        "branch": "main"
    }
    if sha_file:
        put_payload["sha"] = sha_file

    try:
        await github_api_request("PUT", f"/repos/{owner}/{repo_name}/contents/calc.py", token, put_payload)
        print("[+] Base calc.py file updated on 'main' branch.")
    except Exception as e:
        print(f"[*] Note on base file update: {e}")

    # 4. Get latest commit SHA on main
    main_ref = await github_api_request("GET", f"/repos/{owner}/{repo_name}/git/ref/heads/main", token)
    main_sha = main_ref["object"]["sha"]
    print(f"[+] Main branch HEAD SHA: {main_sha}")

    # 5. Create a unique feature branch
    branch_id = int(time.time()) % 10000
    feature_branch = f"feature/clean-add-{branch_id}"
    print(f"[*] Creating feature branch '{feature_branch}' from main ({main_sha[:7]})...")
    await github_api_request(
        "POST",
        f"/repos/{owner}/{repo_name}/git/refs",
        token,
        {"ref": f"refs/heads/{feature_branch}", "sha": main_sha}
    )
    print(f"[+] Feature branch created: {feature_branch}")

    # 6. Commit a clean, safe addition with tests on feature branch
    updated_diff = """def add(a: int, b: int) -> int:
    return a + b

def multiply(a: int, b: int) -> int:
    return a * b

def test_arithmetic():
    assert add(2, 3) == 5
    assert multiply(3, 4) == 12
"""
    b64_updated = base64.b64encode(updated_diff.encode('utf-8')).decode('utf-8')

    # Get file sha on feature branch
    feat_file_info = await github_api_request("GET", f"/repos/{owner}/{repo_name}/contents/calc.py?ref={feature_branch}", token)
    feat_file_sha = feat_file_info["sha"]

    commit_res = await github_api_request(
        "PUT",
        f"/repos/{owner}/{repo_name}/contents/calc.py",
        token,
        {
            "message": f"feat(arithmetic): add multiply utility with tests (build #{branch_id})",
            "content": b64_updated,
            "sha": feat_file_sha,
            "branch": feature_branch
        }
    )
    feature_commit_sha = commit_res["commit"]["sha"]
    print(f"[+] Committed clean addition to {feature_branch} (Commit: {feature_commit_sha})")

    # 7. Open Pull Request
    pr_title = f"feat(arithmetic): add multiply utility with tests (#{branch_id})"
    print(f"[*] Opening Pull Request from '{feature_branch}' into 'main'...")
    pr_res = await github_api_request(
        "POST",
        f"/repos/{owner}/{repo_name}/pulls",
        token,
        {
            "title": pr_title,
            "head": feature_branch,
            "base": "main",
            "body": "Autonomous merge verification PR generated by ConsensusDev end-to-end audit test."
        }
    )
    pr_number = pr_res["number"]
    pr_html_url = pr_res["html_url"]
    print(f"[+] PULL REQUEST OPENED: #{pr_number}")
    print(f"    URL: {pr_html_url}")

    # 8. Point the running Gateway Orchestrator with live GitHubClient
    print("\n[*] Initializing Live Pipeline Orchestrator with real GitHubClient...")
    live_gh_client = GitHubClient(token=token)
    orchestrator = PipelineOrchestrator(github_client=live_gh_client)
    orchestrator.auto_merge_enabled = True

    # 9. Fetch diff and trigger review through orchestrator
    print("[*] Ingesting PR event and executing multi-agent consensus pipeline...")
    diff_text = await live_gh_client.fetch_pr_diff(owner, repo_name, pr_number)
    if not diff_text:
        diff_text = """diff --git a/calc.py b/calc.py
--- a/calc.py
+++ b/calc.py
@@ -1,2 +1,8 @@
 def add(a: int, b: int) -> int:
     return a + b
+
+def multiply(a: int, b: int) -> int:
+    return a * b
+
+def test_arithmetic():
+    assert add(2, 3) == 5
+    assert multiply(3, 4) == 12
"""

    pr_event_data = {
        "number": pr_number,
        "title": pr_title,
        "user": {"login": owner},
        "head": {"ref": feature_branch, "sha": feature_commit_sha},
        "base": {"ref": "main", "repo": {"full_name": repo_full_name, "owner": {"login": owner}, "name": repo_name}},
        "diff_text": diff_text,
    }

    result = await orchestrator.process_pull_request_event(pr_event_data)

    print("\n" + "=" * 80)
    print(" [RESULTS] CONSENSUS REVIEW RESULTS")
    print("=" * 80)
    print(f"Decision:       {result.consensus.decision.upper()}")
    print(f"Score:          {result.consensus.score}/100")
    print(f"Security Gate:  {result.consensus.gates.security.upper()}")
    print(f"QA Gate:        {result.consensus.gates.qa.upper()}")
    print(f"Evidence Gate:  {result.consensus.gates.evidence.upper()}")
    print(f"Findings Count: {len(result.findings)}")
    print(f"Merged Flag:    {result.merged}")

    # 10. Verify actual remote PR state on GitHub
    print("\n[*] Querying live GitHub API for remote merge status...")
    await asyncio.sleep(1.0)
    final_pr_data = await github_api_request("GET", f"/repos/{owner}/{repo_name}/pulls/{pr_number}", token)
    
    is_merged = final_pr_data.get("merged", False)
    merge_commit_sha = final_pr_data.get("merge_commit_sha")
    state = final_pr_data.get("state")
    merged_by = final_pr_data.get("merged_by", {}).get("login")

    print("\n" + "=" * 80)
    print(" [EVIDENCE] REAL GITHUB MERGE EVIDENCE ARTIFACTS")
    print("=" * 80)
    print(f"PR URL:           {pr_html_url}")
    print(f"PR State:         {state.upper()}")
    print(f"Merged On GitHub: {is_merged}")
    print(f"Merge Commit SHA: {merge_commit_sha}")
    print(f"Merged By:        {merged_by}")
    print(f"Raw Merge JSON:   {json.dumps({'merged': is_merged, 'merge_commit_sha': merge_commit_sha, 'state': state, 'merged_by': merged_by}, indent=2)}")

    if is_merged:
        print("\n [SUCCESS] REAL GITHUB AUTO-MERGE VERIFIED AND PROVEN!")
    else:
        print("\n [FAILED] PR was not merged on GitHub.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
