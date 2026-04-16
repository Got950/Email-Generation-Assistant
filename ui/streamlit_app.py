"""
Email Generation Assistant — Professional Dashboard
"""

import asyncio
import json
import sys
import time
import urllib.parse
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import plotly.graph_objects as go
import streamlit as st

# ── Page config ──────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Email Generation Assistant",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="expanded",
)

ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = ROOT / "reports"
DATA_DIR = ROOT / "data"
# #region agent log
import json as _dj
_DLOG = ROOT / "debug-6b90d1.log"
def _dl(loc, msg, data=None, hyp=""):
    with open(_DLOG, "a") as _f:
        _f.write(_dj.dumps({"sessionId":"6b90d1","location":loc,"message":msg,"data":data or {},"hypothesisId":hyp,"timestamp":int(time.time()*1000)})+"\n")
# #endregion

# #region agent log
_dl("streamlit_app.py:init", "Streamlit version", {"version": st.__version__}, "A,C,E")
# #endregion
# ── Design tokens ────────────────────────────────────────────────────────
C = {
    "bg": "#0f1117", "surface": "#1a1c23", "surface2": "#23262f",
    "border": "#2d3039", "border2": "#383b45",
    "text": "#e6e8ec", "text2": "#9ca3af", "text3": "#6b7280",
    "accent": "#818cf8", "accent2": "#6366f1",
    "green": "#34d399", "green_bg": "rgba(52,211,153,0.12)",
    "yellow": "#fbbf24", "yellow_bg": "rgba(251,191,36,0.12)",
    "orange": "#fb923c", "orange_bg": "rgba(251,146,60,0.12)",
    "red": "#f87171", "red_bg": "rgba(248,113,113,0.12)",
    "blue": "#60a5fa", "blue_bg": "rgba(96,165,250,0.12)",
}

# ── Global CSS ───────────────────────────────────────────────────────────
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    *, html, body, [class*="css"] {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }}

    .block-container {{ padding: 2rem 2.5rem 3rem; max-width: 1280px; }}
    [data-testid="stSidebar"] {{ background: {C["surface"]}; border-right: 1px solid {C["border"]}; }}
    [data-testid="stSidebar"] > div:first-child {{ padding-top: 2rem; }}
    footer, #MainMenu, [data-testid="stToolbar"],
    .stDeployButton, [data-testid="stStatusWidget"] {{ visibility: hidden; }}
    header[data-testid="stHeader"] {{ background: transparent; }}

    /* ── Sidebar nav ── */
    .nav-brand {{
        display: flex; align-items: center; gap: 0.65rem;
        padding: 0 1rem 1.5rem; border-bottom: 1px solid {C["border"]};
        margin-bottom: 1.5rem;
    }}
    .nav-brand .icon {{
        width: 36px; height: 36px; border-radius: 10px;
        background: linear-gradient(135deg, {C["accent"]} 0%, {C["accent2"]} 100%);
        display: flex; align-items: center; justify-content: center;
        font-size: 1.1rem;
    }}
    .nav-brand .title {{ font-weight: 700; font-size: 0.95rem; color: {C["text"]}; }}
    .nav-brand .sub {{ font-size: 0.7rem; color: {C["text3"]}; }}

    .nav-section {{ padding: 0 0.6rem; margin-bottom: 0.3rem;
                    font-size: 0.65rem; font-weight: 600; color: {C["text3"]};
                    text-transform: uppercase; letter-spacing: 0.08em; }}

    /* ── Hero header ── */
    .page-header {{
        padding: 0 0 1.8rem;
        border-bottom: 1px solid {C["border"]};
        margin-bottom: 2rem;
    }}
    .page-header h1 {{
        font-size: 1.65rem; font-weight: 800; color: {C["text"]};
        margin: 0 0 0.35rem; letter-spacing: -0.02em;
    }}
    .page-header p {{
        font-size: 0.92rem; color: {C["text2"]}; margin: 0; line-height: 1.5;
    }}

    /* ── Metric cards ── */
    .m-card {{
        background: {C["surface"]}; border: 1px solid {C["border"]};
        border-radius: 12px; padding: 1.25rem 1.4rem;
    }}
    .m-card .m-label {{
        font-size: 0.72rem; font-weight: 600; color: {C["text3"]};
        text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 0.5rem;
    }}
    .m-card .m-value {{
        font-size: 2rem; font-weight: 800; letter-spacing: -0.03em;
        margin-bottom: 0.15rem;
    }}
    .m-card .m-sub {{
        font-size: 0.75rem; color: {C["text3"]};
    }}

    /* ── Strategy badge ── */
    .strat-badge {{
        display: inline-flex; align-items: center; gap: 0.35rem;
        padding: 0.25rem 0.75rem; border-radius: 6px;
        font-size: 0.72rem; font-weight: 600; text-transform: uppercase;
        letter-spacing: 0.05em;
    }}
    .strat-advanced {{ background: {C["blue_bg"]}; color: {C["blue"]}; }}
    .strat-baseline {{ background: {C["yellow_bg"]}; color: {C["yellow"]}; }}

    /* ── Score bar ── */
    .sbar {{
        display: flex; align-items: center; gap: 0.6rem;
        padding: 0.45rem 0;
    }}
    .sbar .lbl {{ width: 140px; font-size: 0.8rem; font-weight: 500; color: {C["text2"]}; }}
    .sbar .track {{
        flex: 1; height: 6px; background: {C["surface2"]};
        border-radius: 99px; overflow: hidden;
    }}
    .sbar .fill {{ height: 100%; border-radius: 99px; transition: width 0.4s ease; }}
    .sbar .num {{ width: 38px; text-align: right; font-weight: 700; font-size: 0.82rem;
                  font-variant-numeric: tabular-nums; }}

    /* ── Email preview box ── */
    .email-preview {{
        background: {C["surface"]}; border: 1px solid {C["border"]};
        border-radius: 10px; padding: 1.4rem 1.6rem;
        font-size: 0.88rem; line-height: 1.75; color: {C["text"]};
        white-space: pre-wrap;
    }}
    .email-preview.empty {{
        min-height: 300px; display: flex; align-items: center;
        justify-content: center; color: {C["text3"]}; font-style: italic;
    }}

    /* ── Live feed rows ── */
    .feed-row {{
        display: flex; align-items: center; gap: 0.75rem;
        padding: 0.6rem 1rem; margin: 0.25rem 0;
        background: {C["surface"]}; border: 1px solid {C["border"]};
        border-radius: 8px; font-size: 0.82rem;
    }}
    .feed-dot {{
        width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0;
    }}
    .feed-info {{ flex: 1; color: {C["text"]}; }}
    .feed-scores {{ display: flex; gap: 0.5rem; }}
    .feed-pill {{
        padding: 0.15rem 0.5rem; border-radius: 5px;
        font-size: 0.75rem; font-weight: 600;
        font-variant-numeric: tabular-nums;
    }}

    /* ── Empty state ── */
    .empty-state {{
        text-align: center; padding: 3.5rem 2rem;
        background: {C["surface"]}; border: 1px solid {C["border"]};
        border-radius: 14px;
    }}
    .empty-state .icon {{ font-size: 2.5rem; margin-bottom: 1rem; opacity: 0.4; }}
    .empty-state h3 {{
        font-size: 1.1rem; font-weight: 700; color: {C["text"]};
        margin: 0 0 0.5rem;
    }}
    .empty-state p {{ color: {C["text3"]}; font-size: 0.88rem; margin: 0; line-height: 1.6; }}

    /* ── Info cards row ── */
    .info-card {{
        background: {C["surface"]}; border: 1px solid {C["border"]};
        border-radius: 10px; padding: 1.1rem 1.2rem;
    }}
    .info-card .ic-title {{
        font-size: 0.78rem; font-weight: 700; color: {C["text"]};
        margin-bottom: 0.35rem;
    }}
    .info-card .ic-desc {{ font-size: 0.75rem; color: {C["text3"]}; line-height: 1.5; }}

    /* ── Scenario card (test scenarios page) ── */
    .sc-card {{
        background: {C["surface"]}; border: 1px solid {C["border"]};
        border-radius: 12px; padding: 1.4rem; margin-bottom: 0.8rem;
    }}
    .sc-header {{
        display: flex; align-items: center; gap: 0.6rem;
        margin-bottom: 1rem; padding-bottom: 0.8rem;
        border-bottom: 1px solid {C["border"]};
    }}
    .sc-num {{
        width: 30px; height: 30px; border-radius: 8px;
        background: {C["accent"]}; color: white;
        display: flex; align-items: center; justify-content: center;
        font-weight: 700; font-size: 0.8rem; flex-shrink: 0;
    }}
    .sc-title {{ font-weight: 600; font-size: 0.9rem; color: {C["text"]}; flex: 1; }}
    .sc-tone {{
        font-size: 0.7rem; font-weight: 600; padding: 0.2rem 0.6rem;
        border-radius: 5px; background: {C["accent"]}20; color: {C["accent"]};
        text-transform: capitalize;
    }}

    /* ── Tabs override ── */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0; border-bottom: 1px solid {C["border"]};
    }}
    .stTabs [data-baseweb="tab"] {{
        padding: 0.6rem 1.2rem; font-weight: 600; font-size: 0.82rem;
        color: {C["text3"]}; border-bottom: 2px solid transparent;
    }}
    .stTabs [aria-selected="true"] {{
        color: {C["accent"]} !important;
        border-bottom: 2px solid {C["accent"]} !important;
    }}

    /* ── Expander style ── */
    [data-testid="stExpander"] {{
        background: {C["surface"]}; border: 1px solid {C["border"]};
        border-radius: 10px; margin-bottom: 0.5rem;
    }}

    /* ── Button override ── */
    .stButton > button[kind="primary"] {{
        background: linear-gradient(135deg, {C["accent"]} 0%, {C["accent2"]} 100%);
        border: none; font-weight: 600;
    }}

    /* ── Progress bar ── */
    .stProgress > div > div > div {{
        background: linear-gradient(90deg, {C["accent"]}, {C["accent2"]});
    }}

    /* ── Send buttons ── */
    .send-btns {{
        display: flex; gap: 0.6rem; margin-top: 0.8rem;
    }}
    .send-btns a {{
        display: inline-flex; align-items: center; gap: 0.4rem;
        padding: 0.45rem 1rem; border-radius: 8px;
        font-size: 0.78rem; font-weight: 600;
        text-decoration: none; transition: opacity 0.15s;
    }}
    .send-btns a:hover {{ opacity: 0.85; }}
    .send-gmail {{
        background: rgba(234,67,53,0.12); color: #ea4335;
        border: 1px solid rgba(234,67,53,0.25);
    }}
    .send-outlook {{
        background: rgba(0,120,212,0.12); color: #0078d4;
        border: 1px solid rgba(0,120,212,0.25);
    }}
</style>
""", unsafe_allow_html=True)


# ── Helpers ──────────────────────────────────────────────────────────────
def run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def sc(v):
    if v >= 85: return C["green"]
    if v >= 70: return C["yellow"]
    if v >= 50: return C["orange"]
    return C["red"]


def sc_bg(v):
    if v >= 85: return C["green_bg"]
    if v >= 70: return C["yellow_bg"]
    if v >= 50: return C["orange_bg"]
    return C["red_bg"]


def badge_html(strat):
    cls = "strat-advanced" if strat == "advanced" else "strat-baseline"
    dot = C["blue"] if strat == "advanced" else C["yellow"]
    return (f'<span class="strat-badge {cls}">'
            f'<span style="width:6px;height:6px;border-radius:50%;background:{dot};"></span>'
            f'{strat}</span>')


def pill_html(v):
    c = sc(v)
    bg = sc_bg(v)
    return f'<span class="feed-pill" style="background:{bg};color:{c};">{v:.0f}</span>'


def render_score_bar(label, v):
    c = sc(v)
    st.markdown(f"""<div class="sbar">
        <span class="lbl">{label}</span>
        <div class="track"><div class="fill" style="width:{min(v,100)}%;background:{c};"></div></div>
        <span class="num" style="color:{c};">{v:.0f}</span>
    </div>""", unsafe_allow_html=True)


def render_metric_card(label, value, sub=""):
    c = sc(value) if isinstance(value, (int, float)) else C["text3"]
    v = f"{value:.1f}" if isinstance(value, (int, float)) else str(value)
    sub_html = f'<div class="m-sub">{sub}</div>' if sub else ""
    st.markdown(f'<div class="m-card"><div class="m-label">{label}</div>'
                f'<div class="m-value" style="color:{c};">{v}</div>{sub_html}</div>',
                unsafe_allow_html=True)


def _parse_email_parts(email_text: str) -> tuple[str, str]:
    """Extract subject and body from a generated email."""
    lines = email_text.strip().split("\n")
    subject = ""
    body_start = 0
    for i, line in enumerate(lines):
        if line.lower().startswith("subject:"):
            subject = line.split(":", 1)[1].strip()
            body_start = i + 1
            break
    body = "\n".join(lines[body_start:]).strip()
    return subject, body


def _mail_links(subject: str, body: str) -> tuple[str, str]:
    """Build Gmail and Outlook compose URLs."""
    s = urllib.parse.quote(subject)
    b = urllib.parse.quote(body)
    gmail = f"https://mail.google.com/mail/?view=cm&su={s}&body={b}"
    outlook = (
        f"https://outlook.live.com/mail/0/deeplink/compose"
        f"?subject={s}&body={b}"
    )
    return gmail, outlook


def load_scenarios():
    p = DATA_DIR / "scenarios.json"
    if p.exists():
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        # #region agent log
        _dl("streamlit_app.py:load_scenarios", "loaded", {"count": len(data), "path": str(p)}, "D")
        # #endregion
        return data
    # #region agent log
    _dl("streamlit_app.py:load_scenarios", "file missing", {"path": str(p)}, "D")
    # #endregion
    return []


def load_report():
    p = REPORTS_DIR / "evaluation_results.json"
    if p.exists():
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        # #region agent log
        _dl("streamlit_app.py:load_report", "loaded", {"keys": list(data.keys()) if isinstance(data, dict) else "not-dict"}, "D")
        # #endregion
        return data
    # #region agent log
    _dl("streamlit_app.py:load_report", "no report file", {"path": str(p)}, "D")
    # #endregion
    return None


def make_radar(metrics_a, metrics_b, names=("Advanced", "Baseline")):
    cats = list(metrics_a.keys())
    fig = go.Figure()
    for vals, name, color in [
        (metrics_a, names[0], C["blue"]),
        (metrics_b, names[1], C["yellow"]),
    ]:
        r = [vals.get(c, 0) for c in cats] + [vals.get(cats[0], 0)]
        fig.add_trace(go.Scatterpolar(
            r=r, theta=cats + [cats[0]], name=name,
            fill="toself", fillcolor=f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.08)",
            line=dict(color=color, width=2),
            marker=dict(size=5),
        ))
    fig.update_layout(
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=True, range=[0, 100], showticklabels=True,
                            tickfont=dict(size=10, color=C["text3"]),
                            gridcolor=C["border"]),
            angularaxis=dict(tickfont=dict(size=11, color=C["text2"]),
                             gridcolor=C["border"]),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color=C["text"]),
        legend=dict(font=dict(size=12), orientation="h", y=-0.15, x=0.5, xanchor="center"),
        margin=dict(t=30, b=50, l=60, r=60),
        height=360,
    )
    return fig


def make_grouped_bar(summary):
    strategies = list(summary.keys())
    metrics = [k for k in summary[strategies[0]] if k != "overall_average"]
    colors = {strategies[0]: C["blue"], strategies[-1]: C["yellow"]} if len(strategies) > 1 else {strategies[0]: C["blue"]}

    fig = go.Figure()
    for strat in strategies:
        fig.add_trace(go.Bar(
            name=strat.title(),
            x=metrics,
            y=[summary[strat].get(m, 0) for m in metrics],
            marker_color=colors.get(strat, C["accent"]),
            marker_line_width=0,
            opacity=0.9,
        ))
    fig.update_layout(
        barmode="group",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color=C["text"]),
        yaxis=dict(range=[0, 100], gridcolor=C["border"], title="Score",
                   titlefont=dict(size=11, color=C["text3"])),
        xaxis=dict(tickfont=dict(size=12)),
        legend=dict(font=dict(size=12), orientation="h", y=-0.2, x=0.5, xanchor="center"),
        margin=dict(t=20, b=60, l=50, r=20),
        height=320,
    )
    return fig


# ── Sidebar ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div class="nav-brand">
        <div class="icon" style="font-family:sans-serif;">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
                 stroke="white" stroke-width="2" stroke-linecap="round"
                 stroke-linejoin="round">
                <rect x="2" y="4" width="20" height="16" rx="2"/>
                <path d="M22 4L12 13 2 4"/>
            </svg>
        </div>
        <div>
            <div class="title">Email Gen Assistant</div>
            <div class="sub">AI-Powered Email Platform</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="nav-section">Pages</div>', unsafe_allow_html=True)
    page = st.radio("Nav", ["Generate Email", "Evaluation Dashboard", "Test Scenarios"],
                    label_visibility="collapsed")
    # #region agent log
    _dl("streamlit_app.py:page", "page selected", {"page": page}, "A,D")
    # #endregion

    st.markdown("---")
    st.markdown('<div class="nav-section">Architecture</div>', unsafe_allow_html=True)

    try:
        from app.config import get_settings
        settings = get_settings()
        provider = settings.resolved_provider.upper()
        model = settings.get_model_name("primary")
        has_key = settings.has_valid_key
        # #region agent log
        _dl("streamlit_app.py:sidebar", "settings loaded ok", {"provider": provider, "model": model, "has_key": has_key}, "B")
        # #endregion
    except Exception as _exc:
        provider = "Not configured"
        model = "—"
        has_key = False
        # #region agent log
        _dl("streamlit_app.py:sidebar", "settings FAILED", {"error": str(_exc)}, "B")
        # #endregion

    key_dot = C["green"] if has_key else C["red"]
    key_label = "Connected" if has_key else "No API key"

    st.markdown(f"""
    <div style="padding:0.6rem; font-size:0.78rem; color:{C['text3']}; line-height:1.8;">
        <div>
            <span style="color:{C['text2']};">Status:</span>
            <span style="display:inline-block;width:7px;height:7px;
                         border-radius:50%;background:{key_dot};
                         margin:0 0.3rem 0 0.15rem;vertical-align:middle;"></span>
            <span style="color:{key_dot};font-weight:600;">{key_label}</span>
        </div>
        <div><span style="color:{C['text2']};">Provider:</span>
             <span style="color:{C['accent']};">{provider}</span></div>
        <div><span style="color:{C['text2']};">Model:</span>
             <span style="color:{C['text']};">{model}</span></div>
        <div style="margin-top:0.6rem; padding-top:0.6rem;
                    border-top:1px solid {C['border']};">
            <div>CoT + Few-Shot + Role-Play</div>
            <div>Self-reflection critic loop</div>
            <div>LLM-as-Judge evaluation</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# =====================================================================
# PAGE : Generate Email
# =====================================================================
if page == "Generate Email":
    st.markdown("""<div class="page-header">
        <h1>Generate Email</h1>
        <p>Craft professional emails using advanced prompting strategies with self-reflection.</p>
    </div>""", unsafe_allow_html=True)

    col_form, col_preview = st.columns([5, 6], gap="large")

    with col_form:
        intent = st.text_input("Intent", placeholder="e.g., Follow up after a product demo call")
        key_facts_text = st.text_area(
            "Key Facts (one per line)",
            placeholder="Demo was held last Tuesday\nClient liked the reporting feature\nNext step is a pilot program",
            height=140,
        )
        c1, c2 = st.columns(2)
        with c1:
            tone = st.selectbox("Tone", [
                "formal", "professional", "friendly-casual", "empathetic",
                "excited", "neutral", "persuasive", "warm-grateful",
                "urgent", "casual-compelling",
            ])
        with c2:
            strategy = st.selectbox("Strategy", ["advanced", "baseline"],
                                    help="Advanced = CoT + Few-Shot + Role-Play + Self-Reflection Critic\nBaseline = Simple zero-shot prompt")
        gen_btn = st.button("Generate Email", type="primary", use_container_width=True)

    with col_preview:
        if gen_btn and intent and key_facts_text:
            from app.config import get_settings as _get_s
            _s = _get_s()
            if not _s.has_valid_key:
                st.error(
                    "**No valid API key.** Add your `OPENAI_API_KEY` to `.env` and restart."
                )
            else:
                key_facts = [f.strip() for f in key_facts_text.strip().split("\n") if f.strip()]
                with st.spinner("Generating email..."):
                    try:
                        from app.core.chains import STRATEGY_MAP
                        result = run_async(STRATEGY_MAP[strategy](intent, key_facts, tone))
                        rev_label = " · Revised by critic" if result.was_revised else ""
                        st.markdown(f'{badge_html(result.strategy)} '
                                    f'<span style="font-size:0.78rem;color:{C["text3"]};margin-left:0.5rem;">'
                                    f'{result.model_name}{rev_label}</span>',
                                    unsafe_allow_html=True)
                        st.markdown("")
                        st.markdown(f'<div class="email-preview">{result.email}</div>',
                                    unsafe_allow_html=True)
                        subj, body = _parse_email_parts(result.email)
                        gmail_url, outlook_url = _mail_links(subj, body)
                        st.markdown(
                            f'<div class="send-btns">'
                            f'<a href="{gmail_url}" target="_blank" class="send-gmail">'
                            f'&#9993; Send via Gmail</a>'
                            f'<a href="{outlook_url}" target="_blank" class="send-outlook">'
                            f'&#9993; Send via Outlook</a>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                    except Exception as e:
                        st.error(f"Generation failed: {e}")
        elif gen_btn:
            st.warning("Please fill in both Intent and Key Facts.")
        else:
            st.markdown('<div class="email-preview empty">Your generated email will appear here</div>',
                        unsafe_allow_html=True)


# =====================================================================
# PAGE : Evaluation Dashboard
# =====================================================================
elif page == "Evaluation Dashboard":
    st.markdown("""<div class="page-header">
        <h1>Evaluation Dashboard</h1>
        <p>Compare Advanced vs Baseline strategies across Fact Recall, Tone Alignment, and Professional Quality.</p>
    </div>""", unsafe_allow_html=True)

    report = load_report()

    # ── action bar ──
    ab1, ab2 = st.columns([4, 1])
    with ab1:
        if report:
            ts = report.get("metadata", {}).get("generated_at", "")
            n = report.get("metadata", {}).get("total_scenarios", 0)
            st.caption(f"Last run: {ts[:19].replace('T',' ')} UTC · {n} scenarios · "
                       f"{', '.join(report.get('metadata',{}).get('strategies_evaluated',[]))}")
    with ab2:
        run_btn = st.button("Run Evaluation", type="primary", use_container_width=True)

    # ── live evaluation runner ──
    if run_btn:
        from app.config import get_settings as _get_s
        _s = _get_s()
        if not _s.has_valid_key:
            st.error(
                "**No valid API key configured.** "
                "Add a valid `OPENAI_API_KEY` to your `.env` file and restart."
            )
            st.stop()

        from app.evaluation.runner import evaluate_single_scenario, load_scenarios as _load_sc, _compute_summary
        from app.evaluation.report import save_json_report, save_csv_report, save_markdown_report
        from app.core.chains import STRATEGY_MAP

        scenarios = _load_sc()
        strategies = ["advanced", "baseline"]
        total = len(scenarios) * len(strategies)
        all_results = []

        progress = st.progress(0, text="Initializing evaluation pipeline...")
        status_text = st.empty()
        live_container = st.container()

        completed = 0
        errors = 0
        start_t = time.time()

        for strat in strategies:
            if strat not in STRATEGY_MAP:
                continue
            for scenario in scenarios:
                sid = scenario["id"]
                elapsed = time.time() - start_t
                eta = (elapsed / max(completed, 1)) * (total - completed) if completed else 0
                status_text.caption(
                    f"Processing scenario {sid} · {strat} · "
                    f"{completed}/{total} complete · "
                    f"~{eta:.0f}s remaining"
                )
                progress.progress(completed / total)

                try:
                    result = run_async(evaluate_single_scenario(scenario, strat))
                    all_results.append(result)
                    sm = {s.metric_name: s.score for s in result.scores}
                    avg = sum(sm.values()) / len(sm)

                    with live_container:
                        st.markdown(
                            f'<div class="feed-row">'
                            f'<div class="feed-dot" style="background:{sc(avg)};"></div>'
                            f'<div class="feed-info">{badge_html(strat)} '
                            f'&nbsp;&nbsp;{scenario["intent"][:50]}</div>'
                            f'<div class="feed-scores">'
                            f'{pill_html(sm.get("Fact Recall",0))} '
                            f'{pill_html(sm.get("Tone Alignment",0))} '
                            f'{pill_html(sm.get("Professional Quality",0))}'
                            f'</div></div>',
                            unsafe_allow_html=True,
                        )
                except Exception as e:
                    errors += 1
                    with live_container:
                        st.markdown(
                            f'<div class="feed-row">'
                            f'<div class="feed-dot" style="background:{C["red"]};"></div>'
                            f'<div class="feed-info">{badge_html(strat)} '
                            f'&nbsp;&nbsp;{scenario["intent"][:50]}</div>'
                            f'<div class="feed-scores">'
                            f'<span class="feed-pill" style="background:{C["red_bg"]};color:{C["red"]};">ERR</span>'
                            f'</div></div>',
                            unsafe_allow_html=True,
                        )

                completed += 1
                time.sleep(0.3)

        elapsed = time.time() - start_t
        progress.progress(1.0)
        err_msg = f" · {errors} errors" if errors else ""
        status_text.caption(f"Completed {completed} scenarios in {elapsed:.0f}s{err_msg}")

        if all_results:
            summary = _compute_summary(all_results)
            save_json_report(all_results, summary)
            save_csv_report(all_results)
            save_markdown_report(all_results, summary)
            time.sleep(1)
            st.rerun()

    # ── results dashboard ──
    if report and not run_btn:
        summary = report.get("summary", {})
        results = report.get("results", [])
        strategies = list(summary.keys())

        # ── top metric cards ──
        st.markdown("")
        cols = st.columns(len(strategies) * 4)
        col_idx = 0
        for strat in strategies:
            m = summary[strat]
            metric_keys = [k for k in m if k != "overall_average"]
            for k in metric_keys:
                with cols[col_idx]:
                    label = f"{strat.title()} · {k}"
                    render_metric_card(label, m[k])
                col_idx += 1
            with cols[col_idx]:
                render_metric_card(f"{strat.title()} · Overall", m.get("overall_average", 0), "weighted avg")
            col_idx += 1

        st.markdown("")

        # ── charts ──
        chart_col1, chart_col2 = st.columns(2, gap="large")

        with chart_col1:
            st.markdown(f'<div style="font-size:0.85rem;font-weight:700;color:{C["text"]};'
                        f'margin-bottom:0.5rem;">Strategy Comparison</div>',
                        unsafe_allow_html=True)
            st.plotly_chart(make_grouped_bar(summary), use_container_width=True, config={"displayModeBar": False})

        with chart_col2:
            if len(strategies) >= 2:
                s1, s2 = strategies[0], strategies[1]
                m1 = {k: v for k, v in summary[s1].items() if k != "overall_average"}
                m2 = {k: v for k, v in summary[s2].items() if k != "overall_average"}
                st.markdown(f'<div style="font-size:0.85rem;font-weight:700;color:{C["text"]};'
                            f'margin-bottom:0.5rem;">Metric Radar</div>',
                            unsafe_allow_html=True)
                st.plotly_chart(make_radar(m1, m2, (s1.title(), s2.title())),
                                use_container_width=True, config={"displayModeBar": False})
            else:
                m1 = {k: v for k, v in summary[strategies[0]].items() if k != "overall_average"}
                st.markdown(f'<div style="font-size:0.85rem;font-weight:700;color:{C["text"]};'
                            f'margin-bottom:0.5rem;">Metric Breakdown</div>',
                            unsafe_allow_html=True)
                st.plotly_chart(make_radar(m1, m1, (strategies[0].title(), "")),
                                use_container_width=True, config={"displayModeBar": False})

        # ── metric definitions ──
        defs = report.get("metric_definitions", [])
        if defs:
            st.markdown(f'<div style="font-size:0.85rem;font-weight:700;color:{C["text"]};'
                        f'margin:1.5rem 0 0.6rem;">Metric Definitions</div>',
                        unsafe_allow_html=True)
            dc = st.columns(len(defs))
            for i, d in enumerate(defs):
                with dc[i]:
                    st.markdown(f'<div class="info-card"><div class="ic-title">{d["name"]}</div>'
                                f'<div class="ic-desc">{d["description"]}</div></div>',
                                unsafe_allow_html=True)

        # ── scenario breakdown ──
        st.markdown(f'<div style="font-size:0.85rem;font-weight:700;color:{C["text"]};'
                    f'margin:2rem 0 0.8rem;">Scenario Breakdown</div>',
                    unsafe_allow_html=True)

        filter_col1, filter_col2, _ = st.columns([1, 1, 4])
        with filter_col1:
            filt = st.selectbox("Strategy", ["All"] + strategies, key="ef", label_visibility="collapsed")
        with filter_col2:
            sort = st.selectbox("Sort", ["Default", "Score ↑", "Score ↓"], key="es", label_visibility="collapsed")

        filtered = [r for r in results if filt == "All" or r["strategy"] == filt]
        if sort == "Score ↑":
            filtered.sort(key=lambda r: sum(s["score"] for s in r["scores"]) / len(r["scores"]))
        elif sort == "Score ↓":
            filtered.sort(key=lambda r: sum(s["score"] for s in r["scores"]) / len(r["scores"]), reverse=True)

        for r in filtered:
            sm = {s["metric_name"]: s["score"] for s in r["scores"]}
            avg = sum(sm.values()) / len(sm) if sm else 0

            with st.expander(f"Scenario {r['scenario_id']}  ·  {r['intent'][:55]}  ·  Avg {avg:.0f}"):
                mc1, mc2 = st.columns([2, 3], gap="medium")
                with mc1:
                    st.markdown(f'{badge_html(r["strategy"])} '
                                f'<span style="font-size:0.78rem;color:{C["text3"]};margin-left:0.5rem;">'
                                f'{r["model_name"]}</span>', unsafe_allow_html=True)
                    st.markdown(f'<span style="font-size:0.82rem;color:{C["text2"]};">Tone: </span>'
                                f'<span style="font-size:0.82rem;color:{C["text"]};">{r["tone"]}</span>',
                                unsafe_allow_html=True)
                    st.markdown("")
                    for s in r["scores"]:
                        render_score_bar(s["metric_name"], s["score"])
                with mc2:
                    st.markdown(f'<div style="font-size:0.78rem;font-weight:600;color:{C["text2"]}; '
                                f'margin-bottom:0.5rem;">Generated Email</div>',
                                unsafe_allow_html=True)
                    st.markdown(f'<div class="email-preview" style="font-size:0.84rem;">'
                                f'{r["generated_email"]}</div>', unsafe_allow_html=True)

    # ── empty state (no report, not running) ──
    elif not run_btn:
        st.markdown("")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f'<div class="info-card"><div class="ic-title">Fact Recall</div>'
                        f'<div class="ic-desc">LLM-as-Judge per-fact verification with '
                        f'sentence-transformer semantic similarity fallback.</div></div>',
                        unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="info-card"><div class="ic-title">Tone Alignment</div>'
                        f'<div class="ic-desc">LLM-as-Judge tone rating (80%) combined with '
                        f'VADER sentiment analysis sanity check (20%).</div></div>',
                        unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="info-card"><div class="ic-title">Professional Quality</div>'
                        f'<div class="ic-desc">Composite: readability (Flesch), conciseness, '
                        f'structure detection, and LLM grammar judge.</div></div>',
                        unsafe_allow_html=True)

        st.markdown(f"""
        <div class="empty-state">
            <div class="icon">📊</div>
            <h3>No evaluation data yet</h3>
            <p>Click <b>Run Evaluation</b> to start the pipeline.<br/>
            20 scenarios (10 per strategy) will be evaluated across 3 custom metrics<br/>
            with live progress streaming to this dashboard.</p>
        </div>
        """, unsafe_allow_html=True)


# =====================================================================
# PAGE : Test Scenarios
# =====================================================================
elif page == "Test Scenarios":
    st.markdown("""<div class="page-header">
        <h1>Test Scenarios</h1>
        <p>10 diverse email scenarios with hand-crafted reference emails used for evaluation benchmarking.</p>
    </div>""", unsafe_allow_html=True)

    scenarios = load_scenarios()
    if not scenarios:
        st.warning("No scenarios found in data/scenarios.json.")
    else:
        for s in scenarios:
            st.markdown(f"""
            <div class="sc-card">
                <div class="sc-header">
                    <div class="sc-num">{s['id']}</div>
                    <div class="sc-title">{s['intent']}</div>
                    <div class="sc-tone">{s['tone']}</div>
                </div>
            </div>""", unsafe_allow_html=True)

            c1, c2 = st.columns([1, 1], gap="medium")
            with c1:
                st.markdown(f'<div style="font-size:0.78rem;font-weight:600;color:{C["text2"]}; '
                            f'margin-bottom:0.4rem;">Key Facts</div>', unsafe_allow_html=True)
                for fact in s["key_facts"]:
                    st.markdown(f"- {fact}")
            with c2:
                st.markdown(f'<div style="font-size:0.78rem;font-weight:600;color:{C["text2"]}; '
                            f'margin-bottom:0.4rem;">Reference Email</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="email-preview" style="font-size:0.82rem;">'
                            f'{s["reference_email"]}</div>', unsafe_allow_html=True)
            st.markdown("")
