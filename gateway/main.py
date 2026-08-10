from fastapi import FastAPI

app = FastAPI(
    title="ConsensusDev Gateway",
    description="Gateway and integration service for ConsensusDev",
    version="0.1.0",
)


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