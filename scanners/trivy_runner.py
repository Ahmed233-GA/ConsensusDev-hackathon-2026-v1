"""Trivy vulnerability scanning runner for ConsensusDev.

Performs vulnerability scanning on dependencies, package lockfiles, and container configs
extracted from git diffs. Supports direct CLI execution if Trivy is installed, with a
deterministic fallback rule engine for common known CVEs and vulnerable dependency pins.
"""

import re
import json
import shutil
import tempfile
import subprocess
from typing import List, Optional
from scanners.schemas import SecurityFinding

# Known vulnerable package version patterns / database for deterministic offline scanning
VULNERABLE_DEPENDENCIES = [
    {
        "ecosystem": "pypi",
        "package": "requests",
        "vulnerable_spec": r"^2\.(?:[0-9]|1[0-9]|2[0-7])\..*",
        "cve": "CVE-2023-32681",
        "severity": "HIGH",
        "title": "Unintended leak of Proxy-Authorization header in requests",
        "description": "Requests library forwards Proxy-Authorization headers to destination servers when redirected to an HTTPS proxy.",
        "recommendation": "Upgrade requests to >= 2.31.0.",
    },
    {
        "ecosystem": "pypi",
        "package": "urllib3",
        "vulnerable_spec": r"^1\.(?:[0-9]|1[0-9]|2[0-5])\..*|^2\.0\.[0-6]$",
        "cve": "CVE-2023-45803",
        "severity": "HIGH",
        "title": "urllib3 Request body not stripped after 303 Redirect",
        "description": "urllib3 doesn't remove the request body when following a 303 redirect, leaking sensitive payload data.",
        "recommendation": "Upgrade urllib3 to >= 2.0.7 or >= 1.26.18.",
    },
    {
        "ecosystem": "pypi",
        "package": "flask",
        "vulnerable_spec": r"^[0-1]\..*",
        "cve": "CVE-2019-1010083",
        "severity": "HIGH",
        "title": "Flask Unexpected Memory Usage DOS",
        "description": "Unexpected memory usage in Flask handling of large payloads.",
        "recommendation": "Upgrade Flask to >= 2.0.0.",
    },
    {
        "ecosystem": "pypi",
        "package": "django",
        "vulnerable_spec": r"^[0-3]\..*|^4\.[0-1]\..*",
        "cve": "CVE-2023-36053",
        "severity": "HIGH",
        "title": "Potential ReDoS in EmailValidator / URLValidator",
        "description": "Django EmailValidator and URLValidator are subject to Regular Expression Denial of Service.",
        "recommendation": "Upgrade Django to >= 4.2.4 or >= 5.0.",
    },
    {
        "ecosystem": "pypi",
        "package": "cryptography",
        "vulnerable_spec": r"^[0-3]\..*|^41\.0\.[0-5]$",
        "cve": "CVE-2023-49083",
        "severity": "MEDIUM",
        "title": "NULL-dereference when loading PKCS7 certificates",
        "description": "Calling load_pem_pkcs7_certificates or load_der_pkcs7_certificates can cause a crash.",
        "recommendation": "Upgrade cryptography to >= 41.0.6.",
    },
    {
        "ecosystem": "npm",
        "package": "lodash",
        "vulnerable_spec": r"^[0-3]\..*|^4\.(?:[0-9]|1[0-6])\..*|^4\.17\.(?:[0-9]|1[0-9]|20)$",
        "cve": "CVE-2021-23337",
        "severity": "HIGH",
        "title": "Prototype Pollution in lodash",
        "description": "Command injection / prototype pollution via template function.",
        "recommendation": "Upgrade lodash to >= 4.17.21.",
    },
    {
        "ecosystem": "npm",
        "package": "axios",
        "vulnerable_spec": r"^0\.(?:[0-9]|1[0-9]|2[0-7])\..*",
        "cve": "CVE-2023-45857",
        "severity": "HIGH",
        "title": "Cross-Site Request Forgery in axios",
        "description": "Axios follows redirect with sensitive headers intact across origins.",
        "recommendation": "Upgrade axios to >= 1.6.0.",
    },
]


def run_trivy_cli(target_dir: str) -> Optional[List[SecurityFinding]]:
    """Attempt to invoke Trivy CLI if installed on the host or container."""
    if not shutil.which("trivy"):
        return None

    findings: List[SecurityFinding] = []
    try:
        cmd = ["trivy", "fs", "--format", "json", "--severity", "CRITICAL,HIGH,MEDIUM", target_dir]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0 and result.stdout:
            data = json.loads(result.stdout)
            for res in data.get("Results", []):
                target_file = res.get("Target", "unknown")
                for vuln in res.get("Vulnerabilities", []):
                    findings.append(
                        SecurityFinding(
                            rule_id=vuln.get("VulnerabilityID", "TRIVY-VULN"),
                            title=f"{vuln.get('PkgName')} - {vuln.get('VulnerabilityID')}",
                            severity=vuln.get("Severity", "HIGH"),
                            description=vuln.get("Title") or vuln.get("Description", "Vulnerability detected by Trivy."),
                            file=target_file,
                            line=None,
                            snippet=f"{vuln.get('PkgName')}@{vuln.get('InstalledVersion')}",
                            recommendation=f"Upgrade to version {vuln.get('FixedVersion', 'latest')}",
                        )
                    )
            return findings
    except Exception:
        pass
    return None


def run_trivy_scan(diff_text: str) -> List[SecurityFinding]:
    """Scan diff lines for dependency updates and package definitions matching known vulnerabilities."""
    findings: List[SecurityFinding] = []
    current_file = None

    lines = diff_text.splitlines()
    for raw_line in lines:
        if raw_line.startswith("+++ b/"):
            current_file = raw_line[6:].strip()
            continue
        elif raw_line.startswith("+++ "):
            current_file = raw_line[4:].strip()
            continue

        if not raw_line.startswith("+") or raw_line.startswith("+++"):
            continue

        added_line = raw_line[1:].strip()

        # Python requirements.txt matching (e.g. requests==2.20.0, django<=3.2.0)
        pypi_match = re.match(r"^([a-zA-Z0-9_\-]+)\s*(?:==|<=|~=)\s*([0-9a-zA-Z\.\-]+)", added_line)
        if pypi_match:
            pkg_name = pypi_match.group(1).lower()
            pkg_ver = pypi_match.group(2)

            for vuln in VULNERABLE_DEPENDENCIES:
                if vuln["ecosystem"] == "pypi" and vuln["package"] == pkg_name:
                    if re.match(vuln["vulnerable_spec"], pkg_ver):
                        findings.append(
                            SecurityFinding(
                                rule_id=vuln["cve"],
                                title=f"Vulnerable Dependency: {vuln['package']} ({vuln['cve']})",
                                severity=vuln["severity"],
                                description=f"{vuln['title']}. {vuln['description']}",
                                file=current_file or "requirements.txt",
                                line=None,
                                snippet=added_line,
                                recommendation=vuln["recommendation"],
                            )
                        )

        # Node package.json / dependencies matching (e.g. "lodash": "4.17.15")
        npm_match = re.match(r"['\"]([a-zA-Z0-9_\-\@\/]+)['\"]\s*:\s*['\"][\^~]?([0-9a-zA-Z\.\-]+)['\"]", added_line)
        if npm_match:
            pkg_name = npm_match.group(1).lower()
            pkg_ver = npm_match.group(2)

            for vuln in VULNERABLE_DEPENDENCIES:
                if vuln["ecosystem"] == "npm" and vuln["package"] == pkg_name:
                    if re.match(vuln["vulnerable_spec"], pkg_ver):
                        findings.append(
                            SecurityFinding(
                                rule_id=vuln["cve"],
                                title=f"Vulnerable NPM Dependency: {vuln['package']} ({vuln['cve']})",
                                severity=vuln["severity"],
                                description=f"{vuln['title']}. {vuln['description']}",
                                file=current_file or "package.json",
                                line=None,
                                snippet=added_line,
                                recommendation=vuln["recommendation"],
                            )
                        )

    return findings
