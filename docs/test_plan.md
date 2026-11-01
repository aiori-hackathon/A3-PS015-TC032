# Test Plan

## 1. Objectives
1. Check that each decision rule gives the right answer for known evidence.
2. Check that the tool says **Inconclusive** instead of guessing when evidence is missing or conflicting.
3. Check that parsers (ping, ipconfig, DNS packets) and the report generator behave correctly.
4. Check that the dashboard runs without errors for every scenario.
5. Plan the real lab fault-injection evaluation required by the proposal (Phase 6).

## 2. Test levels

| Level | Files | Uses | Proves |
|---|---|---|---|
| Unit: parsers and measurement code | `tests/test_router.py`, `tests/test_dns.py` | sample command output, fake ping and DNS functions, a fake DNS server on localhost | modules read data correctly and handle failures |
| Unit: decision rules | `tests/test_diagnosis.py` | hand-made evidence | each rule, confidence level and conflict case |
| Scenario and integration | `tests/test_scenarios.py` | lab simulator (5 seeds x 7 scenarios), fake network, report generator | whole pipeline from evidence to report |
| UI smoke | `tests/test_app_smoke.py` | Streamlit `AppTest` with the simulator | dashboard runs for every scenario with no exception |

Run everything:  `python -m pytest -v`
Create a results file from a real run:  `python scripts/generate_test_results.py`

## 3. Scenario matrix (simulated)

| # | Scenario | Simulated evidence | Expected result | Rule |
|---|---|---|---|---|
| 1 | Normal | all checks healthy, small change under load | No fault detected | R7 |
| 2 | Router unreachable | router and external silent, DNS fails | Router / home network unreachable | R1 |
| 3 | DNS failure | pings fine, all lookups fail | DNS failure | R2 |
| 4 | Added packet loss | router fine, 20% loss to external | Packet loss beyond the router | R4 |
| 5 | Congestion | healthy idle, much worse under load | Possible congestion | R6 |
| 6a | Inconclusive (conflict) | router silent but internet works | Inconclusive | C |
| 6b | Inconclusive (missing data) | router and DNS unavailable | Inconclusive | R0 |

## 4. Extra rule tests
Single lost probe is not a fault; router check unavailable caps confidence at Medium; several issues lower confidence one level;
changing limits changes the answer; congestion is never claimed when the load was not applied or the baseline is already bad.

## 5. Real lab fault-injection evaluation (PLANNED, NOT YET DONE)

The proposal plans to test four fault cases in a controlled lab. Use only your own lab network, with permission.
Record every run honestly, including failures, in the table below.

| Fault case | Suggested lab method | Expected | Run date | Observed result | Correct? |
|---|---|---|---|---|---|
| Router unreachable | Disconnect the test computer from the lab router, or add a Windows Firewall rule that blocks traffic to the router address | R1 (or Inconclusive if the router only ignores ping) | not yet run | not yet run | not yet run |
| DNS failure | Set the computer's DNS server to an address that does not answer | R2 | not yet run | not yet run | not yet run |
| Added packet loss | Add loss on the lab router (`tc netem` on Linux) or with a lab tool such as clumsy on the test computer | R4 | not yet run | not yet run | not yet run |
| Congestion / busy link | Keep the busy-link test on, plus extra parallel downloads on the lab router | R6 | not yet run | not yet run | not yet run |

Also repeat the **normal** case several times on the lab network to see how the proposed limits behave, and tune them
(`Thresholds`) only after you have evidence.

## 6. Known limits of this testing
* Automated tests were executed on the machine named in `docs/test_results.md`. Windows command output is tested with sample text,
  so the first real run on a Windows computer is part of your acceptance check.
* Confidence levels are counting rules, not statistically validated.
