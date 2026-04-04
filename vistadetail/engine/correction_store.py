"""
Features A + C: Correction Learning Loop + Template Confidence Scores.

Uses a local SQLite database (vistadetail.db) to track:
  - every Generate run (template name, params, generated bars)
  - every detailer correction (original row vs. final row)
  - per-template acceptance rate for the confidence display on Dashboard

Schema:
  runs(id, ts, template_name, template_version, params_json, bars_json)
  corrections(id, run_id, mark, original_json, corrected_json, ts)
  ── view: template_confidence (template_name, uses, corrections, acceptance_pct)

Usage:
    store = CorrectionStore()
    run_id = store.log_run("Inlet – 9in Wall", "2.1", params_dict, bars)
    store.log_correction(run_id, "H1", original_bar, corrected_bar)
    stats = store.get_confidence("Inlet – 9in Wall")
"""

from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

from vistadetail.engine.schema import BarRow

_DEFAULT_DB = os.path.join(
    os.path.dirname(__file__), "..", "..", "rebar_generator.db"
)


# ---------------------------------------------------------------------------
# Confidence summary returned to Dashboard
# ---------------------------------------------------------------------------

@dataclass
class TemplateConfidence:
    template_name: str
    uses: int
    corrections: int          # runs where ≥1 correction was made
    accepted_runs: int        # runs with zero corrections
    acceptance_pct: float     # accepted_runs / uses * 100


# ---------------------------------------------------------------------------
# Main store class
# ---------------------------------------------------------------------------

class CorrectionStore:
    """
    Lightweight SQLite persistence for correction learning + confidence scores.

    Thread-safe for single-process use (SQLite WAL mode).
    """

    def __init__(self, db_path: str = _DEFAULT_DB):
        self.db_path = os.path.abspath(db_path)
        self._init_db()

    # ── Public API ──────────────────────────────────────────────────────────

    def log_run(
        self,
        template_name: str,
        template_version: str,
        params: dict,
        bars: list[BarRow],
    ) -> int:
        """
        Record a Generate run. Returns the run_id for subsequent correction logging.
        """
        ts = datetime.utcnow().isoformat()
        bars_json = json.dumps([_bar_to_dict(b) for b in bars])
        params_json = json.dumps(params)

        with self._conn() as conn:
            cur = conn.execute(
                """INSERT INTO runs (ts, template_name, template_version, params_json, bars_json)
                   VALUES (?, ?, ?, ?, ?)""",
                (ts, template_name, template_version, params_json, bars_json),
            )
            return cur.lastrowid

    def log_correction(
        self,
        run_id: int,
        mark: str,
        original: BarRow,
        corrected: BarRow,
    ) -> None:
        """
        Record a detailer correction for one bar mark.
        Capture original generated row vs. final edited row.
        """
        ts = datetime.utcnow().isoformat()
        with self._conn() as conn:
            conn.execute(
                """INSERT INTO corrections (run_id, mark, original_json, corrected_json, ts)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    run_id,
                    mark,
                    json.dumps(_bar_to_dict(original)),
                    json.dumps(_bar_to_dict(corrected)),
                    ts,
                ),
            )

    def log_corrections_from_diff(
        self,
        run_id: int,
        generated: list[BarRow],
        final: list[BarRow],
    ) -> int:
        """
        Diff two bar lists by mark and record all changed rows.
        Returns number of corrections logged.
        """
        gen_map = {b.mark: b for b in generated}
        fin_map = {b.mark: b for b in final}

        count = 0
        all_marks = set(gen_map) | set(fin_map)
        for mark in all_marks:
            orig = gen_map.get(mark)
            corr = fin_map.get(mark)
            if orig is None or corr is None:
                # Added or deleted row — still a correction
                placeholder = corr or orig
                self.log_correction(run_id, mark, orig or placeholder, corr or placeholder)
                count += 1
            elif _bar_differs(orig, corr):
                self.log_correction(run_id, mark, orig, corr)
                count += 1
        return count

    def get_confidence(self, template_name: str) -> TemplateConfidence:
        """Return acceptance stats for one template."""
        with self._conn() as conn:
            row = conn.execute(
                """SELECT uses, corrected_runs, accepted_runs, acceptance_pct
                   FROM template_confidence
                   WHERE template_name = ?""",
                (template_name,),
            ).fetchone()

        if row is None:
            return TemplateConfidence(template_name, 0, 0, 0, 0.0)
        return TemplateConfidence(
            template_name=template_name,
            uses=row[0],
            corrections=row[1],
            accepted_runs=row[2],
            acceptance_pct=row[3],
        )

    def get_all_confidence(self) -> list[TemplateConfidence]:
        """Return acceptance stats for all templates that have been run."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT template_name, uses, corrected_runs, accepted_runs, acceptance_pct "
                "FROM template_confidence ORDER BY uses DESC"
            ).fetchall()
        return [
            TemplateConfidence(r[0], r[1], r[2], r[3], r[4]) for r in rows
        ]

    def get_adjustments(
        self,
        template_name: str,
        min_count: int = 3,
    ) -> list[dict]:
        """
        Feature A: Compute learned adjustments from correction history.

        For each mark that has been corrected >= min_count times with a
        *consistent direction* (all +ve or all -ve), return a suggested offset.

        Only qty and length_in adjustments are returned — never bar size changes,
        which require human review and a rule code edit.

        Returns:
            list of dicts: {mark, field, delta, count}
              - field:  'qty' or 'length_in'
              - delta:  signed offset to add (already averaged + rounded)
              - count:  number of corrections this is based on
        """
        with self._conn() as conn:
            rows = conn.execute(
                """SELECT c.mark, c.original_json, c.corrected_json
                   FROM corrections c
                   JOIN runs r ON r.id = c.run_id
                   WHERE r.template_name = ?
                   ORDER BY c.mark, c.ts""",
                (template_name,),
            ).fetchall()

        if not rows:
            return []

        # Group by mark
        from collections import defaultdict
        by_mark: dict[str, list] = defaultdict(list)
        for mark, orig_json, corr_json in rows:
            by_mark[mark].append((json.loads(orig_json), json.loads(corr_json)))

        adjustments = []
        for mark, pairs in by_mark.items():
            if len(pairs) < min_count:
                continue

            # ── qty delta ────────────────────────────────────────────────
            qty_deltas = [
                c["qty"] - o["qty"]
                for o, c in pairs
                if "qty" in o and "qty" in c and o["qty"] != c["qty"]
            ]
            if len(qty_deltas) >= min_count:
                if all(d > 0 for d in qty_deltas) or all(d < 0 for d in qty_deltas):
                    avg = sum(qty_deltas) / len(qty_deltas)
                    adjustments.append({
                        "mark": mark, "field": "qty",
                        "delta": round(avg),  # integer qty
                        "count": len(qty_deltas),
                    })

            # ── length delta ─────────────────────────────────────────────
            len_deltas = [
                c["length_in"] - o["length_in"]
                for o, c in pairs
                if "length_in" in o and "length_in" in c
                and abs(c["length_in"] - o["length_in"]) > 0.1   # ignore noise < 1/8"
            ]
            if len(len_deltas) >= min_count:
                if all(d > 0 for d in len_deltas) or all(d < 0 for d in len_deltas):
                    avg = sum(len_deltas) / len(len_deltas)
                    # Round to nearest 1/4 inch to avoid float noise
                    rounded = round(avg * 4) / 4
                    adjustments.append({
                        "mark": mark, "field": "length_in",
                        "delta": rounded,
                        "count": len(len_deltas),
                    })

        return adjustments

    def get_pending_rule_suggestions(self, min_corrections: int = 5) -> list[dict]:
        """
        Feature A: Surface templates with repeated corrections on the same mark.
        Returns candidates for rule review.
        """
        with self._conn() as conn:
            rows = conn.execute(
                """SELECT r.template_name, c.mark, COUNT(*) as n,
                          GROUP_CONCAT(c.corrected_json, '||') as samples
                   FROM corrections c
                   JOIN runs r ON r.id = c.run_id
                   GROUP BY r.template_name, c.mark
                   HAVING n >= ?
                   ORDER BY n DESC""",
                (min_corrections,),
            ).fetchall()
        return [
            {"template": r[0], "mark": r[1], "count": r[2], "samples": r[3][:500]}
            for r in rows
        ]

    # ── Internal ────────────────────────────────────────────────────────────

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS runs (
                    id               INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts               TEXT NOT NULL,
                    template_name    TEXT NOT NULL,
                    template_version TEXT NOT NULL,
                    params_json      TEXT NOT NULL,
                    bars_json        TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS corrections (
                    id             INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id         INTEGER NOT NULL REFERENCES runs(id),
                    mark           TEXT NOT NULL,
                    original_json  TEXT NOT NULL,
                    corrected_json TEXT NOT NULL,
                    ts             TEXT NOT NULL
                );

                CREATE VIEW IF NOT EXISTS template_confidence AS
                SELECT
                    r.template_name,
                    COUNT(DISTINCT r.id)                                          AS uses,
                    COUNT(DISTINCT c.run_id)                                      AS corrected_runs,
                    COUNT(DISTINCT r.id) - COUNT(DISTINCT c.run_id)               AS accepted_runs,
                    ROUND(
                        100.0 * (COUNT(DISTINCT r.id) - COUNT(DISTINCT c.run_id))
                        / MAX(COUNT(DISTINCT r.id), 1),
                        1
                    )                                                             AS acceptance_pct
                FROM runs r
                LEFT JOIN corrections c ON c.run_id = r.id
                GROUP BY r.template_name;
            """)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _bar_to_dict(bar: BarRow) -> dict:
    return {
        "mark":      bar.mark,
        "size":      bar.size,
        "qty":       bar.qty,
        "length_in": bar.length_in,
        "shape":     bar.shape,
        "leg_a_in":  bar.leg_a_in,
        "leg_b_in":  bar.leg_b_in,
        "leg_c_in":  bar.leg_c_in,
        "notes":     bar.notes,
        "ref":       bar.ref,
    }


def _bar_differs(a: BarRow, b: BarRow) -> bool:
    """
    Return True if any structural field differs.
    Notes are intentionally excluded — they are informational labels,
    not estimator corrections. Only changes to size, qty, length, or shape
    represent a real correction worth learning from.
    """
    return (
        a.size != b.size
        or a.qty != b.qty
        or abs(a.length_in - b.length_in) > 0.1
        or a.shape != b.shape
    )
