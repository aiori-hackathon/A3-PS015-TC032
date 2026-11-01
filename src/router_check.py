"""Router (default gateway) detection and reachability check."""
from __future__ import annotations

import ipaddress
import platform
import re
from typing import Callable, List, Optional, Tuple

from .latency_check import measure_latency
from .models import ProbeStats
from .system_utils import run_command


def _as_ip(token: str):
    token = token.strip().split("%")[0]  # drop IPv6 scope like fe80::1%12
    try:
        return ipaddress.ip_address(token)
    except ValueError:
        return None


def parse_ipconfig_gateway(text: str) -> Optional[str]:
    """Find the first IPv4 default gateway in Windows `ipconfig` output.

    The IPv6 gateway may be listed first, with the IPv4 one on the next line, so
    we keep reading lines that follow "Default Gateway" until another setting starts.
    """
    capturing = False
    for line in text.splitlines():
        if "Default Gateway" in line:
            capturing = True
            value = line.split(":", 1)[1] if ":" in line else ""
        elif capturing:
            value = line
        else:
            continue
        ip = _as_ip(value) if value.strip() else None
        if ip is not None:
            if ip.version == 4 and str(ip) != "0.0.0.0":
                return str(ip)
        elif capturing and "Default Gateway" not in line and value.strip():
            capturing = False  # a different setting started
    return None


def parse_linux_gateway(text: str) -> Optional[str]:
    """`ip route show default` -> 'default via 192.168.1.1 dev wlan0 ...'"""
    match = re.search(r"default\s+via\s+(\d+\.\d+\.\d+\.\d+)", text)
    return match.group(1) if match else None


def parse_macos_gateway(text: str) -> Optional[str]:
    """`route -n get default` -> '   gateway: 192.168.1.1'"""
    match = re.search(r"gateway:\s*(\d+\.\d+\.\d+\.\d+)", text)
    return match.group(1) if match else None


def get_default_gateway(system: Optional[str] = None, runner: Callable[[List[str]], str] = run_command) -> Optional[str]:
    """Return the default gateway (usually the home router) or None if not found."""
    system = system or platform.system()
    if system == "Windows":
        return parse_ipconfig_gateway(runner(["ipconfig"]))
    if system == "Darwin":
        return parse_macos_gateway(runner(["route", "-n", "get", "default"]))
    return parse_linux_gateway(runner(["ip", "route", "show", "default"]))


def check_router(
    gateway: Optional[str] = None,
    count: int = 10,
    timeout_ms: int = 1000,
    interval_s: float = 0.2,
    ping_fn=None,
    progress=None,
    detector: Callable[[], Optional[str]] = get_default_gateway,
) -> Tuple[Optional[str], ProbeStats]:
    """Detect the gateway (unless given) and ping it several times.

    Returns (gateway_address, ProbeStats). If no gateway is found the stats are
    marked "unavailable" instead of guessing.
    """
    gateway = (gateway or "").strip() or detector()
    if not gateway:
        return None, ProbeStats(
            target="(not detected)",
            role="router",
            available=False,
            error="Default gateway could not be detected on this computer.",
        )
    stats = measure_latency(
        gateway, count=count, timeout_ms=timeout_ms, interval_s=interval_s,
        role="router", ping_fn=ping_fn, progress=progress,
    )
    return gateway, stats
