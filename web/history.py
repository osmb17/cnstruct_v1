"""
history.py — Persistent run history for CNSTRUCT 1.0.
Saves each generated barlist to a local SQLite database.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "cnstruct_history.db"


def init_db() -> None:
    """Create the runs table if it doesn't exist."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS runs (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp       TEXT    NOT NULL,
                template_name   TEXT    NOT NULL,
                job_name        TEXT    DEFAULT '',
                job_number      TEXT    DEFAULT '',
                detailer        TEXT    DEFAULT '',
                params_json     TEXT    NOT NULL,
                bars_json       TEXT    NOT NULL,
                total_weight_lb REAL    DEFAULT 0,
                total_cost_usd  REAL    DEFAULT 0
            )
            """
        )


def save_run(
    template_name: str,
    job_name: str,
    job_number: str,
    detailer: str,
    params: dict,
    bars,
    total_weight_lb: float,
    total_cost_usd: float,
) -> int:
    """Persist a run. Returns the new row id."""
    bars_data = [
        {
            "mark":        b.mark,
            "size":        b.size,
            "qty":         b.qty,
            "length_in":   b.length_in,
            "shape":       b.shape,
            "leg_a_in":    b.leg_a_in,
            "leg_b_in":    b.leg_b_in,
            "leg_c_in":    b.leg_c_in,
            "notes":       b.notes,
            "ref":         b.ref,
            "source_rule": b.source_rule,
            "review_flag": b.review_flag,
        }
        for b in bars
    ]
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            """INSERT INTO runs
               (timestamp, template_name, job_name, job_number, detailer,
                params_json, bars_json, total_weight_lb, total_cost_usd)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                datetime.now().strftime("%Y-%m-%d %H:%M"),
                template_name,
                job_name,
                job_number,
                detailer,
                json.dumps(params),
                json.dumps(bars_data),
                total_weight_lb,
                total_cost_usd,
            ),
        )
        return cur.lastrowid


def list_runs(limit: int = 200) -> list[dict]:
    """Return the most recent runs, newest first."""
    cols = [
        "id", "timestamp", "template_name", "job_name",
        "job_number", "detailer", "total_weight_lb", "total_cost_usd",
    ]
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            f"SELECT {', '.join(cols)} FROM runs ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(zip(cols, row)) for row in rows]


def load_run(run_id: int) -> dict:
    """Load a full run by id. Returns a dict with bars (BarRow list) and metadata."""
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            """SELECT template_name, job_name, job_number, detailer,
                      params_json, bars_json, total_weight_lb, total_cost_usd, timestamp
               FROM runs WHERE id = ?""",
            (run_id,),
        ).fetchone()
    if row is None:
        return {}

    from vistadetail.engine.schema import BarRow
    bars = [BarRow(**d) for d in json.loads(row[5])]

    return {
        "id":               run_id,
        "template_name":    row[0],
        "job_name":         row[1],
        "job_number":       row[2],
        "detailer":         row[3],
        "params":           json.loads(row[4]),
        "bars":             bars,
        "total_weight_lb":  row[6],
        "total_cost_usd":   row[7],
        "timestamp":        row[8],
    }


def delete_run(run_id: int) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM runs WHERE id = ?", (run_id,))
