"""Plotly charts for the dashboard."""
from __future__ import annotations

from typing import List, Optional

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .models import ProbeStats

BLUE = "#0f766e"
ORANGE = "#d97706"
RED = "#dc2626"
GREY = "#8a94a0"


def rtt_chart(stats: Optional[ProbeStats], title: str, color: str = BLUE) -> Optional[go.Figure]:
    """Round-trip time of every probe. Lost probes are shown as red crosses on the bottom."""
    if stats is None or not stats.available or not stats.sequence:
        return None
    xs = list(range(1, len(stats.sequence) + 1))
    ok_x = [x for x, v in zip(xs, stats.sequence) if v is not None]
    ok_y = [v for v in stats.sequence if v is not None]
    lost_x = [x for x, v in zip(xs, stats.sequence) if v is None]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ok_x, y=ok_y, mode="lines+markers", name="Reply (RTT)", line=dict(color=color)))
    if lost_x:
        fig.add_trace(go.Scatter(x=lost_x, y=[0] * len(lost_x), mode="markers", name="No reply (lost)",
                                 marker=dict(color=RED, symbol="x", size=10)))
    if stats.median_ms is not None:
        fig.add_hline(y=stats.median_ms, line_dash="dot", line_color=GREY,
                      annotation_text=f"median {stats.median_ms} ms", annotation_position="top left")
    fig.update_layout(title=title, xaxis_title="Probe number", yaxis_title="Round-trip time (ms)",
                      height=300, margin=dict(l=10, r=10, t=45, b=10), legend=dict(orientation="h", y=-0.3),
                      plot_bgcolor="#ffffff", paper_bgcolor="rgba(0,0,0,0)")
    return fig


def comparison_chart(rows: List[dict]) -> Optional[go.Figure]:
    """Normal vs busy-link bars for median latency, jitter and packet loss."""
    if not rows:
        return None
    fig = make_subplots(rows=1, cols=len(rows), subplot_titles=[f"{r['Metric']} ({r['Unit']})" for r in rows])
    for i, row in enumerate(rows, start=1):
        fig.add_trace(go.Bar(x=["Normal", "Busy link"], y=[row["Normal"] or 0, row["Busy link"] or 0],
                             marker_color=[BLUE, ORANGE], showlegend=False,
                             text=[row["Normal"], row["Busy link"]], textposition="outside"), row=1, col=i)
    fig.update_layout(height=320, margin=dict(l=10, r=10, t=50, b=10), plot_bgcolor="#ffffff", paper_bgcolor="rgba(0,0,0,0)")
    return fig
