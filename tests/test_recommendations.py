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


def test_scenario_rules_get_targeted_recommendations():
    expected = {
        "R1": "Router unreachable",
        "R2": "DNS resolution failure",
        "R3": "Slow DNS resolution",
        "R4": "Packet loss",
        "R5": "High latency",
        "R6": "Congestion under load",
        "R-IF": "Network interface disconnected",
        "C": "Conflicting evidence — verify with another test",
        "R0": "Insufficient measurements",
    }
    for rule, problem in expected.items():
        result = generate_recommendations("Scenario diagnosis", diagnosis_rule=rule)
        assert result["recommendations"][0]["problem"] == problem


def test_dns_failure_does_not_fall_back_to_generic_healthy_advice():
    result = generate_recommendations("DNS failure", diagnosis_rule="R2")
    assert result["recommendations"][0]["problem"] == "DNS resolution failure"
    assert "DNS" in result["recommendations"][0]["action"]
