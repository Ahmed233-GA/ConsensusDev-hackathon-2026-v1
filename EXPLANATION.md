# ConsensusDev — Deep-Dive Codebase Explanation

This document provides a comprehensive, component-by-component explanation of everything built and added in the `feature/soliman-scanners` branch for **ConsensusDev**.

---

## Table of Contents
1. [Architecture & Role in ConsensusDev](#1-architecture--role-in-consensusdev)
2. [`scanners/__init__.py`](#2-scanners__init__py)
3. [`scanners/schemas.py` (Data Models & Contracts)](#3-scannersschemaspy-data-models--contracts)
4. [`scanners/checkov_runner.py` (SAST & IaC Engine)](#4-scannerscheckov_runnerpy-sast--iac-engine)
5. [`scanners/trivy_runner.py` (Dependency Vulnerability Scanner)](#5-scannerstrivy_runnerpy-dependency-vulnerability-scanner)
6. [`scanners/app.py` (FastAPI Service on Port 8002)](#6-scannersapppy-fastapi-service-on-port-8002)
7. [`Dockerfile` (Containerization)](#7-dockerfile-containerization)
8. [`tests/test_scanner.py` (Detailed Breakdown of All 8 Tests)](#8-teststest_scannerpy-detailed-breakdown-of-all-8-tests)
9. [Integration Dataflow: Gateway ➔ Security ➔ AI Engine](#9-integration-dataflow-gateway--security--ai-engine)

---

## 1. Architecture & Role in ConsensusDev

In the ConsensusDev multi-agent workflow:
- **Port 8000 (Gateway - Ahmed):** Intercepts GitHub PR webhooks, downloads the git diff, and dispatches it in parallel to QA and Security.
- **Port 8002 (Security - Soliman):** This service! Analyzes the git diff deterministically for secrets, injection vulnerabilities, dangerous code execution, insecure configurations (IaC), and vulnerable package dependencies (CVEs).
- **Port 8001 (AI Engine - Ahmed/Medhat):** Consumes the findings produced by Port 8002 as factual evidence to perform LLM-based reasoning and consensus decisions.

```
       Developer PR ➔ GitHub Webhook ➔ Gateway (:8000)
                                            │
                             ┌──────────────┴──────────────┐
                             ▼                             ▼
                  Security Service (:8002)            QA Runner (:8003)
                    [This Service]                       (Shahd)
                             │                             │
                             └──────────────┬──────────────┘
                                            ▼
                                    AI Engine (:8001)
                                            │
                                            ▼
                                  Ahmed Decision Gate
```

---

## 2. `scanners/__init__.py`

```python
"""ConsensusDev Security Scanner Package."""
```

### Purpose:
- Converts the `scanners/` directory into a recognized Python package.
- Ensures consistent relative and absolute module importing across Windows, Linux, and containerized Docker environments.
- Enables Uvicorn to resolve `scanners.app:app` without module path errors.

---

## 3. `scanners/schemas.py` (Data Models & Contracts)

Defines strongly-typed Pydantic (v2) models that validate request payloads and structure outgoing responses.

### 1. `ScanRequest`
```python
class ScanRequest(BaseModel):
    diff: str
```
- **Purpose:** Represents the payload sent by the Gateway or developer containing the raw git diff string.
- **Validation:** Enforces that `diff` is provided and is of type `str`.

### 2. `SecurityFinding`
```python
class SecurityFinding(BaseModel):
    rule_id: str
    title: str
    severity: str
    description: str
    file: Optional[str] = None
    line: Optional[int] = None
    snippet: Optional[str] = None
    recommendation: Optional[str] = None
```
- **`rule_id`**: Identifier of the rule triggered (e.g., `SEC-001`, `IAC-002`, `CVE-2023-32681`).
- **`title`**: Concise human-readable name of the vulnerability.
- **`severity`**: Level classification (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, or `INFO`).
- **`description`**: Detailed explanation of the risk.
- **`file`**: Target file path where the issue was detected in the diff.
- **`line`**: Line number in the target file.
- **`snippet`**: The actual code line containing the violation.
- **`recommendation`**: Actionable guidance for the developer on how to remediate the issue.

### 3. `ScanResponse`
```python
class ScanResponse(BaseModel):
    status: str
    vulnerabilities: int
    vulnerabilities_count: int
    critical_issues: List[str] = []
    findings: List[SecurityFinding] = []
    details: List[SecurityFinding] = []
    summary: str
```
- **Dual Compatibility:** Provides fields required by both the simple target format (`status`, `vulnerabilities`) and the rich blueprint specification (`critical_issues`, `findings`, `details`, `summary`).
- **`status`**: `"PASS"` if clean; `"FAIL"` if any security issues exist.
- **`critical_issues`**: Quick string list of all `CRITICAL` and `HIGH` severity findings for rapid evaluation by the AI Engine.

---

## 4. `scanners/checkov_runner.py` (SAST & IaC Engine)

This is the core analysis engine. It operates in three main stages:

### Stage 1: Diff Parsing (`parse_diff_lines`)
Unified git diffs contain metadata headers (`diff --git`, `--- a/...`, `+++ b/...`, `@@ -1,4 +1,6 @@`).
`parse_diff_lines()` extracts:
1. **Target File Name:** Captured from `+++ b/<filename>`.
2. **Line Number Tracking:** Initializes line count from the hunk header `@@ ... +<start_line> @@` and increments as lines are processed.
3. **Added/Modified Lines:** Filters lines starting with `+` (excluding `+++` headers), stripping the leading `+` while preserving code indentation.
4. **Fallback:** If a raw code snippet without diff headers is provided, it processes every line sequentially.

### Stage 2: Security & IaC Rules Evaluation
Evaluates each added code line against deterministic regex rules:

| Rule ID | Category | Severity | Description & Pattern |
| :--- | :--- | :--- | :--- |
| **`SEC-001`** | Secrets | `CRITICAL` | **AWS Access Key ID**: Detects `AKIA`, `ASIA`, `AGPA`, `AIDA`, `AROA` prefixes followed by 16 alphanumeric characters. |
| **`SEC-002`** | Secrets | `CRITICAL` | **Private Cryptographic Keys**: Detects `-----BEGIN RSA/EC/DSA/OPENSSH PRIVATE KEY-----`. |
| **`SEC-003`** | Secrets | `CRITICAL` | **GitHub Tokens**: Detects classic tokens (`ghp_...`, `gho_...`) and fine-grained PATs (`github_pat_...`). |
| **`SEC-004`** | Secrets | `HIGH` | **Generic Secrets/Passwords**: Detects assignments like `password = "..."`, `api_key = "..."`, `auth_token = "..."`. |
| **`SEC-005`** | Injection | `CRITICAL` | **SQL Injection**: Detects SQL statements combined with f-strings (`f"SELECT ... WHERE id = {var}"`), `%` formatting, or non-parameterized queries. |
| **`SEC-006`** | Code Exec | `HIGH` | **Command Injection / Shell Execution**: Detects `os.system()`, `os.popen()`, and `subprocess.*(..., shell=True)`. |
| **`SEC-007`** | Code Exec | `HIGH` | **Dynamic Code Evaluation**: Detects direct `eval()` or `exec()` execution. |
| **`SEC-008`** | Deserialization | `HIGH` | **Unsafe Deserialization**: Detects `pickle.loads()` or `yaml.load()` without `SafeLoader`. |
| **`SEC-009`** | Network/TLS | `HIGH` | **Disabled SSL Verification**: Detects `verify=False` or `NODE_TLS_REJECT_UNAUTHORIZED=0`. |
| **`IAC-001`** | IaC / Cloud | `HIGH` | **Open Ingress (0.0.0.0/0)**: Detects open CIDR blocks `0.0.0.0/0` in Terraform / security groups. |
| **`IAC-002`** | IaC / Cloud | `CRITICAL` | **Public S3 Bucket ACL**: Detects `acl = "public-read"` or `public-read-write`. |
| **`IAC-003`** | IaC / Cloud | `HIGH` | **Wildcard IAM Permissions**: Detects `"Action": "*"` paired with `"Effect": "Allow"`. |

### Stage 3: Aggregation & Deduplication
- Uses a `(rule_id, file, line)` violation set to prevent duplicate findings for identical lines.
- Integrates dependency vulnerability findings from `trivy_runner.py`.
- Computes overall `status` (`PASS` vs `FAIL`), `vulnerabilities_count`, and summary.

---

## 5. `scanners/trivy_runner.py` (Dependency Vulnerability Scanner)

Analyzes package manifests modified in pull requests:

1. **Python Dependencies (`requirements.txt`):**
   - Matches packages and pinned version strings (`package==x.y.z`).
   - Checks against known vulnerability databases (e.g. `requests` < 2.31.0 for Proxy-Authorization leak `CVE-2023-32681`, `urllib3` < 2.0.7 for 303 redirect body leak `CVE-2023-45803`, `django` < 4.2.4 for ReDoS `CVE-2023-36053`, `flask` < 2.0.0 `CVE-2019-1010083`).
2. **Node Dependencies (`package.json`):**
   - Matches npm packages (e.g. `lodash` < 4.17.21 for prototype pollution `CVE-2021-23337`, `axios` < 1.6.0 for CSRF header leak `CVE-2023-45857`).
3. **Native Trivy CLI Hook (`run_trivy_cli`):**
   - Checks if the `trivy` binary is installed on the host system or container (`shutil.which("trivy")`).
   - If available, runs filesystem scans (`trivy fs --format json ...`) and aggregates results. If not, the offline deterministic rule engine runs without external dependencies.

---

## 6. `scanners/app.py` (FastAPI Service on Port 8002)

The API entry point:
- **`title`**: `"ConsensusDev Security Scanner Service"`
- **`CORS Middleware`**: Configured to allow cross-origin requests from Gateway (`:8000`) and Portal (`:8004`).
- **`GET /`**: Returns service name, port `8002`, owner (`Soliman`), and status.
- **`GET /health`**: Health check probe returning `{"status": "healthy", "service": "scanners", "port": 8002}`.
- **`POST /scan`**:
  - Validates incoming `ScanRequest`.
  - Calls `run_security_scan(request.diff)`.
  - Returns `ScanResponse` with HTTP 200 (or HTTP 500 with descriptive detail if an exception occurs).

---

## 7. `Dockerfile` (Containerization)

- **Base Image:** `python:3.11-slim` for minimal container size and fast startup.
- **System Tools:** Installs `curl` and `git`.
- **Dependencies:** Copies and installs `requirements.txt`.
- **Application Code:** Copies `scanners/` package into `/app/scanners/`.
- **Port:** Exposes `8002`.
- **Entrypoint:** `CMD ["uvicorn", "scanners.app:app", "--host", "0.0.0.0", "--port", "8002"]`.

---

## 8. `tests/test_scanner.py` (Detailed Breakdown of All 8 Tests)

All tests are written using Python's standard `unittest` framework with `asyncio`, requiring zero external test drivers.

### 1. `test_root_endpoint`
- **What it does:** Calls `GET /`.
- **Assertion:** Status code 200, service name matches, port equals `8002`, status equals `"running"`.

### 2. `test_health_endpoint`
- **What it does:** Calls `GET /health`.
- **Assertion:** Returns `status="healthy"`, port `8002`. Ensures Gateway health checks pass.

### 3. `test_safe_diff_scan`
- **Input Diff:** Addition of a clean `calculator.py` with standard math functions (`add`, `multiply`).
- **Assertion:** `status == "PASS"`, `vulnerabilities == 0`, `critical_issues` is empty, `findings` is empty.

### 4. `test_vulnerable_diff_hardcoded_aws_key`
- **Input Diff:** Addition of `AWS_ACCESS_KEY_ID = 'AKIAIOSFODNN7EXAMPLE'` in `config.py`.
- **Assertion:** `status == "FAIL"`, `vulnerabilities >= 1`, rule `SEC-001` triggered with severity `CRITICAL`, finding includes file and line number.

### 5. `test_vulnerable_diff_sql_injection`
- **Input Diff:** Addition of `query = f"SELECT * FROM users WHERE id = '{user_id}'"`.
- **Assertion:** `status == "FAIL"`, rule `SEC-005` triggered, `critical_issues` lists SQL Injection warning.

### 6. `test_vulnerable_diff_iac_public_s3`
- **Input Diff:** Addition of Terraform resource `aws_s3_bucket` with `acl = "public-read"`.
- **Assertion:** `status == "FAIL"`, rule `IAC-002` triggered with severity `CRITICAL`.

### 7. `test_vulnerable_diff_trivy_dependency`
- **Input Diff:** Addition of `requests==2.20.0` in `requirements.txt`.
- **Assertion:** `status == "FAIL"`, Trivy engine identifies `CVE-2023-32681` (Proxy-Authorization leak) and recommends upgrading to `>= 2.31.0`.

### 8. `test_direct_runner_execution`
- **Input Diff:** Code containing dangerous shell execution `os.system("rm -rf " + target_dir)`.
- **Assertion:** Directly tests `run_security_scan()` function, verifying rule `SEC-006` flags the command injection vulnerability.

---

## 9. Integration Dataflow: Gateway ➔ Security ➔ AI Engine

```
[1] Developer submits PR on GitHub
        │
[2] GitHub Webhook fires ➔ Gateway (:8000) extracts git diff
        │
[3] Gateway sends POST http://localhost:8002/scan
        {
          "diff": "diff --git a/app.py ...\n+ AWS_SECRET = 'AKIAIOSFODNN7EXAMPLE'"
        }
        │
[4] Security Scanner (:8002) parses diff, executes SAST/IaC/Trivy rules
        │
[5] Security Scanner returns JSON response:
        {
          "status": "FAIL",
          "vulnerabilities": 1,
          "critical_issues": ["[CRITICAL] Hardcoded AWS Access Key in app.py:2"],
          "findings": [...]
        }
        │
[6] Gateway bundles Security JSON + QA Test JSON and calls AI Engine (:8001)
        │
[7] AI Engine Security Specialist Agent reads deterministic findings
        │
[8] AI Engine reaches consensus ➔ Ahmed Decision Gate blocks PR with remediation feedback!
```
