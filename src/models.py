"""Shared data structures used by every module.

Every measurement module returns one of these objects, so the decision
rules (diagnosis.py) and the report generator can treat them all the same.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from statistics import median
from typing import Any, Dict, List, Optional

SOURCE_REAL = "real"
SOURCE_SIMULATED = "simulated"

DEFAULT_DOMAINS = [
    "google.com",
    "wikipedia.org",
    "cloudflare.com",
    "github.com",
    "python.org",
]
DEFAULT_LOAD_URL = "https://speed.cloudflare.com/__down?bytes=100000000"


@dataclass
class TestSettings:
    """Settings used for one test run. They are saved in the report (repeatable tests)."""

    __test__ = False  # stop pytest from treating this class as a test

    router_probes: int = 10
    external_probes: int = 20
    external_target: str = "1.1.1.1"
    domains: List[str] = field(default_factory=lambda: list(DEFAULT_DOMAINS))
    dns_method: str = "auto"  # "auto" = ask detected DNS server directly, "system" = OS resolver
    dns_timeout_s: float = 2.0
    ping_timeout_ms: int = 1000
    probe_interval_s: float = 0.2
    run_load_test: bool = True
    load_url: str = DEFAULT_LOAD_URL
    load_threads: int = 4
    gateway_override: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ProbeStats:
    """Result of sending several ping probes to one target."""

    target: str
    role: str = "external"  # "router" or "external"
    sent: int = 0
    received: int = 0
    # One entry per probe in order. A number is the RTT in ms, None means "no reply".
    sequence: List[Optional[float]] = field(default_factory=list)
    loss_pct: Optional[float] = None
    min_ms: Optional[float] = None
    avg_ms: Optional[float] = None
    median_ms: Optional[float] = None
    max_ms: Optional[float] = None
    stdev_ms: Optional[float] = None
    jitter_ms: Optional[float] = None
    available: bool = True  # False when the measurement could not run at all
    error: str = ""

    @property
    def lost(self) -> int:
        return self.sent - self.received

    @property
    def rtts(self) -> List[float]:
        return [x for x in self.sequence if x is not None]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DnsLookup:
    domain: str
    success: bool
    time_ms: Optional[float] = None
    error: str = ""


@dataclass
class DnsResult:
    servers: List[str] = field(default_factory=list)  # DNS servers found on this computer
    server_tested: str = ""  # the server actually asked ("" = OS resolver)
    method: str = "system"
    lookups: List[DnsLookup] = field(default_factory=list)

    @property
    def success_count(self) -> int:
        return sum(1 for x in self.lookups if x.success)

    @property
    def failure_ratio(self) -> float:
        if not self.lookups:
            return 0.0
        return 1 - self.success_count / len(self.lookups)

    @property
    def median_ms(self) -> Optional[float]:
        times = [x.time_ms for x in self.lookups if x.success and x.time_ms is not None]
        return round(median(times), 1) if times else None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class LoadInfo:
    """Details about the controlled busy-link (load) phase."""

    applied: bool = False
    url: str = ""
    threads: int = 0
    duration_s: float = 0.0
    bytes_downloaded: int = 0
    error: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EvidenceBundle:
    """Everything measured in one run. This is the input of the decision rules."""

    source: str = SOURCE_REAL  # "real" or "simulated"
    scenario: str = ""
    settings: TestSettings = field(default_factory=TestSettings)
    gateway: Optional[str] = None
    router: Optional[ProbeStats] = None
    dns: Optional[DnsResult] = None
    external_baseline: Optional[ProbeStats] = None
    external_loaded: Optional[ProbeStats] = None
    load: Optional[LoadInfo] = None
    notes: List[str] = field(default_factory=list)
    platform: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))

    @property
    def is_simulated(self) -> bool:
        return self.source == SOURCE_SIMULATED

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
