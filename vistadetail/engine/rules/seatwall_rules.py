"""
Rule functions for Playground / Landscape Seatwall template.

Geometry: low rectangular concrete bench wall placed above grade.
Cross-section: wall_width_in × wall_height_in (seat depth × seat height).
Length:        wall_length_ft

Marks:
  S1 — top longitudinal bars (along wall length, upper portion)
  S2 — bottom longitudinal bars (along wall length, lower portion)
  S3 — transverse bars (straight, spanning wall width at regular spacing along length)

Formulas:
  long_length = wall_length_in - 2 × cover_in          (longitudinal bars)
  long_qty    = n_top_bars  (or n_bot_bars)             (user-specified count)
  trans_length = wall_width_in - 2 × cover_in          (transverse bars)
  trans_qty   = floor(wall_length_in / tie_spacing_in)  (transverse count along length)

Cover default: 1.5 in — exposed, above grade, not cast against earth
               (ACI 318-19 Table 20.6.1.3.1).

Example from filename:
  Portola.ES.seatwall.31x2 → 31'-0" long × 24" section
"""

from __future__ import annotations

import math

from vistadetail.engine.reasoning_logger import ReasoningLogger
from vistadetail.engine.schema import BarRow, Params, fmt_inches


# ---------------------------------------------------------------------------
# S1 — top longitudinal bars
# ---------------------------------------------------------------------------

def rule_seatwall_top_long(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Longitudinal bars at the top of the seatwall cross-section.

    Length = wall_length_in - 2 × cover_in
    Qty    = top_bar_count  (typically 2)
    Mark   = S1
    """
    wall_in = p.wall_length_ft * 12
    bar_len = wall_in - 2 * p.cover_in
    qty     = int(p.top_bar_count)

    log.step(
        f"Top long bars (S1): {wall_in:.2f} − 2×{p.cover_in} cover = {bar_len:.2f} in"
        f" = {fmt_inches(bar_len)}",
        detail="wall_length_ft×12 − 2×cover_in",
        source="SeatwallRules",
    )
    log.step(
        f"Qty S1 = {qty} bars (top longitudinal count)",
        detail="user-specified top_bar_count",
        source="SeatwallRules",
    )
    log.result("S1", f"{p.top_bar_size} × {qty} @ {fmt_inches(bar_len)} [top long]",
               detail="seatwall top longitudinal bars", source="SeatwallRules")

    return [BarRow(
        mark="S1",
        size=p.top_bar_size,
        qty=qty,
        length_in=bar_len,
        shape="Str",
        notes="top longitudinal",
        source_rule="rule_seatwall_top_long",
    )]


# ---------------------------------------------------------------------------
# S2 — bottom longitudinal bars
# ---------------------------------------------------------------------------

def rule_seatwall_bot_long(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Longitudinal bars at the bottom of the seatwall cross-section.

    Length = wall_length_in - 2 × cover_in
    Qty    = bot_bar_count  (typically 2)
    Mark   = S2
    """
    wall_in = p.wall_length_ft * 12
    bar_len = wall_in - 2 * p.cover_in
    qty     = int(p.bot_bar_count)

    log.step(
        f"Bot long bars (S2): {wall_in:.2f} − 2×{p.cover_in} cover = {bar_len:.2f} in"
        f" = {fmt_inches(bar_len)}",
        detail="wall_length_ft×12 − 2×cover_in",
        source="SeatwallRules",
    )
    log.step(
        f"Qty S2 = {qty} bars (bottom longitudinal count)",
        detail="user-specified bot_bar_count",
        source="SeatwallRules",
    )
    log.result("S2", f"{p.bot_bar_size} × {qty} @ {fmt_inches(bar_len)} [bot long]",
               detail="seatwall bottom longitudinal bars", source="SeatwallRules")

    return [BarRow(
        mark="S2",
        size=p.bot_bar_size,
        qty=qty,
        length_in=bar_len,
        shape="Str",
        notes="bottom longitudinal",
        source_rule="rule_seatwall_bot_long",
    )]


# ---------------------------------------------------------------------------
# S3 — transverse bars (across wall width, spaced along wall length)
# ---------------------------------------------------------------------------

def rule_seatwall_transverse(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Straight bars spanning the wall width, spaced along the wall length.

    Length = wall_width_in - 2 × cover_in     (across the seat depth)
    Qty    = floor(wall_length_in / tie_spacing_in)
    Mark   = S3

    These bars restrain the longitudinal reinforcement in the cross-section
    and resist thermal/shrinkage splitting forces.
    """
    wall_in  = p.wall_length_ft * 12
    bar_len  = p.wall_width_in  - 2 * p.cover_in
    qty      = math.floor(wall_in / p.tie_spacing_in)

    log.step(
        f"Transverse bars (S3): {p.wall_width_in:.2f} − 2×{p.cover_in} cover"
        f" = {bar_len:.2f} in = {fmt_inches(bar_len)}",
        detail="wall_width_in − 2×cover_in",
        source="SeatwallRules",
    )
    log.step(
        f"Qty S3 = ⌊{wall_in:.2f} ÷ {p.tie_spacing_in}⌋ = {qty}",
        detail="floor(wall_length_in / tie_spacing_in)",
        source="SeatwallRules",
    )
    log.result("S3", f"{p.tie_bar_size} × {qty} @ {fmt_inches(bar_len)} [transverse]",
               detail="transverse bars across seat width", source="SeatwallRules")

    return [BarRow(
        mark="S3",
        size=p.tie_bar_size,
        qty=qty,
        length_in=bar_len,
        shape="Str",
        notes=f"@{int(p.tie_spacing_in)}oc along length",
        source_rule="rule_seatwall_transverse",
    )]


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def rule_validate_seatwall(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    ACI 318-19 checks for seatwall:
      - Cover ≥ 1.5 in for exposed-to-weather bars (Table 20.6.1.3.1)
      - Seat height sanity (warn if < 12 in or > 36 in)
      - Minimum bar count (warn if < 2 longitudinal bars per face)
    """
    if p.cover_in < 1.5:
        log.warn(
            f"Cover {p.cover_in} in < 1.5 in minimum (ACI Table 20.6.1.3.1 exposed-to-weather)",
            detail="ACI 318-19 Table 20.6.1.3.1: ≥ 1.5 in, #6 and smaller, exposed to weather",
            source="Validator",
        )
    else:
        log.ok(
            f"Cover {p.cover_in} in ≥ 1.5 in  [ACI Table 20.6.1.3.1]",
            detail="ACI 318-19 Table 20.6.1.3.1", source="Validator",
        )

    if p.wall_height_in < 12.0:
        log.warn(
            f"Seat height {p.wall_height_in} in < 12 in — verify design (min practical seatwall)",
            detail="Seatwalls are typically 17–19 in for ADA seating height",
            source="Validator",
        )
    elif p.wall_height_in > 36.0:
        log.warn(
            f"Seat height {p.wall_height_in} in > 36 in — consider retaining wall template for tall walls",
            detail="Tall seatwalls may require retaining wall design with shear/moment checks",
            source="Validator",
        )
    else:
        log.ok(
            f"Seat height {p.wall_height_in} in  [reasonable seatwall height]",
            detail="typical range 12–36 in", source="Validator",
        )

    if int(p.top_bar_count) < 2 or int(p.bot_bar_count) < 2:
        log.warn(
            "Less than 2 longitudinal bars on a face — verify design",
            detail="ACI 318-19 minimum: 2 bars per face is standard practice",
            source="Validator",
        )
    else:
        log.ok(
            f"Top bars: {int(p.top_bar_count)}, bot bars: {int(p.bot_bar_count)}  [≥2 each face]",
            detail="minimum 2 bars per face", source="Validator",
        )

    return []
