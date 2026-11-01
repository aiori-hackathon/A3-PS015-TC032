"""Unit tests for the decision rules, using hand-made evidence."""
from src.diagnosis import Thresholds, diagnose
from src.latency_check import summarise
from src.models import DnsLookup, DnsResult, EvidenceBundle, LoadInfo


def probes(role, n, base, loss=0, spread=0.0):
    seq = [base + (i % 3) * spread for i in range(n)]
    for i in range(loss):
        seq[i * 2] = None  # lose every second probe up to `loss` times
    return summarise("t", role, seq)


def dns(ok=5, bad=0, ms=30.0):
    r = DnsResult(servers=["192.168.1.1"], server_tested="192.168.1.1", method="direct")
    r.lookups = [DnsLookup(f"ok{i}.com", True, ms, "") for i in range(ok)] + \
                [DnsLookup(f"bad{i}.com", False, None, "timeout") for i in range(bad)]
    return r


def bundle(router=None, ext=None, d=None, loaded=None, load_ok=True):
    return EvidenceBundle(router=router, external_baseline=ext, dns=d, external_loaded=loaded,
                          load=LoadInfo(applied=load_ok, bytes_downloaded=9_000_000) if loaded else None)


def healthy():
    return dict(router=probes("router", 10, 2), ext=probes("external", 20, 30), d=dns())


def test_normal_with_load_comparison_is_high():
    r = diagnose(bundle(**healthy(), loaded=probes("external", 20, 33)))
    assert (r.status, r.rule_id, r.confidence) == ("normal", "R7", "High")


def test_normal_without_load_comparison_is_medium():
    r = diagnose(bundle(**healthy()))
    assert (r.status, r.confidence) == ("normal", "Medium")


def test_router_unreachable_high_when_external_also_fails():
    r = diagnose(bundle(router=summarise("g", "router", [None] * 10),
                        ext=summarise("t", "external", [None] * 20), d=dns(0, 5)))
    assert (r.status, r.rule_id, r.confidence) == ("fault", "R1", "High")
    assert any(x.rule_id == "R2" and x.state == "not evaluated" for x in r.rules)


def test_router_down_but_internet_works_is_inconclusive_conflict():
    r = diagnose(bundle(router=summarise("g", "router", [None] * 10), ext=probes("external", 20, 30), d=dns()))
    assert r.is_inconclusive and r.rule_id == "C" and r.confidence == "Not applicable"
    assert r.additional_tests


def test_dns_failure_high_when_ip_checks_work():
    r = diagnose(bundle(router=probes("router", 10, 2), ext=probes("external", 20, 30), d=dns(0, 5)))
    assert (r.rule_id, r.confidence) == ("R2", "High")
    assert "192.168.1.1" in r.explanation


def test_dns_partial_failure_medium_and_minority_low():
    assert diagnose(bundle(**{**healthy(), "d": dns(2, 3)})).confidence == "Medium"
    low = diagnose(bundle(**{**healthy(), "d": dns(4, 1)}))
    assert low.rule_id == "R2" and low.confidence == "Low"


def test_slow_dns_rule():
    r = diagnose(bundle(**{**healthy(), "d": dns(5, 0, ms=450.0)}))
    assert r.rule_id == "R3"


def test_packet_loss_beyond_router():
    r = diagnose(bundle(router=probes("router", 10, 2), ext=summarise("t", "external", [30.0, None] * 4 + [30.0] * 12), d=dns()))
    assert r.rule_id == "R4" and "beyond the router" in r.label


def test_single_lost_probe_is_not_a_fault():
    seq = [30.0] * 19 + [None]
    r = diagnose(bundle(router=probes("router", 10, 2), ext=summarise("t", "external", seq), d=dns()))
    assert r.status == "normal"


def test_packet_loss_on_local_segment():
    router = summarise("g", "router", [2.0, None] * 3 + [2.0] * 4)  # 30% loss at the router
    r = diagnose(bundle(router=router, ext=probes("external", 20, 30), d=dns()))
    assert r.rule_id == "R4" and "local" in r.label


def test_congestion_needs_baseline_and_load_evidence():
    loaded = summarise("t", "external", [200.0, 40.0, 220.0, 60.0, 250.0] * 4)
    r = diagnose(bundle(**healthy(), loaded=loaded))
    assert r.rule_id == "R6" and r.confidence in ("Medium", "High")


def test_congestion_not_claimed_when_load_was_not_applied():
    loaded = summarise("t", "external", [200.0, 40.0, 220.0, 60.0, 250.0] * 4)
    r = diagnose(bundle(**healthy(), loaded=loaded, load_ok=False))
    assert r.rule_id != "R6"
    assert any(x.rule_id == "R6" and x.state == "not evaluated" for x in r.rules)


def test_congestion_not_evaluated_when_baseline_already_bad():
    ext = summarise("t", "external", [30.0, None] * 4 + [30.0] * 12)
    loaded = summarise("t", "external", [250.0] * 20)
    r = diagnose(bundle(router=probes("router", 10, 2), ext=ext, d=dns(), loaded=loaded))
    assert r.rule_id == "R4"
    assert any(x.rule_id == "R6" and "baseline" in x.detail for x in r.rules)


def test_high_latency_rule():
    r = diagnose(bundle(router=probes("router", 10, 2), ext=probes("external", 20, 220), d=dns()))
    assert r.rule_id == "R5" and "beyond the home network" in r.explanation


def test_external_down_with_router_ok_is_inconclusive():
    r = diagnose(bundle(router=probes("router", 10, 2), ext=summarise("t", "external", [None] * 20), d=dns(0, 5)))
    assert r.is_inconclusive and r.rule_id == "C"


def test_missing_data_is_inconclusive_not_a_guess():
    r = diagnose(bundle(ext=probes("external", 20, 30)))
    assert r.is_inconclusive and r.rule_id == "R0"


def test_no_rule_fired_but_router_check_missing_is_inconclusive():
    unavailable = summarise("x", "router", [])
    unavailable.available = False
    r = diagnose(bundle(router=unavailable, ext=probes("external", 20, 30), d=dns()))
    assert r.is_inconclusive


def test_multiple_issues_lower_confidence_and_are_listed():
    d = dns(0, 5)
    ext = summarise("t", "external", [30.0, None] * 4 + [30.0] * 12)
    r = diagnose(bundle(router=probes("router", 10, 2), ext=ext, d=d))
    assert r.rule_id == "R2" and r.secondary and r.confidence == "Medium"  # High lowered one level


def test_router_check_unavailable_caps_confidence_at_medium():
    unavailable = summarise("x", "router", [])
    unavailable.available = False
    r = diagnose(bundle(router=unavailable, ext=probes("external", 20, 30), d=dns(0, 5)))
    assert r.rule_id == "R2" and r.confidence == "Medium"


def test_thresholds_can_be_changed():
    ext = probes("external", 20, 100)
    assert diagnose(bundle(router=probes("router", 10, 2), ext=ext, d=dns())).status == "normal"
    assert diagnose(bundle(router=probes("router", 10, 2), ext=ext, d=dns()), Thresholds(latency_high_ms=80)).rule_id == "R5"


def test_every_diagnosis_lists_rules_and_limitations():
    r = diagnose(bundle(**healthy()))
    assert {x.rule_id for x in r.rules} >= {"R0", "R1", "R2", "R3", "R4", "R5", "R6"}
    assert any("not validated" in x or "validated" in x for x in r.limitations)
