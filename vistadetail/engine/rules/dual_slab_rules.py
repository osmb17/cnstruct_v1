"""
Rule functions for Dual Slab template (AT&T / telecom equipment foundations).

Geometry: two adjacent rectangular slabs (Slab A and Slab B) drawn on a
single sheet, each with independent EW mat reinforcing.

Marks:
  A1 — Slab A long bars
  A2 — Slab A short bars
  B1 — Slab B long bars
  B2 — Slab B short bars

Formulas (same as flat slab / slab on grade):
  bar_length = span_dim_in - 2 × cover_in
  qty        = floor(perpendicular_dim_in / spacing_in)

Cover default: 3.0 in (cast against earth, ACI Table 20.6.1.3.1).

Covers 3 PDFs in the clean_examples set:
  2slab.at.and.t     — AT&T dual slab, 2 pages
  2slab.at.andt(A)   — AT&T slab variant A
  2slab.at.and.t(B)  — AT&T slab variant B
"""

from __future__ import annotations

import math

from vistadetail.engine.reasoning_logger import ReasoningLogger
from vistadetail.engine.schema import BarRow, Params, fmt_inches


def _slab_bars(p: Params, log: ReasoningLogger,
               length_ft: float, width_ft: float,
               spacing_in: float, bar_size: str, cover_in: float,
               long_mark: str, short_mark: str,
               source_rule_long: str, source_rule_short: str) -> list[BarRow]:
    """Shared helper: generate long + short bars for one slab."""
    len_in   = length_ft * 12
    wid_in   = width_ft  * 12

    long_len  = len_in - 2 * cover_in
    long_qty  = math.floor(wid_in / spacing_in)
    short_len = wid_in - 2 * cover_in
    short_qty = math.floor(len_in / spacing_in)

    bars = [
        BarRow(mark=long_mark,  size=bar_size, qty=long_qty,  length_in=long_len,
               shape="Str", notes=f"@{int(spacing_in)}oc EW", source_rule=source_rule_long),
        BarRow(mark=short_mark, size=bar_size, qty=short_qty, length_in=short_len,
               shape="Str", notes=f"@{int(spacing_in)}oc EW", source_rule=source_rule_short),
    ]
    for b in bars:
        label = "long" if b.mark == long_mark else "short"
        log.result(b.mark, f"{b.size} × {b.qty} @ {fmt_inches(b.length_in)} [{label}]",
                   detail=f"slab {long_mark[0]} {label} bars", source="DualSlabRules")
    return bars


def rule_dual_slab_A_long(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """Slab A long bars (A1): length = slab_a_length_in − 2c; qty = floor(width/spacing)."""
    len_in  = p.slab_a_length_ft * 12
    wid_in  = p.slab_a_width_ft  * 12
    bar_len = len_in - 2 * p.cover_in
    qty     = math.floor(wid_in / p.slab_a_spacing_in)
    log.step(
        f"Slab A long (A1): {len_in:.1f} − 2×{p.cover_in} = {bar_len:.1f} in"
        f" = {fmt_inches(bar_len)},  qty = ⌊{wid_in:.1f}/{p.slab_a_spacing_in}⌋ = {qty}",
        detail="slab_a long bars", source="DualSlabRules",
    )
    return [BarRow(mark="A1", size=p.slab_a_bar_size, qty=qty, length_in=bar_len,
                   shape="Str", notes=f"@{int(p.slab_a_spacing_in)}oc EW",
                   source_rule="rule_dual_slab_A_long")]


def rule_dual_slab_A_short(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """Slab A short bars (A2): length = slab_a_width_in − 2c; qty = floor(length/spacing)."""
    len_in  = p.slab_a_length_ft * 12
    wid_in  = p.slab_a_width_ft  * 12
    bar_len = wid_in - 2 * p.cover_in
    qty     = math.floor(len_in / p.slab_a_spacing_in)
    log.step(
        f"Slab A short (A2): {wid_in:.1f} − 2×{p.cover_in} = {bar_len:.1f} in"
        f" = {fmt_inches(bar_len)},  qty = ⌊{len_in:.1f}/{p.slab_a_spacing_in}⌋ = {qty}",
        detail="slab_a short bars", source="DualSlabRules",
    )
    return [BarRow(mark="A2", size=p.slab_a_bar_size, qty=qty, length_in=bar_len,
                   shape="Str", notes=f"@{int(p.slab_a_spacing_in)}oc EW",
                   source_rule="rule_dual_slab_A_short")]


def rule_dual_slab_B_long(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """Slab B long bars (B1): length = slab_b_length_in − 2c; qty = floor(width/spacing)."""
    len_in  = p.slab_b_length_ft * 12
    wid_in  = p.slab_b_width_ft  * 12
    bar_len = len_in - 2 * p.cover_in
    qty     = math.floor(wid_in / p.slab_b_spacing_in)
    log.step(
        f"Slab B long (B1): {len_in:.1f} − 2×{p.cover_in} = {bar_len:.1f} in"
        f" = {fmt_inches(bar_len)},  qty = ⌊{wid_in:.1f}/{p.slab_b_spacing_in}⌋ = {qty}",
        detail="slab_b long bars", source="DualSlabRules",
    )
    return [BarRow(mark="B1", size=p.slab_b_bar_size, qty=qty, length_in=bar_len,
                   shape="Str", notes=f"@{int(p.slab_b_spacing_in)}oc EW",
                   source_rule="rule_dual_slab_B_long")]


def rule_dual_slab_B_short(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """Slab B short bars (B2): length = slab_b_width_in − 2c; qty = floor(length/spacing)."""
    len_in  = p.slab_b_length_ft * 12
    wid_in  = p.slab_b_width_ft  * 12
    bar_len = wid_in - 2 * p.cover_in
    qty     = math.floor(len_in / p.slab_b_spacing_in)
    log.step(
        f"Slab B short (B2): {wid_in:.1f} − 2×{p.cover_in} = {bar_len:.1f} in"
        f" = {fmt_inches(bar_len)},  qty = ⌊{len_in:.1f}/{p.slab_b_spacing_in}⌋ = {qty}",
        detail="slab_b short bars", source="DualSlabRules",
    )
    return [BarRow(mark="B2", size=p.slab_b_bar_size, qty=qty, length_in=bar_len,
                   shape="Str", notes=f"@{int(p.slab_b_spacing_in)}oc EW",
                   source_rule="rule_dual_slab_B_short")]


def rule_validate_dual_slab(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """Basic validation checks for dual slab template."""
    for label, spacing in [("A", p.slab_a_spacing_in), ("B", p.slab_b_spacing_in)]:
        if spacing > 18.0:
            log.warn(f"Slab {label} spacing {spacing} in > 18 in max (ACI 318-19 §26.4.1)",
                     detail="ACI 318-19 §26.4.1: s ≤ min(2t, 18 in)", source="Validator")
        else:
            log.ok(f"Slab {label} spacing {spacing} in ≤ 18 in  [ACI §26.4.1]",
                   detail="ACI 318-19 §26.4.1", source="Validator")

    if p.cover_in < 3.0:
        log.warn(
            f"Cover {p.cover_in} in < 3.0 in — cast-against-earth minimum (ACI Table 20.6.1.3.1)",
            detail="ACI 318-19 Table 20.6.1.3.1: ≥ 3 in, concrete cast against and exposed to earth",
            source="Validator",
        )
    else:
        log.ok(f"Cover {p.cover_in} in ≥ 3.0 in  [ACI Table 20.6.1.3.1]",
               detail="ACI 318-19 Table 20.6.1.3.1", source="Validator")

    return []
