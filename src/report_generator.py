"""Diagnostic report generation (Markdown and HTML).

The report contains: test settings, measurements, diagnosis, evidence, confidence,
rules checked, suggested extra tests, and limitations. Simulated data is always labelled.
"""
from __future__ import annotations

import html
import os
import re
from datetime import datetime
from typing import List, Optional, Tuple

from . import project_info as info
from .diagnosis import Diagnosis, Thresholds
from .models import EvidenceBundle, ProbeStats
from .performance import compare_stats

Block = Tuple  # ("p", text) | ("ul", [items]) | ("table", headers, rows)


def _v(value) -> str:
    return "n/a" if value is None or value == "" else str(value)


def _probe_row(label: str, s: Optional[ProbeStats]) -> List[str]:
    if s is None:
        return [label, "not measured", "", "", "", "", "", "", ""]
    if not s.available:
        return [label, f"unavailable ({s.error})", "", "", "", "", "", "", ""]
    return [label, s.target, _v(s.sent), _v(s.received), _v(s.loss_pct), _v(s.avg_ms), _v(s.median_ms),
            _v(s.jitter_ms), f"{_v(s.min_ms)} / {_v(s.max_ms)}"]


def build_sections(bundle: EvidenceBundle, diag: Diagnosis, thresholds: Optional[Thresholds] = None) -> List[Tuple[str, List[Block]]]:
    thresholds = thresholds or Thresholds()
    s = bundle.settings
    sections: List[Tuple[str, List[Block]]] = []

    if bundle.is_simulated:
        banner = ("DATA SOURCE: SIMULATED. This report was produced from the lab simulator "
                  f"(scenario: {bundle.scenario}). The numbers are NOT real network measurements and are not "
                  "fault-injection results.")
    else:
        banner = f"DATA SOURCE: REAL network measurements taken on {bundle.platform} at {bundle.timestamp}."
    sections.append(("Data source", [("p", banner)]))

    sections.append(("Project", [("table", ["Item", "Value"], [
        ["Project", info.PROJECT_TITLE],
        ["Hackathon", f"{info.HACKATHON} | {info.PROBLEM_STATEMENT} | {info.CATEGORY}"],
        ["Team code", info.TEAM_CODE],
        ["Team", ", ".join(info.TEAM_MEMBERS)],
        ["College mentor", info.COLLEGE_MENTOR],
        ["Report created", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        ["Test run time", bundle.timestamp],
    ])]))

    conf = diag.confidence if not diag.is_inconclusive else "Not applicable (Inconclusive)"
    sections.append(("Diagnosis", [
        ("table", ["Item", "Value"], [
            ["Result", diag.label], ["Confidence", conf], ["Rule used", diag.rule_id]]),
        ("p", diag.explanation),
        ("p", "Confidence is a simple evidence-counting level. It is not a validated probability."),
    ]))
    if diag.secondary:
        sections.append(("Other issues also seen", [("ul", diag.secondary)]))
    sections.append(("Supporting evidence", [("ul", diag.evidence or ["No supporting evidence available."])]))
    sections.append(("Why this confidence level", [("ul", diag.confidence_reasons or ["n/a"])]))

    sections.append(("Test settings", [("table", ["Setting", "Value"], [
        ["Router address", _v(bundle.gateway) + (" (entered manually)" if s.gateway_override else " (auto-detected)")],
        ["Router probes", _v(s.router_probes)],
        ["External target", s.external_target],
        ["External probes (normal and busy link)", _v(s.external_probes)],
        ["Probe timeout / interval", f"{s.ping_timeout_ms} ms / {s.probe_interval_s} s"],
        ["DNS domains", ", ".join(s.domains)],
        ["DNS method", bundle.dns.method if bundle.dns else "n/a"],
        ["DNS timeout", f"{s.dns_timeout_s} s"],
        ["Busy-link test", f"{'on' if s.run_load_test else 'off'}; {s.load_threads} download threads"],
    ])]))

    sections.append(("Measurements: ping tests", [("table",
        ["Test", "Target", "Sent", "Received", "Loss %", "Avg ms", "Median ms", "Jitter ms", "Min / Max ms"],
        [_probe_row("Router", bundle.router), _probe_row("External (normal)", bundle.external_baseline),
         _probe_row("External (busy link)", bundle.external_loaded)])]))

    if bundle.dns:
        d = bundle.dns
        blocks: List[Block] = [
            ("p", f"DNS servers found: {', '.join(d.servers) or 'unavailable'}. Server tested: {d.server_tested or 'operating-system resolver'}."),
            ("table", ["Domain", "Result", "Time ms", "Error"],
             [[x.domain, "OK" if x.success else "FAILED", _v(x.time_ms), x.error] for x in d.lookups])]
        sections.append(("Measurements: DNS lookups", blocks))
    else:
        sections.append(("Measurements: DNS lookups", [("p", "DNS check unavailable.")]))

    rows = compare_stats(bundle.external_baseline, bundle.external_loaded)
    if rows and bundle.load:
        ld = bundle.load
        note = (f"Busy link created with {ld.threads} download threads for {ld.duration_s} s "
                f"({ld.bytes_downloaded / 1e6:.1f} MB downloaded; load applied: {ld.applied}). "
                "This compares changes in latency, jitter and loss. It is not a bandwidth test.")
        sections.append(("Network performance: normal vs busy link", [
            ("p", note),
            ("table", ["Metric", "Unit", "Normal", "Busy link", "Change"],
             [[r["Metric"], r["Unit"], _v(r["Normal"]), _v(r["Busy link"]), _v(r["Change"])] for r in rows])]))
    else:
        reason = bundle.load.error if bundle.load and bundle.load.error else "The busy-link test was not run or has no usable result."
        sections.append(("Network performance: normal vs busy link", [("p", reason)]))

    sections.append(("Rules checked", [("table", ["Rule", "Name", "State", "Detail"],
                                        [[r.rule_id, r.name, r.state, r.detail] for r in diag.rules])]))
    if diag.additional_tests:
        title = "Suggested additional tests" if diag.is_inconclusive else "Suggested next steps"
        sections.append((title, [("ul", diag.additional_tests)]))
    if bundle.notes:
        sections.append(("Notes", [("ul", bundle.notes)]))
    sections.append(("Decision limits used (proposed, not validated)", [("table", ["Limit", "Value"],
                    [[k, _v(v)] for k, v in thresholds.to_dict().items()])]))
    sections.append(("Limitations", [("ul", diag.limitations)]))
    return sections


def _md_cell(text: str) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")


def generate_markdown_report(bundle: EvidenceBundle, diag: Diagnosis, thresholds: Optional[Thresholds] = None) -> str:
    lines = [f"# Diagnostic Report: {info.PROJECT_TITLE}", ""]
    for title, blocks in build_sections(bundle, diag, thresholds):
        lines += [f"## {title}", ""]
        for block in blocks:
            if block[0] == "p":
                lines += [block[1], ""]
            elif block[0] == "ul":
                lines += [f"- {item}" for item in block[1]] + [""]
            else:
                _, headers, rows = block
                lines.append("| " + " | ".join(_md_cell(h) for h in headers) + " |")
                lines.append("|" + "---|" * len(headers))
                lines += ["| " + " | ".join(_md_cell(c) for c in row) + " |" for row in rows]
                lines.append("")
    return "\n".join(lines)


_CSS = """body{font-family:Segoe UI,Arial,sans-serif;max-width:960px;margin:24px auto;padding:0 16px;color:#1f2937;background:#fbfaf7;line-height:1.5}
h1{font-size:1.5rem;border-bottom:3px solid #0f766e;padding-bottom:6px}h2{font-size:1.1rem;margin-top:28px;color:#0f766e}
table{border-collapse:collapse;width:100%;font-size:.88rem;margin:8px 0;background:#fff}th,td{border:1px solid #d6ddd6;padding:5px 8px;text-align:left;vertical-align:top}
th{background:#e6f0ec}.banner{padding:10px 14px;border-radius:8px;background:#fef3c7;border:1px solid #e5b84a}
.real{background:#dcfce7;border-color:#86c99a}"""


def generate_html_report(bundle: EvidenceBundle, diag: Diagnosis, thresholds: Optional[Thresholds] = None) -> str:
    esc = html.escape
    out = [f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>Diagnostic Report {esc(info.TEAM_CODE)}</title>",
           f"<style>{_CSS}</style></head><body>", f"<h1>Diagnostic Report: {esc(info.PROJECT_TITLE)}</h1>"]
    for title, blocks in build_sections(bundle, diag, thresholds):
        out.append(f"<h2>{esc(title)}</h2>")
        for block in blocks:
            if block[0] == "p":
                cls = " class='banner real'" if title == "Data source" and not bundle.is_simulated else (
                    " class='banner'" if title == "Data source" else "")
                out.append(f"<p{cls}>{esc(block[1])}</p>")
            elif block[0] == "ul":
                out.append("<ul>" + "".join(f"<li>{esc(str(i))}</li>" for i in block[1]) + "</ul>")
            else:
                _, headers, rows = block
                out.append("<table><tr>" + "".join(f"<th>{esc(h)}</th>" for h in headers) + "</tr>")
                out += ["<tr>" + "".join(f"<td>{esc(str(c))}</td>" for c in row) + "</tr>" for row in rows]
                out.append("</table>")
    out.append("</body></html>")
    return "\n".join(out)


def report_filename(bundle: EvidenceBundle, extension: str) -> str:
    stamp = re.sub(r"[^0-9T]", "", bundle.timestamp.replace("-", "").replace(":", ""))
    tag = "SIMULATED" if bundle.is_simulated else "REAL"
    scenario = f"_{bundle.scenario}" if bundle.is_simulated else ""
    return f"{info.TEAM_CODE}_report_{tag}{scenario}_{stamp}.{extension}"


def save_report(content: str, filename: str, directory: str = "reports") -> str:
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, filename)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(content)
    return path
