"""
Rule functions for Wing Wall template.

Tapered wing wall: varies from full height at headwall to zero at tip.
Uses average height for bar quantity calculation (conservative).

Generates:
  WH1 — wing face horizontal bars (each face)
  WV1 — wing face vertical bars (each face, varying length)
  WC1 — wing corner bars at headwall connection
"""

from __future__ import annotations

import math

from vistadetail.engine.hooks import hook_add
from vistadetail.engine.reasoning_logger import ReasoningLogger
from vistadetail.engine.schema import BarRow, Params, fmt_inches


def rule_wing_horiz(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Horizontal bars each face, full wing length.
    Qty based on the taller (headwall) end height.
    """
    usable_h = (p.hw_height_ft * 12) - (2 * 2.0)
    qty_per_face = math.floor(usable_h / 12.0) + 1
    qty_total = qty_per_face * 2

    hook_add_in = hook_add("std_90", "#4")
    bar_len_in = (p.wing_length_ft * 12) + hook_add_in   # one hooked end at HW

    log.step(f"HW height = {p.hw_height_ft} ft → usable = {usable_h:.1f} in → {qty_per_face} bars/face")
    log.step(f"Wing length = {p.wing_length_ft} ft + hook = {bar_len_in:.1f} in")
    log.result("WH1", f"#4 × {qty_total} @ {fmt_inches(bar_len_in)} [EF]")

    return [BarRow(
        mark="WH1", size="#4", qty=qty_total, length_in=bar_len_in,
        shape="L", leg_a_in=p.wing_length_ft * 12, leg_b_in=hook_add_in,
        notes="Wing Horiz EF", source_rule="rule_wing_horiz",
    )]


def rule_wing_vert(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Vertical bars each face.
    Height tapers from hw_height at heel to tip_height at toe.
    Use maximum (conservative) bar length = hw_height + hooks.
    """
    usable_len = (p.wing_length_ft * 12) - (2 * 2.0)
    qty_per_face = math.floor(usable_len / 12.0) + 1
    qty_total = qty_per_face * 2

    bot_hook = hook_add("std_90", "#4")
    bar_len_in = (p.hw_height_ft * 12) + bot_hook + 6.0   # max height bars

    log.step(f"Wing length = {p.wing_length_ft} ft → {qty_per_face} bars/face")
    log.step(f"Using max height ({p.hw_height_ft} ft) for bar length = {bar_len_in:.1f} in")
    log.step("NOTE: shorter bars may be cut to suit taper in the field")
    log.result("WV1", f"#4 × {qty_total} @ {fmt_inches(bar_len_in)} [EF]")

    return [BarRow(
        mark="WV1", size="#4", qty=qty_total, length_in=bar_len_in,
        shape="L", leg_a_in=p.hw_height_ft * 12 + 6.0, leg_b_in=bot_hook,
        notes="Wing Vert EF (max-length)",
        review_flag="Verify bar lengths suit wall taper",
        source_rule="rule_wing_vert",
    )]


def rule_wing_corner(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """Corner L-bars at headwall–wing junction."""
    leg = max(18.0, min((p.hw_height_ft * 12) / 6.0, 24.0))
    qty = 4
    log.step(f"Corner leg = {leg:.0f} in  qty = {qty}")
    log.result("WC1", f"#4 × {qty}  L {fmt_inches(leg)} × {fmt_inches(leg)}")

    return [BarRow(
        mark="WC1", size="#4", qty=qty,
        length_in=leg * 2, shape="L",
        leg_a_in=leg, leg_b_in=leg,
        notes="Wing Corner", source_rule="rule_wing_corner",
    )]


def rule_validate_wing(p: Params, log: ReasoningLogger) -> list[BarRow]:
    if getattr(p, "tip_height_ft", 0.0) > p.hw_height_ft:
        log.warn("Tip height > headwall height — check taper direction")
    if False:  # cover hardcoded at 2.0
        log.warn(f"Cover {2.0} in < 2 in min for exposed wing wall")
    return []
