"""
ConsensusDev -- Admin Dashboard (v2)
Single-page, top-to-bottom admin view. Polls the FastAPI backend for
stored PR results and renders metrics, the latest verdict, agent
findings, and PR history as one scrollable page.

Run:
    streamlit run dashboard.py
"""

from __future__ import annotations
import time
import requests
import streamlit as st

BACKEND_URL = "http://localhost:8004"
POLL_INTERVAL = 5

def backend_alive() -> bool:
    """Check if backend is reachable."""
    try:
        return requests.get(f"{BACKEND_URL}/health", timeout=2).ok
    except Exception:
        return False

def fetch_metrics() -> dict:
    """Fetch metrics from backend."""
    try:
        r = requests.get(f"{BACKEND_URL}/metrics", timeout=3)
        return r.json() if r.ok else {}
    except Exception:
        return {}

def fetch_prs() -> list:
    """Fetch PR list from backend."""
    try:
        r = requests.get(f"{BACKEND_URL}/prs", timeout=3)
        return r.json().get("prs", []) if r.ok else []
    except Exception:
        return []

def vc(v) -> str:
    """Normalize verdict string to 'a' (approve) or 'r' (request_changes)."""
    return "a" if str(v).lower() == "approve" else "r"

AGENT_META = {
    "security":    {"label": "Security",    "icon": "&#128274;"},
    "tech_debt":   {"label": "Tech Debt",   "icon": "&#128296;"},
    "story":       {"label": "Story Match", "icon": "&#128214;"},
    "performance": {"label": "Performance", "icon": "&#9889;"},
}

st.set_page_config(
    page_title="ConsensusDev - Admin",
    page_icon="🔍",
    layout="centered",
    initial_sidebar_state="collapsed",
)

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: #0a0e14; color: #e0e6f0; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1.5rem; padding-bottom: 3rem; max-width: 880px; }
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0d1117; }
::-webkit-scrollbar-thumb { background: #1abc9c44; border-radius: 3px; }

/* buttons used for control rows only, kept minimal */
.stButton > button {
    background: #0d1117 !important; border: 1px solid #1a2340 !important;
    color: #7888a0 !important; border-radius: 8px !important;
    font-size: 0.78rem !important; padding: 0.35rem 0.9rem !important;
}
.stButton > button:hover { border-color: #1abc9c66 !important; color: #1abc9c !important; }

/* ---- Header / branding ---- */
.cd-header {
    display: flex; align-items: center; justify-content: space-between;
    background: linear-gradient(135deg, #0d1117 0%, #101820 100%);
    border: 1px solid #1a2340; border-radius: 16px;
    padding: 1.1rem 1.5rem; margin-bottom: 1.5rem;
}
.cd-logo-wrap { display: flex; align-items: center; gap: 0.75rem; }
.cd-logo {
    width: 40px; height: 40px;
    background: linear-gradient(135deg, #1abc9c, #0e8c6a);
    border-radius: 10px; display: flex; align-items: center; justify-content: center;
    font-size: 1rem; font-weight: 700; color: #fff; box-shadow: 0 0 16px #1abc9c33;
}
.cd-title { font-size: 1.15rem; font-weight: 700; color: #fff; }
.cd-subtitle { font-size: 0.75rem; color: #5a6a7e; margin-top: 1px; }
.cd-env { border-radius: 999px; padding: 3px 12px; font-size: 0.68rem; font-weight: 700; letter-spacing: 0.5px; }
.env-live { background: #1abc9c1a; color: #1abc9c; border: 1px solid #1abc9c44; }
.env-off  { background: #1a2340; color: #5a6a7e; border: 1px solid #2a3450; }

/* ---- Section labels ---- */
.sh {
    font-size: 0.7rem; font-weight: 700; letter-spacing: 1.2px;
    text-transform: uppercase; color: #1abc9c;
    margin: 2rem 0 0.85rem 0;
    display: flex; align-items: center; gap: 0.5rem;
}
.sh::after { content: ''; flex: 1; height: 1px; background: linear-gradient(90deg, #1abc9c33, transparent); }
.sh.first { margin-top: 0; }

/* ---- KPI row ---- */
.kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.75rem; }
.kpi-card {
    background: linear-gradient(160deg, #131a2e 0%, #0b0f1c 100%);
    border: 1px solid #1a2340; border-radius: 14px;
    padding: 1rem 1.1rem;
}
.kpi-label { font-size: 0.64rem; font-weight: 600; color: #5a6a7e; letter-spacing: 0.8px; text-transform: uppercase; }
.kpi-value { font-size: 1.7rem; font-weight: 700; color: #fff; line-height: 1.15; margin-top: 0.15rem; }
.kpi-sub   { font-size: 0.68rem; color: #3a6655; margin-top: 0.1rem; }

/* ---- Consensus banner ---- */
.consensus-box {
    border-radius: 14px; padding: 1.1rem 1.3rem;
    display: flex; align-items: center; gap: 0.85rem;
}
.ca { background: #1abc9c11; border: 1px solid #1abc9c44; }
.cr { background: #ff475711; border: 1px solid #ff475744; }
.c-icon { font-size: 1.6rem; }
.c-title { font-size: 0.95rem; font-weight: 700; }
.c-reason { font-size: 0.78rem; color: #8494ab; margin-top: 3px; line-height: 1.5; }
.pr-title-lg { font-size: 1.15rem; font-weight: 700; color: #fff; margin-bottom: 0.15rem; }
.pr-meta-lg { font-size: 0.75rem; color: #5a6a7e; margin-bottom: 0.9rem; }

/* ---- Agent verdict grid ---- */
.agent-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.6rem; }
.agent-card {
    background: linear-gradient(160deg, #0d1117 0%, #0b0e18 100%);
    border: 1px solid #1a2340; border-radius: 12px;
    padding: 0.9rem 1rem;
}
.agent-card.a { border-left: 3px solid #1abc9c; }
.agent-card.r { border-left: 3px solid #ff4757; }
.a-name { font-size: 0.7rem; font-weight: 700; color: #7888a0; letter-spacing: 0.5px; }
.a-verdict { font-size: 0.82rem; font-weight: 600; margin: 3px 0; }
.a-verdict.a { color: #1abc9c; }
.a-verdict.r { color: #ff4757; }
.a-reason { font-size: 0.72rem; color: #5a6a7e; line-height: 1.4; }

/* ---- Findings ---- */
.finding-row {
    display: flex; align-items: flex-start; gap: 0.75rem;
    background: #0d1117; border: 1px solid #1a2340;
    border-radius: 10px; padding: 0.75rem 1rem; margin-bottom: 0.5rem;
}
.sb { border-radius: 6px; padding: 2px 8px; font-size: 0.6rem; font-weight: 700; white-space: nowrap; }
.sH { background: #ff475722; color: #ff4757; }
.sM { background: #ffa50222; color: #ffa502; }
.sL { background: #2ed57322; color: #2ed573; }
.f-meta { font-size: 0.7rem; color: #5a6a7e; }
.f-title { font-size: 0.82rem; color: #c8d4e0; font-weight: 500; }
.f-desc  { font-size: 0.72rem; color: #5a6a7e; margin-top: 1px; }
.f-empty { color: #3a4356; padding: 0.75rem; font-size: 0.82rem; }

/* ---- Diff ---- */
.diff-box {
    background: #0a0d14; border: 1px solid #1a2340; border-radius: 12px;
    padding: 1rem; font-family: 'JetBrains Mono', monospace;
    font-size: 0.73rem; line-height: 1.6; max-height: 320px; overflow-y: auto;
    white-space: pre-wrap; color: #8899bb;
}

/* ---- PR history rows ---- */
.hist-row {
    display: flex; align-items: center; justify-content: space-between;
    background: #0d1117; border: 1px solid #1a2340;
    border-radius: 10px; padding: 0.7rem 1rem; margin-bottom: 0.5rem;
}
.hist-left { display: flex; flex-direction: column; }
.hist-num { font-size: 0.66rem; color: #5a6a7e; font-weight: 600; }
.hist-title { font-size: 0.82rem; color: #c8d4e0; font-weight: 500; }
.vpill { display: inline-block; border-radius: 999px; font-size: 0.62rem; font-weight: 700; padding: 3px 11px; }
.va { background: #1abc9c22; color: #1abc9c; border: 1px solid #1abc9c55; }
.vr { background: #ff475722; color: #ff4757; border: 1px solid #ff475755; }
.hist-empty { text-align: center; padding: 2rem; color: #2a3450; font-size: 0.85rem; }

.footer-bar {
    margin-top: 2.5rem; border-top: 1px solid #1a2340; padding-top: 0.85rem;
    display: flex; justify-content: space-between; font-size: 0.68rem; color: #2a3450;
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------- data ----

def render_header(alive: bool) -> None:
    """Render the dashboard header with environment status."""
    env_html = (
        '<span class="cd-env env-live">&#9679; LIVE</span>' if alive
        else '<span class="cd-env env-off">&#9675; OFFLINE</span>'
    )
    st.markdown(f"""
    <div class="cd-header">
      <div class="cd-logo-wrap">
        <div class="cd-logo">CD</div>
        <div>
          <span class="cd-title">ConsensusDev</span>
          <div class="cd-subtitle">Autonomous PR Review &amp; Security Gate &middot; Admin View</div>
        </div>
      </div>
      {env_html}
    </div>""", unsafe_allow_html=True)

    if not alive:
        st.warning("Backend offline. Start it with: uvicorn backend:app --reload")

def render_controls() -> bool:
    """Render control toggle and return auto-refresh flag."""
    ctrl_l, ctrl_r = st.columns([3, 1])
    with ctrl_r:
        auto_r = st.toggle("Auto-refresh", value=False, help=f"Refresh every {POLL_INTERVAL}s")
    return auto_r

def render_kpis(metrics: dict) -> None:
    """Render KPI cards grid."""
    st.markdown('<div class="sh first">Overview</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-label">PRs Reviewed</div>
        <div class="kpi-value">{metrics.get('total_reviewed', 0)}</div>
        <div class="kpi-sub">Total this session</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Approval Rate</div>
        <div class="kpi-value">{metrics.get('approval_rate', 0)}%</div>
        <div class="kpi-sub">Approved by consensus</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Avg Review Time</div>
        <div class="kpi-value">{metrics.get('avg_review_time_label', '--')}</div>
        <div class="kpi-sub">End-to-end latency</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Vulns Caught</div>
        <div class="kpi-value">{metrics.get('vulnerabilities_caught', 0)}</div>
        <div class="kpi-sub">High + medium severity</div>
      </div>
    </div>""", unsafe_allow_html=True)

def render_latest_pr(latest: dict | None) -> None:
    """Render the latest pull request details and findings."""
    st.markdown('<div class="sh">Latest Pull Request</div>', unsafe_allow_html=True)
    if not latest:
        st.markdown('<div class="hist-empty">Awaiting PR submission &mdash; POST to /webhook to begin.</div>', unsafe_allow_html=True)
        return
    consensus = latest.get("consensus", "request_changes")
    con_reason = latest.get("consensus_reason", "No reason provided.")
    agents = latest.get("agents", {})
    findings = latest.get("findings", [])
    diff_text = latest.get("diff_text", "")
    cv = vc(consensus)

    st.markdown(f"""
    <div class="pr-title-lg">#{latest.get('pr_number','?')} &middot; {latest.get('title','Untitled')}</div>
    <div class="pr-meta-lg">{latest.get('repo_name','')}</div>
    """, unsafe_allow_html=True)

    if cv == "a":
        bcls, bicon, btitle, bcolor = "ca", "&#9989;", "Consensus: Approved", "#1abc9c"
    else:
        bcls, bicon, btitle, bcolor = "cr", "&#9940;", "Consensus: Changes Requested", "#ff4757"

    st.markdown(f"""
    <div class="consensus-box {bcls}">
      <div class="c-icon">{bicon}</div>
      <div>
        <div class="c-title" style="color:{bcolor}">{btitle}</div>
        <div class="c-reason">{con_reason}</div>
      </div>
    </div>""", unsafe_allow_html=True)

    # Agent verdicts
    st.markdown('<div class="sh">Agent Verdicts</div>', unsafe_allow_html=True)
    cards_html = '<div class="agent-grid">'
    for key, m in AGENT_META.items():
        ai = agents.get(key, {})
        v = ai.get("verdict", "request_changes")
        rea = ai.get("reason", "--")
        c = vc(v)
        vl = "Approve" if c == "a" else "Request Changes"
        cards_html += f"""
        <div class="agent-card {c}">
            <div class="a-name">{m['icon']} {m['label'].upper()}</div>
            <div class="a-verdict {c}">{vl}</div>
            <div class="a-reason">{rea}</div>
        </div>"""
    cards_html += "</div>"
    st.markdown(cards_html, unsafe_allow_html=True)

    # Findings
    st.markdown('<div class="sh">Static Analysis Findings</div>', unsafe_allow_html=True)
    if not findings:
        st.markdown('<div class="f-empty">No findings.</div>', unsafe_allow_html=True)
    else:
        f_html = ""
        for f in findings:
            sev = f.get("severity", "LOW").upper()
            sc = {"HIGH": "H", "MEDIUM": "M", "LOW": "L"}.get(sev, "L")
            f_html += f"""
            <div class="finding-row">
              <div><span class="sb s{sc}">{sev}</span></div>
              <div>
                <div class="f-title">{f.get('title','?')}</div>
                <div class="f-meta">{f.get('tool','?')} &middot; {f.get('file','?')}:{f.get('line','?')}</div>
                <div class="f-desc">{f.get('description','')}</div>
              </div>
            </div>"""
        st.markdown(f_html, unsafe_allow_html=True)

    # Diff (collapsible)
    with st.expander("View code diff"):
        if diff_text:
            lines = diff_text.splitlines()
            html_lines = []
            for ln in lines:
                esc = ln.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                if ln.startswith("+"):
                    html_lines.append(f'<span style="color:#1abc9c">{esc}</span>')
                elif ln.startswith("-"):
                    html_lines.append(f'<span style="color:#ff4757">{esc}</span>')
                elif ln.startswith("@@"):
                    html_lines.append(f'<span style="color:#ffa502">{esc}</span>')
                else:
                    html_lines.append(esc)
            st.markdown('<div class="diff-box">' + "\n".join(html_lines) + '</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="f-empty">No diff text.</div>', unsafe_allow_html=True)

def render_pr_history(prs: list) -> None:
    """Render the PR history section."""
    st.markdown('<div class="sh">PR History</div>', unsafe_allow_html=True)
    if not prs:
        st.markdown('<div class="hist-empty">No PRs reviewed yet.</div>', unsafe_allow_html=True)
        return
    hist_html = ""
    for pr in prs:
        verdict = pr.get("consensus", "request_changes")
        cls_v = vc(verdict)
        pill = "Approved" if cls_v == "a" else "Changes"
        hist_html += f"""
        <div class="hist-row">
          <div class="hist-left">
            <div class="hist-num">#{pr.get('pr_number','?')}</div>
            <div class="hist-title">{pr.get('title','Untitled')}</div>
          </div>
          <span class="vpill v{cls_v}">{pill}</span>
        </div>"""
    st.markdown(hist_html, unsafe_allow_html=True)

def render_footer(alive: bool) -> None:
    """Render the fixed footer with backend URL."""
    st.markdown(f"""
    <div class="footer-bar">
      <span>ConsensusDev &middot; Admin Dashboard</span>
      <span>Backend: {BACKEND_URL}</span>
    </div>""", unsafe_allow_html=True)

def main() -> None:
    """Main entry point to render the dashboard."""
    alive = backend_alive()
    metrics = fetch_metrics() if alive else {}
    prs = fetch_prs() if alive else []
    latest = prs[0] if prs else None
    render_header(alive)
    auto_r = render_controls()
    render_kpis(metrics)
    render_latest_pr(latest)
    render_pr_history(prs)
    render_footer(alive)
    if auto_r:
        time.sleep(POLL_INTERVAL)
        st.rerun()

if __name__ == "__main__":
    main()