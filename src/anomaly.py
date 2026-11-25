"""Personalized network anomaly detection."""

from typing import Any, Dict, Optional


def detect_network_anomalies(
    current: Dict[str, Any],
    baseline: Dict[str, Any],
) -> Dict[str, Any]:
    """Compare current network metrics against historical baseline."""

    if not baseline.get("ready"):
        return {
            "ready": False,
            "anomalies": [],
            "message": "Historical baseline is not ready.",
        }

    anomalies = []

    checks = [
        ("latency_ms", "Latency", 1.5, "ms"),
        ("jitter_ms", "Jitter", 1.5, "ms"),
        ("packet_loss_pct", "Packet loss", 2.0, "%"),
    ]

    for key, label, multiplier, unit in checks:
        current_value = current.get(key)
        baseline_value = baseline.get(key)

        if current_value is None or baseline_value is None:
            continue

        if baseline_value == 0:
            unusual = current_value > 0
        else:
            unusual = current_value > baseline_value * multiplier

        if unusual:
            anomalies.append({
                "metric": label,
                "current": current_value,
                "baseline": baseline_value,
                "unit": unit,
                "message": (
                    f"{label} is unusually high: "
                    f"{current_value} {unit} compared with "
                    f"your typical {baseline_value} {unit}."
                ),
            })

    return {
        "ready": True,
        "anomaly_detected": bool(anomalies),
        "anomalies": anomalies,
        "message": (
            "Unusual network performance detected."
            if anomalies
            else "Network performance is within your historical range."
        ),
    }