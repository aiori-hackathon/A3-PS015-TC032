# Explainable Home and Last-Mile Connectivity Diagnosis

**AIORI-3 Hackathon | Problem Statement PS-015 | Category: Smart Cities | Team code: A3-PS015-TC032**

| | |
|---|---|
| Team | Divya PR, Sartaj S |
| College mentor | Neethu Mariam Panicker |
| Repository | https://github.com/divyapr-27/A3-PS015-TC032 |
| Live demo | **TO BE ADDED: Streamlit Community Cloud URL (not deployed yet)** |
| Original proposal | [`docs/proposal/Proposed-structure-hackathon.pdf`](docs/proposal/Proposed-structure-hackathon.pdf) |

## What is this?

Ever had the internet "feel broken" while a speed test says everything is fine? A speed test tells you how fast the
link *can* go, not *why* it is acting up. This dashboard runs a handful of quick checks (router, DNS, delay, packet
loss, and a controlled "busy link" test), then tells you where the problem most likely is, in plain words.

Every answer comes with the numbers behind it, the rule that fired, and a confidence level. If the evidence is
missing or contradicts itself, it says **Inconclusive** instead of making something up.

## For evaluators: a 2-minute tour

1. Run the app (see below). It opens on the **lab simulator**, so you do not need a special network setup.
2. Press **Start Diagnosis**. Read the "In plain words" box, then open the **Why this answer** tab to see the evidence.
3. Switch the scenario in the sidebar (normal, router down, DNS failure, packet loss, congestion, two inconclusive cases).
4. Change a decision limit under *Decision limits* and watch the answer update.
5. Download the HTML or Markdown report. Ready-made examples are in `reports/`.

## What it can do

| Feature | Where |
|---|---|
| Find the router (default gateway) and check it repeatedly | `src/router_check.py` |
| DNS success, lookup time and DNS server info | `src/dns_check.py` |
| Latency: average, median, min/max, standard deviation, jitter | `src/latency_check.py` |
| Packet loss with sent/received counts | `src/packet_loss.py` |
| Normal vs busy-link comparison (not a bandwidth test) | `src/performance.py` |
| Rule-based diagnosis with evidence, rules table and confidence | `src/diagnosis.py` |
| "Inconclusive" result with suggested extra tests | `src/diagnosis.py` |
| Downloadable reports (HTML and Markdown) | `src/report_generator.py` |
| Lab simulator for the six required cases (always labelled SIMULATED) | `src/simulator.py` |
| Streamlit dashboard with status badges and charts | `app.py` |

## Where things stand

* Everything above is built and covered by automated tests (106 passing).
* Those tests use sample data, fake network functions and the simulator. Details: [`docs/test_results.md`](docs/test_results.md).
* **Real lab fault-injection testing has not been done yet.** The plan is in [`docs/test_plan.md`](docs/test_plan.md).
* The decision limits are starting values that still need tuning, and the confidence levels are simple counting rules, not validated probabilities.
* Screenshots still need to be captured from the running app (see [`screenshots/README.md`](screenshots/README.md)).

## Install and run (Windows)

You need **Python 3.10 or newer** (https://www.python.org/downloads/, tick "Add python.exe to PATH").

**Easiest:** double-click `run_app.bat`.

**Or, step by step in PowerShell** (open the project folder first):

```powershell
py -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
streamlit run app.py
```

If activation is blocked, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` once and try again.
The browser opens at http://localhost:8501.

### Using the dashboard
1. **Start with the lab simulator** (selected by default). Pick a scenario in the sidebar and press **Start Diagnosis**.
2. For a real test choose *Live measurement (real network)* and press **Start Diagnosis** (about 1 minute). It measures the network of the computer running the app.
3. Read the plain-words summary, the confidence level and the **Why this answer** tab. Change the decision limits in the sidebar to see the answer change.
4. Press **Download Report** (HTML or Markdown).

Windows may ask whether Python can use the network, allow it. If auto-detection of the router fails (for example on a non-English Windows),
type the router address in the sidebar.

## Run the tests

```powershell
python -m pytest -v
python -m src.simulator                       # prints all simulated scenarios
python scripts/generate_test_results.py       # writes docs/test_results.md from a real run
python scripts/make_sample_report.py dns_failure   # writes a SAMPLE report to reports/
```

## Project structure

```
A3-PS015-TC032/
|-- app.py                  Streamlit dashboard
|-- requirements.txt        Python packages
|-- packages.txt            System package for Streamlit Cloud (ping)
|-- run_app.bat, run_tests.bat
|-- src/                    router_check, dns_check, latency_check, packet_loss, performance,
|                           diagnosis, report_generator, simulator, orchestrator, charts, models
|-- tests/                  test_router, test_dns, test_diagnosis, test_scenarios, test_app_smoke
|-- docs/                   architecture, data_flow, test_plan, traceability, test_results, github_submission, proposal/
|-- reports/                generated reports (SAMPLE_* files are simulated examples)
|-- screenshots/            real screenshots go here
|-- scripts/                helper scripts
```

## How a diagnosis is made

Router, DNS, delay/loss and a busy-link test produce evidence. Rules then check it in order:
router unreachable, DNS failure, slow DNS, packet loss, high latency, congestion hint. If measurements are missing or
disagree (for example the router ignores ping but the internet works), the answer is **Inconclusive**.
Full rule table: [`docs/architecture.md`](docs/architecture.md). Data flow: [`docs/data_flow.md`](docs/data_flow.md).

## Limitations (from the proposal)

* No proof of a damaged cable, of causes inside the ISP network, or of Wi-Fi interference (no radio data).
* Ping loss covers both directions; some routers and servers ignore or slow down ping.
* The busy-link test creates download load only and shows how latency, jitter and loss change. It is not a bandwidth test.
* "Congestion" is a hint (queueing), not proof of an ISP fault.

## Deploying the live demo later (Streamlit Community Cloud)

The project is ready for deployment: `requirements.txt` and `packages.txt` (installs `ping`) are included.

1. Push the project to GitHub (see [`docs/github_submission.md`](docs/github_submission.md)).
2. Go to https://share.streamlit.io, sign in with GitHub, choose **Create app**, select this repository, branch `main`, main file `app.py`.
3. Copy the app URL into the **Live demo** row at the top of this README.

Note: on Streamlit Cloud the app runs on a cloud server, so **Live measurement** would measure the server's network, not your home.
For the public demo, use the **Lab simulator** mode.

## References

1. RFC 2330, Framework for IP Performance Metrics. 2. RFC 2681, Round-trip Delay Metric. 3. RFC 7680, One-Way Loss Metric.
4. RFC 3393, IP Packet Delay Variation Metric. 5. RFC 6349, Framework for TCP Throughput Testing.
6. RFC 1034 and 7. RFC 1035, Domain Names. 8. RFC 792, Internet Control Message Protocol.
The decision rules, confidence levels, Inconclusive result and escalation report are our own proposed design, not part of any RFC.
