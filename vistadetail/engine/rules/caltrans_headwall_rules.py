"""
Rule functions for Caltrans Pipe Culvert Headwall (D89A/B).

All dimensions and reinforcement from Caltrans 2025 Standard Plans D89A/B
lookup tables by pipe diameter.

Design basis:
  f'c = 3,600 psi, fy = 60,000 psi
  Earth density = 120 pcf
  Equivalent fluid pressure = 36 pcf
  Cover: 2" stem, 3" footing

Marks:
  HW1 -- c-bars: vertical face bars (bundled #4, each face)
  HW2 -- d-bars: horizontal distribution bars (#4 @ 12, each face)
  HW3 -- top-of-wall bars (#5 Tot 3 along top)
  HW4 -- footing transverse (#4 @ 12)
  HW5 -- footing longitudinal (#5 Tot 4)
  HW6 -- pipe hoop reinforcement (2-#6 around pipe opening)
"""

from __future__ import annotations

import math

from vistadetail.engine.reasoning_logger import ReasoningLogger
from vistadetail.engine.schema import BarRow, Params, fmt_inches


# ---------------------------------------------------------------------------
# Caltrans D89 Lookup Table (Circular Pipe Headwalls)
# ---------------------------------------------------------------------------
# Key = pipe diameter (inches)
# Values: min_H (design height), T (wall thickness), F (footing depth),
#         W (footing width), B (footing back), C (footing front)
# All dimensions in inches.

_D89_TABLE = {
    12: {"H": 47, "T": 8,  "F": 8,  "W": 42,  "B": 24, "C": 18},
    15: {"H": 50, "T": 8,  "F": 8,  "W": 44,  "B": 26, "C": 18},
    18: {"H": 53, "T": 8,  "F": 8,  "W": 46,  "B": 28, "C": 18},
    21: {"H": 56, "T": 8,  "F": 8,  "W": 50,  "B": 30, "C": 20},
    24: {"H": 59, "T": 8,  "F": 8,  "W": 52,  "B": 32, "C": 20},
    27: {"H": 62, "T": 8,  "F": 8,  "W": 56,  "B": 34, "C": 22},
    30: {"H": 65, "T": 8,  "F": 8,  "W": 60,  "B": 36, "C": 24},
    33: {"H": 68, "T": 8,  "F": 8,  "W": 64,  "B": 38, "C": 26},
    36: {"H": 71, "T": 8,  "F": 8,  "W": 68,  "B": 40, "C": 28},
    39: {"H": 74, "T": 8,  "F": 8,  "W": 72,  "B": 42, "C": 30},
    42: {"H": 77, "T": 8,  "F": 8,  "W": 76,  "B": 44, "C": 32},
    45: {"H": 80, "T": 8,  "F": 8,  "W": 80,  "B": 46, "C": 34},
    48: {"H": 83, "T": 8,  "F": 8,  "W": 84,  "B": 48, "C": 36},
    51: {"H": 86, "T": 8,  "F": 8,  "W": 88,  "B": 50, "C": 38},
    54: {"H": 89, "T": 8,  "F": 8,  "W": 92,  "B": 52, "C": 40},
}

_STEM_COVER = 2.0
_FTG_COVER = 3.0


def _snap_dia(d: float) -> int:
    """Snap pipe diameter to nearest D89 table row (3-inch increments)."""
    d_int = round(d)
    # Snap to nearest 3-inch increment
    snapped = round(d_int / 3) * 3
    return max(12, min(54, snapped))


def _get_row(pipe_dia: float) -> dict:
    """Get D89 table row for given pipe diameter."""
    d = _snap_dia(pipe_dia)
    return _D89_TABLE.get(d, _D89_TABLE[36])


# ---------------------------------------------------------------------------
# HW1 -- c-bars: vertical face bars (bundled #4)
# ---------------------------------------------------------------------------

def rule_ct_hw_vert_bars(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """Vertical face bars per D89. Bundled #4 bars each face."""
    row = _get_row(p.pipe_dia_in)
    dia = _snap_dia(p.pipe_dia_in)
    wall_width_in = p.wall_width_ft * 12.0

    design_h = row["H"]
    T = row["T"]
    F = row["F"]

    # #4 bars @ 12" each face per D89 typical section
    spacing = 12
    qty_per_face = math.floor((wall_width_in - 2 * _STEM_COVER) / spacing) + 1
    qty = qty_per_face * 2  # each face

    # Bar length: design H + extend 1'-0" above + embed into footing
    bar_len = design_h + 12.0 + (F - _FTG_COVER)

    log.step(
        f"D89 pipe {dia}\": design H = {fmt_inches(design_h)}, T = {T}\"",
        source="CaltransHeadwallRules",
    )
    log.step(
        f"HW1: #4 @ {spacing}\" EF, {qty_per_face}/face x 2 = {qty} @ {fmt_inches(bar_len)}",
        source="CaltransHeadwallRules",
    )
    log.result("HW1", f"#4 x {qty} @ {fmt_inches(bar_len)}",
               source="CaltransHeadwallRules")

    return [BarRow(
        mark="HW1", size="#4", qty=qty, length_in=bar_len,
        shape="Str", notes=f"c-bars vert EF @ {spacing}\" oc (D89)",
        source_rule="rule_ct_hw_vert_bars",
    )]


# ---------------------------------------------------------------------------
# HW2 -- d-bars: horizontal distribution bars
# ---------------------------------------------------------------------------

def rule_ct_hw_horiz_bars(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """Horizontal distribution bars, #4 @ 12 each face per D89."""
    row = _get_row(p.pipe_dia_in)
    wall_width_in = p.wall_width_ft * 12.0
    design_h = row["H"]

    spacing = 12
    qty_per_face = math.floor((design_h - 2 * _STEM_COVER) / spacing) + 1
    qty = qty_per_face * 2  # each face

    bar_len = wall_width_in - 2 * _STEM_COVER

    log.step(
        f"HW2: #4 @ {spacing}\" horiz EF, {qty_per_face}/face x 2 = {qty} @ {fmt_inches(bar_len)}",
        source="CaltransHeadwallRules",
    )
    log.result("HW2", f"#4 x {qty} @ {fmt_inches(bar_len)}",
               source="CaltransHeadwallRules")

    return [BarRow(
        mark="HW2", size="#4", qty=qty, length_in=bar_len,
        shape="Str", notes=f"d-bars horiz EF @ {spacing}\" oc (D89)",
        source_rule="rule_ct_hw_horiz_bars",
    )]


# ---------------------------------------------------------------------------
# HW3 -- top-of-wall bars (#5 Tot 3 along top per D89)
# ---------------------------------------------------------------------------

def rule_ct_hw_top_bars(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """Top-of-wall longitudinal bars: #5 Tot 3 per D89."""
    wall_width_in = p.wall_width_ft * 12.0
    bar_len = wall_width_in - 2 * _STEM_COVER

    log.step(
        f"HW3: #5 Tot 3 along top of wall @ {fmt_inches(bar_len)}",
        source="CaltransHeadwallRules",
    )
    log.result("HW3", f"#5 x 3 @ {fmt_inches(bar_len)}",
               source="CaltransHeadwallRules")

    return [BarRow(
        mark="HW3", size="#5", qty=3, length_in=bar_len,
        shape="Str", notes="top-of-wall bars #5 Tot 3 (D89)",
        source_rule="rule_ct_hw_top_bars",
    )]


# ---------------------------------------------------------------------------
# HW4/HW5 -- Footing bars
# ---------------------------------------------------------------------------

def rule_ct_hw_footing(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """Footing reinforcement from D89 table."""
    row = _get_row(p.pipe_dia_in)
    wall_width_in = p.wall_width_ft * 12.0
    W = row["W"]

    bars = []

    # HW4: Footing transverse #4 @ 12
    trans_spacing = 12
    trans_qty = math.floor((wall_width_in - 2 * _FTG_COVER) / trans_spacing) + 1
    trans_len = W - 2 * _FTG_COVER

    log.step(
        f"HW4: footing transverse #4 @ {trans_spacing}\", "
        f"W = {fmt_inches(W)}, {trans_qty} bars @ {fmt_inches(trans_len)}",
        source="CaltransHeadwallRules",
    )
    log.result("HW4", f"#4 x {trans_qty} @ {fmt_inches(trans_len)}",
               source="CaltransHeadwallRules")

    bars.append(BarRow(
        mark="HW4", size="#4", qty=trans_qty, length_in=trans_len,
        shape="Str", notes=f"footing transverse @ {trans_spacing}\" oc (D89)",
        source_rule="rule_ct_hw_footing",
    ))

    # HW5: Footing longitudinal #5 Tot 4
    long_len = wall_width_in - 2 * _FTG_COVER

    log.step(f"HW5: #5 Tot 4 footing longitudinal @ {fmt_inches(long_len)}",
             source="CaltransHeadwallRules")
    log.result("HW5", f"#5 x 4 @ {fmt_inches(long_len)}",
               source="CaltransHeadwallRules")

    bars.append(BarRow(
        mark="HW5", size="#5", qty=4, length_in=long_len,
        shape="Str", notes="footing longitudinal #5 Tot 4 (D89)",
        source_rule="rule_ct_hw_footing",
    ))

    return bars


# ---------------------------------------------------------------------------
# HW6 -- Pipe hoop reinforcement
# ---------------------------------------------------------------------------

def rule_ct_hw_pipe_hoops(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """Pipe hoop bars: 2-#6 around pipe opening per D89."""
    pipe_dia = p.pipe_dia_in
    pipe_circ = math.pi * pipe_dia
    # Ring stock length = circumference + lap splice (each free end gets 1 dev length)
    from vistadetail.engine.hooks import bar_diameter
    db = bar_diameter("#6")
    dev_len = 12 * db
    hoop_len = pipe_circ + 2 * dev_len

    log.step(
        f"HW6: 2-#6 pipe rings, circ = {pipe_circ:.0f}\" + 2x{dev_len:.0f}\" lap = {fmt_inches(hoop_len)}",
        source="CaltransHeadwallRules",
    )
    log.result("HW6", f"#6 x 2 @ {fmt_inches(hoop_len)}",
               source="CaltransHeadwallRules")

    return [BarRow(
        mark="HW6", size="#6", qty=2, length_in=hoop_len,
        shape="Rng", notes="pipe ring 2-#6 around opening (D89)",
        source_rule="rule_ct_hw_pipe_hoops",
    )]


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def rule_validate_ct_hw(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """Validate headwall inputs against D89 limits."""
    d = p.pipe_dia_in
    if d < 12:
        log.warn(f"Pipe diameter {d}\" < 12\" minimum per D89", source="CaltransHeadwallRules")
    if d > 54:
        log.warn(f"Pipe diameter {d}\" > 54\" -- exceeds D89 table", source="CaltransHeadwallRules")
    return []
