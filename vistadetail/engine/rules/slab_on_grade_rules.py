"""
Rule functions for Slab on Grade template.

Geometry: rectangular concrete slab placed directly on compacted subgrade.
Single reinforcing mat (unless double-mat variant requested).

Verified formula (same as flat slab, ACI 360R):
  qty  = floor(perpendicular_dim_in / spacing_in)
  len  = span_dim_in - 2 × cover_in

Cover default: 1.5 in (finished surface, ACI 318-19 Table 20.6.1.3.1 — #5 and smaller,
               not exposed to weather and not cast against earth)

Marks:
  G1 — bars spanning the LONG direction  (qty from width)
  G2 — bars spanning the SHORT direction (qty from length)
  G3 — perimeter edge bars (optional; used when thickened edge / haunch is present)

Examples (derived from filenames — gold CSVs pending):
  20'×10' @12oc #4 1.5in cover:
    G1: qty=⌊120/12⌋=10 @ 20'-0"-3"=19'-9" → 10@237in
    G2: qty=⌊240/12⌋=20 @ 10'-0"-3"=9'-9"  → 20@117in
"""

from __future__ import annotations

import math

from vistadetail.engine.reasoning_logger import ReasoningLogger
from vistadetail.engine.schema import BarRow, Params, fmt_inches


# ---------------------------------------------------------------------------
# G1 — bars spanning the LONG way
# ---------------------------------------------------------------------------

def rule_sog_long_bars(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Straight bars spanning the long dimension of the slab.

    Length = slab_length_in - 2 × cover_in
    Qty    = floor(slab_width_in / spacing_in)
    Mark   = G1
    """
    len_in  = p.slab_length_ft * 12
    wid_in  = p.slab_width_ft  * 12
    bar_len = len_in - 2 * p.cover_in
    qty     = math.floor(wid_in / p.spacing_in)

    log.step(
        f"Long bars (G1): {len_in:.2f} − 2×{p.cover_in} cover = {bar_len:.2f} in"
        f" = {fmt_inches(bar_len)}",
        detail="slab_length_ft×12 − 2×cover_in",
        source="SlabOnGradeRules",
    )
    log.step(
        f"Qty G1 = ⌊{wid_in:.2f} ÷ {p.spacing_in}⌋ = {qty}",
        detail="floor(slab_width_in / spacing_in)",
        source="SlabOnGradeRules",
    )
    log.result("G1", f"{p.bar_size} × {qty} @ {fmt_inches(bar_len)} [long EW]",
               detail="slab long-direction bars", source="SlabOnGradeRules")

    return [BarRow(
        mark="G1",
        size=p.bar_size,
        qty=qty,
        length_in=bar_len,
        shape="Str",
        notes=f"@{int(p.spacing_in)}oc EW",
        source_rule="rule_sog_long_bars",
    )]


# ---------------------------------------------------------------------------
# G2 — bars spanning the SHORT way
# ---------------------------------------------------------------------------

def rule_sog_short_bars(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Straight bars spanning the short dimension of the slab.

    Length = slab_width_in - 2 × cover_in
    Qty    = floor(slab_length_in / spacing_in)
    Mark   = G2
    """
    len_in  = p.slab_length_ft * 12
    wid_in  = p.slab_width_ft  * 12
    bar_len = wid_in - 2 * p.cover_in
    qty     = math.floor(len_in / p.spacing_in)

    log.step(
        f"Short bars (G2): {wid_in:.2f} − 2×{p.cover_in} cover = {bar_len:.2f} in"
        f" = {fmt_inches(bar_len)}",
        detail="slab_width_ft×12 − 2×cover_in",
        source="SlabOnGradeRules",
    )
    log.step(
        f"Qty G2 = ⌊{len_in:.2f} ÷ {p.spacing_in}⌋ = {qty}",
        detail="floor(slab_length_in / spacing_in)",
        source="SlabOnGradeRules",
    )
    log.result("G2", f"{p.bar_size} × {qty} @ {fmt_inches(bar_len)} [short EW]",
               detail="slab short-direction bars", source="SlabOnGradeRules")

    return [BarRow(
        mark="G2",
        size=p.bar_size,
        qty=qty,
        length_in=bar_len,
        shape="Str",
        notes=f"@{int(p.spacing_in)}oc EW",
        source_rule="rule_sog_short_bars",
    )]


# ---------------------------------------------------------------------------
# G3 — perimeter / thickened-edge bars (optional)
# ---------------------------------------------------------------------------

def rule_sog_edge_bars(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Straight bars placed in a thickened perimeter edge beam.

    Runs along all four sides.  Two sides run the long way (length), two the short way.
    Total bars = edge_bars_per_side × 4 sides, but we split into two marks:
      G3-L: long-side edge bars  (qty = 2 sides × edge_bars_per_side)
      ...merged into one G3 row with total qty and longest bar length for simplicity.

    Only generated when has_edge_beam = True.
    """
    if not bool(p.has_edge_beam):
        log.step("No thickened edge beam — G3 skipped",
                 detail="has_edge_beam = False", source="SlabOnGradeRules")
        return []

    len_in    = p.slab_length_ft * 12
    wid_in    = p.slab_width_ft  * 12
    n_per     = int(p.edge_bars_per_side)

    # Long-side edge bars
    long_len  = len_in - 2 * p.cover_in
    long_qty  = 2 * n_per   # two long sides

    # Short-side edge bars
    short_len = wid_in - 2 * p.cover_in
    short_qty = 2 * n_per   # two short sides

    log.step(
        f"Edge bars (G3): {n_per} bars/side × 4 sides = {long_qty + short_qty} total",
        detail=f"2×{n_per} long @ {fmt_inches(long_len)}, 2×{n_per} short @ {fmt_inches(short_len)}",
        source="SlabOnGradeRules",
    )
    log.result("G3", f"{p.edge_bar_size} edge bars — {long_qty}@{fmt_inches(long_len)}"
               f" + {short_qty}@{fmt_inches(short_len)}",
               detail="perimeter thickened edge", source="SlabOnGradeRules")

    bars = []
    if long_qty > 0:
        bars.append(BarRow(
            mark="G3",
            size=p.edge_bar_size,
            qty=long_qty,
            length_in=long_len,
            shape="Str",
            notes="thickened edge — long sides",
            source_rule="rule_sog_edge_bars",
        ))
    if short_qty > 0:
        bars.append(BarRow(
            mark="G3",
            size=p.edge_bar_size,
            qty=short_qty,
            length_in=short_len,
            shape="Str",
            notes="thickened edge — short sides",
            source_rule="rule_sog_edge_bars",
        ))
    return bars


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def rule_validate_sog(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    ACI 360R-10 / ACI 318-19 checks for slab on grade:
      - Bar spacing ≤ 18 in (§26.4.1)
      - Cover ≥ 1.5 in for bars not exposed to weather (Table 20.6.1.3.1)
      - Slab thickness sanity (warn if < 4 in)
    """
    if p.spacing_in > 18.0:
        log.warn(
            f"Spacing {p.spacing_in} in > 18 in max (ACI 318-19 §26.4.1)",
            detail="ACI 318-19 §26.4.1: s ≤ min(2t, 18 in)",
            source="Validator",
        )
    else:
        log.ok(
            f"Spacing {p.spacing_in} in ≤ 18 in  [ACI 318-19 §26.4.1]",
            detail="ACI 318-19 §26.4.1", source="Validator",
        )

    if p.cover_in < 1.5:
        log.warn(
            f"Cover {p.cover_in} in < 1.5 in minimum (ACI Table 20.6.1.3.1)",
            detail="ACI 318-19 Table 20.6.1.3.1: ≥ 1.5 in, not exposed to weather",
            source="Validator",
        )
    else:
        log.ok(
            f"Cover {p.cover_in} in ≥ 1.5 in  [ACI Table 20.6.1.3.1]",
            detail="ACI 318-19 Table 20.6.1.3.1", source="Validator",
        )

    if p.slab_thickness_in < 4.0:
        log.warn(
            f"Slab thickness {p.slab_thickness_in} in < 4 in — verify design",
            detail="ACI 360R-10: minimum practical SOG thickness is 4 in",
            source="Validator",
        )
    else:
        log.ok(
            f"Slab thickness {p.slab_thickness_in} in  [ACI 360R-10]",
            detail="ACI 360R-10 slab on grade", source="Validator",
        )

    return []
