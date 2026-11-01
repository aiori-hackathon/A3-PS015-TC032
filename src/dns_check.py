"""DNS resolution check: do names resolve, and how fast?

Two methods are available:
  * "auto"   - send a real DNS query (UDP port 53) straight to the first IPv4 DNS server
               found on this computer. This avoids the operating-system cache, and we know
               exactly which server was tested. Falls back to "system" if no server is found.
  * "system" - use the operating system resolver (socket.getaddrinfo). May be answered from cache.
"""
from __future__ import annotations

import ipaddress
import platform
import random
import re
import socket
import struct
import threading
import time
from typing import Callable, List, Optional, Tuple

from .models import DnsLookup, DnsResult
from .system_utils import run_command


# ---------- finding the DNS servers --------------------------------------------------------
def _clean_ip(token: str) -> Optional[str]:
    token = token.strip().split("%")[0]
    try:
        return str(ipaddress.ip_address(token))
    except ValueError:
        return None


def parse_ipconfig_dns(text: str) -> List[str]:
    """Read DNS servers from Windows `ipconfig /all` output (keeps order, removes duplicates)."""
    servers: List[str] = []
    capturing = False
    for line in text.splitlines():
        if "DNS Servers" in line:
            capturing = True
            value = line.split(":", 1)[1] if ":" in line else ""
            ip = _clean_ip(value)
            if ip and ip not in servers:
                servers.append(ip)
            continue
        if capturing:
            ip = _clean_ip(line)
            if ip:
                if ip not in servers:
                    servers.append(ip)
            else:
                capturing = False
    return servers


def parse_resolv_conf(text: str) -> List[str]:
    servers = []
    for match in re.finditer(r"^\s*nameserver\s+(\S+)", text, re.MULTILINE):
        ip = _clean_ip(match.group(1))
        if ip and ip not in servers:
            servers.append(ip)
    return servers


def parse_scutil_dns(text: str) -> List[str]:
    servers = []
    for match in re.finditer(r"nameserver\[\d+\]\s*:\s*(\S+)", text):
        ip = _clean_ip(match.group(1))
        if ip and ip not in servers:
            servers.append(ip)
    return servers


def get_dns_servers(system: Optional[str] = None, runner: Callable[[List[str]], str] = run_command) -> List[str]:
    """Return DNS servers configured on this computer (empty list if unavailable)."""
    system = system or platform.system()
    if system == "Windows":
        return parse_ipconfig_dns(runner(["ipconfig", "/all"]))
    if system == "Darwin":
        return parse_scutil_dns(runner(["scutil", "--dns"]))
    try:
        with open("/etc/resolv.conf", encoding="utf-8", errors="replace") as handle:
            return parse_resolv_conf(handle.read())
    except OSError:
        return []


# ---------- sending a DNS query by hand ----------------------------------------------------
def build_dns_query(domain: str, query_id: Optional[int] = None) -> Tuple[int, bytes]:
    """Build a standard 'A record' DNS query packet. Returns (id, bytes)."""
    qid = random.randint(0, 65535) if query_id is None else query_id
    header = struct.pack("!HHHHHH", qid, 0x0100, 1, 0, 0, 0)  # recursion desired, 1 question
    qname = b""
    for label in domain.rstrip(".").split("."):
        encoded = label.encode("idna")
        qname += bytes([len(encoded)]) + encoded
    qname += b"\x00"
    return qid, header + qname + struct.pack("!HH", 1, 1)  # type A, class IN


def parse_dns_response(data: bytes, expected_id: int) -> Tuple[bool, str]:
    """Return (success, error_text). Success = right ID, no error code, at least one answer."""
    if len(data) < 12:
        return False, "reply too short"
    rid, flags, _qd, ancount = struct.unpack("!HHHH", data[:8])
    if rid != expected_id:
        return False, "reply ID did not match"
    rcode = flags & 0x000F
    if rcode != 0:
        names = {1: "format error", 2: "server failure", 3: "name does not exist (NXDOMAIN)", 5: "refused"}
        return False, names.get(rcode, f"DNS error code {rcode}")
    if ancount == 0:
        return False, "no answer records"
    return True, ""


def query_dns_udp(domain: str, server: str, timeout_s: float = 2.0) -> DnsLookup:
    """Ask one DNS server directly and time the answer."""
    qid, packet = build_dns_query(domain)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout_s)
    try:
        start = time.perf_counter()
        sock.sendto(packet, (server, 53))
        data, _ = sock.recvfrom(2048)
        elapsed = (time.perf_counter() - start) * 1000
        ok, error = parse_dns_response(data, qid)
        return DnsLookup(domain, ok, round(elapsed, 1) if ok else None, error)
    except socket.timeout:
        return DnsLookup(domain, False, None, "timeout (no reply from DNS server)")
    except OSError as exc:
        return DnsLookup(domain, False, None, f"network error: {exc}")
    finally:
        sock.close()


def query_dns_system(domain: str, timeout_s: float = 2.0) -> DnsLookup:
    """Resolve with the operating-system resolver, with our own timeout."""
    box: dict = {}

    def worker() -> None:
        try:
            socket.getaddrinfo(domain, None, socket.AF_INET)
            box["ok"] = True
        except OSError as exc:
            box["error"] = str(exc)

    start = time.perf_counter()
    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    thread.join(timeout_s)
    elapsed = (time.perf_counter() - start) * 1000
    if box.get("ok"):
        return DnsLookup(domain, True, round(elapsed, 1), "")
    if thread.is_alive():
        return DnsLookup(domain, False, None, "timeout (resolver did not answer)")
    return DnsLookup(domain, False, None, box.get("error", "lookup failed"))


# ---------- main entry point ---------------------------------------------------------------
def check_dns(
    domains: List[str],
    method: str = "auto",
    timeout_s: float = 2.0,
    servers: Optional[List[str]] = None,
    resolver: Optional[Callable[[str, str, float], DnsLookup]] = None,
    progress: Optional[Callable[[int, int], None]] = None,
) -> DnsResult:
    """Look up each domain and record success and time.

    `resolver(domain, server, timeout)` can be replaced in tests; server is "" for the OS resolver.
    """
    if servers is None:
        servers = get_dns_servers()
    ipv4_servers = [s for s in servers if ":" not in s]
    use_direct = method == "auto" and bool(ipv4_servers)
    server_tested = ipv4_servers[0] if use_direct else ""

    if resolver is None:
        def resolver(domain: str, server: str, timeout: float) -> DnsLookup:  # type: ignore[misc]
            if server:
                return query_dns_udp(domain, server, timeout)
            return query_dns_system(domain, timeout)

    result = DnsResult(
        servers=list(servers),
        server_tested=server_tested,
        method="direct query to DNS server" if use_direct else "operating-system resolver",
    )
    for i, domain in enumerate(domains):
        result.lookups.append(resolver(domain, server_tested, timeout_s))
        if progress:
            progress(i + 1, len(domains))
    return result
