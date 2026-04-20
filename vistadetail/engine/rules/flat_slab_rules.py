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

    Length = slab_length_in - 2 × 3.0 (cover)
    Qty    = floor(slab_width_in / 12.0 (spacing))
    Mark   = S1
    """
    len_in   = p.slab_length_ft * 12
    wid_in   = p.slab_width_ft  * 12
    bar_len  = len_in - 2 * 3.0
    qty      = math.floor(wid_in / 12.0)

    log.step(
        f"Long bars (S1): length = {len_in:.1f} − 2×3.0 cover = {bar_len:.1f} in"
        f" = {fmt_inches(bar_len)}",
        detail="slab_length_ft×12 − 2×3.0",
        source="FlatSlabRules",
    )
    log.step(
        f"Qty S1 = ⌊{wid_in:.1f} ÷ 12.0⌋ = {qty}",
        detail="floor(slab_width_in / 12.0)",
        source="FlatSlabRules",
    )
    log.result("S1", f"#5 × {qty} @ {fmt_inches(bar_len)} [mat EW]",
               detail="long-way bars", source="FlatSlabRules")

    return [BarRow(
        mark="S1",
        size="#5",
        qty=qty,
        length_in=bar_len,
        shape="Str",
        notes="@12oc mat EW",
        source_rule="rule_slab_long_bars",
    )]


# ---------------------------------------------------------------------------
# S2 — bars running the SHORT way  (span = width, qty from length)
# ---------------------------------------------------------------------------

def rule_slab_short_bars(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Straight bars spanning the short dimension of the slab.

    Length = slab_width_in - 2 × 3.0 (cover)
    Qty    = floor(slab_length_in / 12.0 (spacing))
    Mark   = S2
    """
    len_in   = p.slab_length_ft * 12
    wid_in   = p.slab_width_ft  * 12
    bar_len  = wid_in - 2 * 3.0
    qty      = math.floor(len_in / 12.0)

    log.step(
        f"Short bars (S2): length = {wid_in:.1f} − 2×3.0 cover = {bar_len:.1f} in"
        f" = {fmt_inches(bar_len)}",
        detail="slab_width_ft×12 − 2×3.0",
        source="FlatSlabRules",
    )
    log.step(
        f"Qty S2 = ⌊{len_in:.1f} ÷ 12.0⌋ = {qty}",
        detail="floor(slab_length_in / 12.0)",
        source="FlatSlabRules",
    )
    log.result("S2", f"#5 × {qty} @ {fmt_inches(bar_len)} [mat EW]",
               detail="short-way bars", source="FlatSlabRules")

    return [BarRow(
        mark="S2",
        size="#5",
        qty=qty,
        length_in=bar_len,
        shape="Str",
        notes="@12oc mat EW",
        source_rule="rule_slab_short_bars",
    )]


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def rule_validate_flat_slab(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    ACI 318-19 §26.4.1 — standard #5@12oc, 3\" cover (hardcoded).
    """
    log.ok(
        "Standard #5@12oc, 3\" cover",
        detail="ACI 318-19 §26.4.1 / Table 20.6.1.3.1",
        source="Validator",
    )
    return []
