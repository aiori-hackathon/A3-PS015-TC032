"""Tests for SQLite diagnosis history."""
import json
from src.history import calculate_historical_baseline
from src.history import get_history, get_real_baseline_runs, save_run
from src.models import EvidenceBundle, ProbeStats, SOURCE_REAL, SOURCE_SIMULATED


def test_save_and_read_history(tmp_path):
    db = tmp_path / "test_history.db"
    bundle = EvidenceBundle(source=SOURCE_REAL, scenario="live")

    run_id = save_run(bundle, db_path=db)

    history = get_history(db_path=db)

    assert len(history) == 1
    assert history[0]["run_id"] == run_id
    assert history[0]["source"] == SOURCE_REAL
    assert history[0]["scenario"] == "live"
    assert history[0]["evidence"]["source"] == SOURCE_REAL


def test_simulated_runs_are_excluded_from_real_baseline(tmp_path):
    db = tmp_path / "test_history.db"

    real_bundle = EvidenceBundle(source=SOURCE_REAL, scenario="live")
    simulated_bundle = EvidenceBundle(source=SOURCE_SIMULATED, scenario="normal")

    save_run(real_bundle, db_path=db)
    save_run(simulated_bundle, db_path=db)

    assert len(get_history(db_path=db)) == 2

    baseline_runs = get_real_baseline_runs(db_path=db)

    assert len(baseline_runs) == 1
    assert baseline_runs[0]["source"] == SOURCE_REAL


def test_diagnosis_details_are_saved(tmp_path):
    db = tmp_path / "test_history.db"
    bundle = EvidenceBundle(source=SOURCE_REAL, scenario="live")

    class FakeDiagnosis:
        rule_id = "R5"
        label = "High latency"

    save_run(bundle, diagnosis=FakeDiagnosis(), db_path=db)

    history = get_history(db_path=db)

    assert history[0]["diagnosis_rule"] == "R5"
    assert history[0]["diagnosis_label"] == "High latency"


def test_history_limit_returns_latest_runs(tmp_path):
    db = tmp_path / "test_history.db"

    for scenario in ("first", "second", "third"):
        save_run(
            EvidenceBundle(source=SOURCE_REAL, scenario=scenario),
            db_path=db,
        )

    history = get_history(limit=2, db_path=db)

    assert len(history) == 2
    assert [item["scenario"] for item in history] == ["third", "second"]
def test_historical_baseline_waits_for_five_real_runs(tmp_path):
    db = tmp_path / "test_history.db"

    for _ in range(6):
        save_run(
            EvidenceBundle(source=SOURCE_SIMULATED, scenario="normal"),
            db_path=db,
        )

    baseline = calculate_historical_baseline(db_path=db)

    assert baseline["ready"] is False
    assert baseline["sample_count"] == 0
    assert baseline["latency_ms"] is None
    assert "5 more" in baseline["message"]
def test_historical_baseline_calculates_median_from_five_real_runs(tmp_path):
    db = tmp_path / "test_history.db"

    for latency in (20, 30, 40, 50, 60):
        bundle = EvidenceBundle(source=SOURCE_REAL, scenario="live")
        bundle.external_baseline = ProbeStats(
            target="1.1.1.1",
            available=True,
            median_ms=latency,
            jitter_ms=2.0,
            loss_pct=0.0,
        )
        save_run(bundle, db_path=db)

    baseline = calculate_historical_baseline(db_path=db)

    assert baseline["ready"] is True
    assert baseline["sample_count"] == 5
    assert baseline["latency_ms"] == 40.0
    assert baseline["jitter_ms"] == 2.0
    assert baseline["packet_loss_pct"] == 0.0