import httpx

from gateway.config import SCANNER_URL


async def scan_diff(diff: str) -> dict:
    url = f"{SCANNER_URL}/scan"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            url,
            json={"diff": diff},
        )

    response.raise_for_status()

    return response.json()