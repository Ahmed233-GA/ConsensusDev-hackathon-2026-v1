# CONSENSUSDEV
## Soliman Handoff & Complete Execution Guide

Detailed handoff: what is built, what is not built, how the services connect, what Soliman should continue, and how the team integrates safely.

---

### System Overview & Port Mapping

| Item | Current State |
| :--- | :--- |
| **Gateway** | `8000` — foundation verified |
| **AI Engine** | `8001` — foundation + initial services |
| **Security (Soliman)** | `8002` — **Soliman's pending service** |
| **QA (Shahd)** | `8003` — Shahd |
| **Portal (Nourhan)** | `8004` — Nourhan |

> [!IMPORTANT]
> A planned component is not treated as complete unless it is implemented and verified.

---

## 1. Executive Summary

ConsensusDev is a multi-agent autonomous code-review and security gate. A Pull Request triggers a webhook, the Gateway collects the diff, security and QA services provide evidence, the AI Engine evaluates the change with four specialist agents, and a zero-trust gate either blocks the PR with feedback or allows merge. The documentation/dashboard layer is updated after a successful merge.

### High-Level Status

| Area | Status | Meaning |
| :--- | :--- | :--- |
| **GitHub repository** | `DONE` | Created and connected. |
| **main branch** | `DONE` | Clean and synced. |
| **Gateway foundation** | `DONE` | FastAPI/Uvicorn; `/`, `/health`, `/docs` verified. |
| **AI Engine foundation** | `DONE` | FastAPI app and initial services committed. |
| **Security scanner** | `NOT DONE` | **Soliman's core deliverable remains.** |
| **QA runner** | `NOT DONE` | Owned by Shahd. |
| **Full integration** | `NOT STARTED` | Waiting for service implementations/contracts. |
| **End-to-end Happy Path**| `NOT STARTED` | Future milestone. |

---

## 2. Complete System Architecture

The mental model is simple: 
- **Gateway** = glue
- **Soliman & Shahd** = evidence providers
- **AI Engine** = reasoning
- **Ahmed** = final Git decision
- **Nourhan** = portal/docs

```
Developer PR
 │
 ▼
GitHub ──webhook──► Ahmed Gateway :8000
 │
 ┌───────┴────────┐
 │ parallel calls │
 ▼                ▼
 Soliman :8002    Shahd :8003
 Security         QA
 │                │
 └───────┬────────┘
         ▼
    AI Engine :8001
    Security / Debt / Story / Perf
         │
    consensus true/false
         ▼
    Ahmed Decision Gate
        / \
   false   true
     │       │
comments+block merge
             │
             ▼
        Nourhan :8004
        Portal / Docs
```

### Why Soliman Matters
Soliman's scanner produces deterministic security/code-quality evidence. It does not make the final merge decision; its findings become evidence for the AI review stage.

---

## 3. What Ahmed Built

### Git Foundation
- **Remote**: `https://github.com/Ahmed233-GA/ConsensusDev-hackathon-2026-v1.git`
- **Main**: `f36f159` — chore: initialize ConsensusDev project
- **Gateway**: `feature/ahmed-gateway` (FastAPI foundation on port 8000)
- **AI Engine**: `feature/ahmed-ai-engine` (commit `3ab3e9d`, FastAPI app on port 8001)

---

## 4. Soliman's Exact Scope

**Role**: Code Analysis & DevSecOps Lead: build a containerized static-analysis/security pipeline, run SAST/IaC tools, and return structured findings.

### Deliverables

| Deliverable | Purpose | Status |
| :--- | :--- | :--- |
| `scanners/app.py` | FastAPI `POST /scan` | NOT DONE |
| `checkov_runner.py` / scanner modules | Run Checkov / SAST / IaC security checks | NOT DONE |
| `Dockerfile` | Containerize scanner | NOT DONE |
| Stable JSON | Predictable integration output | NOT DONE |
| Checkov | IaC/security evidence | NOT DONE |
| Trivy | Vulnerability scanning | TARGET |
| SonarQube | Code quality/debt evidence | TARGET |
| AI-ready evidence | Findings consumed by AI | NOT DONE |

### Documented Contract
- **Endpoint**: `POST http://localhost:8002/scan`
- **Input**:
  ```json
  {
    "diff": "string"
  }
  ```
- **Target Response Structure**:
  ```json
  {
    "vulnerabilities": 0,
    "status": "PASS",
    "vulnerabilities_count": 0,
    "critical_issues": [],
    "details": []
  }
  ```

---

## 5. How Soliman Connects to the Team

| From | To | Handoff Payload |
| :--- | :--- | :--- |
| **Ahmed (Gateway)** | **Soliman (Security)** | `{"diff": "..."}` |
| **Soliman (Security)**| **Ahmed (Gateway)** | Security JSON report |
| **Soliman (Security)**| **AI Engine** | Security findings as structured evidence |

---

## 6. Soliman Verification Checklist

- [ ] **Branch**: `feature/soliman-scanners`
- [ ] **Service**: Starts without import errors (`uvicorn scanners.app:app --reload --port 8002`)
- [ ] **Port**: `8002`
- [ ] **Endpoint**: `POST /scan`
- [ ] **Input**: Documented diff JSON (`{"diff": "..."}`)
- [ ] **Output**: Stable documented JSON (`status`, `vulnerabilities_count`, `critical_issues`, etc.)
- [ ] **Safe sample**: Pass / clean evidence
- [ ] **Vulnerable sample**: Actual security finding identified
- [ ] **Secrets**: No tokens/keys committed
- [ ] **Docker**: `Dockerfile` builds and runs cleanly
- [ ] **Notion / Handoff**: Full handoff record documented

---

## 7. Definition of Done

For this team, **Done** means:
`CODED` → `RUNNABLE` → `TESTED` → `VERIFIED` → `DOCUMENTED` → `PUSH + PR` → `REVIEW / MERGE`

---

## 8. Step-by-Step Execution Order for Soliman

1. **Create Scanner Structure**: Directory `scanners/` with `app.py`, runners, and schemas.
2. **Implement FastAPI `/scan` Endpoint**: Expose `POST /scan` on port `8002`.
3. **Implement Scanner Logic**: Parse diff / files and run security checks (SAST / Checkov / custom security rules).
4. **Stabilize JSON Output**: Ensure consistent response schema that Gateway and AI Engine can consume.
5. **Test Safe & Vulnerable Diff Samples**: Verify clean pass for safe PRs and detection for vulnerable PRs.
6. **Containerization**: Create `Dockerfile` for the scanners service.
7. **Commit & Push**: Commit work to `feature/soliman-scanners` and push to remote.
