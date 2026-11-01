# Diagnostic Report: Explainable Home and Last-Mile Connectivity Diagnosis

## Data source

DATA SOURCE: SIMULATED. This report was produced from the lab simulator (scenario: inconclusive_conflict). The numbers are NOT real network measurements and are not fault-injection results.

## Project

| Item | Value |
|---|---|
| Project | Explainable Home and Last-Mile Connectivity Diagnosis |
| Hackathon | AIORI-3 Hackathon \| PS-015 \| Smart Cities |
| Team code | A3-PS015-TC032 |
| Team | Divya PR, Sartaj S |
| College mentor | Neethu Mariam Panicker |
| Report created | 2026-10-30 05:52:07 |
| Test run time | 2026-10-30T05:52:07 |

## Diagnosis

| Item | Value |
|---|---|
| Result | Inconclusive |
| Confidence | Not applicable (Inconclusive) |
| Rule used | C |

The measurements disagree, so the tool will not guess. The router did not answer any of 10 probes, but the external target replied to 20/20. The router may be ignoring ping, so a router fault cannot be confirmed.

Confidence is a simple evidence-counting level. It is not a validated probability.

## Supporting evidence

- Router (192.168.1.1): 0/10 replies, loss 100.0%, median n/a, jitter n/a
- External target (1.1.1.1): 20/20 replies, loss 0.0%, median 28.6 ms, jitter 2.1 ms

## Why this confidence level

- Conflicting evidence: no cause can be named safely.

## Test settings

| Setting | Value |
|---|---|
| Router address | 192.168.1.1 (auto-detected) |
| Router probes | 10 |
| External target | 1.1.1.1 |
| External probes (normal and busy link) | 20 |
| Probe timeout / interval | 1000 ms / 0.2 s |
| DNS domains | google.com, wikipedia.org, cloudflare.com, github.com, python.org |
| DNS method | simulated DNS server |
| DNS timeout | 2.0 s |
| Busy-link test | on; 4 download threads |

## Measurements: ping tests

| Test | Target | Sent | Received | Loss % | Avg ms | Median ms | Jitter ms | Min / Max ms |
|---|---|---|---|---|---|---|---|---|
| Router | 192.168.1.1 | 10 | 0 | 100.0 | n/a | n/a | n/a | n/a / n/a |
| External (normal) | 1.1.1.1 | 20 | 20 | 0.0 | 28.3 | 28.6 | 2.1 | 24.4 / 31.3 |
| External (busy link) | 1.1.1.1 | 20 | 20 | 0.0 | 30.4 | 31.0 | 2.8 | 23.1 / 33.6 |

## Measurements: DNS lookups

DNS servers found: 192.168.1.1, 8.8.8.8. Server tested: 192.168.1.1.

| Domain | Result | Time ms | Error |
|---|---|---|---|
| google.com | OK | 26.2 |  |
| wikipedia.org | OK | 34.0 |  |
| cloudflare.com | OK | 28.0 |  |
| github.com | OK | 48.7 |  |
| python.org | OK | 23.4 |  |

## Network performance: normal vs busy link

Busy link created with 4 download threads for 12.0 s (38.0 MB downloaded; load applied: True). This compares changes in latency, jitter and loss. It is not a bandwidth test.

| Metric | Unit | Normal | Busy link | Change |
|---|---|---|---|---|
| Median latency | ms | 28.6 | 31.0 | 2.4 |
| Jitter | ms | 2.1 | 2.8 | 0.7 |
| Packet loss | % | 0.0 | 0.0 | 0.0 |

## Rules checked

| Rule | Name | State | Detail |
|---|---|---|---|
| R0 | Enough measurements available | not fired | 3 of 3 core checks usable. |
| R1 | Router unreachable | FIRED | 0/10 router replies. |
| R2 | DNS failure | not evaluated | Skipped: DNS failures are expected when the router is unreachable. |
| R3 | Slow DNS | not evaluated | No usable DNS result. |
| R4 | Packet loss | not evaluated | No usable ping data to compare. |
| R5 | High latency | not evaluated | No external latency available. |
| R6 | Congestion hint (busy link) | not evaluated | No usable baseline. |
| C | Conflicting evidence | CONFLICT | The router did not answer any of 10 probes, but the external target replied to 20/20. The router may be ignoring ping, so a router fault cannot be confirmed. |

## Suggested additional tests

- Ping a second external target (for example 8.8.8.8) and compare.
- Ping the router from another device.
- Repeat the full diagnosis a few minutes later.
- Check whether the router/target blocks ping (ICMP).

## Notes

- SIMULATED data produced by the lab simulator. These are not real network measurements.

## Decision limits used (proposed, not validated)

| Limit | Value |
|---|---|
| min_router_probes | 5 |
| min_probes_reliable | 10 |
| min_dns_lookups | 2 |
| min_lost_packets | 2 |
| loss_warn_pct | 10.0 |
| dns_fail_ratio | 0.5 |
| dns_slow_ms | 300.0 |
| latency_high_ms | 150.0 |
| congestion_latency_ratio | 2.0 |
| congestion_latency_abs_ms | 30.0 |
| congestion_jitter_ratio | 2.0 |
| congestion_jitter_abs_ms | 10.0 |
| congestion_loss_increase_pct | 3.0 |

## Limitations

- Decision limits are proposed values that must still be tested and tuned; they are not validated.
- Confidence levels are simple evidence-counting rules, not statistically validated probabilities.
- A symptom is a hint, not proof. The tool does not prove a damaged cable, causes inside the ISP network, or Wi-Fi interference (no radio data).
- Ping loss covers both directions (request and reply), so it is not the one-way loss of RFC 7680.
- Some routers and servers slow down or ignore ping (ICMP), which can look like loss or an unreachable device.
- The busy-link test creates download load only, and only shows how latency, jitter and loss change. It is not a bandwidth test.
