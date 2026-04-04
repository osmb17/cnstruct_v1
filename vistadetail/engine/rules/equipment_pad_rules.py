"""
Rule functions for Equipment / Concrete Pad template.

Geometry: rectangular concrete equipment pad (SOG variant) with 3 in cover
cast against earth (ACI 318-19 Table 20.6.1.3.1).

Supports single mat and double mat configurations:
  Single mat: P1 (bottom long) + P2 (bottom short)
  Double mat:  P1 (bottom long) + P2 (bottom short)
              + P3 (top long)   + P4 (top short)

Formulas (ACI 318-19 / ACI 360R-10):
  bar_length = span_dim_in - 2 × cover_in
  qty        = floor(perpendicular_dim_in / spacing_in)

Cover default: 3.0 in — concrete cast against and permanently exposed to earth
               (ACI 318-19 Table 20.6.1.3.1, row "cast against and exposed to earth").

Verified against:
  PDF 1 (1.s3.concrete.pad.plans.pdf):    8'-6"×4'-1", 6" thick, #4@12oc, single mat, 3" cover
  PDF 2 (example.equipementfloor.detail): 43'-1"×24'-8.25", 12" thick, #4 typ, double mat, 3" cover
  PDF 3 (transformerpad.doublemat):       4'-4"×4'-0", double mat explicit
"""

from __future__ import annotations

import math

from vistadetail.engine.reasoning_logger import ReasoningLogger
from vistadetail.engine.schema import BarRow, Params, fmt_inches


# ---------------------------------------------------------------------------
# P1 — bottom mat, bars spanning the LONG direction
# ---------------------------------------------------------------------------

def rule_pad_bottom_long(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Straight bars spanning the long dimension of the pad, bottom mat.

    Length = pad_length_in - 2 × cover_in
    Qty    = floor(pad_width_in / spacing_in)
    Mark   = P1
    """
    len_in  = p.pad_length_ft * 12
    wid_in  = p.pad_width_ft  * 12
    bar_len = len_in - 2 * p.cover_in
    qty     = math.floor(wid_in / p.spacing_in)

    label = "bottom " if bool(p.has_double_mat) else ""

    log.step(
        f"Long bars P1 ({label}mat): {len_in:.2f} − 2×{p.cover_in} cover = {bar_len:.2f} in"
        f" = {fmt_inches(bar_len)}",
        detail="pad_length_ft×12 − 2×cover_in",
        source="EquipmentPadRules",
    )
    log.step(
        f"Qty P1 = ⌊{wid_in:.2f} ÷ {p.spacing_in}⌋ = {qty}",
        detail="floor(pad_width_in / spacing_in)",
        source="EquipmentPadRules",
    )
    log.result("P1", f"{p.bar_size} × {qty} @ {fmt_inches(bar_len)} [{label}mat long EW]",
               detail="pad long-direction bars, bottom", source="EquipmentPadRules")

    return [BarRow(
        mark="P1",
        size=p.bar_size,
        qty=qty,
        length_in=bar_len,
        shape="Str",
        notes=f"@{int(p.spacing_in)}oc EW {label.strip() or 'mat'}",
        source_rule="rule_pad_bottom_long",
    )]


# ---------------------------------------------------------------------------
# P2 — bottom mat, bars spanning the SHORT direction
# ---------------------------------------------------------------------------

def rule_pad_bottom_short(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Straight bars spanning the short dimension of the pad, bottom mat.

    Length = pad_width_in - 2 × cover_in
    Qty    = floor(pad_length_in / spacing_in)
    Mark   = P2
    """
    len_in  = p.pad_length_ft * 12
    wid_in  = p.pad_width_ft  * 12
    bar_len = wid_in - 2 * p.cover_in
    qty     = math.floor(len_in / p.spacing_in)

    label = "bottom " if bool(p.has_double_mat) else ""

    log.step(
        f"Short bars P2 ({label}mat): {wid_in:.2f} − 2×{p.cover_in} cover = {bar_len:.2f} in"
        f" = {fmt_inches(bar_len)}",
        detail="pad_width_ft×12 − 2×cover_in",
        source="EquipmentPadRules",
    )
    log.step(
        f"Qty P2 = ⌊{len_in:.2f} ÷ {p.spacing_in}⌋ = {qty}",
        detail="floor(pad_length_in / spacing_in)",
        source="EquipmentPadRules",
    )
    log.result("P2", f"{p.bar_size} × {qty} @ {fmt_inches(bar_len)} [{label}mat short EW]",
               detail="pad short-direction bars, bottom", source="EquipmentPadRules")

    return [BarRow(
        mark="P2",
        size=p.bar_size,
        qty=qty,
        length_in=bar_len,
        shape="Str",
        notes=f"@{int(p.spacing_in)}oc EW {label.strip() or 'mat'}",
        source_rule="rule_pad_bottom_short",
    )]


# ---------------------------------------------------------------------------
# P3 — top mat, bars spanning the LONG direction (double-mat only)
# ---------------------------------------------------------------------------

def rule_pad_top_long(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Straight bars spanning the long dimension of the pad, top mat.
    Only generated when has_double_mat = True.

    Length = pad_length_in - 2 × cover_in
    Qty    = floor(pad_width_in / top_spacing_in)
    Mark   = P3
    """
    if not bool(p.has_double_mat):
        log.step("Single mat only — P3 top long bars skipped",
                 detail="has_double_mat = False", source="EquipmentPadRules")
        return []

    len_in  = p.pad_length_ft * 12
    wid_in  = p.pad_width_ft  * 12
    bar_len = len_in - 2 * p.cover_in
    qty     = math.floor(wid_in / p.top_spacing_in)

    log.step(
        f"Long bars P3 (top mat): {len_in:.2f} − 2×{p.cover_in} cover = {bar_len:.2f} in"
        f" = {fmt_inches(bar_len)}",
        detail="pad_length_ft×12 − 2×cover_in",
        source="EquipmentPadRules",
    )
    log.step(
        f"Qty P3 = ⌊{wid_in:.2f} ÷ {p.top_spacing_in}⌋ = {qty}",
        detail="floor(pad_width_in / top_spacing_in)",
        source="EquipmentPadRules",
    )
    log.result("P3", f"{p.top_bar_size} × {qty} @ {fmt_inches(bar_len)} [top mat long EW]",
               detail="pad long-direction bars, top", source="EquipmentPadRules")

    return [BarRow(
        mark="P3",
        size=p.top_bar_size,
        qty=qty,
        length_in=bar_len,
        shape="Str",
        notes=f"@{int(p.top_spacing_in)}oc EW top mat",
        source_rule="rule_pad_top_long",
    )]


# ---------------------------------------------------------------------------
# P4 — top mat, bars spanning the SHORT direction (double-mat only)
# ---------------------------------------------------------------------------

def rule_pad_top_short(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Straight bars spanning the short dimension of the pad, top mat.
    Only generated when has_double_mat = True.

    Length = pad_width_in - 2 × cover_in
    Qty    = floor(pad_length_in / top_spacing_in)
    Mark   = P4
    """
    if not bool(p.has_double_mat):
        log.step("Single mat only — P4 top short bars skipped",
                 detail="has_double_mat = False", source="EquipmentPadRules")
        return []

    len_in  = p.pad_length_ft * 12
    wid_in  = p.pad_width_ft  * 12
    bar_len = wid_in - 2 * p.cover_in
    qty     = math.floor(len_in / p.top_spacing_in)

    log.step(
        f"Short bars P4 (top mat): {wid_in:.2f} − 2×{p.cover_in} cover = {bar_len:.2f} in"
        f" = {fmt_inches(bar_len)}",
        detail="pad_width_ft×12 − 2×cover_in",
        source="EquipmentPadRules",
    )
    log.step(
        f"Qty P4 = ⌊{len_in:.2f} ÷ {p.top_spacing_in}⌋ = {qty}",
        detail="floor(pad_length_in / top_spacing_in)",
        source="EquipmentPadRules",
    )
    log.result("P4", f"{p.top_bar_size} × {qty} @ {fmt_inches(bar_len)} [top mat short EW]",
               detail="pad short-direction bars, top", source="EquipmentPadRules")

    return [BarRow(
        mark="P4",
        size=p.top_bar_size,
        qty=qty,
        length_in=bar_len,
        shape="Str",
        notes=f"@{int(p.top_spacing_in)}oc EW top mat",
        source_rule="rule_pad_top_short",
    )]


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def rule_validate_equipment_pad(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    ACI 318-19 checks for equipment/concrete pad:
      - Bar spacing ≤ 18 in (§26.4.1)
      - Cover ≥ 3.0 in for concrete cast against earth (Table 20.6.1.3.1)
      - Thickness sanity (warn if < 5 in for equipment pads)
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

    if p.cover_in < 3.0:
        log.warn(
            f"Cover {p.cover_in} in < 3.0 in minimum for cast-against-earth (ACI Table 20.6.1.3.1)",
            detail="ACI 318-19 Table 20.6.1.3.1: ≥ 3 in, concrete cast against and exposed to earth",
            source="Validator",
        )
    else:
        log.ok(
            f"Cover {p.cover_in} in ≥ 3.0 in  [ACI Table 20.6.1.3.1 cast-against-earth]",
            detail="ACI 318-19 Table 20.6.1.3.1", source="Validator",
        )

    if p.pad_thickness_in < 5.0:
        log.warn(
            f"Pad thickness {p.pad_thickness_in} in < 5 in — verify adequacy for equipment loading",
            detail="Equipment pads typically 6 in minimum for light to moderate loads",
            source="Validator",
        )
    else:
        log.ok(
            f"Pad thickness {p.pad_thickness_in} in  [equipment pad]",
            detail="Equipment pad thickness", source="Validator",
        )

    if bool(p.has_double_mat):
        net_depth = p.pad_thickness_in - 2 * p.cover_in
        if net_depth < 2.0:
            log.warn(
                f"Net depth between mats = {net_depth:.2f} in — pad may be too thin for double mat",
                detail="thickness − 2×cover must leave room for both mats",
                source="Validator",
            )
        else:
            log.ok(
                f"Net depth for double mat = {net_depth:.2f} in  [OK]",
                detail="pad_thickness − 2×cover", source="Validator",
            )

    return []


# ---------------------------------------------------------------------------
# D1 — vertical dowels projecting above the pad  (switchboard / anchor grid)
# ---------------------------------------------------------------------------

def rule_pad_vertical_dowels(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Grid of vertical dowels projecting above the top of the pad to anchor
    equipment bases (switchboard panels, transformer frames, etc.).

    Only generated when has_vertical_dowels = True.

    Geometry:
      Total length  = dowel_embed_in + dowel_project_in
      Grid qty      = floor(pad_length_in / dowel_spacing_in)
                    × floor(pad_width_in  / dowel_spacing_in)
    Mark: D1

    ACI ref: ACI 318-19 §25.5.2 (development length, tension); typical embed
             ≥ 12 in (min development) for #4-#5; projection per equipment spec.
    """
    if not bool(p.has_vertical_dowels):
        log.step("No vertical dowels — D1 skipped",
                 detail="has_vertical_dowels = False", source="EquipmentPadRules")
        return []

    len_in     = p.pad_length_ft * 12
    wid_in     = p.pad_width_ft  * 12
    bar_len    = p.dowel_embed_in + p.dowel_project_in
    qty_long   = math.floor(len_in / p.dowel_spacing_in)
    qty_short  = math.floor(wid_in / p.dowel_spacing_in)
    qty        = max(1, qty_long * qty_short)

    log.step(
        f"Vertical dowels D1: embed {p.dowel_embed_in} in + project {p.dowel_project_in} in"
        f" = {bar_len} in = {fmt_inches(bar_len)}",
        detail="dowel_embed_in + dowel_project_in",
        source="EquipmentPadRules",
    )
    log.step(
        f"Qty D1 = ⌊{len_in:.1f}/{p.dowel_spacing_in}⌋ × ⌊{wid_in:.1f}/{p.dowel_spacing_in}⌋"
        f" = {qty_long} × {qty_short} = {qty}",
        detail="floor(L/ds) × floor(W/ds)",
        source="EquipmentPadRules",
    )
    log.result("D1", f"{p.dowel_bar_size} × {qty} @ {fmt_inches(bar_len)} [vert dowels]",
               detail="vertical equipment anchor dowels — grid", source="EquipmentPadRules")

    return [BarRow(
        mark="D1",
        size=p.dowel_bar_size,
        qty=qty,
        length_in=bar_len,
        shape="Str",
        notes=f"vert dowel grid @{int(p.dowel_spacing_in)}oc — embed {int(p.dowel_embed_in)}in + proj {int(p.dowel_project_in)}in",
        source_rule="rule_pad_vertical_dowels",
    )]
