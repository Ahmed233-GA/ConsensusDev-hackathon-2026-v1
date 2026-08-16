from fastapi import FastAPI
from pydantic import BaseModel

from gateway.scanner_client import scan_diff


app = FastAPI(
    title="ConsensusDev Gateway",
    description="Gateway and integration service for ConsensusDev",
    version="0.1.0",
)


class ScanRequest(BaseModel):
    diff: str


@app.get("/")
async def root():
    return {
        "service": "ConsensusDev Gateway",
        "status": "running",
        "version": "0.1.0",
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
    }


@app.post("/scan")
async def scan(request: ScanRequest):
    return await scan_diff(request.diff)