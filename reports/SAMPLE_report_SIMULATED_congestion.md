# Diagnostic Report: Explainable Home and Last-Mile Connectivity Diagnosis

## Data source

DATA SOURCE: SIMULATED. This report was produced from the lab simulator (scenario: congestion). The numbers are NOT real network measurements and are not fault-injection results.

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
| Result | Possible congestion (busy link) |
| Confidence | High |
| Rule used | R6 |

Delay, jitter or loss gets worse when the link is busy, which is a hint of queueing (congestion). This is a hint only; it is not proof of a fault in the ISP network.

Confidence is a simple evidence-counting level. It is not a validated probability.

## Supporting evidence

- Median latency rose from 28.6 ms to 173.6 ms
- Jitter rose from 2.1 ms to 39.2 ms
- Packet loss rose from 0.0% to 5.0%
- Normal (1.1.1.1): 20/20 replies, loss 0.0%, median 28.6 ms, jitter 2.1 ms
- Busy link (1.1.1.1): 19/20 replies, loss 5.0%, median 173.6 ms, jitter 39.2 ms

## Why this confidence level

- 3 of 3 indicators (latency, jitter, loss) got clearly worse under load: High = 3, Medium = 2, Low = 1.

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
| Router | 192.168.1.1 | 10 | 10 | 0.0 | 1.9 | 1.9 | 0.3 | 1.3 / 2.4 |
| External (normal) | 1.1.1.1 | 20 | 20 | 0.0 | 28.3 | 28.6 | 2.1 | 24.4 / 31.3 |
| External (busy link) | 1.1.1.1 | 20 | 19 | 5.0 | 174.8 | 173.6 | 39.2 | 114.9 / 234.5 |

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
| Median latency | ms | 28.6 | 173.6 | 145.0 |
| Jitter | ms | 2.1 | 39.2 | 37.1 |
| Packet loss | % | 0.0 | 5.0 | 5.0 |

## Rules checked

| Rule | Name | State | Detail |
|---|---|---|---|
| R0 | Enough measurements available | not fired | 3 of 3 core checks usable. |
| R1 | Router unreachable | not fired | Router replied to 10/10 probes. |
| R2 | DNS failure | not fired | All 5 lookups succeeded. |
| R3 | Slow DNS | not fired | Median lookup time 28.0 ms (limit 300 ms). |
| R4 | Packet loss | not fired | Loss below 10.0% (or fewer than 2 lost probes). |
| R5 | High latency | not fired | Median 28.6 ms (limit 150 ms). |
| R6 | Congestion hint (busy link) | FIRED | 3 of 3 indicators worse under load. |

## Suggested next steps

- Repeat the busy-link test a few times; congestion hints should appear again.
- Pause other downloads/streaming in the home and test again.
- Run the same test at a different time of day.

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
