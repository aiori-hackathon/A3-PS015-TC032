"""Lab scenario simulator.

Creates SIMULATED measurements for the six required fault scenarios so the decision
rules can be checked safely, without touching a real network. Everything produced here
is marked source="simulated" and is shown as SIMULATED in the app and in reports.

Simulated results are NOT fault-injection results. Real fault-injection testing in the
lab (blocking the router/DNS, adding loss and load) is still a planned activity.

Run all scenarios from the command line:   python -m src.simulator
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List, Optional

from .latency_check import summarise
from .models import (SOURCE_SIMULATED, DnsLookup, DnsResult, EvidenceBundle, LoadInfo,
                     TestSettings)


@dataclass
class ScenarioInfo:
    key: str
    title: str
    description: str
    expected_status: str  # "normal", "fault" or "inconclusive"
    expected_rule: str    # rule id the engine should report


SCENARIOS: Dict[str, ScenarioInfo] = {
    "normal": ScenarioInfo("normal", "1. Normal network condition",
                           "Router, DNS, latency and loss are all healthy and the busy link barely changes anything.",
                           "normal", "R7"),
    "router_unreachable": ScenarioInfo("router_unreachable", "2. Router unreachable",
                                       "The router and everything behind it do not answer.", "fault", "R1"),
    "dns_failure": ScenarioInfo("dns_failure", "3. DNS failure",
                                "Direct IP pings work, but every website name lookup fails.", "fault", "R2"),
    "packet_loss": ScenarioInfo("packet_loss", "4. Added packet loss",
                                "The router is fine but 20% of probes to the outside get no reply.", "fault", "R4"),
    "congestion": ScenarioInfo("congestion", "5. Congestion / busy link",
                               "Healthy when idle, but latency, jitter and loss get much worse under load.", "fault", "R6"),
    "inconclusive_conflict": ScenarioInfo("inconclusive_conflict", "6a. Inconclusive: conflicting evidence",
                                          "The router does not answer ping, yet the internet works fine.", "inconclusive", "C"),
    "inconclusive_missing": ScenarioInfo("inconclusive_missing", "6b. Inconclusive: missing measurements",
                                         "Router address and DNS data are unavailable; only one check worked.", "inconclusive", "R0"),
}

GATEWAY = "192.168.1.1"
DNS_SERVER = "192.168.1.1"
EXTERNAL = "1.1.1.1"


def _sequence(rng: random.Random, n: int, base: float, spread: float, loss_pct: float = 0.0) -> List[Optional[float]]:
    """n probe results. Exactly round(n*loss_pct/100) probes are lost, at random positions."""
    lost = set(rng.sample(range(n), round(n * loss_pct / 100))) if loss_pct else set()
    return [None if i in lost else round(max(0.5, rng.gauss(base, spread)), 1) for i in range(n)]


def _dns(rng: random.Random, domains: List[str], fail: bool) -> DnsResult:
    result = DnsResult(servers=[DNS_SERVER, "8.8.8.8"], server_tested=DNS_SERVER, method="simulated DNS server")
    for domain in domains:
        if fail:
            result.lookups.append(DnsLookup(domain, False, None, "timeout (no reply from DNS server)"))
        else:
            result.lookups.append(DnsLookup(domain, True, round(max(2.0, rng.gauss(30, 8)), 1), ""))
    return result


def simulate_scenario(key: str, seed: int = 42, settings: Optional[TestSettings] = None) -> EvidenceBundle:
    """Return a simulated EvidenceBundle for one scenario (same seed -> same numbers)."""
    if key not in SCENARIOS:
        raise KeyError(f"Unknown scenario {key!r}. Choose from: {', '.join(SCENARIOS)}")
    rng = random.Random(seed)
    settings = settings or TestSettings()
    n_r, n_e = settings.router_probes, settings.external_probes
    bundle = EvidenceBundle(source=SOURCE_SIMULATED, scenario=key, settings=settings, gateway=GATEWAY,
                            platform="lab simulator (no real network used)")
    bundle.notes.append("SIMULATED data produced by the lab simulator. These are not real network measurements.")

    router_seq = _sequence(rng, n_r, 2.0, 0.5)
    ext_seq = _sequence(rng, n_e, 28.0, 2.5)
    loaded_seq = _sequence(rng, n_e, 31.0, 3.0)
    dns = _dns(rng, settings.domains, fail=False)
    load = LoadInfo(True, "(simulated load)", settings.load_threads, 12.0, 38_000_000)

    if key == "router_unreachable":
        router_seq = [None] * n_r
        ext_seq = [None] * n_e
        dns = _dns(rng, settings.domains, fail=True)
        load = LoadInfo(False, "", 0, 0.0, 0, "No connectivity, so the busy-link load could not be applied.")
        loaded_seq = None
    elif key == "dns_failure":
        dns = _dns(rng, settings.domains, fail=True)
    elif key == "packet_loss":
        ext_seq = _sequence(rng, n_e, 29.0, 2.5, loss_pct=20.0)
        loaded_seq = _sequence(rng, n_e, 32.0, 3.0, loss_pct=20.0)
    elif key == "congestion":
        loaded_seq = _sequence(rng, n_e, 180.0, 40.0, loss_pct=5.0)
    elif key == "inconclusive_conflict":
        router_seq = [None] * n_r  # router ignores ping...
    elif key == "inconclusive_missing":
        bundle.gateway = None
        router_seq = None
        dns = None
        loaded_seq = None
        load = None

    gateway = bundle.gateway or "(not detected)"
    if router_seq is not None:
        bundle.router = summarise(gateway, "router", router_seq)
    else:
        from .models import ProbeStats
        bundle.router = ProbeStats(target=gateway, role="router", available=False,
                                   error="Default gateway could not be detected (simulated).")
    bundle.dns = dns
    bundle.external_baseline = summarise(EXTERNAL, "external", ext_seq)
    if loaded_seq is not None:
        bundle.external_loaded = summarise(EXTERNAL, "external", loaded_seq)
    bundle.load = load
    return bundle


def run_all_scenarios(seed: int = 42) -> List[dict]:
    """Run every scenario through the decision engine. Used by the tests and the CLI."""
    from .diagnosis import diagnose

    rows = []
    for key, info in SCENARIOS.items():
        diag = diagnose(simulate_scenario(key, seed))
        rows.append({
            "scenario": info.title,
            "expected": f"{info.expected_status} / {info.expected_rule}",
            "result": diag.label,
            "status": diag.status,
            "rule": diag.rule_id,
            "confidence": diag.confidence,
            "match": diag.status == info.expected_status and diag.rule_id == info.expected_rule,
        })
    return rows


if __name__ == "__main__":
    print("SIMULATED scenarios (lab simulator, not real network measurements)\n")
    for row in run_all_scenarios():
        mark = "OK  " if row["match"] else "FAIL"
        print(f"[{mark}] {row['scenario']:<45} -> {row['result']:<38} rule={row['rule']:<3} confidence={row['confidence']}")
