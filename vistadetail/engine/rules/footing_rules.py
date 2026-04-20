"""
Rule functions for Spread Footing template.

Generates:
  BT1 — bottom transverse bars (short direction, full width)
  BL1 — bottom longitudinal bars (long direction, full length)
  DW1 — dowels (vertical, matching wall/column above)
"""

from __future__ import annotations

import math

from vistadetail.engine.hooks import hook_add
from vistadetail.engine.reasoning_logger import ReasoningLogger
from vistadetail.engine.schema import BarRow, Params, fmt_inches


def rule_bottom_transverse(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Bottom transverse bars spanning the short direction (width).
    Full width minus 2× 3.0 cover; qty based on 12.0 spacing.
    """
    usable_len_in = (p.footing_length_ft * 12) - (2 * 3.0)
    qty = math.floor(usable_len_in / 12.0) + 1

    bar_len_in = (p.footing_width_ft * 12) - (2 * 3.0)

    log.step(f"Footing length = {p.footing_length_ft} ft → usable = {usable_len_in:.1f} in")
    log.step(f"Transverse qty = ⌊{usable_len_in:.1f}/12.0⌋ + 1 = {qty}")
    log.step(f"Bar length = width - 2×3.0 = {bar_len_in:.1f} in = {fmt_inches(bar_len_in)}")
    log.result("BT1", f"#5 × {qty} @ {fmt_inches(bar_len_in)} [Bot]")

    return [BarRow(
        mark="BT1",
        size="#5",
        qty=qty,
        length_in=bar_len_in,
        shape="Str",
        notes="Bot Trans",
        source_rule="rule_bottom_transverse",
    )]


def rule_bottom_longitudinal(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Bottom longitudinal bars spanning the long direction (length).
    Qty based on 12.0 spacing; 3.0 cover.
    """
    usable_width_in = (p.footing_width_ft * 12) - (2 * 3.0)
    qty = math.floor(usable_width_in / 12.0) + 1

    bar_len_in = (p.footing_length_ft * 12) - (2 * 3.0)

    log.step(f"Footing width = {p.footing_width_ft} ft → usable = {usable_width_in:.1f} in")
    log.step(f"Longitudinal qty = ⌊{usable_width_in:.1f}/12.0⌋ + 1 = {qty}")
    log.step(f"Bar length = length - 2×3.0 = {bar_len_in:.1f} in = {fmt_inches(bar_len_in)}")
    log.result("BL1", f"#5 × {qty} @ {fmt_inches(bar_len_in)} [Bot]")

    return [BarRow(
        mark="BL1",
        size="#5",
        qty=qty,
        length_in=bar_len_in,
        shape="Str",
        notes="Bot Long",
        source_rule="rule_bottom_longitudinal",
    )]


def rule_dowels(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Vertical dowels matching wall/column above.
    Length = footing depth + development length into footing + lap splice above.
    """
    if getattr(p, "dowel_qty", 0) == 0:
        log.step("Dowels: none (qty = 0)")
        return []

    from vistadetail.engine.hooks import development_length_tension
    ld_in = development_length_tension(
        "#5", cover_in=3.0
    )
    lap_in = max(ld_in, 18.0)   # minimum 18 in lap splice above footing

    bar_len_in = (p.footing_depth_in - 3.0) + ld_in + lap_in

    log.step(f"Dowel dev length (tension) = {ld_in:.1f} in")
    log.step(f"Lap splice above = {lap_in:.1f} in")
    log.step(
        f"Bar length = (depth - 3.0 cover) + ld + lap "
        f"= ({p.footing_depth_in} - 3.0) + {ld_in:.1f} + {lap_in:.1f} "
        f"= {bar_len_in:.1f} in = {fmt_inches(bar_len_in)}"
    )
    log.result("DW1", f"#5 × {p.dowel_qty} @ {fmt_inches(bar_len_in)}")

    return [BarRow(
        mark="DW1",
        size="#5",
        qty=p.dowel_qty,
        length_in=bar_len_in,
        shape="Str",
        notes="Dowels",
        source_rule="rule_dowels",
    )]


def rule_validate_footing_cover(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """Cast-against-soil footings: 3 in cover hardcoded (ACI 318-19 Table 20.6.1.3.1)."""
    log.ok(
        "3\" cover — cast-against-soil footing  [ACI 318-19 Table 20.6.1.3.1]",
        detail="ACI 318-19 Table 20.6.1.3.1",
        source="Validator",
    )
    return []
