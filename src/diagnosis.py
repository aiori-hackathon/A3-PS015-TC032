"""Explainable, rule-based diagnosis engine.

Every rule is a small, readable function. Each one writes down:
  * what it looked at (evidence),
  * whether it fired,
  * how sure we are (confidence + the reasons for it).

The decision limits (Thresholds) are PROPOSED values that still have to be tested and
tuned. Confidence levels (High / Medium / Low) are simple counting rules based on how
much matching evidence exists. They are NOT scientifically validated probabilities.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from .models import EvidenceBundle, ProbeStats
from .packet_loss import is_loss_significant

LEVELS = ["Low", "Medium", "High"]

LIMITATIONS = [
    "Decision limits are proposed values that must still be tested and tuned; they are not validated.",
    "Confidence levels are simple evidence-counting rules, not statistically validated probabilities.",
    "A symptom is a hint, not proof. The tool does not prove a damaged cable, causes inside the ISP network, or Wi-Fi interference (no radio data).",
    "Ping loss covers both directions (request and reply), so it is not the one-way loss of RFC 7680.",
    "Some routers and servers slow down or ignore ping (ICMP), which can look like loss or an unreachable device.",
    "The busy-link test creates download load only, and only shows how latency, jitter and loss change. It is not a bandwidth test.",
]


@dataclass
class Thresholds:
    """Proposed limits used by the rules (all can be changed in the app sidebar)."""

    min_router_probes: int = 5
    min_probes_reliable: int = 10
    min_dns_lookups: int = 2
    min_lost_packets: int = 2
    loss_warn_pct: float = 10.0
    dns_fail_ratio: float = 0.5
    dns_slow_ms: float = 300.0
    latency_high_ms: float = 150.0
    congestion_latency_ratio: float = 2.0
    congestion_latency_abs_ms: float = 30.0
    congestion_jitter_ratio: float = 2.0
    congestion_jitter_abs_ms: float = 10.0
    congestion_loss_increase_pct: float = 3.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RuleResult:
    rule_id: str
    name: str
    state: str  # "FIRED", "not fired", "not evaluated", "CONFLICT"
    detail: str


@dataclass
class Finding:
    rule_id: str
    label: str
    confidence: str
    explanation: str
    evidence: List[str]
    reasons: List[str]


@dataclass
class Diagnosis:
    status: str  # "fault", "normal" or "inconclusive"
    label: str
    confidence: str  # High / Medium / Low, or "Not applicable" when inconclusive
    rule_id: str
    explanation: str
    evidence: List[str] = field(default_factory=list)
    confidence_reasons: List[str] = field(default_factory=list)
    rules: List[RuleResult] = field(default_factory=list)
    secondary: List[str] = field(default_factory=list)
    additional_tests: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=lambda: list(LIMITATIONS))

    @property
    def is_inconclusive(self) -> bool:
        return self.status == "inconclusive"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


ADDITIONAL_TESTS = {
    "R1": [
        "Check the cable / Wi-Fi connection to the router and that the router is powered on.",
        "Try reaching the router from a second device.",
        "Restart the router, then run this diagnosis again.",
    ],
    "R2": [
        "Repeat the DNS check with a different public DNS server (for example 1.1.1.1 or 8.8.8.8) set on this computer.",
        "Run `nslookup <domain>` manually and compare with the result shown here.",
        "Check whether opening a site by IP address works while names do not.",
    ],
    "R3": [
        "Repeat the DNS test several times to see whether slow lookups are constant.",
        "Compare with a different DNS server.",
    ],
    "R4": [
        "Repeat the test at another time and with a wired connection if possible.",
        "Ping a second external target to check whether the loss follows one server.",
        "If loss is seen at the router too, check the Wi-Fi/cable segment first.",
    ],
    "R5": [
        "Repeat the test at another time of day.",
        "Run the busy-link test to check whether delay grows under load.",
        "Ping a second external target.",
    ],
    "R6": [
        "Repeat the busy-link test a few times; congestion hints should appear again.",
        "Pause other downloads/streaming in the home and test again.",
        "Run the same test at a different time of day.",
    ],
    "NORMAL": ["No extra test needed. Re-run when the problem is happening to capture evidence."],
}


# ------------------------------------------------------------------------------------------
def _usable(stats: Optional[ProbeStats], min_probes: int) -> bool:
    return stats is not None and stats.available and stats.sent >= min_probes


def _probe_line(label: str, s: ProbeStats) -> str:
    median = f"{s.median_ms} ms" if s.median_ms is not None else "n/a"
    jitter = f"{s.jitter_ms} ms" if s.jitter_ms is not None else "n/a"
    return (f"{label} ({s.target}): {s.received}/{s.sent} replies, loss {s.loss_pct}%, "
            f"median {median}, jitter {jitter}")


def _lower(level: str) -> str:
    return LEVELS[max(0, LEVELS.index(level) - 1)]


def _cap(level: str, maximum: str) -> str:
    return LEVELS[min(LEVELS.index(level), LEVELS.index(maximum))]


def diagnose(bundle: EvidenceBundle, th: Optional[Thresholds] = None) -> Diagnosis:
    """Apply the decision rules to the measurements and explain the result."""
    th = th or Thresholds()
    router, ext, dns, loaded = bundle.router, bundle.external_baseline, bundle.dns, bundle.external_loaded

    router_ok = _usable(router, th.min_router_probes)
    ext_ok = _usable(ext, th.min_probes_reliable)
    dns_ok = dns is not None and len(dns.lookups) >= th.min_dns_lookups
    loaded_ok = _usable(loaded, th.min_probes_reliable) and bool(bundle.load and bundle.load.applied)

    router_down = router_ok and router.received == 0
    ext_down = ext_ok and ext.received == 0
    ext_replies = ext_ok and ext.received > 0

    rules: List[RuleResult] = []
    findings: Dict[str, Finding] = {}
    missing = []
    if not router_ok:
        missing.append("router check")
    if not dns_ok:
        missing.append("DNS check")
    if not ext_ok:
        missing.append("external latency/loss check")

    # ---- R0: is there enough data at all? --------------------------------------------------
    usable_count = 3 - len(missing)
    rules.append(RuleResult(
        "R0", "Enough measurements available",
        "not fired" if usable_count >= 2 else "FIRED",
        f"{usable_count} of 3 core checks usable" + (f" (missing: {', '.join(missing)})" if missing else "") + ".",
    ))

    # ---- R1: router unreachable -----------------------------------------------------------
    if not router_ok:
        rules.append(RuleResult("R1", "Router unreachable", "not evaluated",
                                "Router check unavailable or too few probes."))
    elif router_down:
        reasons = [f"All {router.sent} router probes got no reply."]
        conf = "Medium"
        if ext_down:
            conf = "High"
            reasons.append("The external target also failed, which is consistent with a problem at the router or home network.")
        else:
            reasons.append("No external result to cross-check, so confidence is limited to Medium.")
        findings["R1"] = Finding(
            "R1", "Router / home network unreachable", conf,
            "The default gateway did not answer any of the repeated checks, so the problem is likely at the "
            "router, Wi-Fi or this device's connection to it. The tool does not say what physically caused it.",
            [_probe_line("Router", router)], reasons)
        rules.append(RuleResult("R1", "Router unreachable", "FIRED", f"0/{router.sent} router replies."))
    else:
        rules.append(RuleResult("R1", "Router unreachable", "not fired",
                                f"Router replied to {router.received}/{router.sent} probes."))

    # ---- R2: DNS failure ------------------------------------------------------------------
    if router_down:
        rules.append(RuleResult("R2", "DNS failure", "not evaluated",
                                "Skipped: DNS failures are expected when the router is unreachable."))
    elif not dns_ok:
        rules.append(RuleResult("R2", "DNS failure", "not evaluated", "DNS check unavailable or too few lookups."))
    else:
        ratio = dns.failure_ratio
        failed = len(dns.lookups) - dns.success_count
        server = dns.server_tested or "operating-system resolver"
        if ratio >= th.dns_fail_ratio:
            reasons = [f"{failed} of {len(dns.lookups)} name lookups failed (limit: {th.dns_fail_ratio:.0%} or more)."]
            if ext_replies:
                reasons.append("A direct IP check (ping) to the external target worked, so the link itself is up.")
                conf = "High" if ratio == 1.0 and len(dns.lookups) >= 3 else "Medium"
            else:
                reasons.append("No direct IP check available to compare with, so confidence is Low.")
                conf = "Low"
            findings["R2"] = Finding(
                "R2", "DNS failure", conf,
                "Website names fail to resolve while direct IP checks work, so the likely problem is DNS "
                f"(server tested: {server}).",
                [f"DNS ({server}): {failed}/{len(dns.lookups)} lookups failed; errors: "
                 + ", ".join(sorted({x.error for x in dns.lookups if not x.success})),
                 _probe_line("Direct IP check", ext) if ext_replies else "Direct IP check: not available"],
                reasons)
            rules.append(RuleResult("R2", "DNS failure", "FIRED", f"{failed}/{len(dns.lookups)} lookups failed."))
        elif ratio > 0:
            findings["R2"] = Finding(
                "R2", "Intermittent DNS lookup failures", "Low",
                f"Some website names failed to resolve ({failed} of {len(dns.lookups)}) while others worked. "
                "This may be a DNS problem or a temporary glitch.",
                [f"DNS ({server}): {failed}/{len(dns.lookups)} lookups failed"],
                ["Only a minority of lookups failed, so confidence is Low."])
            rules.append(RuleResult("R2", "DNS failure", "FIRED", f"{failed}/{len(dns.lookups)} failed (below the {th.dns_fail_ratio:.0%} limit; Low confidence)."))
        else:
            rules.append(RuleResult("R2", "DNS failure", "not fired", f"All {len(dns.lookups)} lookups succeeded."))

    # ---- R3: slow DNS ---------------------------------------------------------------------
    if not dns_ok or router_down:
        rules.append(RuleResult("R3", "Slow DNS", "not evaluated", "No usable DNS result."))
    elif dns.failure_ratio < th.dns_fail_ratio and dns.median_ms is not None and dns.median_ms > th.dns_slow_ms:
        findings["R3"] = Finding(
            "R3", "Slow DNS lookups", "Medium" if len(dns.lookups) >= 3 else "Low",
            "Names resolve, but slowly, which can make pages feel slow even when the connection itself is fine.",
            [f"Median DNS lookup time {dns.median_ms} ms (limit {th.dns_slow_ms:.0f} ms)"],
            [f"Median lookup time is above the {th.dns_slow_ms:.0f} ms limit over {len(dns.lookups)} lookups."])
        rules.append(RuleResult("R3", "Slow DNS", "FIRED", f"Median {dns.median_ms} ms > {th.dns_slow_ms:.0f} ms."))
    else:
        median = f"{dns.median_ms} ms" if dns.median_ms is not None else "n/a"
        rules.append(RuleResult("R3", "Slow DNS", "not fired", f"Median lookup time {median} (limit {th.dns_slow_ms:.0f} ms)."))

    # ---- R4: added packet loss ------------------------------------------------------------
    router_lossy = router_ok and not router_down and is_loss_significant(router, th.loss_warn_pct, th.min_lost_packets)
    ext_lossy = ext_replies and is_loss_significant(ext, th.loss_warn_pct, th.min_lost_packets)
    if router_down or not (router_ok or ext_ok):
        rules.append(RuleResult("R4", "Packet loss", "not evaluated", "No usable ping data to compare."))
    elif router_lossy or ext_lossy:
        worst = max(s.loss_pct for s, flag in ((router, router_lossy), (ext, ext_lossy)) if flag)
        sent_ok = (ext.sent if ext_lossy else router.sent)
        conf = "High" if worst >= 2 * th.loss_warn_pct and sent_ok >= 2 * th.min_probes_reliable else "Medium"
        scope = "on the local segment (device, Wi-Fi or router)" if router_lossy else "beyond the router"
        ev = []
        if router_ok:
            ev.append(_probe_line("Router", router))
        if ext_ok:
            ev.append(_probe_line("External target", ext))
        findings["R4"] = Finding(
            "R4", "Packet loss " + ("on local segment" if router_lossy else "beyond the router"), conf,
            f"A share of ping probes got no reply {scope} (worst loss {worst}%). The tool does not guess how the loss happened.",
            ev,
            [f"Loss is at or above {th.loss_warn_pct}% with at least {th.min_lost_packets} lost probes.",
             f"Highest loss {worst}% (High needs at least {2 * th.loss_warn_pct}% over {2 * th.min_probes_reliable}+ probes)."])
        rules.append(RuleResult("R4", "Packet loss", "FIRED", f"Worst loss {worst}% (limit {th.loss_warn_pct}%)."))
    else:
        rules.append(RuleResult("R4", "Packet loss", "not fired", f"Loss below {th.loss_warn_pct}% (or fewer than {th.min_lost_packets} lost probes)."))

    # ---- R5: high latency -----------------------------------------------------------------
    if not ext_replies or router_down:
        rules.append(RuleResult("R5", "High latency", "not evaluated", "No external latency available."))
    elif ext.median_ms is not None and ext.median_ms > th.latency_high_ms:
        local = router_ok and router.median_ms is not None and router.median_ms > th.latency_high_ms
        findings["R5"] = Finding(
            "R5", "High latency" + (" on the home network" if local else ""), "Medium" if router_ok else "Low",
            "Replies are slow even without extra load. " + (
                "The router itself answers slowly, so the delay starts on the home network."
                if local else "The router answers normally, so the extra delay is beyond the home network."),
            [_probe_line("External target", ext)] + ([_probe_line("Router", router)] if router_ok else []),
            [f"Median external latency {ext.median_ms} ms is above the {th.latency_high_ms:.0f} ms limit."])
        rules.append(RuleResult("R5", "High latency", "FIRED", f"Median {ext.median_ms} ms > {th.latency_high_ms:.0f} ms."))
    else:
        rules.append(RuleResult("R5", "High latency", "not fired", f"Median {ext.median_ms} ms (limit {th.latency_high_ms:.0f} ms)."))

    # ---- R6: congestion hint --------------------------------------------------------------
    baseline_bad = ext_ok and ((ext.median_ms or 0) > th.latency_high_ms or is_loss_significant(ext, th.loss_warn_pct, th.min_lost_packets))
    if router_down or not ext_replies:
        rules.append(RuleResult("R6", "Congestion hint (busy link)", "not evaluated", "No usable baseline."))
    elif not loaded_ok:
        why = bundle.load.error if bundle.load and bundle.load.error else "Busy-link test was not run or produced too little data."
        rules.append(RuleResult("R6", "Congestion hint (busy link)", "not evaluated", why))
    elif baseline_bad:
        rules.append(RuleResult("R6", "Congestion hint (busy link)", "not evaluated",
                                "The normal baseline is already degraded, so a busy-link comparison would be unreliable."))
    else:
        indicators = []
        if loaded.median_ms is not None and ext.median_ms is not None:
            inc = loaded.median_ms - ext.median_ms
            if inc >= th.congestion_latency_abs_ms and loaded.median_ms >= th.congestion_latency_ratio * ext.median_ms:
                indicators.append(f"Median latency rose from {ext.median_ms} ms to {loaded.median_ms} ms")
        if loaded.jitter_ms is not None:
            base_j = max(ext.jitter_ms or 0.0, 1.0)
            if loaded.jitter_ms - base_j >= th.congestion_jitter_abs_ms and loaded.jitter_ms >= th.congestion_jitter_ratio * base_j:
                indicators.append(f"Jitter rose from {ext.jitter_ms} ms to {loaded.jitter_ms} ms")
        if (loaded.loss_pct or 0) - (ext.loss_pct or 0) >= th.congestion_loss_increase_pct:
            indicators.append(f"Packet loss rose from {ext.loss_pct}% to {loaded.loss_pct}%")
        if indicators:
            conf = {1: "Low", 2: "Medium"}.get(len(indicators), "High")
            findings["R6"] = Finding(
                "R6", "Possible congestion (busy link)", conf,
                "Delay, jitter or loss gets worse when the link is busy, which is a hint of queueing (congestion). "
                "This is a hint only; it is not proof of a fault in the ISP network.",
                indicators + [_probe_line("Normal", ext), _probe_line("Busy link", loaded)],
                [f"{len(indicators)} of 3 indicators (latency, jitter, loss) got clearly worse under load: High = 3, Medium = 2, Low = 1."])
            rules.append(RuleResult("R6", "Congestion hint (busy link)", "FIRED", f"{len(indicators)} of 3 indicators worse under load."))
        else:
            rules.append(RuleResult("R6", "Congestion hint (busy link)", "not fired",
                                    "Latency, jitter and loss stayed close to the normal baseline under load."))

    # ---- Conflicts ------------------------------------------------------------------------
    conflicts: List[str] = []
    if router_down and ext_replies:
        conflicts.append(
            f"The router did not answer any of {router.sent} probes, but the external target replied to "
            f"{ext.received}/{ext.sent}. The router may be ignoring ping, so a router fault cannot be confirmed.")
    if ext_down and not router_down:
        state = "answered" if router_ok else "was not checked"
        conflicts.append(
            f"The external target did not reply to any of {ext.sent} probes while the router {state}. "
            "This could be an outage beyond the home network, or the target ignoring ping; the tool cannot tell which.")
    for text in conflicts:
        rules.append(RuleResult("C", "Conflicting evidence", "CONFLICT", text))

    # ---- Final decision -------------------------------------------------------------------
    def build(status, label, conf, rule_id, explanation, evidence, reasons, secondary=None, tests=None):
        return Diagnosis(status, label, conf, rule_id, explanation, evidence, reasons, rules,
                         secondary or [], tests or [])

    if conflicts:
        return build(
            "inconclusive", "Inconclusive", "Not applicable", "C",
            "The measurements disagree, so the tool will not guess. " + " ".join(conflicts),
            [x for x in (_probe_line("Router", router) if router_ok else "", _probe_line("External target", ext) if ext_ok else "") if x],
            ["Conflicting evidence: no cause can be named safely."],
            tests=["Ping a second external target (for example 8.8.8.8) and compare.",
                   "Ping the router from another device.",
                   "Repeat the full diagnosis a few minutes later.",
                   "Check whether the router/target blocks ping (ICMP)."])

    if usable_count < 2:
        return build(
            "inconclusive", "Inconclusive", "Not applicable", "R0",
            f"Not enough usable measurements to find a cause (missing: {', '.join(missing)}).",
            [], ["Fewer than 2 of the 3 core checks produced usable data."],
            tests=["Run the diagnosis again with ping and DNS lookups allowed on this computer.",
                   "Enter the router address manually in the sidebar if it was not detected.",
                   "Increase the number of probes in the sidebar."])

    if "R1" in findings:
        primary = findings["R1"]
        others: List[Finding] = []
    else:
        order = ["R2", "R4", "R6", "R5", "R3"]
        active = [findings[k] for k in order if k in findings]
        primary, others = (active[0], active[1:]) if active else (None, [])

    if primary is None:
        if len(missing) == 0:
            reasons = ["Router, DNS and external checks all ran, and no rule fired."]
            conf = "Medium"
            if loaded_ok:
                conf = "High"
                reasons.append("The busy-link comparison also stayed close to the baseline.")
            else:
                reasons.append("The busy-link comparison was not available, so confidence is Medium.")
            ev = [_probe_line("Router", router), _probe_line("External target", ext),
                  f"DNS: {dns.success_count}/{len(dns.lookups)} lookups ok, median {dns.median_ms} ms"]
            if loaded_ok:
                ev.append(_probe_line("Busy link", loaded))
            return build("normal", "No fault detected", conf, "R7",
                         "All measured values are within the proposed limits. If the problem comes and goes, run the test again while it is happening.",
                         ev, reasons, tests=ADDITIONAL_TESTS["NORMAL"])
        return build(
            "inconclusive", "Inconclusive", "Not applicable", "R0",
            f"No rule fired, but some checks are missing ({', '.join(missing)}), so 'normal' cannot be confirmed.",
            [], ["Incomplete data."],
            tests=["Run the missing checks and repeat the diagnosis."])

    conf = primary.confidence
    reasons = list(primary.reasons)
    secondary = [f"{o.label} ({o.confidence} confidence)" for o in others]
    if others:
        conf = _lower(conf)
        reasons.append("More than one issue was seen, so confidence was lowered one level and the order of causes is uncertain.")
    if not router_ok and primary.rule_id != "R1":
        conf = _cap(conf, "Medium")
        reasons.append("The router check was unavailable, so confidence is capped at Medium.")
    tests = list(ADDITIONAL_TESTS.get(primary.rule_id, []))
    return build("fault", primary.label, conf, primary.rule_id, primary.explanation,
                 primary.evidence, reasons, secondary, tests)
