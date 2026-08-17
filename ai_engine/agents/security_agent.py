import logging
import re
from typing import Any, Dict, List

from ai_engine.agents.base_agent import BaseReviewAgent
from ai_engine.schemas import AgentEvaluation

logger = logging.getLogger(__name__)


class SecurityAgent(BaseReviewAgent):
    """
    AI Security Reviewer Agent.
    Analyzes code diffs and static scanner findings (from Soliman's Checkov/Trivy service)
    for security vulnerabilities such as SQL injection, XSS, exposed secrets, and insecure functions.
    """

    def __init__(self, weight: float = 2.0):
        super().__init__(name="security", weight=weight)

    async def evaluate(self, diff: str, context: Dict[str, Any]) -> AgentEvaluation:
        diff_meta = self.extract_diff_metadata(diff)
        scanner_payload = context.get("security", {})

        # 1. Try LLM analysis first if API key is configured
        system_prompt = (
            "You are a Principal Application Security Engineer reviewing a Pull Request diff. "
            "Detect vulnerabilities including SQL Injection (CWE-89), XSS (CWE-79), Command Injection (CWE-78), "
            "hardcoded secrets, insecure deserialization, and dangerous standard library calls. "
            "Return JSON matching: {\"score\": int (0-100), \"passed\": bool, \"feedback\": str, "
            "\"critical_issues\": [str], \"suggestions\": [str]}"
        )
        user_prompt = (
            f"PR Diff:\n{diff}\n\n"
            f"Static Scanner Findings:\n{scanner_payload}\n\n"
            "Analyze security posture and return JSON."
        )

        llm_response = await self.call_llm(system_prompt, user_prompt)
        if llm_response and "score" in llm_response and "feedback" in llm_response:
            return AgentEvaluation(
                agent_name=self.name,
                score=int(llm_response["score"]),
                passed=bool(llm_response.get("passed", llm_response["score"] >= 80)),
                feedback=str(llm_response["feedback"]),
                critical_issues=list(llm_response.get("critical_issues", [])),
                suggestions=list(llm_response.get("suggestions", [])),
            )

        # 2. Rule-based Heuristic Analyzer (Local / Offline mode)
        return self._heuristic_analysis(diff_meta, scanner_payload)

    def _heuristic_analysis(
        self, diff_meta: Dict[str, Any], scanner_payload: Dict[str, Any]
    ) -> AgentEvaluation:
        critical_issues: List[str] = []
        suggestions: List[str] = []
        score = 100

        # Incorporate static scanner inputs from Soliman
        scanner_status = scanner_payload.get("status", "").upper()
        if scanner_status == "FAIL":
            score -= 40
            for issue in scanner_payload.get("critical_issues", []):
                critical_issues.append(f"Scanner finding: {issue}")

        # Scan added diff lines for common security anti-patterns
        # SQL Injection patterns (f-strings, string formatting, string concatenation with SQL keywords)
        sqli_fstring_pattern = re.compile(r"f['\"].*(select\s+.*from|insert\s+into|update\s+.*set|delete\s+from).*{.*}", re.IGNORECASE)
        sqli_concat_pattern = re.compile(r"['\"].*(select\s+.*from|insert\s+into|update\s+.*set|delete\s+from).*['\"]\s*(\+|\%|\.format)", re.IGNORECASE)
        sqli_format_pattern = re.compile(r"['\"].*(select\s+.*from|insert\s+into|update\s+.*set|delete\s+from).*\{.*\}['\"]\s*\.format", re.IGNORECASE)
        hardcoded_secret_pattern = re.compile(r"(api[_-]?key|secret[_-]?key|password|token)\s*=\s*['\"][A-Za-z0-9_\-\.]{8,}['\"]", re.IGNORECASE)
        eval_exec_pattern = re.compile(r"\b(eval|exec|os\.system)\s*\(", re.IGNORECASE)
        shell_true_pattern = re.compile(r"subprocess\.(Popen|run|call)\(.*shell\s*=\s*True", re.IGNORECASE)

        for filename, line in diff_meta["added_lines"]:
            stripped = line.strip()

            # SQL Injection check
            if sqli_fstring_pattern.search(stripped) or sqli_concat_pattern.search(stripped) or sqli_format_pattern.search(stripped):
                issue = f"SQL Injection detected in {filename}: string formatting/interpolation used in SQL query"
                if issue not in critical_issues:
                    critical_issues.append(issue)
                    score -= 50
                    suggestions.append("Use parameterized queries or ORM query builders instead of raw string interpolation.")

            # Hardcoded secret check
            if hardcoded_secret_pattern.search(stripped) and not stripped.startswith("#"):
                issue = f"Hardcoded secret/credential detected in {filename}"
                if issue not in critical_issues:
                    critical_issues.append(issue)
                    score -= 40
                    suggestions.append("Move secrets to environment variables or secret manager.")

            # Eval / Exec check
            if eval_exec_pattern.search(stripped) and not stripped.startswith("#"):
                issue = f"Dangerous function call (eval/exec/os.system) in {filename}"
                if issue not in critical_issues:
                    critical_issues.append(issue)
                    score -= 40
                    suggestions.append("Avoid dynamic code execution (eval/exec).")

            # Shell=True check
            if shell_true_pattern.search(stripped):
                issue = f"Command Injection risk (subprocess with shell=True) in {filename}"
                if issue not in critical_issues:
                    critical_issues.append(issue)
                    score -= 30
                    suggestions.append("Pass command arguments as a list and remove shell=True.")

        score = max(0, min(100, score))
        passed = len(critical_issues) == 0 and score >= 80

        if passed:
            feedback = "Clean - no secrets or CVEs found"
        else:
            feedback = f"Security Vulnerabilities Flagged: {'; '.join(critical_issues)}"

        return AgentEvaluation(
            agent_name=self.name,
            score=score,
            passed=passed,
            feedback=feedback,
            critical_issues=critical_issues,
            suggestions=suggestions,
        )
