from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AuthorInfo(BaseModel):
    name: str = "Developer"
    username: str = "developer"
    avatarUrl: Optional[str] = None


class DiffSummary(BaseModel):
    filesChanged: int = 0
    additions: int = 0
    deletions: int = 0


class PRMeta(BaseModel):
    id: str
    prNumber: int
    title: str
    author: AuthorInfo
    commitHash: str
    shortHash: str
    sourceBranch: str
    targetBranch: str = "main"
    repo: str
    createdAt: str
    updatedAt: str
    diffSummary: Optional[DiffSummary] = None


class GateStatuses(BaseModel):
    security: str = Field("pending", description="'passed', 'failed', 'pending', 'unknown'")
    qa: str = Field("pending", description="'passed', 'failed', 'pending', 'unknown'")
    evidence: str = Field("pending", description="'verified', 'unverified', 'pending', 'incomplete'")


class ConsensusScore(BaseModel):
    score: int = Field(0, ge=0, le=100)
    decision: str = Field("pending", description="'approved', 'rejected', 'pending', 'blocked'")
    gates: GateStatuses
    summary: str = ""
    blocking_reasons: List[str] = Field(default_factory=list)


class AgentScore(BaseModel):
    id: str
    agentName: str
    icon: str = "Shield"
    scoreType: str = "numeric"  # "pass-fail" or "numeric"
    status: Optional[str] = None  # "pass" or "fail"
    score: Optional[float] = None  # 0-10 or 0-100
    weightPercent: int = 20
    summary: str = ""
    details: List[str] = Field(default_factory=list)
    confidence: float = 1.0


class Finding(BaseModel):
    id: str
    severity: str = "medium"  # "critical", "high", "medium", "low"
    tool: str = "Scanner"
    ruleId: str
    engine: Optional[str] = "fallback_regex_ast"
    file: str
    line: int = 1
    description: str = ""
    recommendation: Optional[str] = None


class QASuite(BaseModel):
    name: str
    passed: bool
    duration: str
    coverage: float
    totalTests: int


class QAStats(BaseModel):
    status: str = "UNKNOWN"  # "PASS", "FAIL", "UNKNOWN", "OFFLINE"
    testsPassed: int = 0
    testsFailed: int = 0
    coveragePercentage: Optional[float] = None
    mutationScore: Optional[float] = None
    suites: List[QASuite] = Field(default_factory=list)
    error: Optional[str] = None


class SystemNode(BaseModel):
    id: str
    name: str
    port: int
    role: str
    status: str = "online"  # "online", "offline", "degraded"
    latencyMs: int = 0


class PipelineStep(BaseModel):
    step: str
    status: str = "waiting"  # "completed", "running", "waiting", "failed", "blocked"
    service: str
    timestamp: str = ""


class SystemArch(BaseModel):
    nodes: List[SystemNode] = Field(default_factory=list)
    pipelineFlow: List[PipelineStep] = Field(default_factory=list)


class PullRequestReview(BaseModel):
    meta: PRMeta
    consensus: ConsensusScore
    agents: List[AgentScore] = Field(default_factory=list)
    findings: List[Finding] = Field(default_factory=list)
    qaStats: QAStats
    diffText: str = ""
    systemArch: SystemArch
    merged: bool = False
    reviewTimeSeconds: float = 0.0
    status: str = "PROCESSED"  # "QUEUED", "SCANNING", "TESTING", "AI_REVIEW", "CONSENSUS", "APPROVED", "BLOCKED", "MERGED", "FAILED"


class AuditLog(BaseModel):
    id: str
    timestamp: str
    service: str
    level: str  # "INFO", "WARN", "ERROR", "SUCCESS"
    message: str
    review_id: Optional[str] = None
    request_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
