from src.anomaly import detect_network_anomalies


def ready_baseline():
    return {
        "ready": True,
        "latency_ms": 40,
        "jitter_ms": 5,
        "packet_loss_pct": 1,
    }


def test_baseline_not_ready():
    result = detect_network_anomalies(
        {"latency_ms": 50},
        {"ready": False},
    )
    assert result["ready"] is False
    assert result["anomalies"] == []


def test_normal_metrics_no_anomaly():
    current = {
        "latency_ms": 45,
        "jitter_ms": 6,
        "packet_loss_pct": 1.5,
    }
    result = detect_network_anomalies(current, ready_baseline())

    assert result["ready"] is True
    assert result["anomaly_detected"] is False


def test_high_latency_detected():
    current = {
        "latency_ms": 70,
        "jitter_ms": 5,
        "packet_loss_pct": 1,
    }
    result = detect_network_anomalies(current, ready_baseline())

    assert any(a["metric"] == "Latency" for a in result["anomalies"])


def test_high_jitter_detected():
    current = {
        "latency_ms": 40,
        "jitter_ms": 10,
        "packet_loss_pct": 1,
    }
    result = detect_network_anomalies(current, ready_baseline())

    assert any(a["metric"] == "Jitter" for a in result["anomalies"])


def test_high_packet_loss_detected():
    current = {
        "latency_ms": 40,
        "jitter_ms": 5,
        "packet_loss_pct": 3,
    }
    result = detect_network_anomalies(current, ready_baseline())

    assert any(a["metric"] == "Packet loss" for a in result["anomalies"])


def test_zero_baseline_detects_positive_value():
    baseline = {
        "ready": True,
        "latency_ms": 0,
        "jitter_ms": 0,
        "packet_loss_pct": 0,
    }
    current = {
        "latency_ms": 10,
        "jitter_ms": 0,
        "packet_loss_pct": 0,
    }

    result = detect_network_anomalies(current, baseline)

    assert result["anomaly_detected"] is True


def test_missing_metrics_are_skipped():
    result = detect_network_anomalies(
        {"latency_ms": None},
        ready_baseline(),
    )

    assert result["anomalies"] == []