"""
ConsensusDev -- Streamlit Dashboard
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
POLL_INTERVAL = 5

AGENT_META = {
    "security":    {"label": "Security",    "icon": "Lock"},
    "tech_debt":   {"label": "Tech Debt",   "icon": "Wrench"},
    "story":       {"label": "Story Match", "icon": "Book"},
    "performance": {"label": "Performance", "icon": "Zap"},
}

st.set_page_config(
    page_title="ConsensusDev - AI PR Review",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: #0a0e14; color: #e0e6f0; }
section[data-testid="stSidebar"] { background: #0d1117; border-right: 1px solid #1a2340; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1rem; padding-bottom: 2rem; }
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0d1117; }
::-webkit-scrollbar-thumb { background: #1abc9c44; border-radius: 3px; }
.stButton > button {
    background: transparent !important; border: none !important;
    padding: 0 !important; height: 0 !important;
    overflow: hidden !important; position: absolute !important; opacity: 0 !important;
}
.cd-header {
    display: flex; align-items: center; justify-content: space-between;
    background: linear-gradient(135deg, #0d1117 0%, #101820 100%);
    border: 1px solid #1a2340; border-radius: 16px;
    padding: 1rem 1.5rem; margin-bottom: 1.25rem;
}
.cd-logo-wrap { display: flex; align-items: center; gap: 0.75rem; }
.cd-logo {
    width: 42px; height: 42px;
    background: linear-gradient(135deg, #1abc9c, #0e8c6a);
    border-radius: 50%; display: flex; align-items: center; justify-content: center;
    font-size: 1.1rem; font-weight: 700; color: #fff; box-shadow: 0 0 16px #1abc9c44;
}
.cd-title { font-size: 1.25rem; font-weight: 700; color: #fff; }
.cd-badge {
    background: linear-gradient(90deg, #1abc9c22, #0e8c6a22);
    border: 1px solid #1abc9c55; border-radius: 999px;
    font-size: 0.6rem; font-weight: 700; color: #1abc9c;
    padding: 2px 9px; letter-spacing: 1px; margin-left: 6px;
}
.cd-subtitle { font-size: 0.78rem; color: #5a6a7e; margin-top: 1px; }
.cd-header-right { display: flex; align-items: center; gap: 1rem; }
.cd-model-info { font-size: 0.78rem; color: #7888a0; }
.cd-pill { border-radius: 999px; padding: 4px 14px; font-size: 0.72rem; font-weight: 600; }
.live { background: #1abc9c22; color: #1abc9c; border: 1px solid #1abc9c55; animation: pulse 2s infinite; }
.offline { background: #1a2340; color: #5a6a7e; border: 1px solid #2a3450; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.6} }
.metric-card {
    background: linear-gradient(160deg, #131a2e 0%, #0b0f1c 100%);
    border: 1px solid #1a2340; border-radius: 16px;
    padding: 1.25rem 1.5rem; position: relative; overflow: hidden;
    transition: border-color .2s, transform .15s; margin-bottom: 0.75rem;
}
.metric-card:hover { border-color: #1abc9c44; transform: translateY(-2px); }
.metric-card::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, transparent, #1abc9c66, transparent);
}
.mlabel { font-size: 0.7rem; font-weight: 600; color: #5a6a7e; letter-spacing: 1px; text-transform: uppercase; }
.mvalue { font-size: 2.2rem; font-weight: 700; color: #fff; line-height: 1.1; margin: 0.2rem 0; }
.msub   { font-size: 0.72rem; color: #3a6655; }
.micon  { font-size: 1.5rem; position: absolute; top: 1rem; right: 1.25rem; opacity: .35; }
.sh {
    font-size: 0.7rem; font-weight: 700; letter-spacing: 1.2px;
    text-transform: uppercase; color: #1abc9c; margin-bottom: 0.75rem;
    display: flex; align-items: center; gap: 0.5rem;
}
.sh::after { content: ''; flex: 1; height: 1px; background: linear-gradient(90deg, #1abc9c33, transparent); }
.pr-card {
    background: #0d1117; border: 1px solid #1a2340;
    border-radius: 12px; padding: 0.85rem 1rem; margin-bottom: 0.6rem;
    transition: border-color .2s;
}
.pr-card:hover { border-color: #1abc9c44; }
.pr-card.sel { border-color: #1abc9c; background: #0f1e1a; }
.pr-num { font-size: 0.68rem; color: #5a6a7e; font-weight: 600; }
.pr-title { font-size: 0.85rem; color: #c8d4e0; font-weight: 500; margin: 2px 0; }
.vpill { display: inline-block; border-radius: 999px; font-size: 0.62rem; font-weight: 700; padding: 2px 10px; }
.va { background: #1abc9c22; color: #1abc9c; border: 1px solid #1abc9c55; }
.vr { background: #ff475722; color: #ff4757; border: 1px solid #ff475755; }
.consensus-box {
    border-radius: 14px; padding: 1rem 1.25rem;
    display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem;
}
.ca { background: #1abc9c11; border: 1px solid #1abc9c44; }
.cr { background: #ff475711; border: 1px solid #ff475744; }
.c-icon { font-size: 1.5rem; }
.c-title { font-size: 0.9rem; font-weight: 700; }
.c-reason { font-size: 0.75rem; color: #7888a0; margin-top: 2px; }
.agent-card {
    background: linear-gradient(160deg, #0d1117 0%, #0b0e18 100%);
    border: 1px solid #1a2340; border-radius: 14px;
    padding: 1rem 1.1rem; margin-bottom: 0.6rem; transition: border-color .2s;
}
.agent-card:hover { border-color: #1abc9c44; }
.agent-card.a { border-left: 3px solid #1abc9c; }
.agent-card.r { border-left: 3px solid #ff4757; }
.a-name { font-size: 0.75rem; font-weight: 700; color: #7888a0; letter-spacing: 0.5px; }
.a-verdict { font-size: 0.8rem; font-weight: 600; margin: 4px 0; }
.a-verdict.a { color: #1abc9c; }
.a-verdict.r { color: #ff4757; }
.a-reason { font-size: 0.72rem; color: #5a6a7e; line-height: 1.4; }
.finding-row {
    display: flex; align-items: flex-start; gap: 0.75rem;
    background: #0d1117; border: 1px solid #1a2340;
    border-radius: 10px; padding: 0.75rem 1rem; margin-bottom: 0.5rem;
}
.sb { border-radius: 6px; padding: 2px 8px; font-size: 0.62rem; font-weight: 700; }
.sH { background: #ff475722; color: #ff4757; }
.sM { background: #ffa50222; color: #ffa502; }
.sL { background: #2ed57322; color: #2ed573; }
.f-meta { font-size: 0.72rem; color: #5a6a7e; }
.f-title { font-size: 0.82rem; color: #c8d4e0; font-weight: 500; }
.f-desc  { font-size: 0.72rem; color: #5a6a7e; margin-top: 1px; }
.diff-box {
    background: #0a0d14; border: 1px solid #1a2340; border-radius: 12px;
    padding: 1rem; font-family: 'JetBrains Mono', monospace;
    font-size: 0.74rem; line-height: 1.6; max-height: 300px; overflow-y: auto;
    white-space: pre-wrap; color: #8899bb;
}
.step-dot {
    width: 36px; height: 36px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center; font-size: 1rem;
}
.sd { background: #1abc9c22; border: 2px solid #1abc9c; color: #1abc9c; }
.sp { background: #1a2340; border: 2px solid #2a3450; color: #5a6a7e; }
.step-label { font-size: 0.65rem; font-weight: 600; color: #5a6a7e; text-align: center; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def fetch_metrics():
    try:
        r = requests.get(f"{BACKEND_URL}/metrics", timeout=3)
        return r.json() if r.ok else {}
    except Exception:
        return {}


def fetch_prs():
    try:
        r = requests.get(f"{BACKEND_URL}/prs", timeout=3)
        return r.json().get("prs", []) if r.ok else []
    except Exception:
        return []


def backend_alive():
    try:
        return requests.get(f"{BACKEND_URL}/health", timeout=2).ok
    except Exception:
        return False


def vc(v):
    return "a" if str(v).lower() == "approve" else "r"


def metric_card(label, value, sub, icon):
    st.markdown(f"""
    <div class="metric-card">
        <div class="micon">{icon}</div>
        <div class="mlabel">{label}</div>
        <div class="mvalue">{value}</div>
        <div class="msub">{sub}</div>
    </div>""", unsafe_allow_html=True)


if "sel" not in st.session_state:
    st.session_state.sel = 0

alive   = backend_alive()
metrics = fetch_metrics() if alive else {}
prs     = fetch_prs()     if alive else []

spill = '<span class="cd-pill live">&#9679; LIVE</span>' if alive else '<span class="cd-pill offline">&#9675; OFFLINE</span>'
st.markdown(f"""
<div class="cd-header">
  <div class="cd-logo-wrap">
    <div class="cd-logo">CD</div>
    <div>
      <span class="cd-title">ConsensusDev</span>
      <span class="cd-badge">MULTI-AGENT</span>
      <div class="cd-subtitle">Autonomous PR Review &amp; Security Gate</div>
    </div>
  </div>
  <div class="cd-header-right">
    <span class="cd-model-info">gpt-4o-mini &middot; 4 agents</span>
    {spill}
  </div>
</div>""", unsafe_allow_html=True)

if not alive:
    st.warning("Backend offline. Run: uvicorn backend:app --reload")

c1, c2, c3, c4 = st.columns(4, gap="medium")
with c1: metric_card("PRs Reviewed", str(metrics.get("total_reviewed", 0)), "Total this session", "&#128203;")
with c2: metric_card("Approval Rate", f"{metrics.get('approval_rate', 0)}%", "Approved by consensus", "&#9989;")
with c3: metric_card("Avg Review Time", metrics.get("avg_review_time_label", "--"), "End-to-end latency", "&#9201;")
with c4: metric_card("Vulnerabilities", str(metrics.get("vulnerabilities_caught", 0)), "High + medium severity", "&#128737;")

st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

steps = [("&#128279;","Webhook"), ("&#128269;","Static Scan"), ("&#129302;","AI Review"), ("&#9878;","Consensus"), ("&#128227;","Published")]
has_pr = len(prs) > 0
ncols = st.columns(len(steps)*2-1, gap="small")
for i, (icon, lbl) in enumerate(steps):
    with ncols[i*2]:
        cls = "sd" if has_pr else "sp"
        st.markdown(f"""
        <div style="display:flex;flex-direction:column;align-items:center;gap:4px">
            <div class="step-dot {cls}">{icon}</div>
            <div class="step-label">{lbl}</div>
        </div>""", unsafe_allow_html=True)
    if i < len(steps)-1:
        with ncols[i*2+1]:
            st.markdown("<div style='height:18px;display:flex;align-items:center'><div style='flex:1;height:2px;background:#1a2340;margin-top:8px'></div></div>", unsafe_allow_html=True)

st.markdown("<div style='height:.75rem'></div>", unsafe_allow_html=True)

lcol, rcol = st.columns([1, 2.8], gap="large")

with lcol:
    st.markdown('<div class="sh">PR Queue</div>', unsafe_allow_html=True)
    if not prs:
        st.markdown("<div style='text-align:center;padding:2rem;color:#2a3450'>No PRs yet.<br/>POST to /webhook to begin.</div>", unsafe_allow_html=True)
    for idx, pr in enumerate(prs):
        verdict = pr.get("consensus", "request_changes")
        cls_v   = vc(verdict)
        pill    = "Approved" if cls_v == "a" else "Changes"
        sel_cls = "pr-card sel" if idx == st.session_state.sel else "pr-card"
        st.markdown(f"""
        <div class="{sel_cls}">
            <div class="pr-num">#{pr.get('pr_number','?')}</div>
            <div class="pr-title">{pr.get('title','Untitled')}</div>
            <div style="margin-top:6px">
                <span class="vpill v{cls_v}">{pill}</span>
            </div>
        </div>""", unsafe_allow_html=True)
        if st.button(f"Select #{pr.get('pr_number','?')}", key=f"b{idx}", use_container_width=True):
            st.session_state.sel = idx
            st.rerun()

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    auto_r = st.toggle("Auto-refresh (5s)", value=False)

with rcol:
    sel_pr = prs[st.session_state.sel] if prs else None
    if not sel_pr:
        st.markdown("<div style='text-align:center;padding:4rem;color:#2a3450;font-size:1rem'>Awaiting PR submission</div>", unsafe_allow_html=True)
    else:
        pr          = sel_pr
        consensus   = pr.get("consensus","request_changes")
        con_reason  = pr.get("consensus_reason","No reason.")
        agents_data = pr.get("agents",{})
        findings    = pr.get("findings",[])
        diff_text   = pr.get("diff_text","")
        cv = vc(consensus)

        if cv == "a":
            bcls, bicon, btitle, bcolor = "ca","[APPROVED]","Consensus: APPROVED","#1abc9c"
        else:
            bcls, bicon, btitle, bcolor = "cr","[CHANGES]","Consensus: CHANGES REQUESTED","#ff4757"

        st.markdown(f"""
        <div class="consensus-box {bcls}">
            <div class="c-icon">{bicon}</div>
            <div>
                <div class="c-title" style="color:{bcolor}">{btitle}</div>
                <div class="c-reason">{con_reason}</div>
            </div>
        </div>""", unsafe_allow_html=True)

        st.markdown('<div class="sh">Agent Verdicts</div>', unsafe_allow_html=True)
        keys = list(AGENT_META.keys())
        r1, r2 = st.columns(2, gap="medium"), st.columns(2, gap="medium")
        all_cols = list(r1) + list(r2)
        for i, key in enumerate(keys):
            m   = AGENT_META[key]
            ai  = agents_data.get(key, {})
            v   = ai.get("verdict","request_changes")
            rea = ai.get("reason","--")
            c   = vc(v)
            vl  = "Approve" if c=="a" else "Request Changes"
            with all_cols[i]:
                st.markdown(f"""
                <div class="agent-card {c}">
                    <div class="a-name">{m['icon']} {m['label'].upper()}</div>
                    <div class="a-verdict {c}">{vl}</div>
                    <div class="a-reason">{rea}</div>
                </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:.75rem'></div>", unsafe_allow_html=True)

        fcol, dcol = st.columns([1, 1.4], gap="large")

        with fcol:
            st.markdown('<div class="sh">Security Findings</div>', unsafe_allow_html=True)
            if not findings:
                st.markdown("<div style='color:#2a3450;padding:.5rem'>No findings.</div>", unsafe_allow_html=True)
            for f in findings:
                sev = f.get("severity","LOW").upper()
                sc  = {"HIGH":"H","MEDIUM":"M","LOW":"L"}.get(sev,"L")
                st.markdown(f"""
                <div class="finding-row">
                    <div><span class="sb s{sc}">{sev}</span></div>
                    <div>
                        <div class="f-title">{f.get('title','?')}</div>
                        <div class="f-meta">{f.get('tool','?')} &middot; {f.get('file','?')}:{f.get('line','?')}</div>
                        <div class="f-desc">{f.get('description','')}</div>
                    </div>
                </div>""", unsafe_allow_html=True)

        with dcol:
            st.markdown('<div class="sh">Diff Preview</div>', unsafe_allow_html=True)
            if diff_text:
                lines = diff_text.splitlines()
                html_lines = []
                for ln in lines:
                    esc = ln.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
                    if ln.startswith("+"):
                        html_lines.append(f'<span style="color:#1abc9c">{esc}</span>')
                    elif ln.startswith("-"):
                        html_lines.append(f'<span style="color:#ff4757">{esc}</span>')
                    elif ln.startswith("@@"):
                        html_lines.append(f'<span style="color:#ffa502">{esc}</span>')
                    else:
                        html_lines.append(esc)
                st.markdown('<div class="diff-box">' + "\n".join(html_lines) + "</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div style='color:#2a3450;padding:.5rem'>No diff text.</div>", unsafe_allow_html=True)

st.markdown("""
<div style="margin-top:2rem;border-top:1px solid #1a2340;padding-top:.75rem;
    display:flex;justify-content:space-between;font-size:.68rem;color:#2a3450">
  <span>ConsensusDev &middot; Hackathon 2026 &middot; FastAPI + GPT-4o Mini + Streamlit</span>
  <span>Backend: http://localhost:8000</span>
</div>""", unsafe_allow_html=True)

if auto_r:
    time.sleep(POLL_INTERVAL)
    st.rerun()