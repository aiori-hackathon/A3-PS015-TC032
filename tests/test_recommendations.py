from src.recommendations import generate_recommendations


def test_high_packet_loss_recommendation():
    result = generate_recommendations(
        "Network issue",
        packet_loss_pct=5,
    )

    assert result["count"] == 1
    assert result["recommendations"][0]["problem"] == "High packet loss"


def test_high_latency_recommendation():
    result = generate_recommendations(
        "Slow network",
        latency_ms=150,
    )

    assert result["recommendations"][0]["problem"] == "High latency"


def test_high_jitter_recommendation():
    result = generate_recommendations(
        "Unstable network",
        jitter_ms=40,
    )

    assert result["recommendations"][0]["problem"] == "High jitter"


def test_multiple_issues_recommendations():
    result = generate_recommendations(
        "Poor network",
        latency_ms=150,
        jitter_ms=40,
        packet_loss_pct=5,
    )

    assert result["count"] == 3


def test_healthy_network_recommendation():
    result = generate_recommendations(
        "Healthy network",
        latency_ms=30,
        jitter_ms=5,
        packet_loss_pct=0,
    )

    assert result["count"] == 1
    assert (
        result["recommendations"][0]["problem"]
        == "No major metric issue detected"
    )


def test_diagnosis_is_preserved():
    result = generate_recommendations("DNS issue")

    assert result["diagnosis"] == "DNS issue"