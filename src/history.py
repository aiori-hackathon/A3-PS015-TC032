"""SQLite persistence for connectivity diagnosis history."""
from __future__ import annotations

import json
import sqlite3
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import EvidenceBundle, SOURCE_REAL


DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "connectivity_history.db"


def _connect(db_path: Optional[str | Path] = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path is not None else DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(path))
    connection.row_factory = sqlite3.Row
    return connection


def initialize_history(db_path: Optional[str | Path] = None) -> None:
    """Create the history table if it does not already exist."""
    with _connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS diagnosis_history (
                run_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                source TEXT NOT NULL,
                scenario TEXT NOT NULL,
                diagnosis_rule TEXT,
                diagnosis_label TEXT,
                evidence_json TEXT NOT NULL
            )
            """
        )


def save_run(
    bundle: EvidenceBundle,
    diagnosis: Any = None,
    db_path: Optional[str | Path] = None,
) -> str:
    """Save one completed run and return its unique ID."""
    initialize_history(db_path)

    run_id = str(uuid.uuid4())
    rule_id = getattr(diagnosis, "rule_id", None)
    label = getattr(diagnosis, "label", None)

    with _connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO diagnosis_history (
                run_id, timestamp, source, scenario,
                diagnosis_rule, diagnosis_label, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                bundle.timestamp,
                bundle.source,
                bundle.scenario,
                rule_id,
                label,
                json.dumps(bundle.to_dict()),
            ),
        )

    return run_id


def get_history(
    limit: int = 50,
    real_only: bool = False,
    db_path: Optional[str | Path] = None,
) -> List[Dict[str, Any]]:
    """Return recent saved runs, newest first."""
    initialize_history(db_path)

    query = "SELECT * FROM diagnosis_history"
    parameters: List[Any] = []

    if real_only:
        query += " WHERE source = ?"
        parameters.append(SOURCE_REAL)

    query += " ORDER BY timestamp DESC, rowid DESC LIMIT ?"
    parameters.append(max(1, int(limit)))

    with _connect(db_path) as connection:
        rows = connection.execute(query, parameters).fetchall()

    results = []
    for row in rows:
        item = dict(row)
        item["evidence"] = json.loads(item.pop("evidence_json"))
        results.append(item)

    return results


def get_real_baseline_runs(
    limit: int = 100,
    db_path: Optional[str | Path] = None,
) -> List[Dict[str, Any]]:
    """Return real measurement runs only, for historical baseline learning."""
    return get_history(limit=limit, real_only=True, db_path=db_path)
def calculate_historical_baseline(
    limit: int = 100,
    min_samples: int = 5,
    db_path: Optional[str | Path] = None,
) -> Dict[str, Any]:
    """Learn normal network metrics from previous real measurement runs only."""
    runs = get_real_baseline_runs(limit=limit, db_path=db_path)

    samples = []
    for run in runs:
        evidence = run.get("evidence", {})
        stats = evidence.get("external_baseline") or {}

        if not stats.get("available"):
            continue

        samples.append({
            "latency_ms": stats.get("median_ms"),
            "jitter_ms": stats.get("jitter_ms"),
            "packet_loss_pct": stats.get("loss_pct"),
        })

    def valid_values(key: str) -> List[float]:
        return [
            float(sample[key])
            for sample in samples
            if sample[key] is not None
        ]

    def median_value(key: str) -> Optional[float]:
        values = valid_values(key)
        return round(float(__import__("statistics").median(values)), 1) if values else None

    sample_count = len(samples)
    ready = sample_count >= min_samples

    return {
        "ready": ready,
        "sample_count": sample_count,
        "required_samples": min_samples,
        "latency_ms": median_value("latency_ms") if ready else None,
        "jitter_ms": median_value("jitter_ms") if ready else None,
        "packet_loss_pct": median_value("packet_loss_pct") if ready else None,
        "message": (
            "Historical baseline ready."
            if ready
            else f"Need {min_samples - sample_count} more valid real test runs."
        ),
    }
