import logging
from typing import Any, Dict, List, Optional
from fastapi import FastAPI
from pydantic import BaseModel, Field

from qa_runner.runner import QARunner

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("ConsensusDev-QARunner")

app = FastAPI(
    title="ConsensusDev QA Runner",
    description="Automated Test & Mutation Testing Service (Port 8003)",
    version="1.0.0",
)

qa_runner = QARunner()


class RunTestsRequest(BaseModel):
    diff: str = Field(..., description="Unified diff of the Pull Request")
    pr_number: Optional[int] = Field(None, description="PR Number context")


class QASuiteResponse(BaseModel):
    name: str
    passed: bool
    duration: str
    coverage: float
    totalTests: int


class RunTestsResponse(BaseModel):
    status: str  # "PASS", "FAIL", "UNKNOWN", "ERROR"
    available: bool = True
    tests_passed: int
    tests_failed: int
    total_tests: int
    coverage_percentage: Optional[float] = None
    mutation_score: Optional[float] = None
    suites: List[QASuiteResponse] = Field(default_factory=list)
    duration_seconds: Optional[float] = None
    error: Optional[str] = None


@app.get("/")
async def root():
    return {
        "service": "ConsensusDev QA Runner",
        "port": 8003,
        "status": "running",
        "runners": ["Pytest Test Suite", "Coverage Engine", "Mutation Score Analyzer"],
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "qa_runner",
        "port": 8003,
    }


@app.post("/run-tests", response_model=RunTestsResponse)
async def run_tests(request: RunTestsRequest):
    """
    Contract 2: Port 8003
    Executes tests against PR diff in sandboxed workspace and aggregates metrics.
    """
    logger.info("Executing automated test suite and coverage analysis on PR diff...")
    result = await qa_runner.run_tests(diff=request.diff, pr_number=request.pr_number)
    logger.info(f"QA execution complete. Status: {result.get('status')}, Passed: {result.get('tests_passed')}, Failed: {result.get('tests_failed')}")
    return RunTestsResponse(**result)
