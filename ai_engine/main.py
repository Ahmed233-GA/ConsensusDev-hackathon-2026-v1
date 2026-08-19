from fastapi import FastAPI

from ai_engine.schemas import AnalyzePRRequest, AnalyzePRResponse
from ai_engine.services import review_service

app = FastAPI(
    title="ConsensusDev AI Engine",
    description="AI analysis service for ConsensusDev",
    version="0.1.0",
)


@app.get("/")
async def root():
    return {
        "service": "ConsensusDev AI Engine",
        "status": "running",
        "version": "0.1.0",
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
    }


@app.post("/analyze-pr", response_model=AnalyzePRResponse)
async def analyze_pr(request: AnalyzePRRequest):
    return await review_service.analyze_pr(request)