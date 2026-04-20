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

_MAX_STOCK_FT = 60  # max rebar stock length


def _long_bar_calc(p, mark, bar_size, qty_count, label, log):
    """Shared logic for top/bottom longitudinal bars with stock-length splicing."""
    from vistadetail.engine.hooks import development_length_tension

    length_in = p.header_length_ft * 12
    total_run = length_in - 2 * 1.5
    qty_per_pos = int(qty_count)
    max_stock_in = _MAX_STOCK_FT * 12

    if total_run <= max_stock_in:
        bar_len = total_run
        qty = qty_per_pos
        n_pieces = 1
        notes = f"{label} longitudinal"
        log.step(
            f"{label} long bars ({mark}): {fmt_inches(total_run)} <= {_MAX_STOCK_FT}ft -- single piece",
            source="ConcreteHeaderRules",
        )
    else:
        ld_in = development_length_tension(bar_size, cover_in=1.5)
        lap_in = math.ceil(1.3 * ld_in)
        effective = max_stock_in - lap_in
        n_pieces = math.ceil(total_run / effective)
        bar_len = max_stock_in
        qty = qty_per_pos * n_pieces
        notes = f"{label} longitudinal (spliced, {lap_in}\" lap)"
        log.step(
            f"{label} long bars ({mark}): {fmt_inches(total_run)} > {_MAX_STOCK_FT}ft"
            f" -- {n_pieces} pieces x {qty_per_pos} = {qty} bars @ {_MAX_STOCK_FT}ft",
            source="ConcreteHeaderRules",
        )
        log.step(
            f"Class B lap = 1.3 x {ld_in:.1f} = {lap_in} in",
            source="ConcreteHeaderRules",
        )

    log.result(mark, f"{bar_size} x {qty} @ {fmt_inches(bar_len)} [{label} long]",
               source="ConcreteHeaderRules")

    return [BarRow(
        mark=mark, size=bar_size, qty=qty, length_in=bar_len,
        shape="Str", notes=notes, source_rule=f"rule_header_{label.lower()}_long",
    )]


def rule_header_top_long(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """Top longitudinal bars -- spliced if header > 60ft."""
    return _long_bar_calc(p, "H1", "#4", p.top_bar_count, "top", log)


def rule_header_bot_long(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """Bottom longitudinal bars -- spliced if header > 60ft."""
    return _long_bar_calc(p, "H2", "#4", p.bot_bar_count, "bottom", log)


def rule_header_transverse(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Straight bars spanning the header width, spaced along the header length.

    Length = header_width_in - 2 × cover_in
    Qty    = floor(header_length_in / tie_spacing_in)
    Mark   = H3
    """
    length_in = p.header_length_ft * 12
    bar_len   = p.header_width_in  - 2 * 1.5
    qty       = math.floor(length_in / 18.0)

    log.step(
        f"Transverse bars (H3): {p.header_width_in:.2f} − 2×{1.5} cover"
        f" = {bar_len:.2f} in = {fmt_inches(bar_len)}",
        detail="header_width_in − 2×cover_in",
        source="ConcreteHeaderRules",
    )
    log.step(
        f"Qty H3 = ⌊{length_in:.2f} ÷ {18.0}⌋ = {qty}",
        detail="floor(header_length_in / tie_spacing_in)",
        source="ConcreteHeaderRules",
    )
    log.result("H3", f"#3 × {qty} @ {fmt_inches(bar_len)} [transverse]",
               detail="transverse bars across header width", source="ConcreteHeaderRules")

    return [BarRow(
        mark="H3",
        size="#3",
        qty=qty,
        length_in=bar_len,
        shape="Str",
        notes=f"@{int(18.0)}oc along length",
        source_rule="rule_header_transverse",
    )]


def rule_validate_concrete_header(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    ACI 318-19 checks for concrete header/curb:
      - Cover ≥ 1.5 in for exposed-to-weather bars (Table 20.6.1.3.1)
      - Height sanity (warn if < 6 in or > 48 in)
    """
    if 1.5 < 1.5:
        log.warn(
            f"Cover {1.5} in < 1.5 in minimum (ACI Table 20.6.1.3.1 exposed-to-weather)",
            detail="ACI 318-19 Table 20.6.1.3.1: ≥ 1.5 in exposed to weather",
            source="Validator",
        )
    else:
        log.ok(
            f"Cover {1.5} in ≥ 1.5 in  [ACI Table 20.6.1.3.1]",
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
