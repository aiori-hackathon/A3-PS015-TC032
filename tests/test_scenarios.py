"""Scenario tests: the lab simulator + decision engine, plus performance, report and orchestrator checks."""
import pytest

from src.diagnosis import diagnose
from src.models import SOURCE_SIMULATED, TestSettings
from src.orchestrator import run_live_diagnosis
from src.performance import LoadGenerator, compare_stats, measure_loaded
from src.report_generator import generate_html_report, generate_markdown_report, report_filename, save_report
from src.simulator import SCENARIOS, run_all_scenarios, simulate_scenario

SEEDS = [1, 7, 42, 123, 2026]


@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize("key", list(SCENARIOS))
def test_each_scenario_gives_expected_result_for_many_seeds(key, seed):
    info = SCENARIOS[key]
    diag = diagnose(simulate_scenario(key, seed))
    assert diag.status == info.expected_status
    assert diag.rule_id == info.expected_rule


def test_all_scenarios_helper_matches():
    assert all(row["match"] for row in run_all_scenarios())


def test_simulated_data_is_always_labelled():
    for key in SCENARIOS:
        b = simulate_scenario(key)
        assert b.source == SOURCE_SIMULATED and b.is_simulated
        assert any("SIMULATED" in n for n in b.notes)


def test_same_seed_same_numbers():
    a = simulate_scenario("congestion", 5).external_loaded.sequence
    b = simulate_scenario("congestion", 5).external_loaded.sequence
    assert a == b


def test_unknown_scenario_raises():
    with pytest.raises(KeyError):
        simulate_scenario("nope")


def test_inconclusive_scenarios_have_no_confidence_and_suggest_tests():
    for key in ("inconclusive_conflict", "inconclusive_missing"):
        d = diagnose(simulate_scenario(key))
        assert d.confidence == "Not applicable" and d.additional_tests


# ---- reports -------------------------------------------------------------------------------
@pytest.mark.parametrize("key", list(SCENARIOS))
def test_report_contains_required_sections(key):
    b = simulate_scenario(key)
    d = diagnose(b)
    md = generate_markdown_report(b, d)
    for heading in ("Data source", "Test settings", "Measurements: ping tests", "Measurements: DNS lookups",
                    "Diagnosis", "Supporting evidence", "Why this confidence level", "Limitations", "Rules checked"):
        assert f"## {heading}" in md
    assert "SIMULATED" in md and d.label in md
    html = generate_html_report(b, d)
    assert html.startswith("<!DOCTYPE html>") and "SIMULATED" in html


def test_report_filename_and_save(tmp_path):
    b = simulate_scenario("normal")
    name = report_filename(b, "md")
    assert "SIMULATED" in name and name.endswith(".md")
    path = save_report("hello", name, str(tmp_path))
    assert open(path, encoding="utf-8").read() == "hello"


def test_html_report_escapes_text():
    b = simulate_scenario("normal")
    b.notes.append("<script>alert(1)</script>")
    assert "<script>alert(1)</script>" not in generate_html_report(b, diagnose(b))


# ---- performance / load --------------------------------------------------------------------
def test_compare_stats_rows():
    b = simulate_scenario("congestion")
    rows = compare_stats(b.external_baseline, b.external_loaded)
    assert [r["Metric"] for r in rows] == ["Median latency", "Jitter", "Packet loss"]
    assert rows[0]["Change"] > 100
    assert compare_stats(None, b.external_loaded) == []


class FakeResponse:
    def __init__(self, size=300_000):
        self.left = size
    def read(self, n):
        n = min(n, self.left)
        self.left -= n
        return b"x" * n
    def __enter__(self):
        return self
    def __exit__(self, *a):
        return False


def test_measure_loaded_reports_applied_load():
    factory = lambda url, threads: LoadGenerator(url, threads, opener=lambda req, timeout: FakeResponse(2_000_000))
    stats, info = measure_loaded("1.1.1.1", 5, "http://example.invalid/file", 2, interval_s=0,
                                 ping_fn=lambda h, t: 40.0, generator_factory=factory, warmup_s=0.2)
    assert stats.received == 5 and info.applied and info.bytes_downloaded >= 500_000


def test_measure_loaded_says_when_load_failed():
    def failing(req, timeout):
        raise OSError("blocked")
    factory = lambda url, threads: LoadGenerator(url, threads, opener=failing)
    stats, info = measure_loaded("1.1.1.1", 5, "http://example.invalid/file", 2, interval_s=0,
                                 ping_fn=lambda h, t: 40.0, generator_factory=factory, warmup_s=0.1)
    assert not info.applied and "not established" in info.error and "blocked" in info.error


# ---- orchestrator (real code path, fake network) --------------------------------------------
def fake_dns_resolver(domain, server, timeout):
    from src.models import DnsLookup
    return DnsLookup(domain, True, 20.0, "")


def test_orchestrator_builds_complete_bundle_and_diagnosis():
    settings = TestSettings(router_probes=5, external_probes=10, probe_interval_s=0, run_load_test=False,
                            gateway_override="192.168.1.1")
    steps = []
    b = run_live_diagnosis(settings, progress=lambda f, m: steps.append(m), ping_fn=lambda h, t: 5.0,
                           dns_resolver=fake_dns_resolver, dns_servers=["192.168.1.1"])
    assert b.source == "real" and not b.is_simulated
    assert b.router.received == 5 and b.external_baseline.received == 10 and b.dns.success_count == 5
    assert b.external_loaded is None and any("switched off" in n for n in b.notes)
    assert diagnose(b).status == "normal"
    assert steps and "Step 5/5" in steps[-1]


def test_orchestrator_with_load_test_uses_load_generator():
    settings = TestSettings(router_probes=5, external_probes=10, probe_interval_s=0, gateway_override="192.168.1.1")
    factory = lambda url, threads: LoadGenerator(url, threads, opener=lambda req, timeout: FakeResponse(2_000_000))
    b = run_live_diagnosis(settings, ping_fn=lambda h, t: 5.0, dns_resolver=fake_dns_resolver,
                           dns_servers=["192.168.1.1"], load_generator_factory=factory)
    assert b.load.applied and b.external_loaded.received == 10
    assert diagnose(b).confidence == "High"


def test_orchestrator_handles_ping_unavailable():
    from src.latency_check import PingUnavailable
    def no_ping(host, timeout):
        raise PingUnavailable("ping command not found")
    settings = TestSettings(router_probes=5, external_probes=10, probe_interval_s=0, run_load_test=False,
                            gateway_override="192.168.1.1")
    b = run_live_diagnosis(settings, ping_fn=no_ping, dns_resolver=fake_dns_resolver, dns_servers=["192.168.1.1"])
    assert not b.router.available and not b.external_baseline.available
    assert diagnose(b).is_inconclusive
