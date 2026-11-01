# Requirements Traceability (proposal to implementation to tests)

| Proposal requirement | Implemented in | Checked by |
|---|---|---|
| Check router (gateway) reachability, several times | `router_check.py` | `test_router.py`, scenario 2 |
| DNS resolves? how fast? which server? | `dns_check.py` | `test_dns.py`, scenario 3 |
| Reply time and packet loss to router and outside server | `latency_check.py`, `packet_loss.py` | `test_router.py`, `test_diagnosis.py` |
| Normal vs busy-link comparison | `performance.py` | `test_scenarios.py`, scenario 5 |
| Mark missing items "unavailable" | `ProbeStats.available`, `check_router` | `test_router.py`, `test_scenarios.py` |
| Clear rules; show measurements and rule used | `diagnosis.py` (`rules` table, evidence) | `test_diagnosis.py` |
| Confidence levels | `diagnosis.py` | `test_diagnosis.py` |
| "Inconclusive" and extra tests | rules R0 and C | scenarios 6a and 6b |
| Report with evidence when cause not found | `report_generator.py` | `test_scenarios.py` |
| Repeatable tests, saved settings | `TestSettings` saved in each report | `test_scenarios.py` |
| Limits can be changed | `Thresholds` and sidebar | `test_diagnosis.py` |
| Controlled fault injection (planned) | `simulator.py` only simulates; real injection planned | `docs/test_plan.md` section 5 |
| Not claimed: cable damage, ISP-internal cause, Wi-Fi interference | `LIMITATIONS`, wording of every rule | `test_diagnosis.py` |
