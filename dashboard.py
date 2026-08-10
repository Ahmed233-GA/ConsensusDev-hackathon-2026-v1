"""
ConsensusDev — Streamlit Dashboard
Polls the FastAPI backend for stored PR results and displays live metrics,
agent verdicts, and security findings.

Run:
    streamlit run dashboard.py
"""

from __future__ import annotations

import time

import requests
import streamlit as st

BACKEND_URL = "http://localhost:8000"

st.set_page_config(
    page_title="ConsensusDev — AI PR Review",
    page_icon="🔍",
    layout="wide",
)

st.markdown("""
<style>
    .stApp { background: #070a14; }
    .metric-card {
        background: linear-gradient(180deg, #131a2e, #0b0f1c);
        border: 1px solid #1a2340;
        border-radius: 16px;
        padding: 1.2rem;
    }
</style>
""", unsafe_allow_html=True)

st.title("🔍 ConsensusDev — Multi-Agent PR Review")
st.caption("Autonomous code review & security gate · DevOpsDays Cairo 2026")

# ---- Refresh button + auto-poll -----------------------------------------
col1, col2 = st.columns([1, 5])
with col1:
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()
with col2:
    auto = st.checkbox("Auto-refresh every 3s", value=True)

# ---- Fetch data ---------------------------------------------------------
@st.cache_data(ttl=3)
def fetch_metrics():
    try:
        r = requests.get(f"{BACKEND_URL}/metrics", timeout=5)
        return r.json() if r.ok else None
    except Exception:
        return None


@st.cache_data(ttl=3)
def fetch_prs():
    try:
        r = requests.get(f"{BACKEND_URL}/prs", timeout=5)
        return r.json().get("prs", []) if r.ok else []
    except Exception:
        return []


metrics = fetch_metrics()
prs = fetch_prs()

if metrics is None:
    st.warning("Backend not reachable. Start it with: `uvicorn backend:app --port 8000`")
    st.stop()

# ---- Metric cards -------------------------------------------------------
m1, m2, m3, m4 = st.columns(4)
m1.metric("PRs Reviewed", metrics["total_reviewed"])
m2.metric("Approval Rate", f"{metrics['approval_rate']}%")
m3.metric("Avg Review Time", metrics["avg_review_time_label"])
m4.metric("Vulns Caught", metrics["vulnerabilities_caught"])

st.divider()

# ---- Most recent PR -----------------------------------------------------
if not prs:
    st.info("No PRs yet. Run `python demo.py` to simulate a pull request.")
else:
    latest = prs[0]
    st.subheader(f"Latest PR #{latest['pr_number']} — {latest.get('title', '')}")

    # Consensus banner
    verdict = latest["consensus"]
    if verdict == "approve":
        st.success(f"✅ CONSENSUS: APPROVE — {latest.get('consensus_reason', '')}")
    else:
        st.error(f"❌ CONSENSUS: REQUEST CHANGES — {latest.get('consensus_reason', '')}")

    # Agent verdicts
    st.markdown("### 🤖 Agent Verdicts")
    cols = st.columns(4)
    agent_labels = {
        "security": "🔐 Security",
        "tech_debt": "🔧 Tech Debt",
        "story": "📖 Story",
        "performance": "⚡ Performance",
    }
    for i, (key, label) in enumerate(agent_labels.items()):
        agent = latest.get("agents", {}).get(key, {})
        with cols[i]:
            v = agent.get("verdict", "—")
            icon = "✅" if v == "approve" else "❌"
            st.markdown(f"**{label}**  `{v}`")
            st.caption(agent.get("reason", ""))

    # Security findings
    st.markdown("### 🛡️ Static Analysis Findings")
    findings = latest.get("findings", [])
    if findings:
        for f in findings:
            sev = f["severity"].upper()
            color = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(sev, "⚪")
            st.markdown(f"{color} **[{sev}] {f['title']}** — `{f['tool']}` · `{f['file']}:{f['line']}`")
            st.caption(f["description"])
    else:
        st.info("No findings.")

    # Diff
    with st.expander("View code diff"):
        st.code(latest.get("diff_text", ""), language="diff")

# ---- History table ------------------------------------------------------
if prs:
    st.divider()
    st.subheader("📋 PR History")
    st.dataframe(
        [
            {
                "PR": f"#{p['pr_number']}",
                "Title": p.get("title", ""),
                "Consensus": p["consensus"],
                "Review Time": f"{p['review_time_ms'] / 1000:.1f}s",
                "Findings": len(p.get("findings", [])),
            }
            for p in prs
        ],
        use_container_width=True,
        hide_index=True,
    )

# ---- Auto-refresh -------------------------------------------------------
if auto:
    time.sleep(3)
    st.rerun()
