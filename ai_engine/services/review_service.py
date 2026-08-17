import asyncio
import logging
from typing import Dict

from ai_engine.agents.consensus_engine import ConsensusEngine
from ai_engine.agents.debt_agent import TechDebtAgent
from ai_engine.agents.perf_agent import PerformanceAgent
from ai_engine.agents.security_agent import SecurityAgent
from ai_engine.agents.story_agent import StoryAgent
from ai_engine.schemas import AgentEvaluation, AnalyzePRRequest, AnalyzePRResponse

logger = logging.getLogger(__name__)


class ReviewService:
    def __init__(self):
        self.security_agent = SecurityAgent()
        self.debt_agent = TechDebtAgent()
        self.story_agent = StoryAgent()
        self.perf_agent = PerformanceAgent()
        self.consensus_engine = ConsensusEngine()

    async def analyze_pr(self, request: AnalyzePRRequest) -> AnalyzePRResponse:
        """
        Orchestrate parallel analysis of PR diff across all 4 AI Reviewer Agents
        and aggregate results through the Consensus Engine.
        """
        context = {
            "security": request.security or {},
            "tests": request.tests or {},
            "pr_number": request.pr_number,
            "story_description": request.story_description,
        }

        # Run all 4 agents in parallel
        security_task = self.security_agent.evaluate(request.diff, context)
        debt_task = self.debt_agent.evaluate(request.diff, context)
        story_task = self.story_agent.evaluate(request.diff, context)
        perf_task = self.perf_agent.evaluate(request.diff, context)

        eval_security, eval_debt, eval_story, eval_perf = await asyncio.gather(
            security_task,
            debt_task,
            story_task,
            perf_task,
        )

        evaluations: Dict[str, AgentEvaluation] = {
            "security": eval_security,
            "tech_debt": eval_debt,
            "story_match": eval_story,
            "performance": eval_perf,
        }

        # Run Consensus Engine
        response = self.consensus_engine.evaluate_consensus(
            evaluations=evaluations,
            pr_number=request.pr_number,
            security_context=request.security,
            qa_context=request.tests,
        )

        return response


# Global singleton review service instance
_review_service = ReviewService()


async def analyze_pr(request: AnalyzePRRequest) -> AnalyzePRResponse:
    return await _review_service.analyze_pr(request)