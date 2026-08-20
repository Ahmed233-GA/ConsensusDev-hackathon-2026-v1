import asyncio
import logging
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from fastapi import FastAPI

from scanners.checkov_runner import CheckovRunner
from scanners.trivy_runner import TrivyRunner

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("ConsensusDev-SecurityScanner")

app = FastAPI(
    title="ConsensusDev Security Scanner",
    description="DevSecOps SAST, IaC, and Secret Scanner Service (Port 8002)",
    version="1.0.0",
)

checkov_runner = CheckovRunner()
trivy_runner = TrivyRunner()


class ScanRequest(BaseModel):
    diff: str = Field(..., description="Git unified diff of the PR")
    repo_url: Optional[str] = Field(None, description="Optional repository URL")
    commit_sha: Optional[str] = Field(None, description="Optional commit SHA")


class FindingDetail(BaseModel):
    id: str
    severity: str  # "critical", "high", "medium", "low"
    tool: str
    ruleId: str
    engine: str = "fallback_regex_ast"
    file: str
    line: int = 1
    description: str
    recommendation: Optional[str] = None


class ScanResponse(BaseModel):
    status: str  # "PASS", "FAIL", "UNKNOWN", "ERROR"
    available: bool = True
    vulnerabilities_count: int
    critical_issues: List[str]
    findings: List[FindingDetail] = Field(default_factory=list)
    scanners: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@app.get("/")
async def root():
    return {
        "service": "ConsensusDev Security Scanner",
        "port": 8002,
        "status": "running",
        "scanners": ["Checkov (IaC/SAST)", "Trivy (Vulnerabilities/Secrets)", "InternalSAST", "RegexSecretScanner"],
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "scanners", "port": 8002}


@app.post("/scan", response_model=ScanResponse)
async def scan_pr(request: ScanRequest):
    """
    Contract 1: Port 8002
    Executes Checkov/Trivy (or internal AST/Regex fallbacks) over PR diff and normalizes security findings.
    """
    logger.info("Initiating security scans on PR diff...")

    try:
        # Run Checkov and Trivy scanners in parallel
        checkov_task = checkov_runner.run_scan(request.diff)
        trivy_task = trivy_runner.run_scan(request.diff)

        checkov_result, trivy_result = await asyncio.gather(checkov_task, trivy_task)

        critical_issues: List[str] = []
        structured_findings: List[FindingDetail] = []
        total_vulns = checkov_result.get("failed_checks", 0) + trivy_result.get("vulnerabilities_count", 0)

        # Collect Checkov / InternalSAST issues
        chk_engine = checkov_result.get("engine", "fallback_regex_ast")
        chk_tool = checkov_result.get("scanner", "InternalSAST")
        for issue_text in checkov_result.get("issues", []):
            critical_issues.append(issue_text)
            is_secret = "secret" in issue_text.lower() or "token" in issue_text.lower()
            severity = "critical" if is_secret or "injection" in issue_text.lower() else "high"
            rule_id = "CKV_SECRET_1" if is_secret else "CKV_PYTHON_1"
            structured_findings.append(
                FindingDetail(
                    id=f"chk-{uuid.uuid4().hex[:6]}",
                    severity=severity,
                    tool=chk_tool,
                    ruleId=rule_id,
                    engine=chk_engine,
                    file="scanned_code.py",
                    line=1,
                    description=issue_text,
                    recommendation="Sanitize user input with parameterized queries and store tokens in secure vault",
                )
            )

        # Collect Trivy / RegexSecretScanner issues
        trv_engine = trivy_result.get("engine", "fallback_regex_ast")
        trv_tool = trivy_result.get("scanner", "RegexSecretScanner")
        for issue_text in trivy_result.get("critical_issues", []):
            critical_issues.append(issue_text)
            is_secret = "secret" in issue_text.lower() or "token" in issue_text.lower()
            severity = "critical" if is_secret or "eval" in issue_text.lower() or "cwe-94" in issue_text.lower() else "high"
            rule_id = "TRIVY_SECRET" if is_secret else "TRIVY_CWE_94"
            structured_findings.append(
                FindingDetail(
                    id=f"trv-{uuid.uuid4().hex[:6]}",
                    severity=severity,
                    tool=trv_tool,
                    ruleId=rule_id,
                    engine=trv_engine,
                    file="scanned_code.py",
                    line=1,
                    description=issue_text,
                    recommendation="Rotate compromised credentials immediately and eliminate dangerous dynamic evaluation",
                )
            )

        status = "PASS" if total_vulns == 0 and len(critical_issues) == 0 else "FAIL"

        logger.info(f"Scan complete. Status: {status}, Total Vulnerabilities: {total_vulns}, Findings: {len(structured_findings)}")

        return ScanResponse(
            status=status,
            available=True,
            vulnerabilities_count=total_vulns,
            critical_issues=critical_issues,
            findings=structured_findings,
            scanners={
                "checkov": checkov_result,
                "trivy": trivy_result,
            },
        )
    except Exception as e:
        logger.error(f"Security Scanner execution exception: {e}")
        return ScanResponse(
            status="ERROR",
            available=False,
            vulnerabilities_count=0,
            critical_issues=[f"Scanner runtime error: {str(e)}"],
            findings=[],
            error=str(e),
        )
