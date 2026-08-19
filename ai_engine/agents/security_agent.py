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
        diff_meta = self.extract_diff_metadata(diff)
        scanner_payload = context.get("security", {})

        # System prompt for LLM Model
        system_prompt = (
            "You are a Principal Application Security Engineer reviewing a Pull Request diff. "
            "Detect vulnerabilities including SQL Injection (CWE-89), XSS (CWE-79), Command Injection (CWE-78), "
            "hardcoded secrets/credentials, insecure deserialization, and dangerous standard library calls. "
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
            f"PR Diff:\n```diff\n{diff}\n```\n\n"
            f"Static Security Scanner (Checkov/Trivy) Findings:\n{json.dumps(scanner_payload, indent=2)}\n\n"
            "Analyze security posture and return the JSON response."
        )

        # 1. Execute LLM Model Call via OpenRouter
        llm_response = await self.call_llm(system_prompt, user_prompt)
        if llm_response and "score" in llm_response:
            score = int(llm_response.get("score", 100))
            critical_issues = list(llm_response.get("critical_issues", []))
            passed = bool(llm_response.get("passed", score >= 80 and len(critical_issues) == 0))
            feedback = str(llm_response.get("feedback", "Clean - no security issues found"))

            return AgentEvaluation(
                agent_name=self.name,
                score=score,
                passed=passed,
                feedback=feedback,
                critical_issues=critical_issues,
                suggestions=list(llm_response.get("suggestions", [])),
            )

        # 2. Fallback when running offline without API keys
        return self._heuristic_analysis(diff_meta, scanner_payload)

    def _heuristic_analysis(
        self, diff_meta: Dict[str, Any], scanner_payload: Dict[str, Any]
    ) -> AgentEvaluation:
        critical_issues: List[str] = []
        suggestions: List[str] = []
        score = 100

        scanner_status = scanner_payload.get("status", "").upper()
        if scanner_status == "FAIL":
            score -= 40
            for issue in scanner_payload.get("critical_issues", []):
                critical_issues.append(f"Scanner finding: {issue}")

        sqli_fstring = re.compile(r"f['\"].*(select\s+.*from|insert\s+into|update\s+.*set|delete\s+from).*{.*}", re.IGNORECASE)
        sqli_concat = re.compile(r"['\"].*(select\s+.*from|insert\s+into|update\s+.*set|delete\s+from).*['\"]\s*(\+|\%|\.format)", re.IGNORECASE)
        sqli_format = re.compile(r"['\"].*(select\s+.*from|insert\s+into|update\s+.*set|delete\s+from).*\{.*\}['\"]\s*\.format", re.IGNORECASE)
        secret_pat = re.compile(r"(api[_-]?key|secret[_-]?key|password|token)\s*=\s*['\"][A-Za-z0-9_\-\.]{8,}['\"]", re.IGNORECASE)
        eval_pat = re.compile(r"\b(eval|exec|os\.system)\s*\(", re.IGNORECASE)
        shell_pat = re.compile(r"subprocess\.(Popen|run|call)\(.*shell\s*=\s*True", re.IGNORECASE)

        for filename, line in diff_meta["added_lines"]:
            stripped = line.strip()
            if sqli_fstring.search(stripped) or sqli_concat.search(stripped) or sqli_format.search(stripped):
                issue = f"SQL Injection detected in {filename}: string formatting/interpolation used in SQL query"
                if issue not in critical_issues:
                    critical_issues.append(issue)
                    score -= 50
                    suggestions.append("Use parameterized queries or ORM query builders instead of raw string interpolation.")
            if secret_pat.search(stripped) and not stripped.startswith("#"):
                issue = f"Hardcoded secret/credential detected in {filename}"
                if issue not in critical_issues:
                    critical_issues.append(issue)
                    score -= 40
                    suggestions.append("Move secrets to environment variables or secret manager.")
            if eval_pat.search(stripped) and not stripped.startswith("#"):
                issue = f"Dangerous function call (eval/exec/os.system) in {filename}"
                if issue not in critical_issues:
                    critical_issues.append(issue)
                    score -= 40
                    suggestions.append("Avoid dynamic code execution.")
            if shell_pat.search(stripped):
                issue = f"Command Injection risk (subprocess with shell=True) in {filename}"
                if issue not in critical_issues:
                    critical_issues.append(issue)
                    score -= 30
                    suggestions.append("Pass command arguments as a list and remove shell=True.")

        score = max(0, min(100, score))
        passed = len(critical_issues) == 0 and score >= 80
        feedback = "Clean - no secrets or CVEs found" if passed else f"Security Vulnerabilities Flagged: {'; '.join(critical_issues)}"

        return AgentEvaluation(
            agent_name=self.name,
            score=score,
            passed=passed,
            feedback=feedback,
            critical_issues=critical_issues,
            suggestions=suggestions,
        )
