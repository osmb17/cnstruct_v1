"""
Rule functions for G2 Inlet Top and G2 Expanded Inlet Top templates.

Top/cover slab over a Caltrans G2 inlet box.
Bars run each way; no hooks (slab bears on walls at edges).

Marks:
  IT1 — long bars (span the length, spaced along width)
  IT2 — short bars (span the width, spaced along length)
"""

from __future__ import annotations

import math

from vistadetail.engine.reasoning_logger import ReasoningLogger
from vistadetail.engine.schema import BarRow, Params, fmt_inches


def rule_inlet_top_long_bars(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Long bars spanning the slab length direction.

    Length = slab_length_in − 2 × cover_in  (straight, no hooks, slab edges)
    Qty    = floor(slab_width_in / spacing) + 1
    """
    slab_len_in = p.slab_length_ft * 12
    slab_w_in   = p.slab_width_ft  * 12
    bar_len_in  = slab_len_in - (2 * 2.0)
    qty         = math.floor(slab_w_in / 12.0) + 1

    log.step(
        f"Inlet top long: {slab_len_in:.0f} − 2×{2.0} = {bar_len_in:.1f} in = {fmt_inches(bar_len_in)}"
    )
    log.step(f"Qty = ⌊{slab_w_in:.0f}/{12.0}⌋ + 1 = {qty}")
    log.result("IT1", f"#5 × {qty} @ {fmt_inches(bar_len_in)}")

    return [BarRow(
        mark="IT1", size="#5", qty=qty, length_in=bar_len_in,
        shape="Str", notes=f"Top long @{int(12.0)}oc",
        source_rule="rule_inlet_top_long_bars",
    )]


def rule_inlet_top_short_bars(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Short bars spanning the slab width direction.

    Length = slab_width_in − 2 × cover_in
    Qty    = floor(slab_length_in / spacing) + 1
    """
    slab_len_in = p.slab_length_ft * 12
    slab_w_in   = p.slab_width_ft  * 12
    bar_len_in  = slab_w_in - (2 * 2.0)
    qty         = math.floor(slab_len_in / 12.0) + 1

    log.step(
        f"Inlet top short: {slab_w_in:.0f} − 2×{2.0} = {bar_len_in:.1f} in = {fmt_inches(bar_len_in)}"
    )
    log.step(f"Qty = ⌊{slab_len_in:.0f}/{12.0}⌋ + 1 = {qty}")
    log.result("IT2", f"#5 × {qty} @ {fmt_inches(bar_len_in)}")

    return [BarRow(
        mark="IT2", size="#5", qty=qty, length_in=bar_len_in,
        shape="Str", notes=f"Top short @{int(12.0)}oc",
        source_rule="rule_inlet_top_short_bars",
    )]


def rule_validate_inlet_top(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """Validate cover and ACI §24.3.2 max spacing for the inlet top slab."""
    if 2.0 < 1.5:
        log.warn(f"Cover {2.0} in < 1.5 in minimum (ACI §20.6.1.3)")
    t = p.slab_thick_in
    max_sp = min(3 * t, 18.0)
    if 12.0 > max_sp:
        log.warn(f"Long spacing {12.0} in > ACI max {max_sp} in for {t} in slab")
    if 12.0 > max_sp:
        log.warn(f"Short spacing {12.0} in > ACI max {max_sp} in for {t} in slab")
    return []
