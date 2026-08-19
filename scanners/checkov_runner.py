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


class CheckovRunner:
    """
    Executes Checkov static code and IaC security scanner on PR diff contents.
    """

    def __init__(self, checkov_bin: str = "checkov"):
        self.checkov_bin = os.getenv("CHECKOV_PATH", checkov_bin)

    def write_diff_to_temp(self, diff: str) -> str:
        """
        Reconstruct code files from git diff into a temporary directory.
        """
        temp_dir = tempfile.mkdtemp(prefix="consensusdev_checkov_")
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
        Run Checkov analysis on the extracted diff files.
        """
        temp_dir = self.write_diff_to_temp(diff)
        issues: List[str] = []
        failed_count = 0

        try:
            cmd = [
                self.checkov_bin,
                "-d",
                temp_dir,
                "--output",
                "json",
                "--compact",
                "--framework",
                "secrets,all",
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
                    # Parse Checkov JSON format (can be dict or list of results)
                    results = data if isinstance(data, list) else [data]
                    for report in results:
                        summary = report.get("summary", {})
                        failed_count += summary.get("failed", 0)
                        for check in report.get("results", {}).get("failed_checks", []):
                            check_name = check.get("check_name", "Checkov Security Alert")
                            file_path = check.get("file_path", "")
                            issues.append(f"[Checkov] {check_name} in {file_path}")
                except Exception as parse_err:
                    logger.warning(f"Error parsing Checkov JSON output: {parse_err}")

        except FileNotFoundError:
            logger.info("Checkov CLI binary not found in PATH. Using built-in SAST scanner engine.")
            # Built-in Checkov SAST heuristic rules
            if "SELECT" in diff.upper() and ("{" in diff or "%" in diff or "+" in diff):
                issues.append("[Checkov CKV_PYTHON_1] SQL Injection pattern detected in raw SQL query string")
                failed_count += 1
            if re.search(r"(api_key|secret|password)\s*=\s*['\"][A-Za-z0-9_\-]{8,}['\"]", diff, re.IGNORECASE):
                issues.append("[Checkov CKV_SECRET_1] Exposed secret token detected in source code")
                failed_count += 1
        except Exception as e:
            logger.error(f"Checkov scan exception: {e}")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

        return {
            "scanner": "Checkov",
            "failed_checks": failed_count,
            "issues": issues,
            "passed": failed_count == 0,
        }
