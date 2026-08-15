"""Security scanning runner for ConsensusDev.

Performs deterministic Static Application Security Testing (SAST) and
Infrastructure as Code (IaC) analysis on git diffs.
"""

import re
from typing import List, Tuple, Optional
from scanners.schemas import ScanResponse, SecurityFinding
from scanners.trivy_runner import run_trivy_scan



# Regex rules for SAST, Secrets, and IaC scanning
SECURITY_RULES = [
    # --- Secrets & Credentials ---
    {
        "id": "SEC-001",
        "title": "Hardcoded AWS Access Key",
        "severity": "CRITICAL",
        "regex": r"(?:A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}",
        "description": "Detected hardcoded AWS Access Key ID. Hardcoded credentials can lead to unauthorized cloud infrastructure access.",
        "recommendation": "Use environment variables or a secrets manager (e.g., AWS Secrets Manager, HashiCorp Vault).",
    },
    {
        "id": "SEC-002",
        "title": "Hardcoded Private Key",
        "severity": "CRITICAL",
        "regex": r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----",
        "description": "Detected embedded private cryptographic key.",
        "recommendation": "Store private keys in a secure secret store; never commit them to source control.",
    },
    {
        "id": "SEC-003",
        "title": "Hardcoded GitHub Token",
        "severity": "CRITICAL",
        "regex": r"(?:ghp|gho|ghu|ghs|ghr)_[0-9a-zA-Z]{36}|github_pat_[0-9a-zA-Z_]{82}",
        "description": "Detected hardcoded GitHub personal access token.",
        "recommendation": "Revoke the exposed token and configure GitHub Secrets.",
    },
    {
        "id": "SEC-004",
        "title": "Hardcoded Generic Secret / Password",
        "severity": "HIGH",
        "regex": r"(?i)(?:password|passwd|secret|api_key|apikey|access_token|auth_token)\s*[:=]\s*['\"][A-Za-z0-9_\-\.\@\#\$\%\^\&\*\!\?]{8,}['\"]",
        "description": "Detected plaintext secret, password, or API key assignment.",
        "recommendation": "Load sensitive credentials dynamically from environment variables or a vault.",
    },
    # --- Injection & Code Execution ---
    {
        "id": "SEC-005",
        "title": "Potential SQL Injection via String Formatting",
        "severity": "CRITICAL",
        "regex": r"(?i)(?:f['\"].*(?:SELECT|INSERT|UPDATE|DELETE|DROP|ALTER)\b.*\{|['\"].*(?:SELECT|INSERT|UPDATE|DELETE|DROP|ALTER)\b.*%\s*(?:\([^\)]+\)|\w+)|(?:execute|cursor\.execute|raw)\s*\(\s*f?['\"].*(?:SELECT|INSERT|UPDATE|DELETE|DROP|ALTER))",
        "description": "SQL query built using direct string formatting, interpolation, or concatenation without parameterized queries.",
        "recommendation": "Use parameterized queries or an ORM with proper query parameter binding.",
    },
    {
        "id": "SEC-006",
        "title": "Dangerous Command Execution (Shell Injection)",
        "severity": "HIGH",
        "regex": r"(?:subprocess\.(?:Popen|run|call|check_output)\s*\([^)]*shell\s*=\s*True|os\.system\s*\(|os\.popen\s*\()",
        "description": "Invoking shell commands with shell=True or os.system can allow arbitrary code execution.",
        "recommendation": "Avoid shell=True. Pass command arguments as a list of strings instead.",
    },
    {
        "id": "SEC-007",
        "title": "Unsafe Dynamic Code Evaluation (eval/exec)",
        "severity": "HIGH",
        "regex": r"(?:eval\s*\(|exec\s*\()",
        "description": "Direct invocation of eval() or exec() poses severe arbitrary code execution risks.",
        "recommendation": "Refactor to use safer parsing alternatives such as ast.literal_eval() or json.loads().",
    },
    {
        "id": "SEC-008",
        "title": "Unsafe YAML / Object Deserialization",
        "severity": "HIGH",
        "regex": r"(?:yaml\.load\s*\([^)]*(?!Loader=yaml\.SafeLoader|Loader=SafeLoader)[^)]*\)|pickle\.loads?\s*\()",
        "description": "Unsafe deserialization using yaml.load() or pickle can lead to remote code execution.",
        "recommendation": "Use yaml.safe_load() and avoid deserializing untrusted data with pickle.",
    },
    # --- Insecure Transport & Configuration ---
    {
        "id": "SEC-009",
        "title": "Disabled TLS/SSL Certificate Verification",
        "severity": "HIGH",
        "regex": r"(?i)(?:verify\s*=\s*False|NODE_TLS_REJECT_UNAUTHORIZED\s*=\s*['\"]?0['\"]?|InsecureRequestWarning)",
        "description": "TLS certificate validation is explicitly disabled, allowing man-in-the-middle (MitM) attacks.",
        "recommendation": "Ensure SSL/TLS validation is enabled and supply custom CA bundles if required.",
    },
    # --- IaC / Cloud Configuration Vulnerabilities ---
    {
        "id": "IAC-001",
        "title": "Overly Permissive Ingress (0.0.0.0/0)",
        "severity": "HIGH",
        "regex": r"(?i)cidr_blocks\s*=\s*\[\s*['\"]0\.0\.0\.0/0['\"]\s*\]",
        "description": "Security group exposes ingress traffic to the entire internet (0.0.0.0/0).",
        "recommendation": "Restrict CIDR blocks to known IP ranges or internal VPC subnets.",
    },
    {
        "id": "IAC-002",
        "title": "Public S3 Bucket ACL",
        "severity": "CRITICAL",
        "regex": r"(?i)acl\s*=\s*['\"]public-(?:read|read-write)['\"]",
        "description": "S3 bucket configured with public read or write access.",
        "recommendation": "Set S3 bucket ACL to private and enable S3 Block Public Access.",
    },
    {
        "id": "IAC-003",
        "title": "Wildcard IAM Action Allowed",
        "severity": "HIGH",
        "regex": r"(?i)['\"]Action['\"]\s*:\s*(?:['\"]\*['\"]|\[\s*['\"]\*['\"]\s*\])\s*,\s*['\"]Effect['\"]\s*:\s*['\"]Allow['\"]",
        "description": "IAM Policy grants blanket wildcard (*) permissions.",
        "recommendation": "Follow the principle of least privilege by specifying explicit API actions.",
    },
]


def parse_diff_lines(diff_text: str) -> List[Tuple[Optional[str], Optional[int], str]]:
    """Parse a unified git diff and extract added/modified lines with file and line context.
    
    Returns:
        List of tuples: (file_path, line_number, added_code_line)
    """
    results = []
    current_file = None
    current_line = 0

    lines = diff_text.splitlines()
    for raw_line in lines:
        # File header matching
        if raw_line.startswith("+++ b/"):
            current_file = raw_line[6:].strip()
            continue
        elif raw_line.startswith("+++ "):
            current_file = raw_line[4:].strip()
            continue

        # Chunk header matching @@ -1,4 +1,6 @@
        hunk_match = re.match(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@", raw_line)
        if hunk_match:
            current_line = int(hunk_match.group(1))
            continue

        # Added or modified line
        if raw_line.startswith("+") and not raw_line.startswith("+++"):
            code_content = raw_line[1:]
            results.append((current_file, current_line, code_content))
            current_line += 1
        elif not raw_line.startswith("-"):
            current_line += 1

    # Fallback: if no diff headers found, scan every line
    if not results and diff_text.strip():
        for idx, line in enumerate(lines, start=1):
            clean_line = line.lstrip("+")
            results.append((None, idx, clean_line))

    return results


def run_security_scan(diff_text: str) -> ScanResponse:
    """Execute static analysis on the diff and return a standardized ScanResponse."""
    findings: List[SecurityFinding] = []
    critical_issues: List[str] = []

    parsed_lines = parse_diff_lines(diff_text)

    # Track unique issues to avoid duplicate reporting on identical lines
    seen_violations = set()

    for file_path, line_no, line_content in parsed_lines:
        for rule in SECURITY_RULES:
            if re.search(rule["regex"], line_content):
                key = (rule["id"], file_path, line_no)
                if key in seen_violations:
                    continue
                seen_violations.add(key)

                finding = SecurityFinding(
                    rule_id=rule["id"],
                    title=rule["title"],
                    severity=rule["severity"],
                    description=rule["description"],
                    file=file_path,
                    line=line_no,
                    snippet=line_content.strip()[:200],
                    recommendation=rule["recommendation"],
                )
                findings.append(finding)

                if rule["severity"] in ("CRITICAL", "HIGH"):
                    location = f" in {file_path}:{line_no}" if file_path and line_no else ""
                    critical_issues.append(f"[{rule['severity']}] {rule['title']}{location}")

    # Run Trivy vulnerability scanner on dependencies
    trivy_findings = run_trivy_scan(diff_text)
    for tf in trivy_findings:
        findings.append(tf)
        if tf.severity in ("CRITICAL", "HIGH"):
            location = f" in {tf.file}" if tf.file else ""
            critical_issues.append(f"[{tf.severity}] {tf.title}{location}")

    vuln_count = len(findings)
    status = "FAIL" if (critical_issues or vuln_count > 0) else "PASS"

    if status == "PASS":
        summary = "Security scan passed: no vulnerabilities or insecure patterns detected in diff."
    else:
        summary = f"Security scan failed: found {vuln_count} security issue(s) ({len(critical_issues)} high/critical)."

    return ScanResponse(
        status=status,
        vulnerabilities=vuln_count,
        vulnerabilities_count=vuln_count,
        critical_issues=critical_issues,
        findings=findings,
        details=findings,
        summary=summary,
    )

