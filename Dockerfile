# Dockerfile for ConsensusDev Security Scanner Service
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY scanners/ /app/scanners/

# Expose Security Scanner port
EXPOSE 8002

# Run FastAPI app via Uvicorn on port 8002
CMD ["uvicorn", "scanners.app:app", "--host", "0.0.0.0", "--port", "8002"]
