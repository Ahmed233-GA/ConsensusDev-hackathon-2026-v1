"""FastAPI application for ConsensusDev Security Scanner Service (Port 8002)."""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from scanners.schemas import ScanRequest, ScanResponse
from scanners.checkov_runner import run_security_scan

app = FastAPI(
    title="ConsensusDev Security Scanner Service",
    description="Deterministic SAST and IaC Security Analysis Service for ConsensusDev Autonomous Code-Review Gate.",
    version="1.0.0",
)

# Enable CORS for cross-service calls
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Info"])
async def root():
    """Service status and identifier."""
    return {
        "service": "ConsensusDev Security Scanner",
        "owner": "Soliman (Code Analysis & DevSecOps Lead)",
        "port": 8002,
        "status": "running",
        "version": "1.0.0",
    }


@app.get("/health", tags=["Health"])
async def health():
    """Health check endpoint for container probes and Gateway discovery."""
    return {
        "status": "healthy",
        "service": "scanners",
        "port": 8002,
    }


@app.post(
    "/scan",
    response_model=ScanResponse,
    status_code=status.HTTP_200_OK,
    tags=["Scanning"],
    summary="Scan Git Diff for Security & IaC Vulnerabilities",
)
async def scan_diff(request: ScanRequest) -> ScanResponse:
    """Analyze a git diff string for security flaws, credentials, and misconfigurations.
    
    Accepts:
        {"diff": "..."}
        
    Returns:
        Structured ScanResponse containing pass/fail status, vulnerability count,
        critical issues summary, and detailed finding objects.
    """
    try:
        response = run_security_scan(request.diff)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Security scan error: {str(e)}",
        )
