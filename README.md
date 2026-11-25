<img width="1917" height="912" alt="image" src="https://github.com/user-attachments/assets/4ae1d2bd-06de-4477-989a-067220f6b511" /># Explainable Home and Last-Mile Connectivity Diagnosis

**AIORI-3 Hackathon | Problem Statement PS-015 | Category: Smart Cities | Team code: A3-PS015-TC032**

| | |
|---|---|
| Team | Divya PR, Sartaj S |
| College mentor | Neethu Mariam Panicker |
| Repository | https://github.com/aiori-hackathon/A3-PS015-TC032 |
| Live demo | https://youtu.be/qilcN_MvZMw?si=ic9kRI4UaPkU4kxY |
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

| Feature | Description | Location |
|---|---|---|
| Router connectivity | Detects and checks the default gateway | `src/router_check.py` |
| DNS diagnostics | DNS resolution, lookup time and DNS server information | `src/dns_check.py` |
| Latency analysis | Average, median, min/max, standard deviation and jitter | `src/latency_check.py` |
| Packet loss detection | Sent/received packet counts and loss percentage | `src/packet_loss.py` |
| Busy-link comparison | Compares network performance under normal and loaded conditions | `src/performance.py` |
| Explainable diagnosis | Rule-based diagnosis with evidence and confidence explanations | `src/diagnosis.py` |
| Historical baseline | Learns typical network performance from real measurements | `src/history.py` |
| Network history dashboard | Displays previous measurements and performance trends | `app.py` |
| Personalized anomaly detection | Detects unusual latency, jitter and packet loss against historical baselines | `src/anomaly.py` |
| Network health score | Calculates a weighted score from 0–100 with metric breakdown | `src/health_score.py` |
| Smart recommendations | Suggests troubleshooting actions with explanations | `src/recommendations.py` |
| Downloadable reports | Generates HTML and Markdown reports | `src/report_generator.py` |
| Lab simulator | Demonstrates network scenarios using clearly labelled simulated data | `src/simulator.py` |


## Where things stand


- Historical baseline learning from real network measurements.
- Network history dashboard with performance trends.
- Personalized network anomaly detection.
- Network health score with metric-wise breakdown.
- Smart troubleshooting recommendations with explanations.
- Automated test suite: **133 tests passed** in the latest verified run.
- Real lab fault-injection testing has not been completed yet. See `docs/test_plan.md`.
- Health scores and anomaly thresholds are heuristic starting values and need further tuning.
- Confidence levels use simple evidence counting, not validated probabilities.
- Live measurements depend on the network and permissions of the computer running the app.

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


1. **Start with the lab simulator:** Select a scenario and press **Start Diagnosis**. Simulated results are clearly labelled.
2. **Run a live measurement:** Select *Live measurement (real network)* and press **Start Diagnosis**. This measures the network of the computer running the app.
3. **Review the diagnosis:** Read the plain-language summary, supporting evidence, confidence explanation and suggested next steps.
4. **Check network history:** Review previous real measurements and historical performance trends.
5. **Review anomaly alerts:** Once at least 5 real measurements are available, compare current network performance against the historical baseline.
6. **Check network health:** View the 0–100 health score and latency, jitter and packet-loss breakdown.
7. **Follow smart recommendations:** Review suggested troubleshooting actions and explanations.
8. **Download reports:** Export the diagnosis as HTML or Markdown.

**Note:** Health scores and anomaly detection use heuristic thresholds. They are not validated predictions or guarantees of network performance.

## Run the tests

```powershell
python -m pytest -v
python -m src.simulator                       # prints all simulated scenarios
python scripts/generate_test_results.py       # writes docs/test_results.md from a real run
python scripts/make_sample_report.py dns_failure   # writes a SAMPLE report to reports/
```

## Project structure


```text
A3-PS015-TC032/
|-- app.py
|-- requirements.txt
|-- packages.txt
|-- run_app.bat
|-- run_tests.bat
|-- src/
|   |-- router_check.py
|   |-- dns_check.py
|   |-- latency_check.py
|   |-- packet_loss.py
|   |-- performance.py
|   |-- diagnosis.py
|   |-- history.py
|   |-- anomaly.py
|   |-- health_score.py
|   |-- recommendations.py
|   |-- report_generator.py
|   |-- simulator.py
|   |-- orchestrator.py
|   |-- charts.py
|   |-- models.py
|-- tests/
|-- docs/
|-- reports/
|-- screenshots/
|-- scripts/
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
