# ConsensusDev — Multi-Agent Autonomous Code Review & Security Gate

**DevOpsDays Cairo 2026 Hackathon · Team Track 2 (Accelerate Dev)**

ConsensusDev is an AI-powered pull request review system where 4 specialized AI agents — **Security**, **Technical Debt**, **Story Matching**, and **Performance** — debate every PR and reach a consensus decision (approve / request_changes) in seconds.

This repo contains **two demo surfaces**:

| Surface | What it is | Tech |
|---------|-----------|------|
| **Interactive Dashboard** (primary demo) | A polished, animated web UI that simulates the full multi-agent pipeline live in the browser — no backend required. | React + TypeScript + Tailwind + Vite |
| **Python Backend + Streamlit** (team reference impl) | The real FastAPI webhook server, Streamlit dashboard, and `demo.py` script that the team can run locally with the Anthropic API. | FastAPI + Streamlit + Anthropic SDK |

---

## Quick start — Interactive Dashboard (no backend needed)

```bash
npm install
npm run dev
```

Open the app, click **"Run Live Demo"**. Three sample PRs will flow through the pipeline in real time:
1. **PR #142 (clean)** — checkout validation → all agents approve
2. **PR #143 (risky)** — hardcoded secret + SQL injection → Security & Tech Debt agents block it
3. **PR #144 (performance)** — lazy-load + memoization → approved with positive perf note

---

## Quick start — Python Backend + Streamlit

### Prerequisites

```bash
pip install -r requirements.txt
```

Set your Anthropic API key (optional — if not set, the backend uses a deterministic offline fallback):

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Run (two terminals)

**Terminal 1 — Backend:**
```bash
uvicorn backend:app --reload --port 8000
```

**Terminal 2 — Streamlit dashboard:**
```bash
streamlit run dashboard.py
```

**Terminal 3 — Run the live demo (sends 3 sample PRs):**
```bash
python demo.py
```

The demo script opens the Streamlit dashboard in your browser, then sends the clean PR (approved), the risky PR (blocked — SQL injection + hardcoded secret flagged), and a performance PR (approved).

---

## Architecture

```
GitHub/Forgejo Webhook
        │
        ▼
  ┌─────────────┐     ┌──────────────┐
  │  FastAPI     │────▶│  /mock-scan   │  (SonarQube / Trivy / Checkov / Semgrep)
  │  /webhook    │     │  static scan  │
  └──────┬──────┘     └──────┬───────┘
         │                    │
         ▼                    ▼
  ┌──────────────────────────────────┐
  │     Multi-Agent LLM (Claude)      │
  │  ┌─────────┐ ┌─────────┐         │
  │  │ Security│ │ TechDebt│         │
  │  └─────────┘ └─────────┘         │
  │  ┌─────────┐ ┌─────────┐         │
  │  │  Story  │ │  Perf   │         │
  │  └─────────┘ └─────────┘         │
  │          → Consensus (majority)   │
  └──────────────┬───────────────────┘
                 │
                 ▼
  ┌──────────────────────────────────┐
  │  In-memory store  ◀── /prs       │
  │                   ◀── /metrics   │
  └──────────────┬───────────────────┘
                 │
                 ▼
  ┌──────────────────────────────────┐
  │     Streamlit Dashboard           │
  │  Metrics · Agent verdicts · Findings │
  └──────────────────────────────────┘
```

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/webhook` | Receives `{ pr_number, repo_name, diff_text, title, branch, author }`, runs scan + multi-agent review, returns verdict |
| `GET` | `/mock-scan?diff_text=...` | Returns fake static-analysis findings (2 vulnerabilities, 1 code smell) |
| `GET` | `/prs` | Returns all stored PR results |
| `GET` | `/metrics` | Returns aggregate metrics (total reviewed, approval rate, avg review time, vulns caught) |
| `GET` | `/health` | Health check |

---

## Team Roles

| Member | Role | Responsibility |
|--------|------|----------------|
| **Mohammed Medhat** | Multi-Agent AI Lead | The 4-agent LLM prompt + consensus logic (`backend.py`) |
| **Ahmed Atia** | CI/CD & Git Automation Lead | Webhook endpoint + PR event handling (`/webhook`) |
| **Soliman** | Code Analysis & DevSecOps Lead | Static analysis / mock-scan findings (`/mock-scan`) |
| **Shahd Mostafa Depi** | Test & QA Specialist | Test execution + coverage (extension point in pipeline) |
| **Nourhan** | Dev Portal & Pitch Lead | Streamlit dashboard + MkDocs + presentation deck |

---

## 3-Minute Live Demo Script

> **What to say during the demo:**

**0:00 — Intro (15s)**
> "ConsensusDev is a multi-agent AI system that reviews every pull request through 4 specialized agents — Security, Technical Debt, Story Matching, and Performance — and reaches a consensus decision before code can merge."

**0:15 — Open the dashboard (15s)**
> *Click "Run Live Demo" on the interactive dashboard.*
> "Here's the pipeline monitor. Each PR flows through webhook → static scan → AI agent debate → consensus."

**0:30 — Clean PR (30s)**
> *Point to PR #142 as it flows through.*
> "First, a clean PR — checkout form validators. The static scanner finds zero issues. All 4 agents approve. Consensus: approved. This PR can auto-merge."

**1:00 — Risky PR (60s)**
> *Point to PR #143.*
> "Now the risky one — a user search endpoint. Watch the static scanner flag two critical findings: a **hardcoded API key** and a **SQL injection vulnerability** from string interpolation. The Security agent blocks it, Tech Debt flags the legacy pattern. Only Story and Performance approve — that's 2 out of 4, short of the majority. Consensus: **request changes**. This PR is blocked."

**2:00 — Performance PR (30s)**
> *Point to PR #144.*
> "Finally, a performance optimization PR — lazy loading and memoization. The Performance agent notes the positive impact. All agents approve. Consensus: approved."

**2:30 — Metrics & wrap-up (30s)**
> *Point to the metric cards at the top.*
> "In just seconds, we reviewed 3 PRs: 2 approved, 1 blocked, 3 critical vulnerabilities caught — with an average review time under 4 seconds. ConsensusDev brings multi-agent AI review to every pull request, catching security issues before they reach production."

---

## Tech Stack

- **AI**: Anthropic Claude (`claude-sonnet-4-6`) — 4-agent system prompt returning structured JSON
- **Backend**: FastAPI + Pydantic + Uvicorn
- **Dashboard**: Streamlit (Python) / React + Tailwind (interactive)
- **Static Analysis**: Simulated SonarQube / Trivy / Checkov / Semgrep findings
- **No database**: Everything in-memory for the demo
