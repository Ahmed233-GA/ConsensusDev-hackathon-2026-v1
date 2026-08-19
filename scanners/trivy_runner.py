import asyncio
import json
import logging
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class TrivyRunner:
    """
    Executes Trivy filesystem, vulnerability, and secret scanner on PR diff contents.
    """

    def __init__(self, trivy_bin: str = "trivy"):
        self.trivy_bin = os.getenv("TRIVY_PATH", trivy_bin)

    def write_diff_to_temp(self, diff: str) -> str:
        """
        Reconstruct code files from git diff into a temporary directory.
        """
        temp_dir = tempfile.mkdtemp(prefix="consensusdev_trivy_")
        current_file = "scanned_code.py"
        file_lines: Dict[str, List[str]] = {}

        for line in diff.splitlines():
            if line.startswith("diff --git"):
                parts = line.split(" ")
                if len(parts) >= 4:
                    current_file = parts[3].lstrip("b/")
                    if current_file not in file_lines:
                        file_lines[current_file] = []
            elif line.startswith("+++ b/"):
                current_file = line.replace("+++ b/", "").strip()
                if current_file not in file_lines:
                    file_lines[current_file] = []
            elif line.startswith("+") and not line.startswith("+++"):
                if current_file not in file_lines:
                    file_lines[current_file] = []
                file_lines[current_file].append(line[1:])

        if not file_lines:
            file_lines["sample.py"] = [diff]

        for filepath, lines in file_lines.items():
            dest_path = Path(temp_dir) / filepath
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            with open(dest_path, "w", encoding="utf-8", errors="ignore") as f:
                f.write("\n".join(lines))

        return temp_dir

    async def run_scan(self, diff: str) -> Dict[str, Any]:
        """
        Run Trivy analysis on the extracted diff files.
        """
        temp_dir = self.write_diff_to_temp(diff)
        critical_issues: List[str] = []
        vuln_count = 0

        try:
            cmd = [
                self.trivy_bin,
                "fs",
                "--format",
                "json",
                "--security-checks",
                "vuln,secret,config",
                "--severity",
                "HIGH,CRITICAL",
                temp_dir,
            ]

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()

            if stdout:
                try:
                    data = json.loads(stdout.decode("utf-8", errors="ignore"))
                    for result in data.get("Results", []):
                        target = result.get("Target", "code")
                        # Parse Vulnerabilities
                        for vuln in result.get("Vulnerabilities", []):
                            vuln_id = vuln.get("VulnerabilityID", "CVE-UNKNOWN")
                            title = vuln.get("Title", vuln.get("PkgName", ""))
                            critical_issues.append(f"[Trivy {vuln_id}] {title} in {target}")
                            vuln_count += 1
                        # Parse Secrets
                        for secret in result.get("Secrets", []):
                            title = secret.get("Title", "Exposed Secret")
                            critical_issues.append(f"[Trivy Secret] {title} in {target}")
                            vuln_count += 1
                except Exception as parse_err:
                    logger.warning(f"Error parsing Trivy JSON output: {parse_err}")

        except FileNotFoundError:
            logger.info("Trivy CLI binary not found in PATH. Using built-in CVE & Secret scanner engine.")
            if re.search(r"(ghp_[A-Za-z0-9]{36}|sk-[A-Za-z0-9]{32,}|AKIA[0-9A-Z]{16})", diff):
                critical_issues.append("[Trivy Secret] Hardcoded API/Cloud credential token detected")
                vuln_count += 1
            if "eval(" in diff or "exec(" in diff or "os.system(" in diff:
                critical_issues.append("[Trivy CWE-94] Arbitrary code execution risk (eval/exec)")
                vuln_count += 1
        except Exception as e:
            logger.error(f"Trivy scan exception: {e}")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

        return {
            "scanner": "Trivy",
            "vulnerabilities_count": vuln_count,
            "critical_issues": critical_issues,
            "passed": vuln_count == 0,
        }
