from typing import Any

from pydantic import BaseModel


class AnalyzePRRequest(BaseModel):
    diff: str
    security: dict[str, Any]
    tests: dict[str, Any]


class AnalyzePRResponse(BaseModel):
    consensus: bool
    summary: str