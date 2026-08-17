"""
ConsensusDev AI Engine Application Entry Point
Supports running with `uvicorn ai_engine.app:app --port 8001`
"""

from ai_engine.main import app

__all__ = ["app"]
