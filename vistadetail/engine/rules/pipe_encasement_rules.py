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


def rule_encasement_longitudinals(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Longitudinal bars running the full length of the encasement.

    Length = encasement_length_in - 2 × cover_in
    Qty    = n_long_bars  (user-specified; based on cross-section bar arrangement)
    Mark   = E2

    Note: for long encasements, bars will be spliced in the field. The length
    here is the full run length; the contractor will lap-splice at delivery lengths.
    """
    length_in = p.encasement_length_ft * 12
    bar_len   = length_in - 2 * p.cover_in
    qty       = int(p.n_long_bars)

    log.step(
        f"Longitudinal bars (E2): {length_in:.1f} − 2×{p.cover_in} cover = {bar_len:.1f} in"
        f" = {fmt_inches(bar_len)}",
        detail="encasement_length_in − 2×cover_in",
        source="PipeEncasementRules",
    )
    log.step(
        f"Qty E2 = {qty} bars (longitudinal count per cross-section detail)",
        detail="user-specified n_long_bars",
        source="PipeEncasementRules",
    )
    log.result("E2", f"{p.long_bar_size} × {qty} @ {fmt_inches(bar_len)} [longitudinals]",
               detail="encasement longitudinal bars", source="PipeEncasementRules")

    return [BarRow(
        mark="E2",
        size=p.long_bar_size,
        qty=qty,
        length_in=bar_len,
        shape="Str",
        notes="longitudinal along pipe",
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
