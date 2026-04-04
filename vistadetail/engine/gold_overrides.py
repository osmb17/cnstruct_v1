"""
Gold CSV Override System — Feature G.

Allows estimators to permanently override the computed barlist for any
template by placing a hand-edited CSV file in:

    vistadetail/overrides/<TemplateSlug>.csv

Where <TemplateSlug> is the template name with spaces replaced by underscores
and special characters stripped, e.g.:
    "Inlet – 9in Wall"  →  "Inlet_9in_Wall.csv"
    "Box Culvert"        →  "Box_Culvert.csv"

Override CSV format (matches BarList columns):
    Mark, Size, Qty, Length, Shape, Leg A, Leg B, Leg C, Notes, Ref, Review Flag

Rules:
  - If an override CSV exists for the active template, it REPLACES the
    computed barlist entirely. No merging — the CSV is the output.
  - The ReasoningLog will show a prominent notice that an override is active.
  - The override CSV must have a header row matching the column names above.
  - Missing columns default to empty string / 0.
  - To disable an override, delete or rename the CSV file.

Managing overrides from CLI:
    python3 -m vistadetail export-gold   # export current BarList as gold CSV
    python3 -m vistadetail clear-gold    # delete gold CSV for current template

The overrides directory is created automatically on first use.
"""

from __future__ import annotations

import csv
import os
import pathlib
import re

from vistadetail.engine.reasoning_logger import ReasoningLogger
from vistadetail.engine.schema import BarRow

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_OVERRIDES_DIR = pathlib.Path(__file__).resolve().parent.parent / "overrides"


def _slug(template_name: str) -> str:
    """Convert template name to a safe filename slug."""
    slug = re.sub(r"[^\w\s-]", "", template_name)   # strip special chars
    slug = re.sub(r"[\s\-]+", "_", slug.strip())     # spaces/dashes → _
    return slug


def override_path(template_name: str) -> pathlib.Path:
    """Return the expected gold CSV path for a given template name."""
    return _OVERRIDES_DIR / f"{_slug(template_name)}.csv"


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------

def load_gold_override(
    template_name: str,
    log: ReasoningLogger,
) -> list[BarRow] | None:
    """
    Return the gold-override barlist for `template_name`, or None if no
    override file exists.

    Writes a prominent notice to the ReasoningLog when an override is active.
    """
    path = override_path(template_name)
    if not path.exists():
        return None

    bars: list[BarRow] = []
    try:
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                bar = _row_to_barrow(row)
                if bar is not None:
                    bars.append(bar)
    except Exception as exc:
        log.warn(f"Gold override file found but could not be read: {exc}")
        log.warn(f"  Path: {path}")
        log.warn("Falling back to computed barlist.")
        return None

    log.section("⚠  GOLD OVERRIDE ACTIVE")
    log.step(f"Template '{template_name}' output replaced by: {path.name}")
    log.step(f"Override contains {len(bars)} bar rows.")
    log.step("To disable: delete the file from vistadetail/overrides/")
    log.blank()

    return bars


def _row_to_barrow(row: dict) -> BarRow | None:
    """Parse one CSV dict row into a BarRow. Returns None for blank rows."""
    mark = row.get("Mark", "").strip()
    if not mark:
        return None

    def _float(val: str, default: float = 0.0) -> float:
        try:
            return float(val.strip()) if val and val.strip() else default
        except ValueError:
            return default

    def _int(val: str, default: int = 0) -> int:
        try:
            return int(float(val.strip())) if val and val.strip() else default
        except ValueError:
            return default

    def _parse_length(val: str) -> float:
        """Parse a feet-inches string like 6'-9" or 81.0 → decimal inches."""
        if not val or not val.strip():
            return 0.0
        s = val.strip().replace('"', "")
        import re as _re
        m = _re.match(r"(\d+)'-(\d+)(?:\s+(\d+)/(\d+))?", s)
        if m:
            ft = int(m.group(1))
            inches = int(m.group(2))
            if m.group(3) and m.group(4):
                inches += int(m.group(3)) / int(m.group(4))
            return ft * 12.0 + inches
        try:
            return float(s)
        except ValueError:
            return 0.0

    leg_a_raw = row.get("Leg A", "").strip()
    leg_b_raw = row.get("Leg B", "").strip()
    leg_c_raw = row.get("Leg C", "").strip()

    return BarRow(
        mark=mark,
        size=row.get("Size", "").strip(),
        qty=_int(row.get("Qty", "0")),
        length_in=_parse_length(row.get("Length", "")),
        shape=row.get("Shape", "Str").strip() or "Str",
        leg_a_in=_parse_length(leg_a_raw) if leg_a_raw else None,
        leg_b_in=_parse_length(leg_b_raw) if leg_b_raw else None,
        leg_c_in=_parse_length(leg_c_raw) if leg_c_raw else None,
        notes=row.get("Notes", "").strip(),
        ref=row.get("Ref", "").strip(),
        review_flag=row.get("Review Flag", "").strip(),
        source_rule="gold_override",
    )


# ---------------------------------------------------------------------------
# Write (export current BarList as gold)
# ---------------------------------------------------------------------------

def save_gold_override(
    template_name: str,
    bars: list[BarRow],
) -> pathlib.Path:
    """
    Write the current bars list as a gold-override CSV.
    Creates the overrides directory if it doesn't exist.

    Returns the path of the written file.
    """
    _OVERRIDES_DIR.mkdir(parents=True, exist_ok=True)
    path = override_path(template_name)

    header = ["Mark", "Size", "Qty", "Length", "Shape",
              "Leg A", "Leg B", "Leg C", "Notes", "Ref", "Review Flag"]

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for bar in bars:
            writer.writerow([
                bar.mark,
                bar.size,
                bar.qty,
                bar.length_ft_in,
                bar.shape,
                bar.leg_a_ft_in,
                bar.leg_b_ft_in,
                bar.leg_c_ft_in,
                bar.notes,
                bar.ref,
                bar.review_flag,
            ])

    return path


def delete_gold_override(template_name: str) -> bool:
    """
    Delete the gold override CSV for the given template.
    Returns True if a file was deleted, False if none existed.
    """
    path = override_path(template_name)
    if path.exists():
        path.unlink()
        return True
    return False


def list_gold_overrides() -> list[dict]:
    """
    Return a list of all active gold overrides with their paths and row counts.
    """
    if not _OVERRIDES_DIR.exists():
        return []
    result = []
    for csv_path in sorted(_OVERRIDES_DIR.glob("*.csv")):
        try:
            with open(csv_path, newline="", encoding="utf-8") as f:
                rows = sum(1 for _ in csv.reader(f)) - 1  # subtract header
        except Exception:
            rows = -1
        result.append({
            "file": csv_path.name,
            "path": str(csv_path),
            "rows": rows,
        })
    return result
