"""Scenario-aware, explainable network troubleshooting recommendations."""

from typing import Any, Dict, List, Optional


def generate_recommendations(
    diagnosis: str,
    latency_ms: Optional[float] = None,
    jitter_ms: Optional[float] = None,
    packet_loss_pct: Optional[float] = None,
    diagnosis_rule: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate actionable recommendations using diagnosis rule and measured metrics.

    The optional diagnosis_rule keeps the original public API backwards compatible
    while allowing the dashboard to provide targeted advice for rule-based findings.
    """
    recommendations: List[Dict[str, str]] = []

    rule_actions = {
        "R1": (
            "Router unreachable",
            "Check that the router is powered on and reconnect your device to Wi-Fi or Ethernet.",
            "The router did not respond to the local reachability checks, so internet-side checks cannot establish a healthy home connection.",
        ),
        "R2": (
            "DNS resolution failure",
            "Check the configured DNS server and retry with a trusted alternative DNS resolver.",
            "Direct network reachability can work while domain-name lookups fail; DNS must translate website names into IP addresses.",
        ),
        "R3": (
            "Slow DNS resolution",
            "Compare another DNS resolver and repeat lookups at a different time.",
            "Slow name resolution can delay opening websites even when the underlying connection responds.",
        ),
        "R4": (
            "Packet loss",
            "Check Wi-Fi signal and router cables; repeat the test against another external target.",
            "Missing ping replies indicate packet loss, but do not by themselves prove whether Wi-Fi, the router, or the wider path caused it.",
        ),
        "R5": (
            "High latency",
            "Pause background downloads, repeat the test, and compare with a second external target.",
            "High response time can make browsing and real-time applications feel slow.",
        ),
        "R6": (
            "Congestion under load",
            "Pause large downloads or streaming, reduce competing traffic, and repeat the busy-link test.",
            "Latency, jitter or packet loss increased under load, which is evidence of a busy-link problem.",
        ),
        "R-IF": (
            "Network interface disconnected",
            "Turn on Wi-Fi or reconnect the Ethernet cable, then run the diagnosis again.",
            "The device's network interface is disconnected, so the remaining connectivity checks cannot be trusted.",
        ),
        "C": (
            "Conflicting evidence — verify with another test",
            "Repeat the test from a second device and compare router reachability with direct internet access.",
            "The measurements disagree, so the app avoids assigning a fault without additional evidence.",
        ),
        "R0": (
            "Insufficient measurements",
            "Reconnect the device, confirm the router address, and rerun the full diagnosis.",
            "Some required measurements were unavailable, so the cause cannot be determined reliably.",
        ),
    }

    if diagnosis_rule in rule_actions:
        problem, action, reason = rule_actions[diagnosis_rule]
        recommendations.append({"problem": problem, "action": action, "reason": reason})

    # Add metric-specific advice where it contributes new information.
    if packet_loss_pct is not None and packet_loss_pct > 2 and diagnosis_rule != "R4":
        recommendations.append({
            "problem": "High packet loss",
            "action": "Check router cables and Wi-Fi signal strength, then repeat the test.",
            "reason": f"{packet_loss_pct:.1f}% of probes were lost; missing replies can disrupt calls and streaming.",
        })

    if latency_ms is not None and latency_ms > 100 and diagnosis_rule not in ("R5", "R6"):
        recommendations.append({
            "problem": "High latency",
            "action": "Reduce background downloads and move closer to the router.",
            "reason": f"Median latency was {latency_ms:.1f} ms, which can cause noticeable response delays.",
        })

    if jitter_ms is not None and jitter_ms > 30:
        recommendations.append({
            "problem": "High jitter",
            "action": "Use a wired Ethernet connection if possible and reduce competing network traffic.",
            "reason": f"Jitter was {jitter_ms:.1f} ms; variable delay can affect calls and gaming.",
        })

    if not recommendations:
        recommendations.append({
            "problem": "No major metric issue detected",
            "action": "Continue monitoring your network performance.",
            "reason": "The measured latency, jitter and packet loss are within the configured recommendation thresholds.",
        })

    return {
        "diagnosis": diagnosis,
        "recommendations": recommendations,
        "count": len(recommendations),
    }
