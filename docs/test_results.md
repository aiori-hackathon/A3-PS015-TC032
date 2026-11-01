# Test Results (generated from an actual test run)

This file is written by `scripts/generate_test_results.py`. Nothing here is typed by hand.

| Item | Value |
|---|---|
| Run date | 2026-10-30 04:53:49 |
| Operating system | Linux-6.18.44-fc-v185-x86_64-with-glibc2.39 |
| Python | 3.12.3 |
| Streamlit / pandas / plotly / pytest | 1.66.1 / 3.0.2 / 7.1.0 / 9.2.0 |
| Exit status | all tests passed |
| Summary line | `============================= 106 passed in 4.01s ==============================` |

## What these results do and do not show

* The tests use **hand-made evidence, fake network functions and the lab simulator**. They show that the
  decision rules, parsers, report generator and dashboard behave as designed.
* They are **not real network measurements** and **not fault-injection results**. Real lab fault-injection
  (blocking the router/DNS, adding loss and load on a lab router) is a separate activity, recorded in
  `docs/test_plan.md` section 5, and must be filled in only after it has been done.

## Simulator scenario results (SIMULATED data, seed 42)

```
SIMULATED scenarios (lab simulator, not real network measurements)

[OK  ] 1. Normal network condition                   -> No fault detected                      rule=R7  confidence=High
[OK  ] 2. Router unreachable                         -> Router / home network unreachable      rule=R1  confidence=High
[OK  ] 3. DNS failure                                -> DNS failure                            rule=R2  confidence=High
[OK  ] 4. Added packet loss                          -> Packet loss beyond the router          rule=R4  confidence=High
[OK  ] 5. Congestion / busy link                     -> Possible congestion (busy link)        rule=R6  confidence=High
[OK  ] 6a. Inconclusive: conflicting evidence        -> Inconclusive                           rule=C   confidence=Not applicable
[OK  ] 6b. Inconclusive: missing measurements        -> Inconclusive                           rule=R0  confidence=Not applicable
```

## Full pytest output

```
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.2.0, pluggy-1.7.0 -- /usr/bin/python3
rootdir: /home/claude/A3-PS015-TC032
plugins: anyio-4.15.1
collecting ... collected 106 items

tests/test_app_smoke.py::test_dashboard_starts_with_no_error PASSED      [  0%]
tests/test_app_smoke.py::test_dashboard_runs_each_simulated_scenario[normal] PASSED [  1%]
tests/test_app_smoke.py::test_dashboard_runs_each_simulated_scenario[router_unreachable] PASSED [  2%]
tests/test_app_smoke.py::test_dashboard_runs_each_simulated_scenario[dns_failure] PASSED [  3%]
tests/test_app_smoke.py::test_dashboard_runs_each_simulated_scenario[packet_loss] PASSED [  4%]
tests/test_app_smoke.py::test_dashboard_runs_each_simulated_scenario[congestion] PASSED [  5%]
tests/test_app_smoke.py::test_dashboard_runs_each_simulated_scenario[inconclusive_conflict] PASSED [  6%]
tests/test_app_smoke.py::test_dashboard_runs_each_simulated_scenario[inconclusive_missing] PASSED [  7%]
tests/test_diagnosis.py::test_normal_with_load_comparison_is_high PASSED [  8%]
tests/test_diagnosis.py::test_normal_without_load_comparison_is_medium PASSED [  9%]
tests/test_diagnosis.py::test_router_unreachable_high_when_external_also_fails PASSED [ 10%]
tests/test_diagnosis.py::test_router_down_but_internet_works_is_inconclusive_conflict PASSED [ 11%]
tests/test_diagnosis.py::test_dns_failure_high_when_ip_checks_work PASSED [ 12%]
tests/test_diagnosis.py::test_dns_partial_failure_medium_and_minority_low PASSED [ 13%]
tests/test_diagnosis.py::test_slow_dns_rule PASSED                       [ 14%]
tests/test_diagnosis.py::test_packet_loss_beyond_router PASSED           [ 15%]
tests/test_diagnosis.py::test_single_lost_probe_is_not_a_fault PASSED    [ 16%]
tests/test_diagnosis.py::test_packet_loss_on_local_segment PASSED        [ 16%]
tests/test_diagnosis.py::test_congestion_needs_baseline_and_load_evidence PASSED [ 17%]
tests/test_diagnosis.py::test_congestion_not_claimed_when_load_was_not_applied PASSED [ 18%]
tests/test_diagnosis.py::test_congestion_not_evaluated_when_baseline_already_bad PASSED [ 19%]
tests/test_diagnosis.py::test_high_latency_rule PASSED                   [ 20%]
tests/test_diagnosis.py::test_external_down_with_router_ok_is_inconclusive PASSED [ 21%]
tests/test_diagnosis.py::test_missing_data_is_inconclusive_not_a_guess PASSED [ 22%]
tests/test_diagnosis.py::test_no_rule_fired_but_router_check_missing_is_inconclusive PASSED [ 23%]
tests/test_diagnosis.py::test_multiple_issues_lower_confidence_and_are_listed PASSED [ 24%]
tests/test_diagnosis.py::test_router_check_unavailable_caps_confidence_at_medium PASSED [ 25%]
tests/test_diagnosis.py::test_thresholds_can_be_changed PASSED           [ 26%]
tests/test_diagnosis.py::test_every_diagnosis_lists_rules_and_limitations PASSED [ 27%]
tests/test_dns.py::test_parse_ipconfig_dns_reads_continuation_lines PASSED [ 28%]
tests/test_dns.py::test_parse_linux_and_mac_dns PASSED                   [ 29%]
tests/test_dns.py::test_dns_packet_round_trip PASSED                     [ 30%]
tests/test_dns.py::test_dns_response_errors PASSED                       [ 31%]
tests/test_dns.py::test_check_dns_all_ok_records_server_and_times PASSED [ 32%]
tests/test_dns.py::test_check_dns_failure_counts PASSED                  [ 33%]
tests/test_dns.py::test_check_dns_falls_back_to_system_resolver_without_ipv4_server PASSED [ 33%]
tests/test_dns.py::test_check_dns_system_method_never_queries_server_directly PASSED [ 34%]
tests/test_dns.py::test_udp_query_to_local_fake_server_works PASSED      [ 35%]
tests/test_router.py::test_parse_windows_gateway_skips_disconnected_and_ipv6 PASSED [ 36%]
tests/test_router.py::test_parse_windows_gateway_none_when_missing PASSED [ 37%]
tests/test_router.py::test_parse_linux_and_macos_gateway PASSED          [ 38%]
tests/test_router.py::test_get_default_gateway_uses_runner PASSED        [ 39%]
tests/test_router.py::test_check_router_reachable PASSED                 [ 40%]
tests/test_router.py::test_check_router_unreachable PASSED               [ 41%]
tests/test_router.py::test_check_router_no_gateway_is_unavailable_not_guessed PASSED [ 42%]
tests/test_router.py::test_parse_ping_windows_reply PASSED               [ 43%]
tests/test_router.py::test_parse_ping_linux_reply PASSED                 [ 44%]
tests/test_router.py::test_parse_ping_failures_are_none PASSED           [ 45%]
tests/test_router.py::test_build_ping_command_per_os PASSED              [ 46%]
tests/test_router.py::test_validate_host_blocks_bad_input PASSED         [ 47%]
tests/test_router.py::test_summarise_statistics PASSED                   [ 48%]
tests/test_scenarios.py::test_each_scenario_gives_expected_result_for_many_seeds[normal-1] PASSED [ 49%]
tests/test_scenarios.py::test_each_scenario_gives_expected_result_for_many_seeds[normal-7] PASSED [ 50%]
tests/test_scenarios.py::test_each_scenario_gives_expected_result_for_many_seeds[normal-42] PASSED [ 50%]
tests/test_scenarios.py::test_each_scenario_gives_expected_result_for_many_seeds[normal-123] PASSED [ 51%]
tests/test_scenarios.py::test_each_scenario_gives_expected_result_for_many_seeds[normal-2026] PASSED [ 52%]
tests/test_scenarios.py::test_each_scenario_gives_expected_result_for_many_seeds[router_unreachable-1] PASSED [ 53%]
tests/test_scenarios.py::test_each_scenario_gives_expected_result_for_many_seeds[router_unreachable-7] PASSED [ 54%]
tests/test_scenarios.py::test_each_scenario_gives_expected_result_for_many_seeds[router_unreachable-42] PASSED [ 55%]
tests/test_scenarios.py::test_each_scenario_gives_expected_result_for_many_seeds[router_unreachable-123] PASSED [ 56%]
tests/test_scenarios.py::test_each_scenario_gives_expected_result_for_many_seeds[router_unreachable-2026] PASSED [ 57%]
tests/test_scenarios.py::test_each_scenario_gives_expected_result_for_many_seeds[dns_failure-1] PASSED [ 58%]
tests/test_scenarios.py::test_each_scenario_gives_expected_result_for_many_seeds[dns_failure-7] PASSED [ 59%]
tests/test_scenarios.py::test_each_scenario_gives_expected_result_for_many_seeds[dns_failure-42] PASSED [ 60%]
tests/test_scenarios.py::test_each_scenario_gives_expected_result_for_many_seeds[dns_failure-123] PASSED [ 61%]
tests/test_scenarios.py::test_each_scenario_gives_expected_result_for_many_seeds[dns_failure-2026] PASSED [ 62%]
tests/test_scenarios.py::test_each_scenario_gives_expected_result_for_many_seeds[packet_loss-1] PASSED [ 63%]
tests/test_scenarios.py::test_each_scenario_gives_expected_result_for_many_seeds[packet_loss-7] PASSED [ 64%]
tests/test_scenarios.py::test_each_scenario_gives_expected_result_for_many_seeds[packet_loss-42] PASSED [ 65%]
tests/test_scenarios.py::test_each_scenario_gives_expected_result_for_many_seeds[packet_loss-123] PASSED [ 66%]
tests/test_scenarios.py::test_each_scenario_gives_expected_result_for_many_seeds[packet_loss-2026] PASSED [ 66%]
tests/test_scenarios.py::test_each_scenario_gives_expected_result_for_many_seeds[congestion-1] PASSED [ 67%]
tests/test_scenarios.py::test_each_scenario_gives_expected_result_for_many_seeds[congestion-7] PASSED [ 68%]
tests/test_scenarios.py::test_each_scenario_gives_expected_result_for_many_seeds[congestion-42] PASSED [ 69%]
tests/test_scenarios.py::test_each_scenario_gives_expected_result_for_many_seeds[congestion-123] PASSED [ 70%]
tests/test_scenarios.py::test_each_scenario_gives_expected_result_for_many_seeds[congestion-2026] PASSED [ 71%]
tests/test_scenarios.py::test_each_scenario_gives_expected_result_for_many_seeds[inconclusive_conflict-1] PASSED [ 72%]
tests/test_scenarios.py::test_each_scenario_gives_expected_result_for_many_seeds[inconclusive_conflict-7] PASSED [ 73%]
tests/test_scenarios.py::test_each_scenario_gives_expected_result_for_many_seeds[inconclusive_conflict-42] PASSED [ 74%]
tests/test_scenarios.py::test_each_scenario_gives_expected_result_for_many_seeds[inconclusive_conflict-123] PASSED [ 75%]
tests/test_scenarios.py::test_each_scenario_gives_expected_result_for_many_seeds[inconclusive_conflict-2026] PASSED [ 76%]
tests/test_scenarios.py::test_each_scenario_gives_expected_result_for_many_seeds[inconclusive_missing-1] PASSED [ 77%]
tests/test_scenarios.py::test_each_scenario_gives_expected_result_for_many_seeds[inconclusive_missing-7] PASSED [ 78%]
tests/test_scenarios.py::test_each_scenario_gives_expected_result_for_many_seeds[inconclusive_missing-42] PASSED [ 79%]
tests/test_scenarios.py::test_each_scenario_gives_expected_result_for_many_seeds[inconclusive_missing-123] PASSED [ 80%]
tests/test_scenarios.py::test_each_scenario_gives_expected_result_for_many_seeds[inconclusive_missing-2026] PASSED [ 81%]
tests/test_scenarios.py::test_all_scenarios_helper_matches PASSED        [ 82%]
tests/test_scenarios.py::test_simulated_data_is_always_labelled PASSED   [ 83%]
tests/test_scenarios.py::test_same_seed_same_numbers PASSED              [ 83%]
tests/test_scenarios.py::test_unknown_scenario_raises PASSED             [ 84%]
tests/test_scenarios.py::test_inconclusive_scenarios_have_no_confidence_and_suggest_tests PASSED [ 85%]
tests/test_scenarios.py::test_report_contains_required_sections[normal] PASSED [ 86%]
tests/test_scenarios.py::test_report_contains_required_sections[router_unreachable] PASSED [ 87%]
tests/test_scenarios.py::test_report_contains_required_sections[dns_failure] PASSED [ 88%]
tests/test_scenarios.py::test_report_contains_required_sections[packet_loss] PASSED [ 89%]
tests/test_scenarios.py::test_report_contains_required_sections[congestion] PASSED [ 90%]
tests/test_scenarios.py::test_report_contains_required_sections[inconclusive_conflict] PASSED [ 91%]
tests/test_scenarios.py::test_report_contains_required_sections[inconclusive_missing] PASSED [ 92%]
tests/test_scenarios.py::test_report_filename_and_save PASSED            [ 93%]
tests/test_scenarios.py::test_html_report_escapes_text PASSED            [ 94%]
tests/test_scenarios.py::test_compare_stats_rows PASSED                  [ 95%]
tests/test_scenarios.py::test_measure_loaded_reports_applied_load PASSED [ 96%]
tests/test_scenarios.py::test_measure_loaded_says_when_load_failed PASSED [ 97%]
tests/test_scenarios.py::test_orchestrator_builds_complete_bundle_and_diagnosis PASSED [ 98%]
tests/test_scenarios.py::test_orchestrator_with_load_test_uses_load_generator PASSED [ 99%]
tests/test_scenarios.py::test_orchestrator_handles_ping_unavailable PASSED [100%]

============================= 106 passed in 4.01s ==============================
```
