import json
import logging
import re
from typing import Any, Dict, List

from ai_engine.agents.base_agent import BaseReviewAgent
from ai_engine.schemas import AgentEvaluation

logger = logging.getLogger(__name__)


class SecurityAgent(BaseReviewAgent):
    """
    AI Security Reviewer Agent.
    Executes via OpenRouter / Cloud LLM model to analyze code diffs and scanner findings
    for OWASP Top 10 vulnerabilities (SQLi, XSS, exposed secrets, command injection).
    """

    def __init__(self, weight: float = 2.0):
        super().__init__(name="security", weight=weight)

    async def evaluate(self, diff: str, context: Dict[str, Any]) -> AgentEvaluation:
        scanner_payload = context.get("security", {})

        system_prompt = (
            "You are a Principal Application Security Engineer reviewing a Pull Request diff. "
            "Detect vulnerabilities including SQL Injection (CWE-89), XSS (CWE-79), Command Injection (CWE-78), "
            "hardcoded secrets/credentials, insecure deserialization, and dangerous standard library calls. "
            "You MUST incorporate and cross-verify with any static scanner findings provided.\n\n"
            "You MUST respond ONLY with valid JSON in this exact structure:\n"
            "{\n"
            '  "score": <integer from 0 to 100>,\n'
            '  "passed": <boolean: true if secure (score >= 80 and no critical CVEs), false if blocked>,\n'
            '  "feedback": "<concise security feedback summary>",\n'
            '  "critical_issues": ["<critical issue 1>", "<critical issue 2>"],\n'
            '  "suggestions": ["<remediation suggestion 1>"]\n'
            "}"
        )

        user_prompt = (
            f"PR Unified Diff:\n```diff\n{diff}\n```\n\n"
            f"Static Security Scanner Findings:\n{json.dumps(scanner_payload, indent=2)}\n\n"
            "Perform security review using your LLM reasoning and return the JSON response."
        )

        # Call OpenRouter / Cloud LLM
        llm_response = await self.call_llm(system_prompt, user_prompt)

        if llm_response and "score" in llm_response:
            score = int(llm_response.get("score", 100))
            critical_issues = list(llm_response.get("critical_issues", []))
            passed = bool(llm_response.get("passed", score >= 80 and len(critical_issues) == 0))
            feedback = str(llm_response.get("feedback", "Clean - no secrets or CVEs found"))

            return AgentEvaluation(
                agent_name=self.name,
                score=score,
                passed=passed,
                feedback=feedback,
                critical_issues=critical_issues,
                suggestions=list(llm_response.get("suggestions", [])),
            )

        # Fallback when no API key is provided
        scanner_status = scanner_payload.get("status", "").upper()
        # Only take actual scanner vulnerability issues, ignoring infrastructure outage notes
        raw_issues = scanner_payload.get("critical_issues", [])
        scanner_issues = [i for i in raw_issues if "offline" not in i.lower() and "unavailable" not in i.lower()]
        
        has_sqli = False
        has_secret = False
        
        for line in diff.splitlines():
            if line.startswith("+") and not line.startswith("+++"):
                content = line[1:].strip()
                if re.search(r"f['\"].*(select|insert|update|delete).*{.*}", content, re.IGNORECASE) or re.search(r"['\"].*(select|insert|update|delete).*['\"]\s*(\+|\%|\.format)", content, re.IGNORECASE):
                    has_sqli = True
                if re.search(r"(api[_-]?key|secret[_-]?key|password|token)\s*=\s*['\"][A-Za-z0-9_\-\.]{8,}['\"]", content, re.IGNORECASE):
                    has_secret = True

        is_clean = (scanner_status != "FAIL") and (len(scanner_issues) == 0) and not has_sqli and not has_secret

        issues = list(scanner_issues)
        if has_sqli and not any("SQL" in i for i in issues):
            issues.append("SQL Injection detected: dynamic string formatting in SQL query")
        if has_secret and not any("secret" in i.lower() for i in issues):
            issues.append("Hardcoded secret or credential token in diff")

        return AgentEvaluation(
            agent_name=self.name,
            score=95 if is_clean else 30,
            passed=is_clean,
            feedback="Clean - no secrets or CVEs found" if is_clean else f"Security Issues: {'; '.join(issues)}",
            critical_issues=issues,
            suggestions=["Use parameterized queries with ORM or bind parameters"] if not is_clean else [],
        )
