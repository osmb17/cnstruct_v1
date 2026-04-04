"""
Rule functions for Concrete Pipe Collar template.

Geometry: rectangular reinforced concrete collar block placed around a pipe
penetration. Straight bars in two orthogonal directions form a grid mat.

Verified formula (from collar PDFs):
  qty  = floor(perpendicular_dim_in / spacing_in)
  len  = span_dim_in - 2 × cover_in

Examples:
  4'-4 3/4" × 5'-2 1/4", #4 @9" both ways, 3in cover:
    C1 (long):  qty = floor(52.25 / 9) = 5,  len = 62.75 - 6 = 56.75in = 4'-8 3/4"
    C2 (short): qty = floor(62.75 / 9) = 6,  len = 52.25 - 6 = 46.25in = 3'-10 1/4"
"""

from __future__ import annotations

import math

from vistadetail.engine.reasoning_logger import ReasoningLogger
from vistadetail.engine.schema import BarRow, Params, fmt_inches


# ---------------------------------------------------------------------------
# C1 — bars running the LONG way
# ---------------------------------------------------------------------------

def rule_collar_long_bars(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Straight bars spanning the long dimension of the collar.

    Length = collar_length_in - 2 × cover_in
    Qty    = floor(collar_width_in / spacing_in)
    Mark   = C1
    """
    len_in  = p.collar_length_ft * 12
    wid_in  = p.collar_width_ft  * 12
    bar_len = len_in - 2 * p.cover_in
    qty     = math.floor(wid_in / p.spacing_in)

    log.step(
        f"Long bars (C1): length = {len_in:.2f} − 2×{p.cover_in} cover = {bar_len:.2f} in"
        f" = {fmt_inches(bar_len)}",
        detail="collar_length_ft×12 − 2×cover_in",
        source="CollarRules",
    )
    log.step(
        f"Qty C1 = ⌊{wid_in:.2f} ÷ {p.spacing_in}⌋ = {qty}",
        detail="floor(collar_width_in / spacing_in)",
        source="CollarRules",
    )
    log.result("C1", f"{p.bar_size} × {qty} @ {fmt_inches(bar_len)} [long-way]",
               detail="long-direction collar bars", source="CollarRules")

    return [BarRow(
        mark="C1",
        size=p.bar_size,
        qty=qty,
        length_in=bar_len,
        shape="Str",
        notes=f"collar long bars @{int(p.spacing_in)}oc",
        source_rule="rule_collar_long_bars",
    )]


# ---------------------------------------------------------------------------
# C2 — bars running the SHORT way
# ---------------------------------------------------------------------------

def rule_collar_short_bars(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Straight bars spanning the short dimension of the collar.

    Length = collar_width_in - 2 × cover_in
    Qty    = floor(collar_length_in / spacing_in)
    Mark   = C2
    """
    len_in  = p.collar_length_ft * 12
    wid_in  = p.collar_width_ft  * 12
    bar_len = wid_in - 2 * p.cover_in
    qty     = math.floor(len_in / p.spacing_in)

    log.step(
        f"Short bars (C2): length = {wid_in:.2f} − 2×{p.cover_in} cover = {bar_len:.2f} in"
        f" = {fmt_inches(bar_len)}",
        detail="collar_width_ft×12 − 2×cover_in",
        source="CollarRules",
    )
    log.step(
        f"Qty C2 = ⌊{len_in:.2f} ÷ {p.spacing_in}⌋ = {qty}",
        detail="floor(collar_length_in / spacing_in)",
        source="CollarRules",
    )
    log.result("C2", f"{p.bar_size} × {qty} @ {fmt_inches(bar_len)} [short-way]",
               detail="short-direction collar bars", source="CollarRules")

    return [BarRow(
        mark="C2",
        size=p.bar_size,
        qty=qty,
        length_in=bar_len,
        shape="Str",
        notes=f"collar short bars @{int(p.spacing_in)}oc",
        source_rule="rule_collar_short_bars",
    )]


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def rule_validate_collar(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    ACI 318-19 §26.4.1 — max bar spacing min(2t, 18 in).
    Cover check: ≥ 2 in finished surface (ACI Table 20.6.1.3.1).
    """
    if p.spacing_in > 18.0:
        log.warn(
            f"Spacing {p.spacing_in} in > 18 in max for slabs/collars (ACI §26.4.1)",
            detail="ACI 318-19 §26.4.1: s ≤ min(2t, 18 in)",
            source="Validator",
        )
    else:
        log.ok(
            f"Spacing {p.spacing_in} in ≤ 18 in  [ACI 318-19 §26.4.1]",
            detail="ACI 318-19 §26.4.1",
            source="Validator",
        )

    if p.cover_in < 2.0:
        log.warn(
            f"Cover {p.cover_in} in < 2 in — finished surface min is 1.5 in (ACI Table 20.6.1.3.1)",
            detail="ACI 318-19 Table 20.6.1.3.1 — #5 and smaller: 1.5 in; consider 2 in min",
            source="Validator",
        )
    else:
        log.ok(
            f"Cover {p.cover_in} in ≥ 2 in  [ACI 318-19 Table 20.6.1.3.1]",
            detail="ACI 318-19 Table 20.6.1.3.1",
            source="Validator",
        )

    return []
