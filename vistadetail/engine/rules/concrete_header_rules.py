"""
Rule functions for Concrete Header / Curb template.

Geometry: low rectangular concrete border beam used as a playground header,
curb, or landscape edge. Cross-section: header_width_in × header_height_in.
Length: header_length_ft.

Marks:
  H1 — top longitudinal bars (along header length)
  H2 — bottom longitudinal bars (along header length)
  H3 — transverse bars (straight, spanning header width, spaced along length)

Formulas:
  long_length  = header_length_in - 2 × cover_in
  trans_length = header_width_in  - 2 × cover_in
  trans_qty    = floor(header_length_in / tie_spacing_in)

Cover default: 1.5 in (exposed to weather, ACI Table 20.6.1.3.1).

Examples from filenames (Portola ES playground):
  Portola.ES.header.67x3 → 67'-0" long × 36" section (3' = 36")
  Portola.ES.header45x3  → 45'-0" long × 36" section
"""

from __future__ import annotations

import math

from vistadetail.engine.reasoning_logger import ReasoningLogger
from vistadetail.engine.schema import BarRow, Params, fmt_inches


def rule_header_top_long(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Longitudinal bars at the top of the header cross-section.

    Length = header_length_in - 2 × cover_in
    Qty    = top_bar_count
    Mark   = H1
    """
    length_in = p.header_length_ft * 12
    bar_len   = length_in - 2 * p.cover_in
    qty       = int(p.top_bar_count)

    log.step(
        f"Top long bars (H1): {length_in:.2f} − 2×{p.cover_in} cover = {bar_len:.2f} in"
        f" = {fmt_inches(bar_len)}",
        detail="header_length_ft×12 − 2×cover_in",
        source="ConcreteHeaderRules",
    )
    log.step(f"Qty H1 = {qty} bars (top longitudinal count)",
             detail="user-specified top_bar_count", source="ConcreteHeaderRules")
    log.result("H1", f"{p.top_bar_size} × {qty} @ {fmt_inches(bar_len)} [top long]",
               detail="header top longitudinal bars", source="ConcreteHeaderRules")

    return [BarRow(
        mark="H1",
        size=p.top_bar_size,
        qty=qty,
        length_in=bar_len,
        shape="Str",
        notes="top longitudinal",
        source_rule="rule_header_top_long",
    )]


def rule_header_bot_long(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Longitudinal bars at the bottom of the header cross-section.

    Length = header_length_in - 2 × cover_in
    Qty    = bot_bar_count
    Mark   = H2
    """
    length_in = p.header_length_ft * 12
    bar_len   = length_in - 2 * p.cover_in
    qty       = int(p.bot_bar_count)

    log.step(
        f"Bot long bars (H2): {length_in:.2f} − 2×{p.cover_in} cover = {bar_len:.2f} in"
        f" = {fmt_inches(bar_len)}",
        detail="header_length_ft×12 − 2×cover_in",
        source="ConcreteHeaderRules",
    )
    log.step(f"Qty H2 = {qty} bars (bottom longitudinal count)",
             detail="user-specified bot_bar_count", source="ConcreteHeaderRules")
    log.result("H2", f"{p.bot_bar_size} × {qty} @ {fmt_inches(bar_len)} [bot long]",
               detail="header bottom longitudinal bars", source="ConcreteHeaderRules")

    return [BarRow(
        mark="H2",
        size=p.bot_bar_size,
        qty=qty,
        length_in=bar_len,
        shape="Str",
        notes="bottom longitudinal",
        source_rule="rule_header_bot_long",
    )]


def rule_header_transverse(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Straight bars spanning the header width, spaced along the header length.

    Length = header_width_in - 2 × cover_in
    Qty    = floor(header_length_in / tie_spacing_in)
    Mark   = H3
    """
    length_in = p.header_length_ft * 12
    bar_len   = p.header_width_in  - 2 * p.cover_in
    qty       = math.floor(length_in / p.tie_spacing_in)

    log.step(
        f"Transverse bars (H3): {p.header_width_in:.2f} − 2×{p.cover_in} cover"
        f" = {bar_len:.2f} in = {fmt_inches(bar_len)}",
        detail="header_width_in − 2×cover_in",
        source="ConcreteHeaderRules",
    )
    log.step(
        f"Qty H3 = ⌊{length_in:.2f} ÷ {p.tie_spacing_in}⌋ = {qty}",
        detail="floor(header_length_in / tie_spacing_in)",
        source="ConcreteHeaderRules",
    )
    log.result("H3", f"{p.tie_bar_size} × {qty} @ {fmt_inches(bar_len)} [transverse]",
               detail="transverse bars across header width", source="ConcreteHeaderRules")

    return [BarRow(
        mark="H3",
        size=p.tie_bar_size,
        qty=qty,
        length_in=bar_len,
        shape="Str",
        notes=f"@{int(p.tie_spacing_in)}oc along length",
        source_rule="rule_header_transverse",
    )]


def rule_validate_concrete_header(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    ACI 318-19 checks for concrete header/curb:
      - Cover ≥ 1.5 in for exposed-to-weather bars (Table 20.6.1.3.1)
      - Height sanity (warn if < 6 in or > 48 in)
    """
    if p.cover_in < 1.5:
        log.warn(
            f"Cover {p.cover_in} in < 1.5 in minimum (ACI Table 20.6.1.3.1 exposed-to-weather)",
            detail="ACI 318-19 Table 20.6.1.3.1: ≥ 1.5 in exposed to weather",
            source="Validator",
        )
    else:
        log.ok(
            f"Cover {p.cover_in} in ≥ 1.5 in  [ACI Table 20.6.1.3.1]",
            detail="ACI 318-19 Table 20.6.1.3.1", source="Validator",
        )

    if p.header_height_in < 6.0:
        log.warn(
            f"Header height {p.header_height_in} in < 6 in — verify practical minimum",
            detail="Minimum practical header height for reinforcing placement is ~6 in",
            source="Validator",
        )
    else:
        log.ok(
            f"Header height {p.header_height_in} in  [OK]",
            detail="header cross-section height", source="Validator",
        )

    return []
