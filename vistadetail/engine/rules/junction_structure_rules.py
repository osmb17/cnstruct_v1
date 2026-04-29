"""
Rule functions for Junction Structure template (v3.0).

Caltrans CIP rectangular junction box connecting two circular pipes.

Marks produced:
  JT1 — Top slab transverse bars   (#6 @ 6", across Span, EF)
  JT2 — Top slab longitudinal bars (#6 @ 6", along Length, EF)
  JF1 — Floor transverse bars      (#6 @ 6", across Span, EF) — same dims as JT1
  JF2 — Floor longitudinal bars    (#6 @ 6", along Length, EF) — same dims as JT2
  JW1 — Long wall horizontal bars  (#6 @ 6", along Length, EF, 2 walls)
  JW2 — Long wall vertical bars    (#4 @ 12", up wall height, EF, 2 walls)
  JS1 — Short wall horizontal bars (#6 @ 6", across Span, EF, 2 walls)
  JS2 — Short wall vertical bars   (#4 @ 12", up wall height, EF, 2 walls)
  JA1 — Additional "a" bars at pipe openings (#6, 3 at D1 + 3 at D2)

Geometry reference:
  - span_ft   = inside clear dimension perpendicular to pipe flow
  - length_ft = inside clear dimension along pipe flow
  - hb_ft     = inside height (floor to top slab soffit), min 5'-6"
  - wall_thick_in = uniform wall/slab thickness T
  - Outside Span   = span_ft×12 + 2×T
  - Outside Length = length_ft×12 + 2×T
  - Cover = 2" throughout
"""

from __future__ import annotations

import math

from vistadetail.engine.hooks import hook_add
from vistadetail.engine.reasoning_logger import ReasoningLogger
from vistadetail.engine.schema import BarRow, Params, fmt_inches

_COVER = 2.0


def rule_junction_top_slab_trans(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Top slab transverse bars — #6 @ 6", running across the Span direction.
    Bar length spans the full outside span minus cover each end.
    Qty spaced at 6" o/c along the Length.
    """
    outside_span_in = p.span_ft * 12 + 2 * p.wall_thick_in
    bar_len_in      = outside_span_in - 2 * _COVER
    qty             = math.floor((p.length_ft * 12) / 6.0) + 1

    log.step(
        f"Top slab trans: outside span = {outside_span_in:.0f} in  "
        f"bar = {bar_len_in:.1f} in = {fmt_inches(bar_len_in)}",
        source="JunctionRules",
    )
    log.step(f"Qty = floor({p.length_ft*12:.0f}/6) + 1 = {qty}", source="JunctionRules")
    log.result("JT1", f"#6 × {qty} @ {fmt_inches(bar_len_in)}", source="JunctionRules")

    return [BarRow(
        mark="JT1", size="#6", qty=qty, length_in=bar_len_in,
        shape="Str", notes="Top slab transverse EF",
        source_rule="rule_junction_top_slab_trans",
    )]


def rule_junction_top_slab_long(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Top slab longitudinal bars — #6 @ 6", running along the Length direction.
    Bar length spans the full outside length minus cover each end.
    Qty spaced at 6" o/c across the Span.
    """
    outside_len_in = p.length_ft * 12 + 2 * p.wall_thick_in
    bar_len_in     = outside_len_in - 2 * _COVER
    qty            = math.floor((p.span_ft * 12) / 6.0) + 1

    log.step(
        f"Top slab long: outside length = {outside_len_in:.0f} in  "
        f"bar = {bar_len_in:.1f} in = {fmt_inches(bar_len_in)}",
        source="JunctionRules",
    )
    log.step(f"Qty = floor({p.span_ft*12:.0f}/6) + 1 = {qty}", source="JunctionRules")
    log.result("JT2", f"#6 × {qty} @ {fmt_inches(bar_len_in)}", source="JunctionRules")

    return [BarRow(
        mark="JT2", size="#6", qty=qty, length_in=bar_len_in,
        shape="Str", notes="Top slab longitudinal EF",
        source_rule="rule_junction_top_slab_long",
    )]


def rule_junction_floor_trans(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Floor transverse bars — #6 @ 6", same dimensions as top slab transverse.
    """
    outside_span_in = p.span_ft * 12 + 2 * p.wall_thick_in
    bar_len_in      = outside_span_in - 2 * _COVER
    qty             = math.floor((p.length_ft * 12) / 6.0) + 1

    log.step(
        f"Floor trans: outside span = {outside_span_in:.0f} in  "
        f"bar = {bar_len_in:.1f} in = {fmt_inches(bar_len_in)}",
        source="JunctionRules",
    )
    log.step(f"Qty = floor({p.length_ft*12:.0f}/6) + 1 = {qty}", source="JunctionRules")
    log.result("JF1", f"#6 × {qty} @ {fmt_inches(bar_len_in)}", source="JunctionRules")

    return [BarRow(
        mark="JF1", size="#6", qty=qty, length_in=bar_len_in,
        shape="Str", notes="Floor transverse EF",
        source_rule="rule_junction_floor_trans",
    )]


def rule_junction_floor_long(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Floor longitudinal bars — #6 @ 6", same dimensions as top slab longitudinal.
    """
    outside_len_in = p.length_ft * 12 + 2 * p.wall_thick_in
    bar_len_in     = outside_len_in - 2 * _COVER
    qty            = math.floor((p.span_ft * 12) / 6.0) + 1

    log.step(
        f"Floor long: outside length = {outside_len_in:.0f} in  "
        f"bar = {bar_len_in:.1f} in = {fmt_inches(bar_len_in)}",
        source="JunctionRules",
    )
    log.step(f"Qty = floor({p.span_ft*12:.0f}/6) + 1 = {qty}", source="JunctionRules")
    log.result("JF2", f"#6 × {qty} @ {fmt_inches(bar_len_in)}", source="JunctionRules")

    return [BarRow(
        mark="JF2", size="#6", qty=qty, length_in=bar_len_in,
        shape="Str", notes="Floor longitudinal EF",
        source_rule="rule_junction_floor_long",
    )]


def rule_junction_long_wall_horiz(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Horizontal bars in the two long walls — #6 @ 6", EF.
    Bars run the full outside length of the structure minus cover each end.
    Qty = rows spaced at 6" up the wall height, × 2 faces × 2 long walls.
    """
    outside_len_in = p.length_ft * 12 + 2 * p.wall_thick_in
    bar_len_in     = outside_len_in - 2 * _COVER
    usable_h_in    = p.hb_ft * 12 - 2 * _COVER
    qty_per_face   = math.floor(usable_h_in / 6.0) + 1
    qty            = qty_per_face * 2 * 2   # 2 faces × 2 long walls

    log.step(
        f"Long wall horiz: outside length = {outside_len_in:.0f} in  "
        f"bar = {bar_len_in:.1f} in = {fmt_inches(bar_len_in)}",
        source="JunctionRules",
    )
    log.step(
        f"Qty = {qty_per_face} rows/face × 2 faces × 2 walls = {qty}",
        source="JunctionRules",
    )
    log.result("JW1", f"#6 × {qty} @ {fmt_inches(bar_len_in)}", source="JunctionRules")

    return [BarRow(
        mark="JW1", size="#6", qty=qty, length_in=bar_len_in,
        shape="Str", notes="Long wall horiz EF (2 walls)",
        source_rule="rule_junction_long_wall_horiz",
    )]


def rule_junction_long_wall_vert(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Vertical bars in the two long walls — #4 @ 12", EF.
    Bar length = HB + 90-deg hook at base + 6" stub at top.
    """
    usable_len_in = p.length_ft * 12 - 2 * _COVER
    qty_per_face  = math.floor(usable_len_in / 12.0) + 1
    qty           = qty_per_face * 2 * 2   # 2 faces × 2 long walls
    bot_hook_in   = hook_add("std_90", "#4")
    bar_len_in    = p.hb_ft * 12 + bot_hook_in + 6.0

    log.step(
        f"Long wall vert: usable length = {usable_len_in:.1f} in  "
        f"→ {qty_per_face} cols/face × 2 faces × 2 walls = {qty}",
        source="JunctionRules",
    )
    log.step(
        f"Bar length = {p.hb_ft*12:.0f} + {bot_hook_in} hook + 6 stub "
        f"= {bar_len_in:.1f} in = {fmt_inches(bar_len_in)}",
        source="JunctionRules",
    )
    log.result("JW2", f"#4 × {qty} @ {fmt_inches(bar_len_in)}", source="JunctionRules")

    return [BarRow(
        mark="JW2", size="#4", qty=qty, length_in=bar_len_in,
        shape="L", leg_a_in=p.hb_ft * 12 + 6.0, leg_b_in=bot_hook_in,
        notes="Long wall vert EF (2 walls)",
        source_rule="rule_junction_long_wall_vert",
    )]


def rule_junction_short_wall_horiz(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Horizontal bars in the two short walls (pipe end walls) — #6 @ 6", EF.
    Short walls fit between the long walls — bar length = inside span minus cover.
    """
    bar_len_in   = p.span_ft * 12 - 2 * _COVER
    usable_h_in  = p.hb_ft * 12 - 2 * _COVER
    qty_per_face = math.floor(usable_h_in / 6.0) + 1
    qty          = qty_per_face * 2 * 2   # 2 faces × 2 short walls

    log.step(
        f"Short wall horiz: bar = {p.span_ft*12:.0f} − 2×{_COVER:.0f} "
        f"= {bar_len_in:.1f} in = {fmt_inches(bar_len_in)}",
        source="JunctionRules",
    )
    log.step(f"Qty = {qty_per_face} × 2 faces × 2 walls = {qty}", source="JunctionRules")
    log.result("JS1", f"#6 × {qty} @ {fmt_inches(bar_len_in)}", source="JunctionRules")

    return [BarRow(
        mark="JS1", size="#6", qty=qty, length_in=bar_len_in,
        shape="Str", notes="Short wall horiz EF (2 walls, pipe end)",
        source_rule="rule_junction_short_wall_horiz",
    )]


def rule_junction_short_wall_vert(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Vertical bars in the two short walls — #4 @ 12", EF.
    """
    usable_span_in = p.span_ft * 12 - 2 * _COVER
    qty_per_face   = math.floor(usable_span_in / 12.0) + 1
    qty            = qty_per_face * 2 * 2   # 2 faces × 2 short walls
    bot_hook_in    = hook_add("std_90", "#4")
    bar_len_in     = p.hb_ft * 12 + bot_hook_in + 6.0

    log.step(
        f"Short wall vert: usable span = {usable_span_in:.1f} in  "
        f"→ {qty_per_face} cols/face × 2 faces × 2 walls = {qty}",
        source="JunctionRules",
    )
    log.result("JS2", f"#4 × {qty} @ {fmt_inches(bar_len_in)}", source="JunctionRules")

    return [BarRow(
        mark="JS2", size="#4", qty=qty, length_in=bar_len_in,
        shape="L", leg_a_in=p.hb_ft * 12 + 6.0, leg_b_in=bot_hook_in,
        notes="Short wall vert EF (2 walls, pipe end)",
        source_rule="rule_junction_short_wall_vert",
    )]


def rule_junction_a_bars(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Additional "a" bars at pipe openings — #6, 3 bars per opening (Tot 3 each).

    These transverse bars run the full outside span and are concentrated alongside
    the circular cutout to compensate for interrupted slab bars at each pipe entry.
    3 at D1 (inlet) + 3 at D2 (outlet) = 6 total.
    """
    outside_span_in = p.span_ft * 12 + 2 * p.wall_thick_in
    bar_len_in      = outside_span_in - 2 * _COVER
    qty             = 6   # 3 at D1 + 3 at D2

    log.step(
        f"'a' bars: outside span = {outside_span_in:.0f} in  "
        f"bar = {bar_len_in:.1f} in = {fmt_inches(bar_len_in)}",
        source="JunctionRules",
    )
    log.step(
        f"Qty = 3 at D1 ({p.d1_in}\") + 3 at D2 ({p.d2_in}\") = {qty}",
        source="JunctionRules",
    )
    log.result("JA1", f"#6 × {qty} @ {fmt_inches(bar_len_in)}", source="JunctionRules")

    return [BarRow(
        mark="JA1", size="#6", qty=qty, length_in=bar_len_in,
        shape="Str",
        notes=f"Addl 'a' bars at pipe openings — 3 at D1 ({p.d1_in}\") + 3 at D2 ({p.d2_in}\")",
        source_rule="rule_junction_a_bars",
    )]


def rule_validate_junction(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """Validate junction structure geometry."""
    d1 = int(p.d1_in)
    d2 = int(p.d2_in)
    d_max = max(d1, d2)

    if p.hb_ft < 5.5:
        log.warn(
            f"HB = {fmt_inches(p.hb_ft * 12)} is below the 5'-6\" minimum",
            detail="Caltrans minimum junction structure height for maintenance access",
        )
    if d_max / 12.0 > p.span_ft - 2.0:
        log.warn(
            f"Largest pipe ({d_max}\") may be too wide for inside span "
            f"({p.span_ft:.2f} ft — recommend span ≥ {d_max/12.0 + 2.0:.1f} ft)",
            detail="Allow min 1'-0\" clearance each side between pipe OD and wall",
        )
    if d_max / 12.0 > p.hb_ft - 2 * p.wall_thick_in / 12.0 - 1.0:
        log.warn(
            f"Largest pipe ({d_max}\") may not fit within HB = {fmt_inches(p.hb_ft*12)} "
            f"after accounting for top/bottom slab",
            detail="Verify crown and invert clearances",
        )
    return []
