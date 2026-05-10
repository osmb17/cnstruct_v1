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


def _reset_db() -> None:
    """Delete the corrupted database file and recreate from scratch."""
    try:
        DB_PATH.unlink(missing_ok=True)
    except OSError:
        pass


def _create_tables(conn: sqlite3.Connection) -> None:
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
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS presets (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            structure_type  TEXT NOT NULL,
            name            TEXT NOT NULL,
            params_json     TEXT NOT NULL,
            created_at      TEXT NOT NULL
        )
        """
    )


def _connect() -> sqlite3.Connection:
    """Open a connection, auto-recovering if the database is malformed."""
    try:
        conn = sqlite3.connect(DB_PATH)
        # Quick integrity check — raises OperationalError if malformed
        conn.execute("SELECT name FROM sqlite_master LIMIT 1").fetchone()
        return conn
    except sqlite3.DatabaseError:
        try:
            conn.close()
        except Exception:
            pass
        _reset_db()
        conn = sqlite3.connect(DB_PATH)
        _create_tables(conn)
        conn.commit()
        return conn


def init_db() -> None:
    """Create the runs table if it doesn't exist."""
    with _connect() as conn:
        _create_tables(conn)


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
    with _connect() as conn:
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
    with _connect() as conn:
        rows = conn.execute(
            f"SELECT {', '.join(cols)} FROM runs ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(zip(cols, row)) for row in rows]


def load_run(run_id: int) -> dict:
    """Load a full run by id. Returns a dict with bars (BarRow list) and metadata."""
    with _connect() as conn:
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
    with _connect() as conn:
        conn.execute("DELETE FROM runs WHERE id = ?", (run_id,))


# ── Presets ────────────────────────────────────────────────────────────────────

def init_presets() -> None:
    """Create the presets table if it doesn't exist (no-op: handled by init_db)."""
    init_db()


def save_preset(structure_type: str, name: str, params: dict) -> int:
    """Save a named input preset. Returns the new row id."""
    init_presets()
    with _connect() as conn:
        cur = conn.execute(
            """INSERT INTO presets (structure_type, name, params_json, created_at)
               VALUES (?, ?, ?, ?)""",
            (
                structure_type,
                name,
                json.dumps(params),
                datetime.now().strftime("%Y-%m-%d %H:%M"),
            ),
        )
        return cur.lastrowid


def list_presets(structure_type: str) -> list[dict]:
    """Return all presets for a given structure type, newest first."""
    init_presets()
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, name, created_at FROM presets WHERE structure_type = ? ORDER BY id DESC",
            (structure_type,),
        ).fetchall()
    return [{"id": r[0], "name": r[1], "created_at": r[2]} for r in rows]


def load_preset_params(preset_id: int) -> dict:
    """Return the params dict for a preset by id."""
    init_presets()
    with _connect() as conn:
        row = conn.execute(
            "SELECT params_json FROM presets WHERE id = ?", (preset_id,)
        ).fetchone()
    if row is None:
        return {}
    return json.loads(row[0])


def delete_preset(preset_id: int) -> None:
    """Delete a preset by id."""
    init_presets()
    with _connect() as conn:
        conn.execute("DELETE FROM presets WHERE id = ?", (preset_id,))
