import argparse
import asyncio
import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gateway.github_client import GitHubClient


async def main():
    parser = argparse.ArgumentParser(description="ConsensusDev — Automatic GitHub Webhook Creator")
    parser.add_argument("--url", help="Public URL of the webhook (e.g. https://your-domain.ngrok-free.app/webhook/github)", required=False)
    parser.add_argument("--token", help="GitHub Personal Access Token (with repo / admin:repo_hook permissions)", required=False)
    parser.add_argument("--repo", help="Repository in 'owner/repo' format (default: Ahmed233-GA/ConsensusDev-hackathon-2026-v1)", default="Ahmed233-GA/ConsensusDev-hackathon-2026-v1")
    parser.add_argument("--secret", help="Webhook secret passphrase", default=None)

    args = parser.parse_args()

    # Load environment variables
    token = args.token or os.getenv("GITHUB_TOKEN")
    if not token or token.startswith("ghp_your_"):
        token = input("Enter your GitHub Personal Access Token (with repo hooks permission): ").strip()

    webhook_url = args.url
    if not webhook_url:
        webhook_url = input("Enter your public Webhook URL (e.g. https://xxxx.ngrok-free.app/webhook/github): ").strip()

    if not webhook_url.endswith("/webhook/github"):
        if webhook_url.endswith("/"):
            webhook_url = webhook_url + "webhook/github"
        else:
            webhook_url = webhook_url + "/webhook/github"

    secret = args.secret or os.getenv("WEBHOOK_SECRET", "")
    parts = args.repo.split("/")
    owner = parts[0]
    repo_name = parts[1]

    print(f"\n[ConsensusDev] Registering Webhook on https://github.com/{owner}/{repo_name}...")
    print(f"Target URL: {webhook_url}")

    client = GitHubClient(token=token)
    result = await client.register_webhook(
        owner=owner,
        repo=repo_name,
        webhook_url=webhook_url,
        secret=secret,
        events=["pull_request", "push", "ping"],
    )

    if result.get("success"):
        print(f"\n[SUCCESS] Webhook created successfully! (Hook ID: {result.get('hook_id')})")
        print("GitHub will now automatically forward all Pull Request events to your Gateway!")
    else:
        print(f"\n[ERROR] Failed to create webhook: {result.get('error')}")
        print("Please check that your GitHub Token has 'admin:repo_hook' or 'repo' permissions.")


if __name__ == "__main__":
    asyncio.run(main())
