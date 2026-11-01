"""Streamlit dashboard: Explainable Home and Last-Mile Connectivity Diagnosis (A3-PS015-TC032).

Run with:   streamlit run app.py
"""
import pandas as pd
import streamlit as st

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

MODE_LIVE = "Live measurement (real network)"
MODE_SIM = "Lab simulator (simulated data)"

st.set_page_config(page_title=f"{info.TEAM_CODE} | Connectivity Diagnosis", page_icon="📡", layout="wide")

st.markdown(
    """
<style>
.block-container {padding-top: 1.6rem; max-width: 1200px;}
.hero {background: linear-gradient(120deg, #0f766e 0%, #115e59 100%); color: #fff; padding: 22px 28px;
       border-radius: 14px; margin-bottom: 16px;}
.hero h1 {color: #fff; font-size: 1.8rem; margin: 0 0 4px 0; padding: 0;}
.hero p {margin: 2px 0; color: #d5f2ee; font-size: 0.98rem;}
.badge {display:inline-block; padding: 2px 11px; border-radius: 999px; font-weight: 600; font-size: 0.85rem;}
.ok {background:#dcfce7; color:#166534;} .bad {background:#fee2e2; color:#991b1b;}
.warn {background:#fef3c7; color:#92400e;} .na {background:#e5e7eb; color:#4b5563;}
.diag {border-left: 8px solid; padding: 16px 20px; border-radius: 10px; margin: 10px 0;}
.diag h2 {margin: 0 0 6px 0; font-size: 1.55rem;}
.diag-fault {border-color:#dc2626; background:#fef2f2;} .diag-normal {border-color:#16a34a; background:#f0fdf4;}
.diag-inconclusive {border-color:#d97706; background:#fffbeb;}
.plain {background:#ffffff; border:1px solid #d6ddd6; border-radius:10px; padding:12px 18px; margin: 8px 0 12px 0;}
.plain b {color:#0f766e;}
.src-sim {background:#fef3c7; border:1px solid #e5b84a; padding:9px 14px; border-radius:10px;}
.src-real {background:#dcfce7; border:1px solid #86c99a; padding:9px 14px; border-radius:10px;}
.step {background:#ffffff; border:1px solid #d6ddd6; border-radius:12px; padding:14px 16px; height:100%;}
.step .n {display:inline-block; width:28px; height:28px; line-height:28px; text-align:center; border-radius:50%;
          background:#0f766e; color:#fff; font-weight:700; margin-bottom:6px;}
.foot {color:#6b7280; font-size:0.85rem; margin-top:26px; text-align:center;}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="hero">
<h1>📡 Why does my internet feel broken?</h1>
<p>Runs a few quick checks, finds the most likely weak spot, and shows its working so you can verify it.</p>
</div>
""",
    unsafe_allow_html=True,
)


# ------------------------------------------------------------------ sidebar: settings
with st.sidebar:
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
        external_target = st.text_input("External target (IP)", "1.1.1.1", key="external_target")
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
    router_probes=router_probes, external_probes=external_probes, external_target=external_target.strip() or "1.1.1.1",
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
    else:
        bar = st.progress(0.0, text="Starting...")
        try:
            st.session_state["bundle"] = run_live_diagnosis(settings, progress=lambda f, m: bar.progress(f, text=m))
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

# ------------------------------------------------------------------ detail tabs
tab_e, tab_m, tab_p, tab_r = st.tabs(["Why this answer", "Raw measurements", "Normal vs busy link", "Report preview"])

with tab_m:
    st.dataframe(probe_table([("Router", r), ("External (normal)", e), ("External (busy link)", bundle.external_loaded)]),
                 width="stretch", hide_index=True)
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
