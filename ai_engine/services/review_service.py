from ai_engine.schemas import AnalyzePRRequest, AnalyzePRResponse


async def analyze_pr(request: AnalyzePRRequest) -> AnalyzePRResponse:
    """
    Analyze a pull request.

    This is currently a placeholder for the real AI review pipeline.
    The agents and consensus logic will be added here later.
    """

    return AnalyzePRResponse(
        consensus=False,
        summary="AI review pipeline is not implemented yet.",
    )