# 🛡️ ConsensusDev — Autonomous Multi-Agent PR Review & DevSecOps Platform

**ConsensusDev** is an autonomous DevSecOps and code review gate. It intercepts GitHub Pull Requests via webhooks, executes concurrent static vulnerability and QA test scans, evaluates changes across four specialized AI reviewer agents, and synthesizes a weighted **Consensus Decision** to either approve auto-merge or block regressions and critical security flaws.

---

## 🏗️ Architecture & Microservices Topology

```
                  ┌─────────────────────────────────┐
                  │      GitHub Webhook Event       │
                  └────────────────┬────────────────┘
                                   │ HMAC-SHA256 Signed
                                   ▼
             ┌───────────────────────────────────────────┐
             │       ConsensusDev Gateway (:8000)        │
             │     Orchestrator, Bot & Store Cache       │
             └───────┬───────────────────────────┬───────┘
                     │                           │
         ┌───────────┴───────────┐   ┌───────────┴───────────┐
         │                       │   │                       │
         ▼                       ▼   ▼                       ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│ Security Scanner │    │    QA Runner     │    │ AI Review Engine │
│     (:8002)      │    │     (:8003)      │    │     (:8001)      │
│ Checkov + Trivy  │    │ Pytest + Mutmut  │    │ 4 Review Agents  │
└────────┬─────────┘    └────────┬─────────┘    └────────┬─────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │ Evidence & Findings
                                 ▼
                 ┌───────────────────────────────┐
                 │       Consensus Engine        │
                 │   (Score >= 80, 0 Crit CVEs)  │
                 └───────┬───────────────┬───────┘
                         │               │
                         ▼               ▼
         ┌──────────────────────┐ ┌──────────────────────┐
         │ React Dashboard      │ │ Portal & Docs        │
         │       (:3000)        │ │       (:8004)        │
         └──────────────────────┘ └──────────────────────┘
```

---

## 🔌 Microservices & Network Ports

| Service | Port | Primary Responsibilities & Endpoints |
| :--- | :---: | :--- |
| **Gateway Service** | `:8000` | Webhook HMAC verification, idempotency deduplication, parallel evidence dispatch, deterministic consensus gate enforcement, SHA race check, GitHub review posting, and auto-merge.<br>`POST /webhook/github`, `GET /health`, `GET /api/health`, `GET /api/pull-requests`, `GET /api/logs`, `GET /api/agents`, `POST /api/reviews/trigger` |
| **AI Consensus Engine** | `:8001` | Multi-agent LLM review synthesis across 4 specialized agents (Security: 40%, Tech Debt: 20%, Story Match: 20%, Performance: 20%).<br>`GET /health`, `POST /analyze-pr` |
| **Security Scanner** | `:8002` | Checkov (IaC/SAST) & Trivy (CVE/Secrets) dual scanning engine returning structured findings.<br>`GET /health`, `POST /scan` |
| **QA Test Runner** | `:8003` | Sandboxed test execution, code coverage calculation, and mutation score analyzer.<br>`GET /health`, `POST /run-tests` |
| **Portal & Docs** | `:8004` | Live DORA telemetry, PR changelog compilation, and architecture documentation.<br>`GET /health`, `GET /docs`, `GET /metrics`, `POST /update-docs` |
| **React Frontend** | `:3000` | Real-time cybernetic DevSecOps console with live telemetry, PR inspections, and simulation triggers. |

---

## ⚡ Quickstart

### 1. Prerequisites
- Python 3.10+
- Node.js 18+ & npm

### 2. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

### 3. Start All 6 Services Concurrently
```bash
python start_services.py
```
This starts:
- 🌐 **Frontend Dashboard**: [http://localhost:3000/](http://localhost:3000/)
- 🚪 **Gateway Orchestrator**: [http://localhost:8000/](http://localhost:8000/)
- 🧠 **AI Consensus Engine**: [http://localhost:8001/](http://localhost:8001/)
- 🔍 **Security Scanner**: [http://localhost:8002/](http://localhost:8002/)
- 🧪 **QA Test Runner**: [http://localhost:8003/](http://localhost:8003/)
- 📚 **Portal & Docs**: [http://localhost:8004/](http://localhost:8004/)

---

## 🧪 Automated Testing

### Run Complete Pytest Test Suite:
```bash
.venv\Scripts\python.exe -m pytest tests -s -v
```

### Run Live Demonstration Review:
```bash
.venv\Scripts\python.exe tests/run_live_demo.py
```

### Build Frontend Production Bundle:
```bash
cd frontend && npm run build
```

---

## 📊 Deterministic Consensus & Auto-Merge Formula

Auto-merge is granted **only if all deterministic gates pass**:
$$\text{Consensus Score} = 0.40 \times \text{Security} + 0.20 \times \text{TechDebt} + 0.20 \times \text{StoryMatch} + 0.20 \times \text{Performance} \ge 80$$
$$\text{Security Gate} == \text{PASS} \quad (\text{Vulnerabilities} == 0)$$
$$\text{QA Gate} == \text{PASS} \quad (\text{Tests Failed} == 0 \land \text{Evidence Available})$$
$$\text{Head SHA Verified} \quad (\text{Reviewed SHA} == \text{Current GitHub Head SHA})$$
$$\text{Branch Status Checks} == \text{SUCCESS}$$
