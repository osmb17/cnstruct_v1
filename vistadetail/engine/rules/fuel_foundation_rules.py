"""
Rule functions for Fuel Tank / Disconnect Foundation template.

Geometry: rectangular concrete mat foundation for fuel tanks, fuel disconnect
panels, or similar above-ground equipment requiring a robust base mat.

This is structurally identical to the equipment pad with double mat, but with
engineering defaults tuned for fuel/utility foundations:
  - Cover: 3 in (cast against earth, ACI 318-19 Table 20.6.1.3.1)
  - Typical: double mat, heavier bar sizes, curb/stem optional

Marks:
  F1 — bottom mat, long direction
  F2 — bottom mat, short direction
  F3 — top mat, long direction
  F4 — top mat, short direction

Formulas:
  bar_length = span_dim_in - 2 × cover_in
  qty        = floor(perpendicular_dim_in / spacing_in)

Cover default: 3.0 in (cast against and permanently exposed to earth).

Covers 2 PDFs in the clean_examples set:
  fueldisconnectfoundation.clean
  fueltankfoundationseamair.clean
"""

from __future__ import annotations

import math

from vistadetail.engine.reasoning_logger import ReasoningLogger
from vistadetail.engine.schema import BarRow, Params, fmt_inches


def rule_fuel_bottom_long(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """F1: bottom mat, bars spanning the long direction."""
    len_in  = p.fdn_length_ft * 12
    wid_in  = p.fdn_width_ft  * 12
    bar_len = len_in - 2 * 3.0
    qty     = math.floor(wid_in / 12.0)

    log.step(
        f"Bottom long (F1): {len_in:.2f} − 2×3.0 = {bar_len:.2f} in = {fmt_inches(bar_len)}",
        detail="fdn_length_ft×12 − 2×3.0", source="FuelFoundationRules",
    )
    log.step(f"Qty F1 = ⌊{wid_in:.2f} ÷ 12.0⌋ = {qty}",
             detail="floor(fdn_width_in / 12.0)", source="FuelFoundationRules")
    log.result("F1", f"#5 × {qty} @ {fmt_inches(bar_len)} [bot long]",
               detail="fuel foundation bottom long bars", source="FuelFoundationRules")

    return [BarRow(mark="F1", size="#5", qty=qty, length_in=bar_len,
                   shape="Str", notes="@12oc EW bottom",
                   source_rule="rule_fuel_bottom_long")]


def rule_fuel_bottom_short(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """F2: bottom mat, bars spanning the short direction."""
    len_in  = p.fdn_length_ft * 12
    wid_in  = p.fdn_width_ft  * 12
    bar_len = wid_in - 2 * 3.0
    qty     = math.floor(len_in / 12.0)

    log.step(
        f"Bottom short (F2): {wid_in:.2f} − 2×3.0 = {bar_len:.2f} in = {fmt_inches(bar_len)}",
        detail="fdn_width_ft×12 − 2×3.0", source="FuelFoundationRules",
    )
    log.step(f"Qty F2 = ⌊{len_in:.2f} ÷ 12.0⌋ = {qty}",
             detail="floor(fdn_length_in / 12.0)", source="FuelFoundationRules")
    log.result("F2", f"#5 × {qty} @ {fmt_inches(bar_len)} [bot short]",
               detail="fuel foundation bottom short bars", source="FuelFoundationRules")

    return [BarRow(mark="F2", size="#5", qty=qty, length_in=bar_len,
                   shape="Str", notes="@12oc EW bottom",
                   source_rule="rule_fuel_bottom_short")]


def rule_fuel_top_long(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """F3: top mat, bars spanning the long direction. Always generated (has_top_mat=1.0)."""
    len_in  = p.fdn_length_ft * 12
    wid_in  = p.fdn_width_ft  * 12
    bar_len = len_in - 2 * 3.0
    qty     = math.floor(wid_in / 12.0)

    log.step(
        f"Top long (F3): {len_in:.2f} − 2×3.0 = {bar_len:.2f} in = {fmt_inches(bar_len)}",
        detail="fdn_length_ft×12 − 2×3.0", source="FuelFoundationRules",
    )
    log.step(f"Qty F3 = ⌊{wid_in:.2f} ÷ 12.0⌋ = {qty}",
             detail="floor(fdn_width_in / 12.0)", source="FuelFoundationRules")
    log.result("F3", f"#5 × {qty} @ {fmt_inches(bar_len)} [top long]",
               detail="fuel foundation top long bars", source="FuelFoundationRules")

    return [BarRow(mark="F3", size="#5", qty=qty, length_in=bar_len,
                   shape="Str", notes="@12oc EW top",
                   source_rule="rule_fuel_top_long")]


def rule_fuel_top_short(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """F4: top mat, bars spanning the short direction. Always generated (has_top_mat=1.0)."""
    len_in  = p.fdn_length_ft * 12
    wid_in  = p.fdn_width_ft  * 12
    bar_len = wid_in - 2 * 3.0
    qty     = math.floor(len_in / 12.0)

    log.step(
        f"Top short (F4): {wid_in:.2f} − 2×3.0 = {bar_len:.2f} in = {fmt_inches(bar_len)}",
        detail="fdn_width_ft×12 − 2×3.0", source="FuelFoundationRules",
    )
    log.step(f"Qty F4 = ⌊{len_in:.2f} ÷ 12.0⌋ = {qty}",
             detail="floor(fdn_length_in / 12.0)", source="FuelFoundationRules")
    log.result("F4", f"#5 × {qty} @ {fmt_inches(bar_len)} [top short]",
               detail="fuel foundation top short bars", source="FuelFoundationRules")

    return [BarRow(mark="F4", size="#5", qty=qty, length_in=bar_len,
                   shape="Str", notes="@12oc EW top",
                   source_rule="rule_fuel_top_short")]


def rule_validate_fuel_foundation(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    ACI 318-19 checks for fuel tank / disconnect foundation.
    Standard #5@12oc double mat, 3\" cover (hardcoded).
    """
    log.ok(
        "Standard #5@12oc double mat, 3\" cover  [ACI Table 20.6.1.3.1 cast-against-earth]",
        detail="ACI 318-19 Table 20.6.1.3.1", source="Validator",
    )

    if p.fdn_thickness_in < 8.0:
        log.warn(
            f"Foundation thickness {p.fdn_thickness_in} in < 8 in — verify for fuel/equipment loading",
            detail="Fuel foundations typically 8–12 in minimum for mat integrity and cover",
            source="Validator",
        )
    else:
        log.ok(
            f"Foundation thickness {p.fdn_thickness_in} in  [fuel foundation]",
            detail="fuel / equipment foundation", source="Validator",
        )

    return []
