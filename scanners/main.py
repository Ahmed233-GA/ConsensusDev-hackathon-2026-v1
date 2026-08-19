import asyncio
import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from fastapi import FastAPI

from scanners.checkov_runner import CheckovRunner
from scanners.trivy_runner import TrivyRunner

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("ConsensusDev-SecurityScanner")

app = FastAPI(
    title="ConsensusDev Security Scanner",
    description="DevSecOps SAST, IaC, and Secret Scanner Service (Port 8002 - Soliman)",
    version="1.0.0",
)

checkov_runner = CheckovRunner()
trivy_runner = TrivyRunner()


class ScanRequest(BaseModel):
    diff: str


class ScanResponse(BaseModel):
    status: str  # "PASS" or "FAIL"
    vulnerabilities_count: int
    critical_issues: List[str]
    scanners: Optional[Dict[str, Any]] = None


@app.get("/")
async def root():
    return {
        "service": "ConsensusDev Security Scanner",
        "port": 8002,
        "status": "running",
        "scanners": ["Checkov (IaC/SAST)", "Trivy (Vulnerabilities/Secrets)"],
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "scanners"}


@app.post("/scan", response_model=ScanResponse)
async def scan_pr(request: ScanRequest):
    """
    Contract 1: Soliman (Port 8002)
    Executes Checkov and Trivy concurrently over PR diff and aggregates security findings.
    """
    logger.info("Initiating dual Checkov & Trivy security scans on PR diff...")

    # Run Checkov and Trivy in parallel
    checkov_task = checkov_runner.run_scan(request.diff)
    trivy_task = trivy_runner.run_scan(request.diff)

    checkov_result, trivy_result = await asyncio.gather(checkov_task, trivy_task)

    critical_issues: List[str] = []
    total_vulns = checkov_result.get("failed_checks", 0) + trivy_result.get("vulnerabilities_count", 0)

    critical_issues.extend(checkov_result.get("issues", []))
    critical_issues.extend(trivy_result.get("critical_issues", []))

    status = "PASS" if total_vulns == 0 and len(critical_issues) == 0 else "FAIL"

    logger.info(f"Scan complete. Status: {status}, Total Vulnerabilities: {total_vulns}")

    return ScanResponse(
        status=status,
        vulnerabilities_count=total_vulns,
        critical_issues=critical_issues,
        scanners={
            "checkov": checkov_result,
            "trivy": trivy_result,
        },
    )
