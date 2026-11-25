"""Smart network troubleshooting recommendations."""

from typing import Any, Dict, List


def generate_recommendations(
    diagnosis: str,
    latency_ms: float = None,
    jitter_ms: float = None,
    packet_loss_pct: float = None,
) -> Dict[str, Any]:
    """Generate actionable recommendations from network metrics."""

    recommendations: List[Dict[str, str]] = []

    if packet_loss_pct is not None and packet_loss_pct > 2:
        recommendations.append({
            "problem": "High packet loss",
            "action": "Check router cables and Wi-Fi signal strength.",
            "reason": "Packet loss means some network packets are not reaching their destination.",
        })

    if latency_ms is not None and latency_ms > 100:
        recommendations.append({
            "problem": "High latency",
            "action": "Reduce background downloads and move closer to the router.",
            "reason": "High latency causes delays in network communication.",
        })

    if jitter_ms is not None and jitter_ms > 30:
        recommendations.append({
            "problem": "High jitter",
            "action": "Use a wired Ethernet connection and reduce network congestion.",
            "reason": "High jitter means network delay varies significantly.",
        })

    if not recommendations:
        recommendations.append({
            "problem": "No major metric issue detected",
            "action": "Continue monitoring your network performance.",
            "reason": "Current latency, jitter and packet loss are within the configured thresholds.",
        })

    return {
        "diagnosis": diagnosis,
        "recommendations": recommendations,
        "count": len(recommendations),
    }