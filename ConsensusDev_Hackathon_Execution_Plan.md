# ConsensusDev — Master Hackathon Execution Blueprint & Team Operating Guide

> **Project:** ConsensusDev (Autonomous Multi-Agent Code Review & Security Gate)  
> **Team:** 5 Members (Ahmed Atia, Mohammed Medhat, Soliman, Shahd Mostafa, Nourhan)  
> **Architecture Style:** Microservices & Event-Driven Pipeline  
> **Target:** Live 3-Minute Hackathon Demo (Webhook → Scanners → 4 AI Agents → Consensus → Auto-Merge/Block → Docs)

---

## 1. Project Overview in Plain English

### A. The Core Idea
ConsensusDev is an autonomous engineering review gate. Instead of relying on a single human reviewer or a basic chatbot, a developer opens a GitHub Pull Request (PR), and ConsensusDev orchestrates automated static security analysis, unit/mutation testing, and 4 specialized AI Reviewer Agents. A central consensus engine evaluates all evidence and either blocks the PR with actionable feedback or automatically merges it and updates documentation.

### B. The 5-Service Architecture & Port Allocation
```
                       ┌─────────────────────────┐
                       │    GitHub Pull Request  │
                       └────────────┬────────────┘
                                    │ Webhook (ngrok)
                                    ▼
                       ┌─────────────────────────┐
                       │   Ahmed (Team Leader)   │
                       │     Gateway Service     │
                       │      Port: 8000         │
                       └──────┬─────┬─────┬──────┘
                              │     │     │
            ┌─────────────────┘     │     └─────────────────┐
            │ Diff                  │ Diff                  │ Diff + Reports
            ▼                       ▼                       ▼
┌───────────────────────┐ ┌───────────────────┐ ┌───────────────────────┐
│        Soliman        │ │       Shahd       │ │        Medhat         │
│    Security Scanners  │ │     QA Runner     │ │       AI Engine       │
│      Port: 8002       │ │    Port: 8003     │ │      Port: 8001       │
│  /scan (Checkov/Trivy)│ │ /run-tests (Pytest│ │ /analyze-pr (4 Agents)│
└───────────┬───────────┘ └─────────┬─────────┘ └───────────┬───────────┘
            │                       │                       │
            └───────────────┬───────┴───────────────────────┘
                            │ Aggregated Reports
                            ▼
                ┌───────────────────────┐
                │   Consensus Decision  │
                │     (true / false)    │
                └───────────┬───────────┘
                            │
               ┌────────────┴────────────┐
               ▼ (false)                 ▼ (true)
    ┌─────────────────────┐   ┌─────────────────────┐
    │ GitHub Inline Block │   │   Auto-Merge PR     │
    │  & Review Comments  │   └──────────┬──────────┘
    └─────────────────────┘              │ Notification
                                         ▼
                              ┌─────────────────────┐
                              │       Nourhan       │
                              │    Portal & Docs    │
                              │      Port: 8004     │
                              │ /update-docs & DORA │
                              └─────────────────────┘
```

---

## 2. Team Member Role Matrix

| Member | Role Name | System Port | Endpoint | Core Technologies | Primary Deliverable |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Ahmed Atia** | Team Leader & CI/CD Lead ("The Glue") | `8000` | `POST /webhook/github` | FastAPI, Uvicorn, HTTPX, GitHub REST API, ngrok | Central Orchestration Gateway & GitHub Automation |
| **Mohammed Medhat** | Multi-Agent AI Architect ("The Brain") | `8001` | `POST /analyze-pr` | Python, LiteLLM, LangChain, OpenAI / Ollama, Pydantic | 4 AI Agents (Security, Tech Debt, Story, Perf) & Consensus Engine |
| **Soliman** | DevSecOps & Security Lead ("The Sensor") | `8002` | `POST /scan` | Docker, Checkov, Trivy, SonarQube, FastAPI | Automated SAST, IaC, and Secret Scanner Service |
| **Shahd Mostafa** | QA & Test Automation Lead ("The Validator") | `8003` | `POST /run-tests` | Pytest, pytest-cov, mutmut, FastAPI | Test Execution, Coverage Analyzer & Mutation Benchmark |
| **Nourhan** | Dev Portal & Documentation Lead ("The Storyteller") | `8004` | `POST /update-docs` | Streamlit, MkDocs (Material), Mermaid.js | Live DORA Metrics Dashboard & Automated Architecture Docs |

---

## 3. Strict API Contracts & Data Payloads

### Contract 1: Ahmed (Gateway) → Soliman (Security Scanner)
* **Endpoint:** `POST http://localhost:8002/scan`
* **Request Payload:**
```json
{
  "diff": "diff --git a/app/db.py b/app/db.py\n+ query = f'SELECT * FROM users WHERE id = {user_input}'"
}
```
* **Response Payload:**
```json
{
  "status": "FAIL",
  "vulnerabilities_count": 1,
  "critical_issues": [
    "SQL Injection detected in app/db.py (CWE-89)"
  ]
}
```

---

### Contract 2: Ahmed (Gateway) → Shahd (QA Runner)
* **Endpoint:** `POST http://localhost:8003/run-tests`
* **Request Payload:**
```json
{
  "diff": "diff --git a/app/calc.py b/app/calc.py\n+ def add(a, b): return a + b"
}
```
* **Response Payload:**
```json
{
  "status": "PASS",
  "tests_passed": 12,
  "tests_failed": 0,
  "coverage_percentage": 94.5,
  "mutation_score": 88.0
}
```

---

### Contract 3: Ahmed (Gateway) → Medhat (AI Engine)
* **Endpoint:** `POST http://localhost:8001/analyze-pr`
* **Request Payload:**
```json
{
  "diff": "...",
  "security": {
    "status": "PASS",
    "vulnerabilities_count": 0,
    "critical_issues": []
  },
  "tests": {
    "status": "PASS",
    "tests_passed": 12,
    "coverage_percentage": 95.0
  }
}
```
* **Response Payload:**
```json
{
  "consensus": true,
  "score": 92,
  "agents_feedback": {
    "security": "Clean - no secrets or CVEs found",
    "tech_debt": "Adheres to PEP8 standards",
    "story_match": "Satisfies user story requirements",
    "performance": "O(1) time complexity, minimal memory overhead"
  },
  "summary": "PR #142 meets all quality and security criteria. Approved for auto-merge."
}
```

---

### Contract 4: Ahmed (Gateway) → Nourhan (Portal & Docs)
* **Endpoint:** `POST http://localhost:8004/update-docs`
* **Request Payload:**
```json
{
  "repo": "AhmedAtia/ConsensusDev",
  "pr_number": 142,
  "status": "merged",
  "author": "Ahmed",
  "metrics": {
    "review_time_seconds": 4.2,
    "consensus_score": 92
  }
}
```
* **Response Payload:**
```json
{
  "docs_updated": true,
  "dashboard_refreshed": true
}
```

---

## 4. Individual Member "DO THIS NOW" Checklists

### 👑 Ahmed Atia (Team Leader & Gateway Lead)
1. **Environment Setup:**
   ```bash
   mkdir ConsensusDev && cd ConsensusDev
   git init
   python -m venv venv
   source venv/Scripts/activate  # (or source venv/bin/activate on Mac/Linux)
   pip install fastapi uvicorn httpx requests
   pip freeze > requirements.txt
   ```
2. **Scaffold Folder Structure:**
   * Create folders: `gateway/`, `ai_engine/`, `scanners/`, `qa_runner/`, `portal/`, `docs/`.
   * Create `.gitignore` (ignore `venv/`, `.env`, `__pycache__/`).
   * Create `.env.example` with placeholders for `GITHUB_TOKEN`, `WEBHOOK_SECRET`.
3. **Build Gateway Minimal Server:**
   * Code `gateway/main.py` with `@app.get("/health")` and `@app.post("/webhook/github")`.
   * Verify locally on `http://localhost:8000/docs`.
4. **Expose with ngrok:**
   ```bash
   ngrok http 8000
   ```
5. **GitHub Orchestration:**
   * Build `gateway/github_client.py` using `httpx` to query GitHub REST API, fetch diffs, create review comments, and trigger PR merges.

---

### 🤖 Mohammed Medhat (Multi-Agent AI Lead)
1. **Installation:**
   ```bash
   pip install fastapi uvicorn litellm langchain pydantic openai
   ```
2. **Directory Structure:**
   * `ai_engine/app.py` (FastAPI listener on port `8001`)
   * `ai_engine/agents/security_agent.py`
   * `ai_engine/agents/debt_agent.py`
   * `ai_engine/agents/story_agent.py`
   * `ai_engine/agents/perf_agent.py`
3. **Execution Rule:**
   * Each agent prompt takes the PR diff + static evidence and returns a structured JSON score and review comment.
   * Combine all 4 agent results into a consensus calculation (`consensus: true/false`).

---

### 🛡️ Soliman (DevSecOps Lead)
1. **Installation:**
   * Docker Desktop running.
   ```bash
   pip install checkov trivy-python fastapi uvicorn
   ```
2. **Directory Structure:**
   * `scanners/app.py` (FastAPI listener on port `8002`)
   * `scanners/checkov_runner.py`
   * `scanners/trivy_runner.py`
3. **Execution Rule:**
   * `POST /scan` takes the diff, writes it to a temporary file/folder, executes Checkov/Trivy via subprocess, parses output into JSON, and returns vulnerability counts.

---

### 🧪 Shahd Mostafa (QA Lead)
1. **Installation:**
   ```bash
   pip install fastapi uvicorn pytest pytest-cov mutmut
   ```
2. **Directory Structure:**
   * `qa_runner/app.py` (FastAPI listener on port `8003`)
   * `qa_runner/test_executor.py`
3. **Execution Rule:**
   * `POST /run-tests` executes tests programmatically via `pytest --cov`, calculates coverage percentage and mutation score, and returns clean JSON.

---

### 📊 Nourhan (Portal & Documentation Lead)
1. **Installation:**
   ```bash
   pip install streamlit mkdocs mkdocs-material fastapi uvicorn
   ```
2. **Directory Structure:**
   * `portal/app.py` (FastAPI listener on port `8004` with `/update-docs`)
   * `portal/streamlit_app.py` (Live DORA metrics dashboard)
   * `mkdocs.yml` & `docs/index.md` (Mermaid architecture diagrams & guides)
3. **Execution Rule:**
   * Run Streamlit on port `8501`. Display PR evaluation history, DORA MTTR, and review lead times.

---

## 5. Team Communication Protocol ("DONE CARD")

When any member completes their component, post this format to Discord/WhatsApp:

```
━━━━━━━━━━━━━━━━━━━━━━
✅ DONE CARD — [MEMBER NAME]
━━━━━━━━━━━━━━━━━━━━━━
Component: [e.g., Security Scanner Service]
Port: localhost:[XXXX]
Endpoint: POST /[endpoint_name]
Sample Input: { "diff": "..." }
Sample Output: { "status": "PASS", ... }
Local Test Status: PASSED (Verified via Postman)
Git Branch: feature/[role-branch]
Commit Hash: [abc1234]
Ready for Integration with Ahmed: YES
━━━━━━━━━━━━━━━━━━━━━━
```

---

## 6. Git Branching & Collaboration Strategy

* **Protected Branch:** `main` (Production only, auto-merged by ConsensusDev Gateway)
* **Feature Branches:**
  * `feature/ahmed-gateway`
  * `feature/medhat-ai`
  * `feature/soliman-security`
  * `feature/shahd-qa`
  * `feature/nourhan-portal`

### Git Command Cheat-Sheet (Git Bash)
```bash
# Clone and create branch
git clone https://github.com/AhmedAtia/ConsensusDev.git
cd ConsensusDev
git checkout -b feature/your-feature-name

# Daily commit workflow
git add .
git commit -m "feat: implement endpoint /your-endpoint"
git push origin feature/your-feature-name
```

---

## 7. 3-Minute Live Hackathon Demo Scenario

1. **Step 1 (The Bad PR):** Open a GitHub Pull Request with deliberate SQL Injection and zero unit tests.
2. **Step 2 (The Interception):** GitHub sends webhook → Ahmed's Gateway (`:8000`) intercepts event.
3. **Step 3 (Parallel Analysis):** Gateway calls Soliman (`:8002`) and Shahd (`:8003`). Security flags vulnerability; QA flags 0% coverage.
4. **Step 4 (AI Consensus):** Medhat's AI Engine (`:8001`) receives evidence, returns `consensus: false`.
5. **Step 5 (Automated Block):** Gateway posts line-by-line review comments on GitHub and locks the PR.
6. **Step 6 (The Good PR):** Developer pushes a fix with parameterized SQL and 100% test coverage.
7. **Step 7 (Auto-Merge & Docs):** All scans pass, AI consensus reaches `true` → PR is automatically merged → Nourhan's docs (`:8004`) update in real time.