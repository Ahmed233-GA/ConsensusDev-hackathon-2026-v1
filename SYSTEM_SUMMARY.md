# 🛡️ Consensus Dev — Complete System Summary & Architecture Specification

**Consensus Dev** is an autonomous DevSecOps and code review gate platform. It intercepts GitHub Pull Requests via webhooks, executes concurrent static security scans and automated test suites, dispatches code diffs across four specialized AI review agents, and synthesizes a weighted **Consensus Decision** to either approve auto-merge or block security flaws and regressions.

---

## 🏗️ 1. Microservices Architecture & Port Topology

The system is architected as an event-driven, decoupled microservices mesh:

```
                            ┌─────────────────────────────────┐
                            │    GitHub PR Webhook Event      │
                            └────────────────┬────────────────┘
                                             │
                                             ▼
                      ┌──────────────────────────────────────────────┐
                      │        Consensus Gateway (Port 8000)         │
                      │       Orchestrator & GitHub Bot Client       │
                      └──────┬───────────────┬───────────────┬───────┘
                             │               │               │
                 ┌───────────┘               │               └───────────┐
                 ▼                           ▼                           ▼
      ┌────────────────────┐      ┌────────────────────┐      ┌────────────────────┐
      │  Security Scanner  │      │     QA Runner      │      │ AI Consensus Engine│
      │    (Port 8002)     │      │    (Port 8003)     │      │    (Port 8001)     │
      │  Checkov + Trivy   │      │  Pytest + Mutmut   │      │ 4 Reviewer Agents  │
      └──────────┬─────────┘      └──────────┬─────────┘      └──────────┬─────────┘
                 │                           │                           │
                 └───────────────────────────┼───────────────────────────┘
                                             │ Aggregated Evidence
                                             ▼
                              ┌──────────────────────────────┐
                              │       Consensus Engine       │
                              │    (Score >= 80, 0 CVEs)     │
                              └──────────────┬───────────────┘
                                             │
                                             ▼
                              ┌──────────────────────────────┐
                              │    React Frontend (:3000)    │
                              │  Dashboard, Diffs, Telemetry │
                              └──────────────────────────────┘
```

| Service | Port | Primary Responsibility | Key Technologies |
| :--- | :---: | :--- | :--- |
| **Gateway Orchestrator** | `8000` | Webhook verification (HMAC-SHA256), parallel service dispatch, GitHub bot comments, auto-merge, and store persistence. | FastAPI, Async HTTPX, GitHub REST API, Pydantic |
| **AI Consensus Engine** | `8001` | Multi-agent prompt evaluation, structured JSON consensus generation. | FastAPI, OpenRouter / OpenAI / GPT-4o Mini |
| **Security Scanner** | `8002` | SAST, IaC misconfigurations, secret scanning, CVE detection. | Checkov, Trivy, Built-in Regex SAST |
| **QA Runner** | `8003` | Automated unit testing, mutation testing, test coverage analysis. | Pytest, Mutmut, Coverage.py |
| **Portal & Docs** | `8004` | DORA telemetry, live documentation, PR changelog compilation. | FastAPI, Markdown, Swagger |
| **Frontend Portal** | `3000` | Real-time UI dashboard, circular progress gauges, drill-down findings, live logs. | React 19, TypeScript, Vite, Tailwind CSS |

---

## 🤖 2. The 4 Specialized AI Reviewer Agents

Instead of generic monolithic reviews, Consensus Dev divides analysis among four specialized agents:

```
┌─────────────────────────┐  ┌─────────────────────────┐  ┌─────────────────────────┐  ┌─────────────────────────┐
│    Security Auditor     │  │  Code Quality Reviewer  │  │  Architecture Evaluator │  │   QA & Mutation Guard   │
│       Weight: 40%       │  │       Weight: 20%       │  │       Weight: 20%       │  │       Weight: 20%       │
│  SAST, Secrets, & CVEs  │  │  PEP8 & Tech Debt Guard │  │ Domain Boundary & Specs │  │ Coverage & Test Passes  │
└─────────────────────────┘  └─────────────────────────┘  └─────────────────────────┘  └─────────────────────────┘
```

1. **Security Auditor (40% Weight — Blocking Gate)**:
   - Evaluates Checkov & Trivy findings, detects SQL injection, hardcoded API keys, and insecure dependencies.
   - Any critical vulnerability triggers an immediate blocking veto.
2. **Code Quality Reviewer (20% Weight)**:
   - Evaluates PEP8 style, type safety, cyclomatic/cognitive complexity ($< 10$), and bare exception handling.
3. **Architecture Evaluator (20% Weight)**:
   - Enforces domain boundaries, modular design, idempotency on webhook handlers, and zero circular imports.
4. **QA & Mutation Guard (20% Weight — Blocking Gate)**:
   - Analyzes test results, calculates code coverage ($\ge 80\%$), and inspects mutation kill scores.

---

## ⚖️ 3. Consensus Decision Formula & Blocking Rules

### Weighted Consensus Score:
$$\text{Score} = 0.40 \times \text{Security} + 0.20 \times \text{CodeQuality} + 0.20 \times \text{Architecture} + 0.20 \times \text{QA}$$

### 🛑 Non-Negotiable Blocking Gates:
1. **Zero Critical Vulnerabilities**: Auto-merge is blocked if any critical CVE or exposed secret is found.
2. **100% Test Pass Rate**: Zero failing test cases allowed.
3. **Minimum Score Threshold**: The aggregated score must be **$\ge 80 / 100$** for approval.

---

## 💻 4. Frontend Portal Features (`http://localhost:3000`)

- **PR Review View**:
  - **PR Meta Strip**: Author (`Ahmed233`), Commit hash (`8f2a1c9`), Source branch (`source: feature/auth`).
  - **Consensus Score Card**: Custom stroke-based SVG circular progress ring, centered `88 / 100` score, `APPROVED` badge, and 3 sub-cells (`Security Gate: Passed`, `QA Gate: Passed`, `Evidence: Verified`).
  - **4-Agent Score Grid**: Dynamic cards with score gauges, weights, and agent rationales.
  - **4 Drill-Down Tabs**:
    - 🔒 **Security & Vulnerability**: Severity stat cards (`0 Critical`, `2 High`, `5 Medium`) and findings table (`Checkov`, `Trivy`, `SonarQube`, `main.tf`, `package.json`, `jwt_service.ts`).
    - 🧪 **QA & Test**: Suite breakdowns, 82% coverage gauge, 88% mutation score.
    - 📄 **Diff Inspector**: Syntax-highlighted unified diff viewer.
    - 🌐 **System Arch**: Microservices topology diagram and scoring formula breakdown.
- **Interactive Navigation**:
  - Sidebar buttons (`Security`, `Code Quality`, `Architecture`, `QA`, `System Health`) smoothly scroll and switch the drill-down view.
- **Operational Pages**:
  - `/pull-requests`: Filterable list of all PR reviews.
  - `/dashboard`: High-level throughput, approval rates, latency statistics.
  - `/agents`: Agent prompt templates, model configurations, and vote weight adjustments.
  - `/pipelines`: Interactive end-to-end CI/CD pipeline simulation.
  - `/logs`: Streaming real-time audit log terminal.

---

## 📁 5. Directory Structure

```
├── ai_engine/          # Medhat: AI Agent orchestration & consensus logic
│   ├── agents/         # Security, Tech Debt, Story, Perf, Consensus
│   ├── services/       # Review service pipeline
│   └── main.py         # FastAPI service (Port 8001)
├── frontend/           # React + TypeScript + Tailwind CSS Dashboard (Port 3000)
│   ├── src/components/ # PRHeaderBar, ConsensusScoreCard, AgentCards, FindingsTabs
│   ├── src/context/    # NavigationContext for sidebar state & tabs
│   └── src/pages/      # PullRequestPage, Dashboard, Agents, Pipelines, Logs
├── gateway/            # Ahmed: Webhook receiver & microservice orchestrator (Port 8000)
├── scanners/           # Soliman: Checkov & Trivy SAST scanners (Port 8002)
├── tests/              # Full unit, integration, and live demo test suite
├── start_services.py   # Unified multi-service launcher
└── requirements.txt    # Production & test dependencies
```

---

## ⚡ 6. How to Run and Test

### 1. Launch All Services (One Command):
```bash
python start_services.py
```

### 2. Run the Automated Test Suite (17/17 Passed):
```bash
pytest -s tests/
```

### 3. Run the End-to-End Live PR Analysis Demo:
```bash
python tests/run_live_demo.py
```
- **Bad PR (SQL Injection + 0% Coverage)** $\rightarrow$ **Blocked** (`Score: 28/100`, specific CWE-89 remediation suggestions).
- **Good PR (Clean Code + 95% Coverage)** $\rightarrow$ **Approved for Auto-Merge** (`Score: 95/100`).
