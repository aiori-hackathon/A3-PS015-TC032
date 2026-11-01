"""Create a sample report from the lab simulator.

Usage (from the project folder):
    python scripts/make_sample_report.py              # congestion scenario
    python scripts/make_sample_report.py dns_failure  # any scenario key

Reports from this script are always labelled SIMULATED.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.diagnosis import diagnose  # noqa: E402
from src.report_generator import generate_html_report, generate_markdown_report, save_report  # noqa: E402
from src.simulator import SCENARIOS, simulate_scenario  # noqa: E402

key = sys.argv[1] if len(sys.argv) > 1 else "congestion"
if key not in SCENARIOS:
    sys.exit(f"Unknown scenario '{key}'. Choose one of: {', '.join(SCENARIOS)}")

bundle = simulate_scenario(key, seed=42)
diag = diagnose(bundle)
folder = os.path.join(ROOT, "reports")
base = f"SAMPLE_report_SIMULATED_{key}"
print(save_report(generate_markdown_report(bundle, diag), base + ".md", folder))
print(save_report(generate_html_report(bundle, diag), base + ".html", folder))
