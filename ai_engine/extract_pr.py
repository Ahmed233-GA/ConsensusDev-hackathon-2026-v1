"""
extract_pr.py

Given a GitHub PR URL, automatically produces diff.txt and ticket.txt
ready to feed into run_all.py.

Usage:
    python extract_pr.py https://github.com/owner/repo/pull/42

Optional: set GITHUB_TOKEN env var to raise rate limits / access private repos.
    $env:GITHUB_TOKEN="ghp_xxxxxxxx"
"""

import os
import re
import sys
import json
import urllib.request


def parse_pr_url(url: str):
    match = re.search(r"github\.com/([^/]+)/([^/]+)/pull/(\d+)", url)
    if not match:
        raise ValueError("URL doesn't look like a GitHub PR URL, e.g. https://github.com/owner/repo/pull/42")
    owner, repo, number = match.groups()
    return owner, repo, number


def _get(url: str, headers: dict) -> bytes:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        return resp.read()


def fetch_diff(owner: str, repo: str, number: str, headers: dict) -> str:
    diff_headers = dict(headers)
    diff_headers["Accept"] = "application/vnd.github.v3.diff"
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}"
    return _get(url, diff_headers).decode("utf-8")


def fetch_pr_json(owner: str, repo: str, number: str, headers: dict) -> dict:
    json_headers = dict(headers)
    json_headers["Accept"] = "application/vnd.github+json"
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}"
    return json.loads(_get(url, json_headers).decode("utf-8"))


def fetch_linked_issue(owner: str, repo: str, pr_body: str, headers: dict):
    # Looks for "Closes #12", "Fixes #7", "Resolves #3", etc.
    match = re.search(r"(closes|fixes|resolves)\s+#(\d+)", pr_body or "", re.IGNORECASE)
    if not match:
        return None
    issue_number = match.group(2)
    json_headers = dict(headers)
    json_headers["Accept"] = "application/vnd.github+json"
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}"
    try:
        return json.loads(_get(url, json_headers).decode("utf-8"))
    except Exception:
        return None


def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_pr.py <github_pr_url>")
        sys.exit(1)

    pr_url = sys.argv[1]
    owner, repo, number = parse_pr_url(pr_url)

    headers = {}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    print(f"Fetching PR #{number} from {owner}/{repo}...")

    diff_text = fetch_diff(owner, repo, number, headers)
    with open("diff.txt", "w", encoding="utf-8") as f:
        f.write(diff_text)
    print(f"Wrote diff.txt ({len(diff_text)} chars)")

    pr_data = fetch_pr_json(owner, repo, number, headers)
    title = pr_data.get("title", "")
    body = pr_data.get("body", "") or ""

    # Prefer the linked issue's description as the "ticket" if one exists,
    # since that's usually the real requirements doc. Fall back to the PR body.
    issue = fetch_linked_issue(owner, repo, body, headers)
    if issue:
        ticket_text = f"Title: {issue.get('title', '')}\n\n{issue.get('body', '') or ''}"
        print("Found linked issue, using it as the ticket description.")
    else:
        ticket_text = f"Title: {title}\n\n{body}"
        print("No linked issue found, using the PR description as the ticket.")

    with open("ticket.txt", "w", encoding="utf-8") as f:
        f.write(ticket_text)
    print(f"Wrote ticket.txt ({len(ticket_text)} chars)")

    print("\nDone. You can now run:")
    print("  python run_all.py diff.txt ticket.txt")


if __name__ == "__main__":
    main()