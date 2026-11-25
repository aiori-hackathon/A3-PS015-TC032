"""Network health score calculation."""


def calculate_health_score(
    latency_ms,
    jitter_ms,
    packet_loss_pct,
):
    """Calculate an explainable network health score from 0 to 100."""

    metrics = {
        "latency": latency_ms,
        "jitter": jitter_ms,
        "packet_loss": packet_loss_pct,
    }

    if any(value is None or value < 0 for value in metrics.values()):
        return {
            "ready": False,
            "score": None,
            "grade": "Unavailable",
            "breakdown": {},
            "message": "Valid network metrics are required.",
        }

    latency_score = max(0, 100 - (latency_ms / 2))
    jitter_score = max(0, 100 - (jitter_ms * 2))
    loss_score = max(0, 100 - (packet_loss_pct * 10))

    score = round(
        latency_score * 0.4
        + jitter_score * 0.3
        + loss_score * 0.3
    )

    if score >= 90:
        grade = "Excellent"
    elif score >= 75:
        grade = "Good"
    elif score >= 50:
        grade = "Fair"
    else:
        grade = "Poor"

    return {
        "ready": True,
        "score": score,
        "grade": grade,
        "breakdown": {
            "latency": round(latency_score),
            "jitter": round(jitter_score),
            "packet_loss": round(loss_score),
        },
        "message": f"Network health is {grade.lower()} ({score}/100).",
    }