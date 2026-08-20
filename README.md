# 🛡️ Consensus Dev — Autonomous Multi-Agent PR Review Platform

**Consensus Dev** is an autonomous DevSecOps and code review gate. It intercepts GitHub Pull Requests via webhooks, executes concurrent static vulnerability and test scans, evaluates changes across four specialized AI reviewer agents, and synthesizes a weighted **Consensus Decision** to either approve auto-merge or block regressions and critical security flaws.

---

## 🏗️ Architecture & Microservices Topology

```
                  ┌─────────────────────────────────┐
                  │      GitHub Webhook Event       │
                  └────────────────┬────────────────┘
                                   │
                                   ▼
             ┌───────────────────────────────────────────┐
             │       ConsensusDev Gateway (:8000)        │
             │   (Ahmed - Orchestrator & GitHub Bot)     │
             └───────┬───────────────────────────┬───────┘
                     │                           │
         ┌───────────┴───────────┐   ┌───────────┴───────────┐
         │                       │   │                       │
         ▼                       ▼   ▼                       ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│ Security Scanner │    │    QA Runner     │    │ AI Review Engine │
│  (Soliman :8002) │    │  (Shahd :8003)   │    │  (Medhat :8001)  │
│ Checkov + Trivy  │    │ Pytest + Mutmut  │    │ 4 Review Agents  │
└────────┬─────────┘    └────────┬─────────┘    └────────┬─────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │ Evidence & Findings
                                 ▼
                 ┌───────────────────────────────┐
                 │       Consensus Engine        │
                 │   (Threshold >= 80, 0 CVEs)   │
                 └───────────────┬───────────────┘
                                 │
                                 ▼
                 ┌───────────────────────────────┐
                 │     React Dashboard (:3000)   │
                 │ (Nourhan / Consensus Frontend)│
                 └───────────────────────────────┘
```

---

## ⚡ Quickstart

### 1. Prerequisites
- Python 3.10+
- Node.js 18+ & npm

### 2. Install Dependencies
```bash
# Python backend & testing dependencies
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt

# React frontend dependencies
cd frontend
npm install
cd ..
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Ensure your `OPENROUTER_API_KEY` (or `OPENAI_API_KEY`) and optional `GITHUB_TOKEN` are set.

### 4. Start All Services with One Command
```bash
python start_services.py
```
This concurrently starts:
- 🌐 **Frontend Dashboard**: [http://localhost:3000/](http://localhost:3000/)
- 🚪 **Gateway Orchestrator**: [http://localhost:8000/](http://localhost:8000/)
- 🧠 **AI Consensus Engine**: [http://localhost:8001/](http://localhost:8001/)
- 🔍 **Security Scanner**: [http://localhost:8002/](http://localhost:8002/)

---

## 🧪 Automated Testing

Execute the comprehensive end-to-end test suite:
```bash
pytest -s tests/
```

### Run Live PR Analysis Demo:
```bash
python tests/run_live_demo.py
```

---

## 📊 Consensus Scoring Formula

$$\text{Score} = 0.40 \times \text{Security} + 0.20 \times \text{TechDebt} + 0.20 \times \text{Architecture} + 0.20 \times \text{QA}$$

### Blocking Rules:
1. **Zero Critical Vulnerabilities**: Any critical CVE or hardcoded secret blocks auto-merge immediately.
2. **100% Test Pass Rate**: Zero failing unit tests.
3. **Minimum Consensus Threshold**: Overall score must be $\ge 80 / 100$.

---

## 📁 Repository Structure

```
├── ai_engine/          # Medhat: AI Agent orchestration & consensus logic
│   ├── agents/         # Security, Tech Debt, Story, Perf, Consensus
│   ├── services/       # Review service pipeline
│   └── main.py         # FastAPI service (Port 8001)
├── frontend/           # React + TypeScript + Tailwind CSS Dashboard (Port 3000)
│   ├── src/components/ # PRHeaderBar, ConsensusScoreCard, AgentCards, FindingsTabs
│   └── src/pages/      # PullRequestPage, Dashboard, Agents, Pipelines, Logs
├── gateway/            # Ahmed: Webhook receiver & microservice orchestrator (Port 8000)
├── scanners/           # Soliman: Checkov & Trivy SAST scanners (Port 8002)
├── tests/              # Full unit, integration, and live demo test suite
├── start_services.py   # Unified multi-service launcher
└── requirements.txt    # Production & test dependencies
```
