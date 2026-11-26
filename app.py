"""Streamlit dashboard: Explainable Home and Last-Mile Connectivity Diagnosis (A3-PS015-TC032).

Run with:   streamlit run app.py
"""
import pandas as pd
import streamlit as st
import plotly.io as pio
from src.recommendations import generate_recommendations
from src.health_score import calculate_health_score
from src import project_info as info
from src.charts import ORANGE, comparison_chart, rtt_chart
from src.diagnosis import Diagnosis, Thresholds, diagnose
from src.models import DEFAULT_DOMAINS, DEFAULT_LOAD_URL, EvidenceBundle, ProbeStats, TestSettings
from src.orchestrator import run_live_diagnosis
from src.packet_loss import loss_summary
from src.performance import compare_stats
from src.report_generator import (generate_html_report, generate_markdown_report, report_filename,
                                  save_report)
from src.simulator import SCENARIOS, simulate_scenario

from src.history import calculate_historical_baseline, get_history, initialize_history, save_run
from src.anomaly import detect_network_anomalies
initialize_history()
MODE_LIVE = "Live measurement (real network)"
MODE_SIM = "Lab simulator (simulated data)"

st.set_page_config(
    page_title="NetPulse | Network Intelligence",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

pio.templates.default = "plotly_dark"
st.markdown(
    """
<style>
/* NetPulse - Dark Professional Theme */

.stApp {
    background: linear-gradient(135deg, #081321, #0d1b2e, #101f35);
    color: #e6edf7;
}

.block-container {
    padding-top: 1.5rem;
    max-width: 1450px;
}

[data-testid="stSidebar"] {
    background: #0b1728;
    border-right: 1px solid #203b59;
}

[data-testid="stMetric"] {
    background: linear-gradient(145deg, #142b45, #102139);
    border: 1px solid #244767;
    padding: 18px;
    border-radius: 13px;
    box-shadow: 0 4px 18px rgba(0, 150, 255, 0.08);
}

[data-testid="stMetricValue"] {
    color: #38cfff;
}

.hero {
    background: linear-gradient(110deg, #102c4b, #124b70, #12375c);
    border: 1px solid #2879a8;
    color: white;
    padding: 25px 28px;
    border-radius: 16px;
    margin-bottom: 22px;
    box-shadow: 0 5px 25px rgba(0, 180, 255, 0.12);
}

.hero h1 {
    color: white;
    font-size: 1.9rem;
    margin: 0 0 8px 0;
}

.hero p {
    color: #b8d9ef;
    font-size: 1rem;
}

h1, h2, h3 {
    color: #e6f3ff;
}

.stTabs [data-baseweb="tab"] {
    color: #b8cce0;
}

.stTabs [aria-selected="true"] {
    color: #38cfff;
    border-bottom-color: #38cfff;
}

.stButton > button {
    background: linear-gradient(100deg, #087eae, #1766b4);
    color: white;
    border: 1px solid #38cfff;
    border-radius: 9px;
    font-weight: 600;
    transition: 0.2s ease;
}

.stButton > button:hover {
    background: #159bd0;
    border-color: #75e1ff;
}

.step, .plain {
    background: #14263b;
    border: 1px solid #294866;
    border-radius: 12px;
    padding: 16px;
    color: #e6edf7;
}

.step .n {
    background: #087eae;
    color: white;
}

.diag {
    padding: 18px;
    border-radius: 12px;
    margin: 12px 0;
}

.diag-fault {
    background: #351d2b;
    border-color: #ef6479;
    color: #ffe0e5;
}

.diag-normal {
    background: #12352f;
    border-color: #36c99a;
    color: #d4fff0;
}

.diag-inconclusive {
    background: #3a301c;
    border-color: #e9b64e;
    color: #fff0c9;
}

.src-sim, .src-real {
    padding: 12px 16px;
    border-radius: 10px;
    margin: 12px 0;
}

.src-sim {
    background: #3b301b;
    border: 1px solid #d9a441;
    color: #ffe8b2;
}

.src-real {
    background: #12372d;
    border: 1px solid #36c99a;
    color: #d2ffed;
}

.foot {
    color: #8da9c5;
    font-size: 0.85rem;
    margin-top: 30px;
    text-align: center;
    border-top: 1px solid #294866;
    padding-top: 15px;
}

[data-testid="stDataFrame"] {
    border: 1px solid #294866;
    border-radius: 10px;
}

hr {
    border-color: #294866;
}

/* FIX 1: Make all text readable */

.stApp, .stApp p, .stApp label,
.stApp span, .stApp small,
.stApp [data-testid="stMarkdownContainer"] {
    color: #dce8f5;
}

[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] small {
    color: #dce8f5 !important;
}

/* Sidebar section headings */
[data-testid="stSidebar"] h2 {
    color: #42d5ff !important;
}

/* FIX 2: Improve information boxes */
[data-testid="stAlert"] {
    background: #162e49 !important;
    border: 1px solid #34709a !important;
    color: #e6f3ff !important;
}

[data-testid="stAlert"] p {
    color: #e6f3ff !important;
}

/* FIX 3: Make numbered circles small again */
.step .n {
    display: inline-flex !important;
    width: 32px !important;
    height: 32px !important;
    min-width: 32px !important;
    line-height: 32px !important;
    align-items: center;
    justify-content: center;
    text-align: center;
    border-radius: 50% !important;
    background: #087eae !important;
    color: white !important;
    font-weight: 700;
    margin-bottom: 10px;
}

/* FIX 4: Sidebar separation */
[data-testid="stSidebar"] {
    background: #0b1728 !important;
    border-right: 1px solid #294866;
}

/* FIX 5: Hide the white toolbar background */
header[data-testid="stHeader"] {
    background: #0b1728 !important;
}

/* FIX 6: Improve expander text */
[data-testid="stExpander"] {
    border: 1px solid #294866;
    border-radius: 10px;
}

[data-testid="stExpander"] summary {
    color: #e6edf7 !important;
}

/* FIX 7: Smooth card hover */
.step, [data-testid="stMetric"] {
    transition: all 0.3s ease;
}

.step:hover, [data-testid="stMetric"]:hover {
    border-color: #38cfff;
    box-shadow: 0 0 16px rgba(56, 207, 255, 0.18);
    transform: translateY(-3px);
}

/* FIX: Streamlit success, warning, error and info boxes */

/* Success */
[data-testid="stAlert"][kind="success"] {
    background: #123b30 !important;
    border: 1px solid #27c995 !important;
}
[data-testid="stAlert"][kind="success] * {
    color: #d7fff0 !important;
}

/* Warning */
[data-testid="stAlert"][kind="warning"] {
    background: #3d301a !important;
    border: 1px solid #e8b34c !important;
}
[data-testid="stAlert"][kind="warning"] * {
    color: #ffedc2 !important;
}

/* Error */
[data-testid="stAlert"][kind="error"] {
    background: #401f2a !important;
    border: 1px solid #ef6479 !important;
}
[data-testid="stAlert"][kind="error"] * {
    color: #ffe0e5 !important;
}

/* Information */
[data-testid="stAlert"][kind="info"] {
    background: #142f4b !important;
    border: 1px solid #38a9e8 !important;
}
[data-testid="stAlert"][kind="info"] * {
    color: #d9efff !important;
}

/* General alert text fallback */
[data-testid="stAlert"] p,
[data-testid="stAlert"] span {
    color: #e6f3ff !important;
}

/* Fix white download buttons */
.stDownloadButton button {
    background: #173451 !important;
    color: #e6f3ff !important;
    border: 1px solid #34709a !important;
}

/* =====================================
   NETPULSE - FINAL READABILITY FIX
   ===================================== */

/* Force every Streamlit alert to dark theme */
div[data-testid="stAlert"],
div[data-testid="stAlert"] > div,
div[data-testid="stAlert"] [data-testid] {
    background: #142b45 !important;
    background-color: #142b45 !important;
    border-color: #34709a !important;
}

/* Force alert text to white */
div[data-testid="stAlert"],
div[data-testid="stAlert"] p,
div[data-testid="stAlert"] span,
div[data-testid="stAlert"] label,
div[data-testid="stAlert"] div,
div[data-testid="stAlert"] li {
    color: #e6f3ff !important;
}

/* Success messages */
div[data-testid="stAlert"]:has(svg[data-testid="stSuccessIcon"]) {
    border: 1px solid #27c995 !important;
}

/* Warning and info messages */
div[data-testid="stAlert"] {
    border-radius: 12px !important;
    padding: 12px !important;
}

/* Metric change indicators */
[data-testid="stMetricDelta"],
[data-testid="stMetricDelta"] p,
[data-testid="stMetricDelta"] span {
    color: #38cfff !important;
    background: transparent !important;
}

/* Download buttons */
[data-testid="stDownloadButton"] button {
    background: #173451 !important;
    color: #ffffff !important;
    border: 1px solid #38cfff !important;
}

[data-testid="stDownloadButton"] button p {
    color: #ffffff !important;
}

/* All normal buttons */
.stButton button,
.stButton button p {
    color: white !important;
}

/* Keep input fields readable */
.stTextInput input,
.stTextArea textarea,
.stNumberInput input,
[data-baseweb="select"] div {
    color: #172b42 !important;
}

/* Improve captions */
.stCaption, [data-testid="stCaptionContainer"] {
    color: #a9bed4 !important;
}

/* Smooth appearance */
[data-testid="stAlert"],
[data-testid="stMetric"] {
    transition: all 0.25s ease;
}

/* NetPulse Branding */
.brand-header {
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 18px;
    padding: 12px 4px;
}

.brand-logo {
    width: 48px;
    height: 48px;
    border-radius: 13px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 27px;
    background: linear-gradient(135deg, #087eae, #6546c8);
    box-shadow: 0 0 20px rgba(56, 207, 255, 0.3);
}

.brand-name {
    color: #38cfff;
    font-size: 25px;
    font-weight: 800;
    letter-spacing: 1px;
}

.brand-tagline {
    color: #a9bed4;
    font-size: 12px;
    letter-spacing: 2px;
}


/* BIG NETPULSE SIDEBAR BRANDING */

.sidebar-brand {
    display: flex !important;
    flex-direction: row !important;
    align-items: center !important;
    gap: 16px !important;
    width: 100%;
    padding: 24px 12px 28px 12px !important;
    margin-bottom: 25px !important;
    border-bottom: 1px solid #294866;
}

.sidebar-logo {
    width: 68px !important;
    height: 68px !important;
    min-width: 68px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    border-radius: 18px !important;
    font-size: 40px !important;
    background: linear-gradient(135deg, #087eae, #6546c8);
    box-shadow: 0 0 25px rgba(56,207,255,0.35);
}

.sidebar-brand-name {
    color: #38cfff !important;
    font-size: 34px !important;
    font-weight: 850 !important;
    letter-spacing: 1px !important;
    line-height: 1.2 !important;
}

.sidebar-brand-sub {
    color: #a9bed4 !important;
    font-size: 11px !important;
    letter-spacing: 1.5px !important;
    margin-top: 5px;
}

[data-testid="stSidebar"] {
    width: 320px !important;
    min-width: 320px !important;
}

</style>
""",
    unsafe_allow_html=True,
)


st.markdown(
    """
    <div class="brand-header">
        <div class="brand-logo">📡</div>
        <div>
            <div class="brand-name">NetPulse</div>
            <div class="brand-tagline">
                NETWORK INTELLIGENCE PLATFORM
            </div>
        </div>
    </div>

    <div class="hero">
        <h1>Understand Your Network. Diagnose Every Problem.</h1>
        <p>
            Intelligent connectivity diagnosis, network health
            monitoring and explainable anomaly detection.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)



# ------------------------------------------------------------------ sidebar: settings

with st.sidebar:



    st.markdown(
        """<div style="display:flex;align-items:center;gap:15px;padding:20px 5px;margin-bottom:20px;border-bottom:1px solid #294866;">
        <div style="width:65px;height:65px;min-width:65px;border-radius:16px;background:linear-gradient(135deg,#087eae,#6546c8);display:flex;align-items:center;justify-content:center;font-size:38px;box-shadow:0 0 20px #087eae66;">📡</div>
        <div style="display:flex;flex-direction:column;">
        <div style="color:#38cfff;font-size:32px;font-weight:800;line-height:1.2;">NetPulse</div>
        <div style="color:#a9bed4;font-size:10px;letter-spacing:1.5px;">NETWORK INTELLIGENCE</div>
        </div></div>""",
        unsafe_allow_html=True
    )

    st.header("1. Choose a test")

    mode = st.radio("Where should the data come from?", [MODE_LIVE, MODE_SIM], index=1, key="mode",
                    help="The simulator needs no internet and is the quickest way to see every result type.")
    scenario_key, seed = "normal", 42
    if mode == MODE_SIM:
        scenario_key = st.selectbox("Lab scenario", list(SCENARIOS), format_func=lambda k: SCENARIOS[k].title, key="scenario")
        st.caption(SCENARIOS[scenario_key].description)
        seed = int(st.number_input("Random seed", 0, 99999, 42, key="seed", help="Same seed = same simulated numbers."))
        st.info("Simulator numbers are made up on purpose. They only show how the decision rules behave.")
    else:
        st.caption("Live mode tests the network of the computer running this app (takes about a minute).")

    with st.expander("Advanced test settings", expanded=False):       
        router_probes = st.slider("Router probes", 5, 30, 10, key="router_probes")
        external_probes = st.slider("External probes", 10, 60, 20, key="external_probes")
        external_targets = st.text_area(
            "External targets (one IP per line)",
            "1.1.1.1\n8.8.8.8\n9.9.9.9",
            key="external_targets"
        )
    gateway_override = st.text_input("Router address (blank = auto-detect)", "", key="gateway_override")
    domains_text = st.text_area("Domains to resolve (one per line)", "\n".join(DEFAULT_DOMAINS), key="domains")
    dns_method = st.selectbox("DNS method", ["auto", "system"], key="dns_method",
                                  help="auto = ask the detected DNS server directly; system = use the operating-system resolver.")
    run_load = st.checkbox("Run busy-link (load) test", True, key="run_load")
    load_threads = st.slider("Download threads for load", 1, 8, 4, key="load_threads")
    load_url = st.text_input("Load download URL", DEFAULT_LOAD_URL, key="load_url")

    with st.expander("Decision limits (advanced)", expanded=False):
        st.caption("Starting values we picked; they still need tuning. Change one and the diagnosis updates instantly.")
        th = Thresholds(
            loss_warn_pct=st.number_input("Packet loss warning (%)", 1.0, 100.0, 10.0, key="th_loss"),
            dns_slow_ms=st.number_input("Slow DNS (ms)", 50.0, 5000.0, 300.0, key="th_dns"),
            latency_high_ms=st.number_input("High latency (ms)", 20.0, 2000.0, 150.0, key="th_lat"),
            congestion_latency_abs_ms=st.number_input("Congestion: latency rise (ms)", 5.0, 1000.0, 30.0, key="th_clat"),
            congestion_jitter_abs_ms=st.number_input("Congestion: jitter rise (ms)", 1.0, 500.0, 10.0, key="th_cjit"),
            congestion_loss_increase_pct=st.number_input("Congestion: loss rise (%)", 1.0, 100.0, 3.0, key="th_closs"),
        )

settings = TestSettings(
   router_probes=router_probes,
external_probes=external_probes,
external_targets=[x.strip() for x in external_targets.splitlines() if x.strip()] or ["1.1.1.1", "8.8.8.8", "9.9.9.9"],
    domains=[d.strip() for d in domains_text.splitlines() if d.strip()] or list(DEFAULT_DOMAINS),
    dns_method=dns_method, run_load_test=run_load, load_threads=load_threads,
    load_url=load_url.strip() or DEFAULT_LOAD_URL, gateway_override=gateway_override.strip(),
)


# ------------------------------------------------------------------ helpers
def badge(text: str, kind: str) -> str:
    return f'<span class="badge {kind}">{text}</span>'


def router_status(s):
    if s is None or not s.available:
        return "Unavailable", "na"
    if s.received == 0:
        return "UNREACHABLE", "bad"
    if s.loss_pct and s.loss_pct >= th.loss_warn_pct and s.lost >= 2:
        return "Reachable (loss)", "warn"
    return "Reachable", "ok"


def dns_status(d):
    if d is None or not d.lookups:
        return "Unavailable", "na"
    if d.success_count == 0:
        return "FAILED", "bad"
    if d.failure_ratio > 0:
        return "Partly failing", "warn"
    if d.median_ms is not None and d.median_ms > th.dns_slow_ms:
        return "Slow", "warn"
    return "Resolving", "ok"


def fmt(value, unit=""):
    return "n/a" if value is None else f"{value}{unit}"


def probe_table(stats_list):
    rows = []
    for label, s in stats_list:
        if s is None:
            continue
        if not s.available:
            rows.append({"Test": label, "Target": s.target, "Result": f"unavailable: {s.error}"})
            continue
        rows.append({"Test": label, "Target": s.target, "Sent": s.sent, "Received": s.received,
                     "Loss %": s.loss_pct, "Min ms": s.min_ms, "Avg ms": s.avg_ms, "Median ms": s.median_ms,
                     "Max ms": s.max_ms, "Std dev ms": s.stdev_ms, "Jitter ms": s.jitter_ms})
    return pd.DataFrame(rows)


PLAIN = {
    "R0": ("There was not enough data to decide.", "Run the test again, or check that ping is allowed on this computer."),
    "C": ("The checks disagree with each other, so any answer would be a guess.",
          "Run the suggested extra tests below to find out which check is wrong."),
    "R1": ("Your device cannot reach the router, so the problem is inside your home network.",
           "Check the Wi-Fi or cable, restart the router, and try again."),
    "R2": ("The internet is reachable, but website names are not turning into addresses.",
           "Try another DNS server (for example 1.1.1.1) or restart the router."),
    "R3": ("Websites are slow to start loading because name lookups take too long.",
           "Try a faster DNS server and compare the lookup times."),
    "R4": ("Some of the data you send never gets a reply, which causes stalls and glitches.",
           "Test over a cable, move closer to the router, and see if the loss is only on Wi-Fi."),
    "R5": ("Replies arrive, but slowly, so everything feels laggy.",
           "Check whether other devices are busy, then repeat the test at a quieter time."),
    "R6": ("The connection is fine when idle but gets much worse when it is busy.",
           "Pause big downloads or streams, and ask the provider if the slowdown happens at certain hours."),
    "R7": ("Everything we checked looks healthy.",
           "If it still feels slow, repeat the test while the problem is actually happening."),
}


def plain_summary(d):
    what, todo = PLAIN.get(d.rule_id, ("See the evidence tab for details.", "Open the 'Why this answer' tab."))
    return what, todo


# ------------------------------------------------------------------ run
if st.button("Start Diagnosis", type="primary", width="stretch", key="start"):
    if mode == MODE_SIM:
        st.session_state["bundle"] = simulate_scenario(scenario_key, seed, settings)
        save_run(st.session_state["bundle"], diagnose(st.session_state["bundle"], th))
    else:
        bar = st.progress(0.0, text="Starting...")
        try:
            st.session_state["bundle"] = run_live_diagnosis(settings, progress=lambda f, m: bar.progress(f, text=m))
            save_run(st.session_state["bundle"], diagnose(st.session_state["bundle"], th))
        except Exception as exc:  # keep the page usable if the network is blocked
            st.error(f"The live test could not finish ({exc}). Try the lab simulator, or check your network and firewall.")
        finally:
            bar.empty()

bundle = st.session_state.get("bundle")
if bundle is None:
    c1, c2, c3 = st.columns(3)
    c1.markdown('<div class="step"><div class="n">1</div><br><b>Pick a test</b><br>Use the sidebar. '
                'The lab simulator is selected for you, so nothing touches your network.</div>', unsafe_allow_html=True)
    c2.markdown('<div class="step"><div class="n">2</div><br><b>Press Start Diagnosis</b><br>'
                'Try a few different scenarios to see each kind of result.</div>', unsafe_allow_html=True)
    c3.markdown('<div class="step"><div class="n">3</div><br><b>Read the answer</b><br>You get a plain summary, '
                'a confidence level, and the evidence behind it.</div>', unsafe_allow_html=True)
    st.write("")
    with st.expander("What does the tool actually check?"):
        st.markdown(
            "1. The **router** (can we reach it?)  \n2. **DNS** (do website names resolve, and how fast?)  \n"
            "3. **Delay, jitter and packet loss** using repeated pings  \n"
            "4. How those numbers change when the link is **busy**  \n"
            "5. Simple **readable rules** turn that into an answer, with the evidence shown  \n"
            "6. If the evidence is missing or contradictory it says **Inconclusive** instead of guessing."
        )
    with st.expander("About this project"):
        st.markdown(f"**{info.PROJECT_TITLE}**  \n{info.HACKATHON} | {info.PROBLEM_STATEMENT} | {info.CATEGORY} | "
                    f"Team code {info.TEAM_CODE}  \nTeam: {', '.join(info.TEAM_MEMBERS)}. Mentor: {info.COLLEGE_MENTOR}.")
    st.stop()

diag: Diagnosis = diagnose(bundle, th)
historical = calculate_historical_baseline()
# Network Health Score
st.markdown("### Network Health Score")
# For a congestion diagnosis, score the loaded measurements so the score reflects
# the degraded experience. Otherwise use the normal external baseline.
score_stats = bundle.external_loaded if diag.rule_id == "R6" and bundle.external_loaded else bundle.external_baseline
health = calculate_health_score(
    score_stats.median_ms if score_stats else None,
    score_stats.jitter_ms if score_stats else None,
    score_stats.loss_pct if score_stats else None,
)

if health["ready"]:
    score_col, grade_col = st.columns([1, 2])
    score_col.metric("Network Health Score", f'{health["score"]}/100')
    grade_col.metric("Network Status", health["grade"])
    h1, h2, h3 = st.columns(3)
    h1.metric("Latency Score", health["breakdown"]["latency"])
    h2.metric("Jitter Score", health["breakdown"]["jitter"])
    h3.metric("Packet Loss Score", health["breakdown"]["packet_loss"])
    st.caption(
        health["message"] + (
            " Score uses busy-link measurements because congestion was detected."
            if diag.rule_id == "R6" else
            " Score is based on external latency, jitter and packet loss."
        )
    )
else:
    st.info(
        "A numeric health score is unavailable because the required external latency/jitter "
        "measurements could not be collected. The diagnosis below explains the connectivity issue."
    )

# Personalized anomaly detection intentionally uses REAL history only.
st.markdown("### Personalized Network Anomaly Detection")
if bundle.source == "real" and historical["ready"]:
    current_metrics = {
        "latency_ms": bundle.external_baseline.median_ms,
        "jitter_ms": bundle.external_baseline.jitter_ms,
        "packet_loss_pct": bundle.external_baseline.loss_pct,
    }
    anomaly_result = detect_network_anomalies(current_metrics, historical)
    if anomaly_result["anomaly_detected"]:
        st.warning(anomaly_result["message"])
        for anomaly in anomaly_result["anomalies"]:
            st.write(f"⚠️ {anomaly['message']}")
    else:
        st.success(anomaly_result["message"])
elif bundle.source == "simulated":
    st.info("Personalized anomaly detection is reserved for real measurements. Simulated runs are not added to your historical baseline.")
elif not historical["ready"]:
    st.info("Personalized anomaly detection will be available after 5 real network runs.")
else:
    st.info("Personalized anomaly detection needs a valid real historical baseline.")

# Smart Network Recommendations
st.markdown("### Smart Network Recommendations")
recommendation_stats = score_stats
recommendation_result = generate_recommendations(
    diagnosis=diag.label,
    diagnosis_rule=diag.rule_id,
    latency_ms=recommendation_stats.median_ms if recommendation_stats else None,
    jitter_ms=recommendation_stats.jitter_ms if recommendation_stats else None,
    packet_loss_pct=recommendation_stats.loss_pct if recommendation_stats else None,
)
if bundle.source == "simulated":
    st.caption("Recommendations below are generated from the selected simulated scenario.")
for item in recommendation_result["recommendations"]:
    st.warning(f"**{item['problem']}**")
    st.write(f"**Recommended action:** {item['action']}")
    st.caption(f"Why: {item['reason']}")

st.markdown("### Historical Network Baseline")

if historical["ready"]:
    st.caption(
        f"Based on {historical['sample_count']} saved real network test runs."
    )

    b1, b2, b3 = st.columns(3)

    b1.metric(
        "Typical Latency",
        f"{historical['latency_ms']} ms"
        if historical["latency_ms"] is not None else "N/A",
    )
    b2.metric(
        "Typical Jitter",
        f"{historical['jitter_ms']} ms"
        if historical["jitter_ms"] is not None else "N/A",
    )
    b3.metric(
        "Typical Packet Loss",
        f"{historical['packet_loss_pct']}%"
        if historical["packet_loss_pct"] is not None else "N/A",
    )
else:
    st.info(
        f"Historical baseline not ready. {historical['message']} "
        "Only real network tests are counted; simulator runs are excluded."
    )

# ------------------------------------------------------------------ source banner
if bundle.is_simulated:
    st.markdown(f'<div class="src-sim"><b>SIMULATED DATA</b> &nbsp; Lab simulator scenario: '
                f'{SCENARIOS[bundle.scenario].title}. These are not real network measurements.</div>', unsafe_allow_html=True)
else:
    st.markdown(f'<div class="src-real"><b>REAL MEASUREMENTS</b> &nbsp; Taken on {bundle.platform} at {bundle.timestamp}.</div>',
                unsafe_allow_html=True)

# ------------------------------------------------------------------ diagnosis
css = {"fault": "diag-fault", "normal": "diag-normal", "inconclusive": "diag-inconclusive"}[diag.status]
conf_kind = {"High": "ok", "Medium": "warn", "Low": "bad"}.get(diag.confidence, "na")
conf_text = diag.confidence if not diag.is_inconclusive else "Not applicable"
st.markdown(
    f'<div class="diag {css}"><h2>{diag.label}</h2>'
    f'Confidence: {badge(conf_text, conf_kind)} &nbsp; Rule used: <b>{diag.rule_id}</b><br><br>{diag.explanation}</div>',
    unsafe_allow_html=True)
what, todo = plain_summary(diag)
st.markdown(f'<div class="plain"><b>In plain words:</b> {what}<br><b>What to try:</b> {todo}</div>', unsafe_allow_html=True)
if diag.is_inconclusive:
    st.warning("The tool will not guess. See the suggested additional tests under **Why this answer**.")

md_report = generate_markdown_report(bundle, diag, th)
html_report = generate_html_report(bundle, diag, th)
c1, c2, c3 = st.columns(3)
c1.download_button("Download Report (HTML)", html_report, report_filename(bundle, "html"), "text/html",
                   width="stretch", key="dl_html")
c2.download_button("Download Report (Markdown)", md_report, report_filename(bundle, "md"), "text/markdown",
                   width="stretch", key="dl_md")
if c3.button("Save a copy to the reports folder", width="stretch", key="save_copy"):
    path = save_report(html_report, report_filename(bundle, "html"))
    save_report(md_report, report_filename(bundle, "md"))
    st.success(f"Saved: {path}")

# ------------------------------------------------------------------ status tiles
r, d, e = bundle.router, bundle.dns, bundle.external_baseline
t1, t2, t3, t4 = st.columns(4)
with t1:
    st.subheader("Router")
    text, kind = router_status(r)
    st.markdown(badge(text, kind), unsafe_allow_html=True)
    st.metric("Gateway", bundle.gateway or "not detected", f"avg {fmt(r.avg_ms, ' ms')}" if r and r.available else None, delta_color="off")
with t2:
    st.subheader("DNS")
    text, kind = dns_status(d)
    st.markdown(badge(text, kind), unsafe_allow_html=True)
    st.metric("Lookups OK", f"{d.success_count}/{len(d.lookups)}" if d else "n/a",
              f"median {fmt(d.median_ms, ' ms')}" if d else None, delta_color="off")
with t3:
    st.subheader("Latency")
    ok = e is not None and e.available and e.received > 0
    st.markdown(badge("Measured" if ok else "Unavailable", "ok" if ok else "na"), unsafe_allow_html=True)
    st.metric("Median RTT", fmt(e.median_ms, " ms") if e and e.available else "n/a",
              f"avg {fmt(e.avg_ms, ' ms')} | jitter {fmt(e.jitter_ms, ' ms')}" if e and e.available else None, delta_color="off")
with t4:
    st.subheader("Packet loss")
    if e is not None and e.available:
        lossy = (e.loss_pct or 0) >= th.loss_warn_pct and e.lost >= 2
        st.markdown(badge("Loss seen" if lossy else "Low", "bad" if lossy else "ok"), unsafe_allow_html=True)
        st.metric("Loss", fmt(e.loss_pct, " %"), f"{e.received} of {e.sent} replies", delta_color="off")
    else:
        st.markdown(badge("Unavailable", "na"), unsafe_allow_html=True)
        st.metric("Loss", "n/a")

# ------------------------------------------------------------------
# Visual Connection Path
st.markdown("### 🌐 Visual Connection Path")

router_ok = r is not None and r.available
dns_ok = d is not None and d.success_count == len(d.lookups) and len(d.lookups) > 0

target_results = bundle.external_target_results or ([e] if e else [])
targets_reached = sum(
    1 for result in target_results
    if result is not None and result.available and result.received > 0
)
internet_ok = targets_reached > 0

def path_card(title, status, color, detail, emoji):
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(145deg, #ffffff, #f1f5f9);
            border: 1px solid {color};
            border-top: 4px solid {color};
            border-radius: 14px;
            padding: 18px 10px;
            min-height: 145px;
            text-align: center;
            box-shadow: 0 4px 12px rgba(0,0,0,0.06);
        ">
            <div style="font-size:25px;">{emoji}</div>
            <div style="font-size:16px;font-weight:700;color:#1e293b;margin:8px 0;">
                {title}
            </div>
            <div style="font-size:14px;font-weight:700;color:{color};">
                {status}
            </div>
            <div style="font-size:12px;color:#64748b;margin-top:8px;">
                {detail}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

c1, a1, c2, a2, c3, a3, c4 = st.columns(
    [1, 0.18, 1, 0.18, 1, 0.18, 1]
)

with c1:
    path_card("Your Device", "Test running", "#2563eb",
              "Local device", "💻")

with a1:
    st.markdown("<div style='text-align:center;padding-top:48px;font-size:24px;color:#64748b;'>➜</div>",
                unsafe_allow_html=True)

with c2:
    path_card("Router",
              "Reachable" if router_ok else "Unavailable",
              "#16a34a" if router_ok else "#dc2626",
              str(bundle.gateway or "Not detected"), "📡")

with a2:
    st.markdown("<div style='text-align:center;padding-top:48px;font-size:24px;color:#64748b;'>➜</div>",
                unsafe_allow_html=True)

with c3:
    path_card("ISP / Last Mile", "Not directly measured",
              "#d97706",
              "Needs ISP-side evidence", "🏢")

with a3:
    st.markdown("<div style='text-align:center;padding-top:48px;font-size:24px;color:#64748b;'>➜</div>",
                unsafe_allow_html=True)

with c4:
    path_card("Public Internet",
              f"{targets_reached}/{len(target_results)} targets reachable",
              "#16a34a" if internet_ok else "#dc2626",
              "External ping checks", "🌍")

st.markdown("")

dns_color = "#16a34a" if dns_ok else "#dc2626"
dns_status = "All lookups working" if dns_ok else "Lookup issue detected"
dns_detail = (
    f"{d.success_count}/{len(d.lookups)} lookups successful"
    if d else "Not tested"
)

path_card("DNS Resolution", dns_status, dns_color,
          dns_detail, "🔎")

st.markdown("")


# Smart Bottleneck Detection
st.markdown("### 🧠 Smart Bottleneck Detection")

loss_issue = (
    e is not None and e.available
    and (e.loss_pct or 0) >= th.loss_warn_pct
    and e.lost >= 2
)

latency_issue = (
    e is not None and e.available
    and e.avg_ms is not None and e.avg_ms > 100
)

jitter_issue = (
    e is not None and e.available
    and e.jitter_ms is not None and e.jitter_ms > 30
)

# Compare normal and busy-link measurements
loaded = bundle.external_loaded

congestion_latency = (
    e is not None and loaded is not None
    and e.median_ms is not None and loaded.median_ms is not None
    and loaded.median_ms > e.median_ms * 2
    and loaded.median_ms - e.median_ms >= 50
)

congestion_jitter = (
    e is not None and loaded is not None
    and e.jitter_ms is not None and loaded.jitter_ms is not None
    and loaded.jitter_ms - e.jitter_ms >= 15
)

congestion_loss = (
    e is not None and loaded is not None
    and e.loss_pct is not None and loaded.loss_pct is not None
    and loaded.loss_pct - e.loss_pct >= 2
)

congestion_detected = (
    bundle.load is not None
    and bundle.load.applied
    and (congestion_latency or congestion_jitter or congestion_loss)
)

if not router_ok:
    st.error(
        "Possible local connectivity issue: Router is not reachable. "
        "Check your Wi-Fi or LAN connection."
    )
elif not internet_ok:
    st.warning(
        "Possible upstream connectivity issue: No external targets responded. "
        "ISP / last-mile fault is not confirmed."
    )
elif not dns_ok:
    st.warning("Possible DNS issue: One or more DNS lookups failed.")
elif congestion_detected:
    st.warning("Busy-link congestion detected in the comparison measurements.")

    if congestion_latency:
        st.write(
            f"🔴 Median latency increased from "
            f"{e.median_ms:.1f} ms to {loaded.median_ms:.1f} ms."
        )

    if congestion_jitter:
        st.write(
            f"🟠 Jitter increased from "
            f"{e.jitter_ms:.1f} ms to {loaded.jitter_ms:.1f} ms."
        )

    if congestion_loss:
        st.write(
            f"🔴 Packet loss increased from "
            f"{e.loss_pct:.1f}% to {loaded.loss_pct:.1f}%."
        )

elif loss_issue or latency_issue or jitter_issue:
    st.warning("Network quality issues detected.")

    if loss_issue:
        st.write(f"🔴 Packet loss: {e.loss_pct:.1f}%")
    if latency_issue:
        st.write(f"🟠 High average latency: {e.avg_ms:.1f} ms")
    if jitter_issue:
        st.write(f"🟠 High jitter: {e.jitter_ms:.1f} ms")

else:
    st.success(
        "No major connectivity issue detected. "
        "Router, external reachability, DNS and network quality look healthy."
    )
st.markdown("## Network History Dashboard")

history_runs = get_history(limit=20)

if history_runs:
    st.caption(f"Showing {len(history_runs)} recent diagnosis runs.")

    history_rows = []

    for run in history_runs:
        evidence = run.get("evidence", {})
        stats = evidence.get("external_baseline") or {}

        history_rows.append({
            "Date": run.get("timestamp", ""),
            "Source": run.get("source", ""),
            "Scenario": run.get("scenario", ""),
            "Diagnosis": run.get("diagnosis_label") or "N/A",
            "Latency (ms)": stats.get("median_ms"),
            "Jitter (ms)": stats.get("jitter_ms"),
            "Packet Loss (%)": stats.get("loss_pct"),
        })
    history_rows.reverse()

    st.markdown("### Network Performance Trends")

    trend_data = pd.DataFrame(history_rows)

    trend_data["Date"] = pd.to_datetime(trend_data["Date"])

    trend_data = trend_data.dropna(subset=["Latency (ms)"])

    if not trend_data.empty:
        st.line_chart(
            trend_data.set_index("Date")[
                ["Latency (ms)", "Jitter (ms)"]
            ]
        )

        st.line_chart(
            trend_data.set_index("Date")[["Packet Loss (%)"]]
        )
    else:
        st.info("Not enough measurement data to show trends.")
    st.dataframe(history_rows, width="stretch")
else:
    st.info("No diagnosis history available yet.")
# ------------------------------------------------------------------ detail tabs
tab_e, tab_m, tab_p, tab_r = st.tabs(["Why this answer", "Raw measurements", "Normal vs busy link", "Report preview"])

with tab_m:
    st.dataframe(probe_table([("Router", r), ("External (normal)", e), ("External (busy link)", bundle.external_loaded)]),
                 width="stretch", hide_index=True)
    if bundle.external_target_results:
        st.subheader("External target results")
        st.dataframe(
                probe_table([
                    (f"External target {i + 1}", result)
                    for i, result in enumerate(bundle.external_target_results)
                ]),
                width="stretch",
                hide_index=True
            )
    if e is not None and e.available:
        st.caption("Packet loss details (sent / received / lost):")
        st.dataframe(pd.DataFrame([loss_summary(s) for s in (r, e) if s is not None and s.available]),
                     width="stretch", hide_index=True)
    cols = st.columns(2)
    for col, (title, stats) in zip(cols, [("Router round-trip times", r), ("External round-trip times", e)]):
        fig = rtt_chart(stats, title)
        if fig is not None:
            col.plotly_chart(fig, width="stretch")
        else:
            col.info(f"{title}: no data.")
    st.markdown("**DNS lookups**")
    if d is not None:
        st.write(f"DNS servers found: {', '.join(d.servers) or 'unavailable'}. Tested: {d.server_tested or 'operating-system resolver'} ({d.method}).")
        st.dataframe(pd.DataFrame([{"Domain": x.domain, "Result": "OK" if x.success else "FAILED",
                                    "Time ms": x.time_ms, "Error": x.error} for x in d.lookups]),
                     width="stretch", hide_index=True)

with tab_p:
    rows = compare_stats(e, bundle.external_loaded)
    st.info("This compares how latency, jitter and loss CHANGE when the link is busy. "
            "A ping test is not a bandwidth test, so no speed is claimed.")
    if rows and bundle.load:
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
        st.plotly_chart(comparison_chart(rows), width="stretch")
        st.caption(f"Load: {bundle.load.threads} download threads for {bundle.load.duration_s} s, "
                   f"{bundle.load.bytes_downloaded / 1e6:.1f} MB downloaded (applied: {bundle.load.applied}).")
        fig = rtt_chart(bundle.external_loaded, "External round-trip times during busy link", ORANGE)
        if fig is not None:
            st.plotly_chart(fig, width="stretch")
    else:
        st.warning(bundle.load.error if bundle.load and bundle.load.error else "No busy-link result is available for this run.")

with tab_e:
    st.markdown("**Supporting evidence**")
    for line in diag.evidence or ["No supporting evidence available."]:
        st.markdown(f"- {line}")
    st.markdown("**Why this confidence level**  \n*(simple evidence counting, not a validated probability)*")
    for line in diag.confidence_reasons:
        st.markdown(f"- {line}")
    if diag.secondary:
        st.markdown("**Other issues also seen**")
        for line in diag.secondary:
            st.markdown(f"- {line}")
    st.markdown("**Rules checked**")
    st.dataframe(pd.DataFrame([{"Rule": x.rule_id, "Name": x.name, "State": x.state, "Detail": x.detail} for x in diag.rules]),
                 width="stretch", hide_index=True)
    st.markdown("**Suggested additional tests**" if diag.is_inconclusive else "**Suggested next steps**")
    for line in diag.additional_tests:
        st.markdown(f"- {line}")
    if bundle.notes:
        st.markdown("**Notes**")
        for line in bundle.notes:
            st.markdown(f"- {line}")
    st.markdown("**Limitations**")
    for line in diag.limitations:
        st.markdown(f"- {line}")

with tab_r:
    st.markdown(md_report)

st.markdown(f'<div class="foot">{info.TEAM_CODE} | {info.PROJECT_TITLE}</div>', unsafe_allow_html=True)
