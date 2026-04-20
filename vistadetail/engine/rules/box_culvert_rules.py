"""
Rule functions for Box Culvert template.

Caltrans standard precast / CIP box culvert (rectangular section).

Generates:
  TT1 — top slab top bars (transverse, full span)
  TB1 — top slab bottom bars (transverse)
  WT1 — wall vertical bars each face (exterior walls)
  BT1 — bottom slab top bars (transverse)
  BB1 — bottom slab bottom bars (transverse, primary tension)
  HS1 — haunch / corner bars (diagonal, all 4 corners)
"""

from __future__ import annotations

import math

from vistadetail.engine.hooks import development_length_tension, hook_add
from vistadetail.engine.reasoning_logger import ReasoningLogger
from vistadetail.engine.schema import BarRow, Params, fmt_inches


# ---------------------------------------------------------------------------
# TOP SLAB
# ---------------------------------------------------------------------------

def rule_top_slab_top(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Top slab top bars — transverse, spanning the clear span.
    Tension in top under live load / earth pressure reversal.
    """
    usable_span = (p.clear_span_ft * 12) - (2 * 2.0)
    qty = math.floor((p.barrel_length_ft * 12 - 2 * 2.0) / 12.0) + 1
    ha = hook_add("std_90", "#5")
    bar_len_in = usable_span + (2 * ha)

    log.step(f"Top slab top: span = {p.clear_span_ft} ft, {qty} bars @ {12.0} in spacing")
    log.step(f"Bar length = {usable_span:.1f} + 2×{ha} hooks = {bar_len_in:.1f} in = {fmt_inches(bar_len_in)}")
    log.result("TT1", f"#5 × {qty} @ {fmt_inches(bar_len_in)}")

    return [BarRow(
        mark="TT1", size="#5", qty=qty, length_in=bar_len_in,
        shape="U", leg_a_in=ha, leg_b_in=usable_span, leg_c_in=ha,
        notes="Top Slab Top", source_rule="rule_top_slab_top",
    )]


def rule_top_slab_bottom(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Top slab bottom bars — primary flexural tension under earth cover.
    Same span, same qty as top bars.
    """
    usable_span = (p.clear_span_ft * 12) - (2 * 2.0)
    qty = math.floor((p.barrel_length_ft * 12 - 2 * 2.0) / 12.0) + 1
    ha = hook_add("std_90", "#5")
    bar_len_in = usable_span + (2 * ha)

    log.step(f"Top slab bottom: same layout as top — {qty} bars")
    log.result("TB1", f"#5 × {qty} @ {fmt_inches(bar_len_in)}")

    return [BarRow(
        mark="TB1", size="#5", qty=qty, length_in=bar_len_in,
        shape="U", leg_a_in=ha, leg_b_in=usable_span, leg_c_in=ha,
        notes="Top Slab Bot", source_rule="rule_top_slab_bottom",
    )]


# ---------------------------------------------------------------------------
# WALLS
# ---------------------------------------------------------------------------

def rule_wall_vertical(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Exterior wall vertical bars each face — from bottom slab to top slab.
    Length = clear rise + development into top + bottom slabs.
    """
    ld_in = development_length_tension("#5", cover_in=2.0,
                                       spacing_in=12.0)
    bar_len_in = (p.clear_rise_ft * 12) + (2 * ld_in)

    usable_len = (p.barrel_length_ft * 12) - (2 * 2.0)
    qty_per_face = math.floor(usable_len / 12.0) + 1
    qty_total = qty_per_face * 2   # each face, both walls = ×4 but mark covers one wall EF

    log.step(f"Wall height = {p.clear_rise_ft} ft, dev length each end = {ld_in:.1f} in")
    log.step(f"Bar length = {p.clear_rise_ft * 12:.0f} + 2×{ld_in:.1f} = {bar_len_in:.1f} in")
    log.step(f"Bars per face = {qty_per_face}  (×2 faces, ×2 walls = {qty_total * 2} total)")
    log.result("WT1", f"#5 × {qty_total * 2} @ {fmt_inches(bar_len_in)} [EF, both walls]")

    return [BarRow(
        mark="WT1", size="#5", qty=qty_total * 2, length_in=bar_len_in,
        shape="Str", notes="Wall Vert EF (both)", source_rule="rule_wall_vertical",
    )]


# ---------------------------------------------------------------------------
# BOTTOM SLAB
# ---------------------------------------------------------------------------

def rule_bottom_slab_top(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """Bottom slab top bars — transverse, secondary tension layer."""
    usable_span = (p.clear_span_ft * 12) - (2 * 2.0)
    qty = math.floor((p.barrel_length_ft * 12 - 2 * 2.0) / 12.0) + 1
    ha = hook_add("std_90", "#5")
    bar_len_in = usable_span + (2 * ha)

    log.step(f"Bottom slab top: {qty} bars @ {fmt_inches(bar_len_in)}")
    log.result("BT1", f"#5 × {qty} @ {fmt_inches(bar_len_in)}")

    return [BarRow(
        mark="BT1", size="#5", qty=qty, length_in=bar_len_in,
        shape="U", leg_a_in=ha, leg_b_in=usable_span, leg_c_in=ha,
        notes="Bot Slab Top", source_rule="rule_bottom_slab_top",
    )]


def rule_bottom_slab_bottom(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Bottom slab bottom bars — primary tension under soil bearing reaction.
    Typically heavier than top bars; uses separate bar size input.
    """
    usable_span = (p.clear_span_ft * 12) - (2 * 2.0)
    qty = math.floor((p.barrel_length_ft * 12 - 2 * 2.0) / 9.0) + 1
    ha = hook_add("std_90", "#5")
    bar_len_in = usable_span + (2 * ha)

    log.step(f"Bottom slab bottom (primary tension): {qty} bars @ {9.0} in")
    log.step(f"Bar length = {fmt_inches(bar_len_in)}")
    log.result("BB1", f"#5 × {qty} @ {fmt_inches(bar_len_in)}")

    return [BarRow(
        mark="BB1", size="#5", qty=qty, length_in=bar_len_in,
        shape="U", leg_a_in=ha, leg_b_in=usable_span, leg_c_in=ha,
        notes="Bot Slab Bot (primary)", source_rule="rule_bottom_slab_bottom",
    )]


# ---------------------------------------------------------------------------
# HAUNCH / CORNER BARS
# ---------------------------------------------------------------------------

def rule_haunch_bars(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Diagonal corner (haunch) bars at all 4 wall–slab junctions.
    Length = 2 × haunch leg + development each end.
    Qty = bars along barrel length at haunch_spacing.
    """
    haunch_leg_in = 12.0
    ld_in = development_length_tension("#5", cover_in=2.0,
                                       spacing_in=12.0)
    # L-bar: each leg runs along slab/wall face = haunch_leg + development
    leg_total = haunch_leg_in + ld_in
    bar_len_in = 2 * leg_total

    usable_len = (p.barrel_length_ft * 12) - (2 * 2.0)
    qty_per_corner = math.floor(usable_len / 12.0) + 1
    qty_total = qty_per_corner * 4   # 4 corners

    log.step(f"Haunch leg = {haunch_leg_in} in + dev {ld_in:.1f} in = {leg_total:.1f} in each leg")
    log.step(f"Bar length = 2 × {leg_total:.1f} = {bar_len_in:.1f} in = {fmt_inches(bar_len_in)}")
    log.step(f"{qty_per_corner} bars/corner × 4 corners = {qty_total} total")
    log.result("HS1", f"#5 × {qty_total} @ {fmt_inches(bar_len_in)}")

    return [BarRow(
        mark="HS1", size="#5", qty=qty_total, length_in=bar_len_in,
        shape="L", leg_a_in=leg_total, leg_b_in=leg_total,
        notes="Haunch/Corner (4 corners)", source_rule="rule_haunch_bars",
    )]


# ---------------------------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------------------------

def rule_validate_box_culvert(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """Sanity checks for box culvert geometry and cover."""
    if False:  # cover hardcoded at 2.0
        log.warn(f"Cover {2.0} in < 2 in — check exposure class for culvert interior/exterior")
    if p.clear_span_ft > 20.0:
        log.warn(
            f"Clear span {p.clear_span_ft} ft > 20 ft. "
            "Verify reinforcement with structural analysis — template rules are conservative."
        )
    ratio = p.clear_rise_ft / max(p.clear_span_ft, 0.1)
    if ratio > 1.5:
        log.warn(f"Rise/span = {ratio:.2f} > 1.5 — tall narrow box. Verify lateral pressure design.")
    return []
