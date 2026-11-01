"""Tests for router detection and the router reachability check (no real network used)."""
from src.latency_check import (build_ping_command, parse_ping_output, summarise, validate_host)
from src.router_check import (check_router, get_default_gateway, parse_ipconfig_gateway,
                              parse_linux_gateway, parse_macos_gateway)
import pytest

WINDOWS_IPCONFIG = """
Windows IP Configuration

Ethernet adapter Ethernet 2:

   Media State . . . . . . . . . . . : Media disconnected
   Default Gateway . . . . . . . . . :

Wireless LAN adapter Wi-Fi:

   Connection-specific DNS Suffix  . : lan
   IPv4 Address. . . . . . . . . . . : 192.168.29.45
   Default Gateway . . . . . . . . . : fe80::1%14
                                       192.168.29.1
"""


def test_parse_windows_gateway_skips_disconnected_and_ipv6():
    assert parse_ipconfig_gateway(WINDOWS_IPCONFIG) == "192.168.29.1"


def test_parse_windows_gateway_none_when_missing():
    assert parse_ipconfig_gateway("   Default Gateway . . . . : \n\nSomething : else") is None


def test_parse_linux_and_macos_gateway():
    assert parse_linux_gateway("default via 10.0.0.1 dev wlan0 proto dhcp") == "10.0.0.1"
    assert parse_macos_gateway("   route to: default\n    gateway: 192.168.0.1\n") == "192.168.0.1"
    assert parse_linux_gateway("") is None


def test_get_default_gateway_uses_runner():
    assert get_default_gateway("Windows", runner=lambda cmd: WINDOWS_IPCONFIG) == "192.168.29.1"
    assert get_default_gateway("Linux", runner=lambda cmd: "default via 10.1.1.1 dev eth0") == "10.1.1.1"


def test_check_router_reachable():
    gw, stats = check_router("192.168.1.1", count=6, interval_s=0, ping_fn=lambda h, t: 2.0)
    assert gw == "192.168.1.1"
    assert stats.sent == 6 and stats.received == 6 and stats.loss_pct == 0.0


def test_check_router_unreachable():
    gw, stats = check_router("192.168.1.1", count=6, interval_s=0, ping_fn=lambda h, t: None)
    assert stats.received == 0 and stats.loss_pct == 100.0 and stats.available


def test_check_router_no_gateway_is_unavailable_not_guessed():
    gw, stats = check_router("", count=5, interval_s=0, detector=lambda: None)
    assert gw is None and stats.available is False and "gateway" in stats.error.lower()


# ---- ping parsing -------------------------------------------------------------------------
def test_parse_ping_windows_reply():
    assert parse_ping_output("Reply from 192.168.1.1: bytes=32 time=3ms TTL=64") == 3.0
    assert parse_ping_output("Reply from 192.168.1.1: bytes=32 time<1ms TTL=64") == 1.0


def test_parse_ping_linux_reply():
    assert parse_ping_output("64 bytes from 1.1.1.1: icmp_seq=1 ttl=57 time=12.4 ms") == 12.4


def test_parse_ping_failures_are_none():
    assert parse_ping_output("Request timed out.") is None
    # Windows prints 'Reply from' for unreachable too - it must NOT count as success
    assert parse_ping_output("Reply from 192.168.1.5: Destination host unreachable.") is None
    assert parse_ping_output("") is None


def test_build_ping_command_per_os():
    assert build_ping_command("1.1.1.1", 1000, "Windows") == ["ping", "-n", "1", "-w", "1000", "1.1.1.1"]
    assert build_ping_command("1.1.1.1", 1000, "Linux")[:4] == ["ping", "-n", "-c", "1"]
    assert build_ping_command("1.1.1.1", 1000, "Darwin") == ["ping", "-c", "1", "-W", "1000", "1.1.1.1"]


def test_validate_host_blocks_bad_input():
    assert validate_host("1.1.1.1") == "1.1.1.1"
    for bad in ["", "-c 100 x", "1.1.1.1; rm -rf /", "a b"]:
        with pytest.raises(ValueError):
            validate_host(bad)


def test_summarise_statistics():
    s = summarise("x", "external", [10.0, 20.0, None, 30.0])
    assert (s.sent, s.received, s.lost, s.loss_pct) == (4, 3, 1, 25.0)
    assert s.avg_ms == 20.0 and s.median_ms == 20.0 and s.min_ms == 10.0 and s.max_ms == 30.0
    assert s.jitter_ms == 10.0  # |20-10| and |30-20| -> mean 10
