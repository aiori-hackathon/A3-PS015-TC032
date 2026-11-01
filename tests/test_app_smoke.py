"""Smoke test: the Streamlit dashboard runs the lab simulator for every scenario without errors."""
import os

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest

from src.simulator import SCENARIOS

SIM = "Lab simulator (simulated data)"
APP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")


def test_dashboard_starts_with_no_error():
    at = AppTest.from_file(APP, default_timeout=60).run()
    assert not at.exception
    assert any("Start Diagnosis" in b.label for b in at.button)


@pytest.mark.parametrize("key", list(SCENARIOS))
def test_dashboard_runs_each_simulated_scenario(key):
    at = AppTest.from_file(APP, default_timeout=60).run()
    at.radio(key="mode").set_value(SIM).run()
    at.selectbox(key="scenario").set_value(key).run()
    at.button(key="start").click().run()
    assert not at.exception
    text = " ".join(m.value for m in at.markdown)
    assert "SIMULATED DATA" in text
    assert "Inconclusive" in text if key.startswith("inconclusive") else "Confidence:" in text
