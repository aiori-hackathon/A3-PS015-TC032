"""Latency (round-trip time) measurement using the operating system's ping command.

Works on Windows, Linux and macOS. One probe = one ping packet, so we know
exactly which probes were lost and can calculate loss, median and jitter.
"""
from __future__ import annotations

import math
import os
import platform
import re
import statistics
import subprocess
import time
from typing import Callable, List, Optional

from .models import ProbeStats
from .packet_loss import calculate_loss_pct

_HOST_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.\-:]*$")
# Matches "time=12ms", "time<1ms", "time=12.3 ms"
_TIME_RE = re.compile(r"time\s*([=<])\s*([\d.,]+)\s*ms", re.IGNORECASE)


class PingUnavailable(Exception):
    """Raised when the ping command cannot be used at all on this computer."""


def validate_host(host: str) -> str:
    """Only allow plain host names / IP addresses (protects against odd input)."""
    host = (host or "").strip()
    if not host or not _HOST_RE.match(host):
        raise ValueError(f"Invalid host name or IP address: {host!r}")
    return host


def parse_ping_output(text: str) -> Optional[float]:
    """Return the RTT in ms if the ping output shows a real reply, otherwise None.

    A reply must contain 'time=' or 'time<'. This matters on Windows, where
    'Destination host unreachable' lines also start with 'Reply from'.
    'time<1ms' is recorded as 1.0 ms (an upper bound).
    """
    match = _TIME_RE.search(text or "")
    if not match:
        return None
    return float(match.group(2).replace(",", "."))


def build_ping_command(host: str, timeout_ms: int, system: Optional[str] = None) -> List[str]:
    system = system or platform.system()
    if system == "Windows":
        return ["ping", "-n", "1", "-w", str(int(timeout_ms)), host]
    if system == "Darwin":  # macOS: -W is in milliseconds
        return ["ping", "-c", "1", "-W", str(int(timeout_ms)), host]
    seconds = max(1, math.ceil(timeout_ms / 1000))  # Linux: -W is in seconds
    return ["ping", "-n", "-c", "1", "-W", str(seconds), host]


def ping_once(host: str, timeout_ms: int = 1000, runner: Callable = subprocess.run) -> Optional[float]:
    """Send one ping. Returns RTT in ms, or None if there was no reply."""
    validate_host(host)
    cmd = build_ping_command(host, timeout_ms)
    kwargs = dict(
        capture_output=True,
        text=True,
        errors="replace",
        timeout=timeout_ms / 1000 + 3,
    )
    if os.name == "nt":
        kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        proc = runner(cmd, **kwargs)
    except subprocess.TimeoutExpired:
        return None
    except OSError as exc:  # ping program missing or not allowed
        raise PingUnavailable(f"The ping command could not be run: {exc}") from exc
    return parse_ping_output((proc.stdout or "") + (proc.stderr or ""))


def summarise(target: str, role: str, sequence: List[Optional[float]]) -> ProbeStats:
    """Turn a list of probe results (RTT or None) into statistics."""
    sent = len(sequence)
    rtts = [x for x in sequence if x is not None]
    stats = ProbeStats(
        target=target,
        role=role,
        sent=sent,
        received=len(rtts),
        sequence=list(sequence),
        loss_pct=calculate_loss_pct(sent, len(rtts)),
    )
    if rtts:
        stats.min_ms = round(min(rtts), 1)
        stats.max_ms = round(max(rtts), 1)
        stats.avg_ms = round(statistics.mean(rtts), 1)
        stats.median_ms = round(statistics.median(rtts), 1)
    if len(rtts) >= 2:
        stats.stdev_ms = round(statistics.stdev(rtts), 1)
        # Jitter = average change between consecutive replies (a simple, readable definition
        # in the spirit of delay variation, RFC 3393).
        diffs = [abs(b - a) for a, b in zip(rtts, rtts[1:])]
        stats.jitter_ms = round(statistics.mean(diffs), 1)
    return stats


def measure_latency(
    target: str,
    count: int = 20,
    timeout_ms: int = 1000,
    interval_s: float = 0.2,
    role: str = "external",
    ping_fn: Optional[Callable[[str, int], Optional[float]]] = None,
    progress: Optional[Callable[[int, int], None]] = None,
) -> ProbeStats:
    """Send `count` pings (one at a time) and return the statistics.

    If ping cannot run, the result has available=False (shown as "unavailable").
    """
    ping_fn = ping_fn or ping_once
    try:
        validate_host(target)
        sequence: List[Optional[float]] = []
        for i in range(count):
            sequence.append(ping_fn(target, timeout_ms))
            if progress:
                progress(i + 1, count)
            if interval_s > 0 and i < count - 1:
                time.sleep(interval_s)
    except (PingUnavailable, ValueError) as exc:
        return ProbeStats(target=target, role=role, available=False, error=str(exc))
    return summarise(target, role, sequence)
