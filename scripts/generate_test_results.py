"""Run the automated tests and write the ACTUAL output to docs/test_results.md.

Usage (from the project folder):    python scripts/generate_test_results.py

Run this on your own Windows computer before submission so the results file shows
your real environment. The file is produced from a real test run, never typed by hand.
"""
import datetime
import os
import platform
import subprocess
import sys
from importlib import metadata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run(args):
    proc = subprocess.run([sys.executable] + args, cwd=ROOT, capture_output=True, text=True, errors="replace")
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def version(name):
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return "not installed"


code, tests = run(["-m", "pytest", "-v", "--tb=short", "-p", "no:cacheprovider"])
_, scenarios = run(["-m", "src.simulator"])
summary = [line for line in tests.splitlines() if line.strip()][-1]

text = f"""# Test Results (generated from an actual test run)

This file is written by `scripts/generate_test_results.py`. Nothing here is typed by hand.

| Item | Value |
|---|---|
| Run date | {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} |
| Operating system | {platform.platform()} |
| Python | {platform.python_version()} |
| Streamlit / pandas / plotly / pytest | {version("streamlit")} / {version("pandas")} / {version("plotly")} / {version("pytest")} |
| Exit status | {"all tests passed" if code == 0 else "SOME TESTS FAILED"} |
| Summary line | `{summary}` |

## What these results do and do not show

* The tests use **hand-made evidence, fake network functions and the lab simulator**. They show that the
  decision rules, parsers, report generator and dashboard behave as designed.
* They are **not real network measurements** and **not fault-injection results**. Real lab fault-injection
  (blocking the router/DNS, adding loss and load on a lab router) is a separate activity, recorded in
  `docs/test_plan.md` section 5, and must be filled in only after it has been done.

## Simulator scenario results (SIMULATED data, seed 42)

```
{scenarios}
```

## Full pytest output

```
{tests}
```
"""
with open(os.path.join(ROOT, "docs", "test_results.md"), "w", encoding="utf-8") as handle:
    handle.write(text)
print(summary)
print("Written: docs/test_results.md")
