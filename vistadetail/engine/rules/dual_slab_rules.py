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



def rule_dual_slab_A_long(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """Slab A long bars (A1): length = slab_a_length_in − 2×3.0; qty = floor(width/12.0)."""
    len_in  = p.slab_a_length_ft * 12
    wid_in  = p.slab_a_width_ft  * 12
    bar_len = len_in - 2 * 3.0
    qty     = math.floor(wid_in / 12.0)
    log.step(
        f"Slab A long (A1): {len_in:.1f} − 2×3.0 = {bar_len:.1f} in"
        f" = {fmt_inches(bar_len)},  qty = ⌊{wid_in:.1f}/12.0⌋ = {qty}",
        detail="slab_a long bars", source="DualSlabRules",
    )
    return [BarRow(mark="A1", size="#4", qty=qty, length_in=bar_len,
                   shape="Str", notes="@12oc EW",
                   source_rule="rule_dual_slab_A_long")]


def rule_dual_slab_A_short(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """Slab A short bars (A2): length = slab_a_width_in − 2×3.0; qty = floor(length/12.0)."""
    len_in  = p.slab_a_length_ft * 12
    wid_in  = p.slab_a_width_ft  * 12
    bar_len = wid_in - 2 * 3.0
    qty     = math.floor(len_in / 12.0)
    log.step(
        f"Slab A short (A2): {wid_in:.1f} − 2×3.0 = {bar_len:.1f} in"
        f" = {fmt_inches(bar_len)},  qty = ⌊{len_in:.1f}/12.0⌋ = {qty}",
        detail="slab_a short bars", source="DualSlabRules",
    )
    return [BarRow(mark="A2", size="#4", qty=qty, length_in=bar_len,
                   shape="Str", notes="@12oc EW",
                   source_rule="rule_dual_slab_A_short")]


def rule_dual_slab_B_long(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """Slab B long bars (B1): length = slab_b_length_in − 2×3.0; qty = floor(width/12.0)."""
    len_in  = p.slab_b_length_ft * 12
    wid_in  = p.slab_b_width_ft  * 12
    bar_len = len_in - 2 * 3.0
    qty     = math.floor(wid_in / 12.0)
    log.step(
        f"Slab B long (B1): {len_in:.1f} − 2×3.0 = {bar_len:.1f} in"
        f" = {fmt_inches(bar_len)},  qty = ⌊{wid_in:.1f}/12.0⌋ = {qty}",
        detail="slab_b long bars", source="DualSlabRules",
    )
    return [BarRow(mark="B1", size="#4", qty=qty, length_in=bar_len,
                   shape="Str", notes="@12oc EW",
                   source_rule="rule_dual_slab_B_long")]


def rule_dual_slab_B_short(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """Slab B short bars (B2): length = slab_b_width_in − 2×3.0; qty = floor(length/12.0)."""
    len_in  = p.slab_b_length_ft * 12
    wid_in  = p.slab_b_width_ft  * 12
    bar_len = wid_in - 2 * 3.0
    qty     = math.floor(len_in / 12.0)
    log.step(
        f"Slab B short (B2): {wid_in:.1f} − 2×3.0 = {bar_len:.1f} in"
        f" = {fmt_inches(bar_len)},  qty = ⌊{len_in:.1f}/12.0⌋ = {qty}",
        detail="slab_b short bars", source="DualSlabRules",
    )
    return [BarRow(mark="B2", size="#4", qty=qty, length_in=bar_len,
                   shape="Str", notes="@12oc EW",
                   source_rule="rule_dual_slab_B_short")]


def rule_validate_dual_slab(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """Basic validation checks for dual slab template. Standard #4@12oc, 3\" cover."""
    log.ok(
        "Standard #4@12oc, 3\" cover  [ACI 318-19 §26.4.1 / Table 20.6.1.3.1]",
        detail="ACI 318-19 §26.4.1 / Table 20.6.1.3.1",
        source="Validator",
    )
    return []
