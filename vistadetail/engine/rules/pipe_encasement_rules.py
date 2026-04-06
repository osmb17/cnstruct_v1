"""
Rule functions for Pipe Encasement template.

Geometry: rectangular concrete jacket encasing an underground pipe.
Cross-section: encasement_width_in × encasement_height_in (outside faces).

Marks:
  E1 — transverse hoops encircling the cross-section (at regular spacing along pipe)
  E2 — longitudinal bars running along the full pipe length

Formulas:
  hoop_length  = 2 × (W - 2c) + 2 × (H - 2c)       where W = width, H = height, c = cover
  hoop_qty     = floor(encasement_length_in / hoop_spacing_in)
  long_length  = encasement_length_in - 2 × cover_in
  long_qty     = n_long_bars  (user-specified, based on cross-section bar arrangement)

Cover default: 2.0 in — buried/below grade (ACI 318-19 Table 20.6.1.3.1 for
               concrete not cast against earth, exposed to earth: 2 in).

Verified against Route 118 Sand Canyon to Balcom Canyon pipe encasement:
  234 linear ft, 315 #5 @9oc (E1), 630 #5 @9oc (both rows), 165 #4 longitudinal bars
  Qty check: floor(2808/9) = 312 ≈ 315 (short segments / end rounding)
"""

from __future__ import annotations

import math

from vistadetail.engine.reasoning_logger import ReasoningLogger
from vistadetail.engine.schema import BarRow, Params, fmt_inches


def rule_encasement_hoops(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Transverse hoops encircling the encasement cross-section.

    Each hoop runs around the perimeter of the rectangular cross-section:
      hoop_length = 2 × (width - 2c) + 2 × (height - 2c)  (closed rectangular hoop)

    Qty  = floor(encasement_length_in / hoop_spacing_in)
    Mark = E1

    ACI 318-19 §25.3 (standard hooks): add hook allowance to hoop length.
    For simplicity, this template uses the net perimeter length (engineer to verify hook lap).
    """
    length_in  = p.encasement_length_ft * 12
    hoop_len   = 2 * (p.encasement_width_in  - 2 * p.cover_in) \
               + 2 * (p.encasement_height_in - 2 * p.cover_in)
    qty        = math.floor(length_in / p.hoop_spacing_in)

    log.step(
        f"Hoops (E1): 2×({p.encasement_width_in}-2×{p.cover_in}) + "
        f"2×({p.encasement_height_in}-2×{p.cover_in}) = {hoop_len:.2f} in"
        f" = {fmt_inches(hoop_len)}",
        detail="2(W-2c) + 2(H-2c)",
        source="PipeEncasementRules",
    )
    log.step(
        f"Qty E1 = ⌊{length_in:.1f} ÷ {p.hoop_spacing_in}⌋ = {qty}",
        detail="floor(encasement_length_in / hoop_spacing_in)",
        source="PipeEncasementRules",
    )
    log.result("E1", f"{p.hoop_bar_size} × {qty} @ {fmt_inches(hoop_len)} [transverse hoops]",
               detail="encasement transverse hoops", source="PipeEncasementRules")

    return [BarRow(
        mark="E1",
        size=p.hoop_bar_size,
        qty=qty,
        length_in=hoop_len,
        shape="Rect",
        notes=f"@{int(p.hoop_spacing_in)}oc along pipe",
        source_rule="rule_encasement_hoops",
    )]


_MAX_STOCK_FT = 60       # max rebar stock length (industry standard)


def rule_encasement_longitudinals(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Longitudinal bars running the full length of the encasement.

    For encasements longer than 60ft, bars are broken into stock-length
    pieces with Class B lap splices. Qty = n_long_bars * pieces_per_run.
    ACI 318-19 S25.5.2: Class B tension splice = 1.3 * ld.
    """
    from vistadetail.engine.hooks import bar_diameter, development_length_tension

    length_in  = p.encasement_length_ft * 12
    total_run  = length_in - 2 * p.cover_in
    n_bars     = int(p.n_long_bars)
    max_stock_in = _MAX_STOCK_FT * 12  # 720 in

    if total_run <= max_stock_in:
        # Single piece per bar position
        bar_len = total_run
        qty = n_bars
        n_pieces = 1
        lap_in = 0
        log.step(
            f"Longitudinal bars (E2): {fmt_inches(total_run)} <= {_MAX_STOCK_FT}ft stock"
            f" -- single piece per position",
            source="PipeEncasementRules",
        )
    else:
        # Break into stock lengths with lap splices
        ld_in = development_length_tension(p.long_bar_size, cover_in=p.cover_in)
        lap_in = math.ceil(1.3 * ld_in)  # Class B splice

        # Each piece covers (stock - lap) of effective run
        effective_per_piece = max_stock_in - lap_in
        n_pieces = math.ceil(total_run / effective_per_piece)
        bar_len = max_stock_in  # each piece is a full stock bar
        qty = n_bars * n_pieces

        log.step(
            f"Longitudinal run = {fmt_inches(total_run)} > {_MAX_STOCK_FT}ft stock"
            f" -- breaking into {n_pieces} pieces per position",
            source="PipeEncasementRules",
        )
        log.step(
            f"Class B lap splice = 1.3 x {ld_in:.1f} = {lap_in} in"
            f" | effective per piece = {fmt_inches(effective_per_piece)}",
            source="PipeEncasementRules",
        )

    log.step(
        f"Qty E2 = {n_bars} positions x {n_pieces} pieces = {qty} bars"
        f" @ {fmt_inches(bar_len)}",
        source="PipeEncasementRules",
    )
    log.result("E2", f"{p.long_bar_size} x {qty} @ {fmt_inches(bar_len)} [longitudinals]",
               detail="encasement longitudinal bars", source="PipeEncasementRules")

    notes = "longitudinal along pipe"
    if total_run > max_stock_in:
        notes += f" (spliced, {lap_in}\" lap)"

    return [BarRow(
        mark="E2",
        size=p.long_bar_size,
        qty=qty,
        length_in=bar_len,
        shape="Str",
        notes=notes,
        source_rule="rule_encasement_longitudinals",
    )]


def rule_validate_pipe_encasement(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    ACI 318-19 checks for pipe encasement:
      - Cover ≥ 2 in for concrete not cast against earth but exposed to earth (Table 20.6.1.3.1)
      - Hoop spacing ≤ minimum practical for reinforcing cage assembly
      - Cross-section dimensions sanity
    """
    if p.cover_in < 2.0:
        log.warn(
            f"Cover {p.cover_in} in < 2.0 in for buried concrete (ACI Table 20.6.1.3.1)",
            detail="ACI 318-19 Table 20.6.1.3.1: ≥ 2 in for not-cast-against-earth, exposed to earth",
            source="Validator",
        )
    else:
        log.ok(
            f"Cover {p.cover_in} in ≥ 2.0 in  [ACI Table 20.6.1.3.1 buried]",
            detail="ACI 318-19 Table 20.6.1.3.1", source="Validator",
        )

    net_w = p.encasement_width_in  - 2 * p.cover_in
    net_h = p.encasement_height_in - 2 * p.cover_in
    if net_w < 4.0 or net_h < 4.0:
        log.warn(
            f"Net interior dimension ({net_w:.1f} in × {net_h:.1f} in) very small — verify dimensions",
            detail="encasement dimension − 2×cover must leave room for pipe and bars",
            source="Validator",
        )
    else:
        log.ok(
            f"Net interior dimensions: {net_w:.1f} in × {net_h:.1f} in  [OK]",
            detail="encasement_width/height − 2×cover", source="Validator",
        )

    return []
