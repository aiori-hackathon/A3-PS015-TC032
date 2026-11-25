from src.health_score import calculate_health_score


def test_excellent_network_score():
    result = calculate_health_score(10, 2, 0)

    assert result["ready"] is True
    assert result["score"] == 97
    assert result["grade"] == "Excellent"


def test_poor_network_score():
    result = calculate_health_score(250, 60, 10)

    assert result["score"] == 0
    assert result["grade"] == "Poor"


def test_good_network_score():
    result = calculate_health_score(30, 5, 1)

    assert result["grade"] == "Good"


def test_score_breakdown_available():
    result = calculate_health_score(20, 5, 1)

    assert "latency" in result["breakdown"]
    assert "jitter" in result["breakdown"]
    assert "packet_loss" in result["breakdown"]


def test_missing_metric_returns_unavailable():
    result = calculate_health_score(None, 5, 1)

    assert result["ready"] is False
    assert result["score"] is None


def test_negative_metric_returns_unavailable():
    result = calculate_health_score(20, -5, 1)

    assert result["ready"] is False