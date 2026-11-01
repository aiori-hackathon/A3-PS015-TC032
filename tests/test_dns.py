"""Tests for the DNS check (fake resolvers, no real network)."""
import socket
import struct

from src.dns_check import (build_dns_query, check_dns, parse_dns_response, parse_ipconfig_dns,
                           parse_resolv_conf, parse_scutil_dns)
from src.models import DnsLookup

IPCONFIG_ALL = """
Wireless LAN adapter Wi-Fi:
   DNS Servers . . . . . . . . . . . : 192.168.29.1
                                       8.8.8.8
                                       2001:4860:4860::8888
   NetBIOS over Tcpip. . . . . . . . : Enabled
"""


def test_parse_ipconfig_dns_reads_continuation_lines():
    assert parse_ipconfig_dns(IPCONFIG_ALL) == ["192.168.29.1", "8.8.8.8", "2001:4860:4860::8888"]


def test_parse_linux_and_mac_dns():
    assert parse_resolv_conf("# comment\nnameserver 127.0.0.53\nnameserver 1.1.1.1\n") == ["127.0.0.53", "1.1.1.1"]
    assert parse_scutil_dns("  nameserver[0] : 10.0.0.1\n  nameserver[1] : 10.0.0.2") == ["10.0.0.1", "10.0.0.2"]


def _answer(qid, rcode=0, answers=1):
    flags = 0x8180 | rcode
    return struct.pack("!HHHHHH", qid, flags, 1, answers, 0, 0)


def test_dns_packet_round_trip():
    qid, packet = build_dns_query("example.com", query_id=1234)
    assert struct.unpack("!H", packet[:2])[0] == 1234
    assert b"\x07example\x03com\x00" in packet
    assert parse_dns_response(_answer(1234), 1234) == (True, "")


def test_dns_response_errors():
    assert parse_dns_response(_answer(1, rcode=3), 1)[0] is False
    assert "NXDOMAIN" in parse_dns_response(_answer(1, rcode=3), 1)[1]
    assert parse_dns_response(_answer(1, answers=0), 1)[0] is False
    assert parse_dns_response(_answer(2), 1) == (False, "reply ID did not match")
    assert parse_dns_response(b"\x00", 1)[0] is False


def test_check_dns_all_ok_records_server_and_times():
    fake = lambda domain, server, timeout: DnsLookup(domain, True, 25.0, "")
    res = check_dns(["a.com", "b.com", "c.com"], servers=["192.168.1.1", "8.8.8.8"], resolver=fake)
    assert res.success_count == 3 and res.failure_ratio == 0 and res.median_ms == 25.0
    assert res.server_tested == "192.168.1.1" and res.servers == ["192.168.1.1", "8.8.8.8"]


def test_check_dns_failure_counts():
    fake = lambda domain, server, timeout: DnsLookup(domain, False, None, "timeout")
    res = check_dns(["a.com", "b.com"], servers=["192.168.1.1"], resolver=fake)
    assert res.success_count == 0 and res.failure_ratio == 1.0 and res.median_ms is None


def test_check_dns_falls_back_to_system_resolver_without_ipv4_server():
    seen = []
    def fake(domain, server, timeout):
        seen.append(server)
        return DnsLookup(domain, True, 10.0, "")
    res = check_dns(["a.com"], servers=["2001:db8::1"], resolver=fake)
    assert seen == [""] and res.server_tested == "" and "operating-system" in res.method


def test_check_dns_system_method_never_queries_server_directly():
    seen = []
    def fake(domain, server, timeout):
        seen.append(server)
        return DnsLookup(domain, True, 10.0, "")
    check_dns(["a.com"], method="system", servers=["192.168.1.1"], resolver=fake)
    assert seen == [""]


def test_udp_query_to_local_fake_server_works():
    """End-to-end check of the UDP code using a tiny fake DNS server on this computer."""
    import threading
    from src import dns_check

    original = socket.socket.sendto  # keep the real sendto for the fake server's reply
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind(("127.0.0.1", 0))
    port = server.getsockname()[1]

    def serve():
        data, addr = server.recvfrom(512)
        original(server, _answer(struct.unpack("!H", data[:2])[0]), addr)

    threading.Thread(target=serve, daemon=True).start()

    # query_dns_udp always uses port 53, so point it at our fake port for this test only
    def patched(self, data, addr):
        return original(self, data, (addr[0], port))

    socket.socket.sendto = patched
    try:
        lookup = dns_check.query_dns_udp("example.com", "127.0.0.1", timeout_s=2)
    finally:
        socket.socket.sendto = original
        server.close()
    assert lookup.success and lookup.time_ms is not None
