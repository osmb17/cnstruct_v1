"""
Rule functions for Flat Slab template.

Geometry: rectangular slab, bars each way (EW), straight bars, no hooks.

Verified formula (from gold barlists):
  qty  = floor(span_in / spacing_in)
  len  = other_dim_in - 2 × cover_in

Examples confirmed:
  10'2" × 3'6" @12oc #5 → S1: 3 bars @ 9'-8"  S2: 10 bars @ 3'-0"
  10'2" × 4'4" @10oc #5 → S1: 5 bars @ 9'-8"  S2: 12 bars @ 3'-10"
"""

from __future__ import annotations

import math

from vistadetail.engine.reasoning_logger import ReasoningLogger
from vistadetail.engine.schema import BarRow, Params, fmt_inches


# ---------------------------------------------------------------------------
# S1 — bars running the LONG way  (span = length, qty from width)
# ---------------------------------------------------------------------------

def rule_slab_long_bars(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Straight bars spanning the long dimension of the slab.

    Length = slab_length_in - 2 × cover_in
    Qty    = floor(slab_width_in / spacing_in)
    Mark   = S1
    """
    len_in   = p.slab_length_ft * 12
    wid_in   = p.slab_width_ft  * 12
    bar_len  = len_in - 2 * p.cover_in
    qty      = math.floor(wid_in / p.spacing_in)

    log.step(
        f"Long bars (S1): length = {len_in:.1f} − 2×{p.cover_in} cover = {bar_len:.1f} in"
        f" = {fmt_inches(bar_len)}",
        detail=f"slab_length_ft×12 − 2×cover_in",
        source="FlatSlabRules",
    )
    log.step(
        f"Qty S1 = ⌊{wid_in:.1f} ÷ {p.spacing_in}⌋ = {qty}",
        detail=f"floor(slab_width_in / spacing_in)",
        source="FlatSlabRules",
    )
    log.result("S1", f"{p.bar_size} × {qty} @ {fmt_inches(bar_len)} [mat EW]",
               detail=f"long-way bars", source="FlatSlabRules")

    return [BarRow(
        mark="S1",
        size=p.bar_size,
        qty=qty,
        length_in=bar_len,
        shape="Str",
        notes=f"@{int(p.spacing_in)}oc mat EW",
        source_rule="rule_slab_long_bars",
    )]


# ---------------------------------------------------------------------------
# S2 — bars running the SHORT way  (span = width, qty from length)
# ---------------------------------------------------------------------------

def rule_slab_short_bars(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Straight bars spanning the short dimension of the slab.

    Length = slab_width_in - 2 × cover_in
    Qty    = floor(slab_length_in / spacing_in)
    Mark   = S2
    """
    len_in   = p.slab_length_ft * 12
    wid_in   = p.slab_width_ft  * 12
    bar_len  = wid_in - 2 * p.cover_in
    qty      = math.floor(len_in / p.spacing_in)

    log.step(
        f"Short bars (S2): length = {wid_in:.1f} − 2×{p.cover_in} cover = {bar_len:.1f} in"
        f" = {fmt_inches(bar_len)}",
        detail=f"slab_width_ft×12 − 2×cover_in",
        source="FlatSlabRules",
    )
    log.step(
        f"Qty S2 = ⌊{len_in:.1f} ÷ {p.spacing_in}⌋ = {qty}",
        detail=f"floor(slab_length_in / spacing_in)",
        source="FlatSlabRules",
    )
    log.result("S2", f"{p.bar_size} × {qty} @ {fmt_inches(bar_len)} [mat EW]",
               detail=f"short-way bars", source="FlatSlabRules")

    return [BarRow(
        mark="S2",
        size=p.bar_size,
        qty=qty,
        length_in=bar_len,
        shape="Str",
        notes=f"@{int(p.spacing_in)}oc mat EW",
        source_rule="rule_slab_short_bars",
    )]


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def rule_validate_flat_slab(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    ACI 318-19 §26.4.1 — maximum bar spacing in slabs: min(2t, 18 in).
    For flat slabs cast against earth, cover ≥ 3 in (ACI Table 20.6.1.3.1).
    """
    # Estimate slab thickness from cover (conservative: assume t ≥ 4 in)
    max_spacing = min(18.0, 2 * 6.0)   # 6 in assumed min thickness → 12 in max
    if p.spacing_in > 18.0:
        log.warn(
            f"Spacing {p.spacing_in} in exceeds ACI 318 §26.4.1 max 18 in for slabs",
            detail="ACI 318-19 §26.4.1: s ≤ min(2t, 18 in)",
            source="Validator",
        )
    else:
        log.ok(
            f"Spacing {p.spacing_in} in ≤ 18 in max  [ACI 318-19 §26.4.1]",
            detail="ACI 318-19 §26.4.1",
            source="Validator",
        )

    if p.cover_in < 3.0:
        log.warn(
            f"Cover {p.cover_in} in < 3 in minimum for concrete cast against earth",
            detail="ACI 318-19 Table 20.6.1.3.1 — cast against earth: 3 in min",
            source="Validator",
        )
    else:
        log.ok(
            f"Cover {p.cover_in} in ≥ 3 in  [ACI 318-19 Table 20.6.1.3.1]",
            detail="ACI 318-19 Table 20.6.1.3.1",
            source="Validator",
        )

    return []
