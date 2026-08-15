"""Pydantic schemas for the ConsensusDev Security Scanner Service."""

from typing import List, Optional
from pydantic import BaseModel, Field


class ScanRequest(BaseModel):
    """Payload received from Gateway or developer containing the git diff."""
    diff: str = Field(
        ...,
        description="The git diff string to scan for security vulnerabilities.",
        example="diff --git a/app.py b/app.py\n+ AWS_SECRET = 'AKIAIOSFODNN7EXAMPLE'",
    )


class SecurityFinding(BaseModel):
    """Detailed record for a single security finding or vulnerability."""
    rule_id: str = Field(..., description="Unique identifier for the triggered security rule.")
    title: str = Field(..., description="Short summary title of the security issue.")
    severity: str = Field(..., description="Severity level: CRITICAL, HIGH, MEDIUM, LOW, or INFO.")
    description: str = Field(..., description="Detailed description of the risk.")
    file: Optional[str] = Field(None, description="File path where the vulnerability was detected.")
    line: Optional[int] = Field(None, description="Line number of the detected vulnerability in the diff.")
    snippet: Optional[str] = Field(None, description="Relevant code snippet containing the violation.")
    recommendation: Optional[str] = Field(None, description="Remediation guidance to fix the issue.")


class ScanResponse(BaseModel):
    """Output contract for the Security Scanner service.
    
    Compatible with both the simplified target format ({"status": "PASS", "vulnerabilities": 0})
    and the rich blueprint schema expected by AI Engine and Gateway.
    """
    status: str = Field(..., description="'PASS' if no high/critical vulnerabilities, otherwise 'FAIL'.")
    vulnerabilities: int = Field(..., description="Total count of vulnerabilities found.")
    vulnerabilities_count: int = Field(..., description="Alias count for full schema compatibility.")
    critical_issues: List[str] = Field(default_factory=list, description="List of high/critical issue summaries.")
    findings: List[SecurityFinding] = Field(default_factory=list, description="Structured list of all findings.")
    details: List[SecurityFinding] = Field(default_factory=list, description="Alias list of findings for compatibility.")
    summary: str = Field(..., description="Human-readable overview of the scan results.")
