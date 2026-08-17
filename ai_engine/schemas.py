from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AgentEvaluation(BaseModel):
    agent_name: str
    score: int = Field(..., ge=0, le=100, description="Score from 0 to 100")
    passed: bool = Field(..., description="Whether the check passed acceptable thresholds")
    feedback: str = Field(..., description="Human-readable review comment for this agent")
    critical_issues: List[str] = Field(default_factory=list, description="List of blocking critical issues found")
    suggestions: List[str] = Field(default_factory=list, description="List of improvement suggestions")


class AgentsFeedback(BaseModel):
    security: str = Field(..., description="Feedback from Security Agent")
    tech_debt: str = Field(..., description="Feedback from Tech Debt Agent")
    story_match: str = Field(..., description="Feedback from Story Match Agent")
    performance: str = Field(..., description="Feedback from Performance Agent")


class AnalyzePRRequest(BaseModel):
    diff: str = Field(..., description="Git unified diff of the PR")
    security: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Static security scanner findings from Soliman's Scanner (Checkov/Trivy)",
    )
    tests: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="QA & Test Runner findings from Shahd's QA Runner (Pytest/Coverage)",
    )
    pr_number: Optional[int] = Field(None, description="Optional PR number for context")
    story_description: Optional[str] = Field(
        None, description="User story or PR description for Story Match verification"
    )


class AnalyzePRResponse(BaseModel):
    consensus: bool = Field(..., description="True if PR is approved for auto-merge, False if blocked")
    score: int = Field(..., ge=0, le=100, description="Overall weighted consensus score (0-100)")
    agents_feedback: Dict[str, str] = Field(
        ..., description="Review comments keyed by agent: security, tech_debt, story_match, performance"
    )
    summary: str = Field(..., description="Executive consensus summary for the PR")
    details: Optional[Dict[str, Any]] = Field(
        default=None, description="Detailed agent breakdown scores and flags"
    )