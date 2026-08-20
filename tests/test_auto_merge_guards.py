import hashlib
import hmac
import pytest
from httpx import ASGITransport, AsyncClient

from gateway.github_client import GitHubClient
from gateway.main import app


def test_hmac_signature_verification():
    client = GitHubClient()
    secret = "test_super_secret_key_12345"
    payload = b'{"action": "opened", "number": 101}'

    # 1. Valid Signature
    valid_sig = "sha256=" + hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    assert client.verify_webhook_signature(payload, valid_sig, secret) is True

    # 2. Invalid Signature
    invalid_sig = "sha256=" + "0" * 64
    assert client.verify_webhook_signature(payload, invalid_sig, secret) is False

    # 3. Missing Signature
    assert client.verify_webhook_signature(payload, None, secret) is False

    # 4. Empty Secret with allow_unsigned_dev=False
    assert client.verify_webhook_signature(payload, valid_sig, "", allow_unsigned_dev=False) is False

    # 5. Empty Secret with allow_unsigned_dev=True
    assert client.verify_webhook_signature(payload, valid_sig, "", allow_unsigned_dev=True) is True


@pytest.mark.asyncio
async def test_webhook_rejects_unsigned_when_secret_set(monkeypatch):
    monkeypatch.setenv("WEBHOOK_SECRET", "prod_secret_98765")
    monkeypatch.setenv("WEBHOOK_ALLOW_UNSIGNED_DEV", "false")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Send without signature
        res = await client.post("/webhook/github", json={"action": "opened", "number": 101})
        assert res.status_code == 401


@pytest.mark.asyncio
async def test_webhook_idempotency_deduplication(monkeypatch):
    monkeypatch.setenv("WEBHOOK_SECRET", "test_secret")
    secret = "test_secret"
    payload_dict = {
        "action": "opened",
        "number": 199,
        "pull_request": {
            "number": 199,
            "title": "Idempotency PR test",
            "head": {"ref": "feature/idempotent", "sha": "abcdef1234567890"},
            "base": {
                "ref": "main",
                "repo": {"full_name": "Ahmed233-GA/ConsensusDev-hackathon-2026-v1"},
            },
            "user": {"login": "AhmedDev"},
        },
    }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # First Delivery
        import json
        body = json.dumps(payload_dict).encode()
        sig = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        headers = {
            "x-github-event": "pull_request",
            "x-hub-signature-256": sig,
            "x-github-delivery": "delivery-unique-001",
            "x-consensusdev-sync": "true",
        }

        res1 = await client.post("/webhook/github", content=body, headers=headers)
        assert res1.status_code == 200
        data1 = res1.json()
        assert data1["status"] in ["processed_sync", "accepted"]

        # Duplicate Delivery with same delivery ID
        res2 = await client.post("/webhook/github", content=body, headers=headers)
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2["status"] == "already_processed"
