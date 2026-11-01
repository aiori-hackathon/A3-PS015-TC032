"""Diagnostic orchestrator: runs the real measurement steps in the proposed order."""
from __future__ import annotations

import platform
from typing import Callable, Optional

from .dns_check import check_dns
from .latency_check import measure_latency
from .models import SOURCE_REAL, EvidenceBundle, TestSettings
from .performance import measure_loaded
from .router_check import check_router

ProgressFn = Callable[[float, str], None]


def run_live_diagnosis(
    settings: TestSettings,
    progress: Optional[ProgressFn] = None,
    ping_fn=None,
    dns_resolver=None,
    dns_servers=None,
    gateway_detector=None,
    load_generator_factory=None,
) -> EvidenceBundle:
    """Run all checks on the real network and return the evidence.

    The keyword arguments after `progress` exist so tests can replace the real network.
    """
    def report(fraction: float, message: str) -> None:
        if progress:
            progress(min(fraction, 1.0), message)

    bundle = EvidenceBundle(source=SOURCE_REAL, scenario="live", settings=settings,
                            platform=f"{platform.system()} {platform.release()}")

    # Steps 2-3: router
    report(0.02, "Step 1/5: Finding the router (default gateway)...")
    kwargs = {"detector": gateway_detector} if gateway_detector else {}
    bundle.gateway, bundle.router = check_router(
        settings.gateway_override, count=settings.router_probes, timeout_ms=settings.ping_timeout_ms,
        interval_s=settings.probe_interval_s, ping_fn=ping_fn,
        progress=lambda i, n: report(0.02 + 0.18 * i / n, f"Step 1/5: Pinging the router ({i}/{n})..."), **kwargs)
    if bundle.router and not bundle.router.available:
        bundle.notes.append(f"Router check unavailable: {bundle.router.error}")

    # Step 4: DNS
    report(0.20, "Step 2/5: Checking DNS lookups...")
    bundle.dns = check_dns(
        settings.domains, method=settings.dns_method, timeout_s=settings.dns_timeout_s,
        servers=dns_servers, resolver=dns_resolver,
        progress=lambda i, n: report(0.20 + 0.15 * i / n, f"Step 2/5: DNS lookup {i}/{n}..."))
    if bundle.dns.method.startswith("operating-system"):
        bundle.notes.append("DNS was tested with the operating-system resolver, which may answer from its cache.")

    # Step 5: latency + loss (normal conditions)
    report(0.35, "Step 3/5: Measuring delay and packet loss (normal conditions)...")
    bundle.external_baseline = measure_latency(
        settings.external_target, count=settings.external_probes, timeout_ms=settings.ping_timeout_ms,
        interval_s=settings.probe_interval_s, role="external", ping_fn=ping_fn,
        progress=lambda i, n: report(0.35 + 0.25 * i / n, f"Step 3/5: Ping {i}/{n} to {settings.external_target}..."))
    if not bundle.external_baseline.available:
        bundle.notes.append(f"External ping unavailable: {bundle.external_baseline.error}")

    # Step 6: busy-link comparison
    if settings.run_load_test and bundle.external_baseline.available and bundle.external_baseline.received > 0:
        report(0.60, "Step 4/5: Creating a controlled busy link and measuring again...")
        extra = {"generator_factory": load_generator_factory} if load_generator_factory else {}
        warmup = {"warmup_s": 0.0} if load_generator_factory else {}
        bundle.external_loaded, bundle.load = measure_loaded(
            settings.external_target, count=settings.external_probes, load_url=settings.load_url,
            threads=settings.load_threads, timeout_ms=settings.ping_timeout_ms,
            interval_s=settings.probe_interval_s, ping_fn=ping_fn,
            progress=lambda i, n: report(0.60 + 0.35 * i / n, f"Step 4/5: Busy-link ping {i}/{n}..."),
            **extra, **warmup)
        if bundle.load and not bundle.load.applied:
            bundle.notes.append(bundle.load.error)
    elif settings.run_load_test:
        bundle.notes.append("Busy-link test skipped because the external target did not answer in normal conditions.")
    else:
        bundle.notes.append("Busy-link test was switched off in the settings.")

    report(0.97, "Step 5/5: Applying the decision rules...")
    return bundle
