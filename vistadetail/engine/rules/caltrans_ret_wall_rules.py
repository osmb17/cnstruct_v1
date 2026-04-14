"""
Rule functions for Caltrans Retaining Wall Type 1 (B3-1A/B/C).

All bar sizes, spacings, and dimensions from Caltrans 2025 Standard Plans
B3-1 lookup tables. Design H drives every output.

Design basis:
  AASHTO LRFD 8th Ed w/ CA Amendments (Preface Apr 2019)
  f'c = 3,600 psi, fy = 60,000 psi
  Soil: gamma = 120 pcf, phi = 34 deg (backfill), phi = 32 deg (base friction)
  Seismic: kh = 0.2, kv = 0.0
  Cover: 2" stem, 3" footing

Marks:
  CW1 -- c-bars: primary vertical stem steel (tension side)
  CW2 -- a-bars: back face horizontal distribution (#5 @ 12)
  CW3 -- b-bars: front face horizontal distribution (#5 @ 12)
  CW4 -- d-bars: toe/heel transverse footing bars
  CW5 -- dowel bars at stem-footing construction joint
  CW6 -- shear key bars (optional)
  CW7 -- e-bars: transverse bars at expansion joints
  CW8 -- s-bars: secondary vertical (Zone 2, tall walls only)
"""

from __future__ import annotations

import math

from vistadetail.engine.reasoning_logger import ReasoningLogger
from vistadetail.engine.schema import BarRow, Params, fmt_inches


# ---------------------------------------------------------------------------
# Caltrans B3-1A Lookup Table (Case 1 -- level backfill, vertical ext face)
# ---------------------------------------------------------------------------
# Key = Design H (ft)
# Values: stem_thick_in, footing_W_in, footing_B_in (heel), footing_C_in (toe),
#         footing_F_in (depth), c_size, c_spacing, d_size, d_spacing,
#         s_size (Zone 2 secondary vert), s_spacing

_B3_1A_TABLE = {
    4:  {"T": 8,  "W": 42,  "B": 20, "C": 14, "F": 12, "c": "#4", "cS": 12, "d": "#4", "dS": 12, "s": None, "sS": None},
    6:  {"T": 8,  "W": 54,  "B": 30, "C": 16, "F": 12, "c": "#5", "cS": 12, "d": "#4", "dS": 12, "s": None, "sS": None},
    8:  {"T": 8,  "W": 66,  "B": 38, "C": 20, "F": 12, "c": "#5", "cS": 10, "d": "#5", "dS": 12, "s": None, "sS": None},
    10: {"T": 10, "W": 78,  "B": 46, "C": 22, "F": 15, "c": "#6", "cS": 10, "d": "#5", "dS": 10, "s": None, "sS": None},
    12: {"T": 10, "W": 96,  "B": 58, "C": 28, "F": 15, "c": "#6", "cS": 8,  "d": "#6", "dS": 10, "s": None, "sS": None},
    14: {"T": 12, "W": 114, "B": 68, "C": 34, "F": 18, "c": "#7", "cS": 8,  "d": "#6", "dS": 8,  "s": None, "sS": None},
    16: {"T": 12, "W": 126, "B": 76, "C": 38, "F": 18, "c": "#7", "cS": 6,  "d": "#7", "dS": 8,  "s": None, "sS": None},
    18: {"T": 14, "W": 144, "B": 88, "C": 42, "F": 21, "c": "#8", "cS": 6,  "d": "#7", "dS": 6,  "s": "#5", "sS": 12},
    20: {"T": 14, "W": 156, "B": 96, "C": 46, "F": 21, "c": "#8", "cS": 6,  "d": "#8", "dS": 6,  "s": "#5", "sS": 12},
    22: {"T": 16, "W": 174, "B": 106, "C": 52, "F": 24, "c": "#9", "cS": 6, "d": "#8", "dS": 6,  "s": "#5", "sS": 12},
    24: {"T": 16, "W": 186, "B": 114, "C": 56, "F": 24, "c": "#9", "cS": 6, "d": "#9", "dS": 6,  "s": "#5", "sS": 12},
    26: {"T": 18, "W": 204, "B": 124, "C": 62, "F": 27, "c": "#10","cS": 6, "d": "#9", "dS": 6,  "s": "#6", "sS": 12},
}

# Caltrans covers
_STEM_COVER = 2.0   # inches
_FTG_COVER = 3.0    # inches


def _snap_h(h_ft: float) -> int:
    """Snap design H to nearest Caltrans table row (even feet 4-26)."""
    h = round(h_ft)
    if h < 4:
        h = 4
    elif h > 26:
        h = 26
    # Round up to next even number
    if h % 2 != 0:
        h += 1
    return min(h, 26)


def _get_row(h_ft: float) -> dict:
    """Get the B3-1A table row for the given design height."""
    return _B3_1A_TABLE[_snap_h(h_ft)]


# ---------------------------------------------------------------------------
# CW1 -- c-bars: primary vertical stem steel (tension/soil side)
# ---------------------------------------------------------------------------

def rule_ct_rw_stem_vert(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """Primary vertical stem bars (c-bars) from B3-1A table."""
    row = _get_row(p.design_h_ft)
    h = _snap_h(p.design_h_ft)
    wall_len_in = p.wall_length_ft * 12.0

    c_size = row["c"]
    c_spacing = row["cS"]
    stem_ht_in = p.design_h_ft * 12.0
    stem_thick = row["T"]
    ftg_depth = row["F"]

    # Qty: spaced along wall length
    qty = math.floor((wall_len_in - 2 * _STEM_COVER) / c_spacing) + 1

    # Bar length: stem height + embed into footing (footing depth - cover)
    embed = ftg_depth - _FTG_COVER
    bar_len = stem_ht_in + embed

    log.step(
        f"B3-1A H={h}': c-bars = {c_size} @ {c_spacing}\" oc (primary vertical)",
        source="CaltransRetWallRules",
    )
    log.step(
        f"CW1: {qty} bars, length = {stem_ht_in:.0f} stem + {embed:.0f} embed = {fmt_inches(bar_len)}",
        source="CaltransRetWallRules",
    )

    bars = [BarRow(
        mark="CW1", size=c_size, qty=qty, length_in=bar_len,
        shape="Str", notes=f"c-bars primary vert @ {c_spacing}\" oc (B3-1A H={h}')",
        source_rule="rule_ct_rw_stem_vert",
    )]

    # s-bars: secondary vertical for Zone 2 (H >= 18')
    if row["s"] is not None:
        s_size = row["s"]
        s_spacing = row["sS"]
        s_qty = math.floor((wall_len_in - 2 * _STEM_COVER) / s_spacing) + 1
        # Zone 2 length: approximated as 60% of stem height.
        # Actual zone boundary varies by height per B3-1 plan sheet.
        s_len = stem_ht_in * 0.6

        log.step(
            f"CW8: s-bars = {s_size} @ {s_spacing}\" oc (Zone 2, H >= 18')",
            source="CaltransRetWallRules",
        )
        log.result("CW8", f"{s_size} x {s_qty} @ {fmt_inches(s_len)}",
                   source="CaltransRetWallRules")

        bars.append(BarRow(
            mark="CW8", size=s_size, qty=s_qty, length_in=s_len,
            shape="Str", notes=f"s-bars Zone 2 vert @ {s_spacing}\" oc (B3-1A)",
            source_rule="rule_ct_rw_stem_vert",
            review_flag="Zone 2 length uses 0.6×H approximation — verify against B3-1 plan sheet",
        ))

    log.result("CW1", f"{c_size} x {qty} @ {fmt_inches(bar_len)}",
               source="CaltransRetWallRules")

    return bars


# ---------------------------------------------------------------------------
# CW2/CW3 -- a-bars and b-bars: horizontal distribution steel
# ---------------------------------------------------------------------------

def rule_ct_rw_stem_horiz(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """Horizontal distribution bars: a-bars (back face) and b-bars (front face).
    Per B3-1: #5 @ 12 each face for all heights."""
    row = _get_row(p.design_h_ft)
    wall_len_in = p.wall_length_ft * 12.0
    stem_ht_in = p.design_h_ft * 12.0

    # Both a and b bars are #5 @ 12 per B3-1 typical section
    size = "#5"
    spacing = 12

    # Qty per face: bars spaced vertically up stem height
    qty_per_face = math.floor((stem_ht_in - 2 * _STEM_COVER) / spacing) + 1

    # Bar length: runs along wall length
    bar_len = wall_len_in - 2 * _STEM_COVER

    bars = []

    # CW2 -- a-bars (back/soil face)
    log.step(
        f"CW2 a-bars: {size} @ {spacing}\" oc, {qty_per_face} bars (back face)",
        source="CaltransRetWallRules",
    )
    log.result("CW2", f"{size} x {qty_per_face} @ {fmt_inches(bar_len)}",
               source="CaltransRetWallRules")

    bars.append(BarRow(
        mark="CW2", size=size, qty=qty_per_face, length_in=bar_len,
        shape="Str", notes="a-bars horiz back face @ 12\" oc (B3-1)",
        source_rule="rule_ct_rw_stem_horiz",
    ))

    # CW3 -- b-bars (front/exposed face)
    log.step(
        f"CW3 b-bars: {size} @ {spacing}\" oc, {qty_per_face} bars (front face)",
        source="CaltransRetWallRules",
    )
    log.result("CW3", f"{size} x {qty_per_face} @ {fmt_inches(bar_len)}",
               source="CaltransRetWallRules")

    bars.append(BarRow(
        mark="CW3", size=size, qty=qty_per_face, length_in=bar_len,
        shape="Str", notes="b-bars horiz front face @ 12\" oc (B3-1)",
        source_rule="rule_ct_rw_stem_horiz",
    ))

    return bars


# ---------------------------------------------------------------------------
# CW4 -- d-bars: toe/heel transverse footing bars
# ---------------------------------------------------------------------------

def rule_ct_rw_toe_heel(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """Footing transverse bars (d-bars) from B3-1A table.
    Toe bars (bottom) and heel bars (top) at same size/spacing."""
    row = _get_row(p.design_h_ft)
    h = _snap_h(p.design_h_ft)
    wall_len_in = p.wall_length_ft * 12.0

    d_size = row["d"]
    d_spacing = row["dS"]
    footing_W = row["W"]

    # Qty: spaced along wall length
    qty = math.floor((wall_len_in - 2 * _FTG_COVER) / d_spacing) + 1

    # Bar length: full footing width minus cover each side
    bar_len = footing_W - 2 * _FTG_COVER

    log.step(
        f"B3-1A H={h}': d-bars = {d_size} @ {d_spacing}\" oc, "
        f"footing W = {fmt_inches(footing_W)}",
        source="CaltransRetWallRules",
    )

    bars = []

    # Toe bars (bottom face)
    log.step(
        f"CW4-T: toe bars, {qty} @ {fmt_inches(bar_len)}",
        source="CaltransRetWallRules",
    )
    log.result("CW4", f"{d_size} x {qty} @ {fmt_inches(bar_len)} [toe+heel]",
               source="CaltransRetWallRules")

    bars.append(BarRow(
        mark="CW4", size=d_size, qty=qty, length_in=bar_len,
        shape="Str", notes=f"toe d-bars bot @ {d_spacing}\" oc (B3-1A)",
        source_rule="rule_ct_rw_toe_heel",
    ))

    # Heel bars (top face) -- same size/spacing
    bars.append(BarRow(
        mark="CW5", size=d_size, qty=qty, length_in=bar_len,
        shape="Str", notes=f"heel d-bars top @ {d_spacing}\" oc (B3-1A)",
        source_rule="rule_ct_rw_toe_heel",
    ))

    # Footing longitudinal: #5 Tot 4 at top of footing per B3-1
    long_len = wall_len_in - 2 * _FTG_COVER
    log.step("CW6: #5 Tot 4 footing longitudinal (B3-1)", source="CaltransRetWallRules")
    log.result("CW6", f"#5 x 4 @ {fmt_inches(long_len)}", source="CaltransRetWallRules")

    bars.append(BarRow(
        mark="CW6", size="#5", qty=4, length_in=long_len,
        shape="Str", notes="footing longitudinal #5 Tot 4 (B3-1)",
        source_rule="rule_ct_rw_toe_heel",
    ))

    return bars


# ---------------------------------------------------------------------------
# CW7 -- Dowels at stem-footing construction joint
# ---------------------------------------------------------------------------

def rule_ct_rw_dowels(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """Dowels at the stem-to-footing construction joint.
    Same size/spacing as c-bars, lap per Caltrans table."""
    row = _get_row(p.design_h_ft)
    h = _snap_h(p.design_h_ft)
    wall_len_in = p.wall_length_ft * 12.0

    c_size = row["c"]
    c_spacing = row["cS"]
    ftg_depth = row["F"]

    qty = math.floor((wall_len_in - 2 * _STEM_COVER) / c_spacing) + 1

    # Dowel: embed into footing + lap into stem
    # Caltrans specifies lap by H: H<=18' = 35db, H>=20' = 45db
    from vistadetail.engine.hooks import bar_diameter
    db = bar_diameter(c_size)
    if h <= 18:
        lap_db = 35
    else:
        lap_db = 45
    lap_in = math.ceil(lap_db * db)

    embed = ftg_depth - _FTG_COVER
    bar_len = embed + lap_in

    log.step(
        f"CW7 dowels: {c_size} @ {c_spacing}\" oc, "
        f"embed {embed:.0f}\" + {lap_db}db lap = {lap_in}\" = {fmt_inches(bar_len)}",
        source="CaltransRetWallRules",
    )
    log.result("CW7", f"{c_size} x {qty} @ {fmt_inches(bar_len)}",
               source="CaltransRetWallRules")

    return [BarRow(
        mark="CW7", size=c_size, qty=qty, length_in=bar_len,
        shape="Str", notes=f"stem-ftg dowels, {lap_db}db lap (B3-1)",
        source_rule="rule_ct_rw_dowels",
    )]


# ---------------------------------------------------------------------------
# CW9 -- Shear key bars (optional)
# ---------------------------------------------------------------------------

def rule_ct_rw_shear_key(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """Shear key U-bars if requested. Key depth per Caltrans table."""
    if p.shear_key != "yes":
        log.step("No shear key requested", source="CaltransRetWallRules")
        return []

    row = _get_row(p.design_h_ft)
    wall_len_in = p.wall_length_ft * 12.0
    d_size = row["d"]
    d_spacing = row["dS"]

    qty = math.floor((wall_len_in - 2 * _FTG_COVER) / d_spacing) + 1

    # Key depth: 1'-0" typical for all heights per B3-1
    key_depth = 12.0
    from vistadetail.engine.hooks import min_bend_diameter
    bend_d = min_bend_diameter(d_size)   # ACI 318-19 Table 25.3.1
    leg = key_depth - _FTG_COVER
    bar_len = 2 * leg + bend_d
    bar_len = max(bar_len, 12.0)

    log.step(
        f"CW9 shear key: {d_size} U-bars @ {d_spacing}\" oc, {qty} bars, "
        f"bend dia={bend_d:.2f}\"",
        source="CaltransRetWallRules",
    )
    log.result("CW9", f"{d_size} x {qty} @ {fmt_inches(bar_len)}",
               source="CaltransRetWallRules")

    return [BarRow(
        mark="CW9", size=d_size, qty=qty, length_in=bar_len,
        shape="U", leg_a_in=leg, leg_b_in=bend_d, leg_c_in=leg,
        notes=f"shear key U-bars @ {d_spacing}\" oc (B3-1)",
        source_rule="rule_ct_rw_shear_key",
    )]


# ---------------------------------------------------------------------------
# CW10 -- e-bars: transverse at expansion joints
# ---------------------------------------------------------------------------

def rule_ct_rw_e_bars(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """Transverse e-bars at expansion joints per B3-1 Note 5.
    #6 @ 10\" x 18'-0\" over 8'-0\" at each expansion joint."""
    h = _snap_h(p.design_h_ft)
    if h < 16:
        log.step("H < 16': e-bars not required per B3-1 Note 5", source="CaltransRetWallRules")
        return []

    wall_len_in = p.wall_length_ft * 12.0

    # Expansion joints at ~30'-0" centers for retaining walls
    n_joints = max(1, math.floor(p.wall_length_ft / 30.0))

    # At each joint: #6 @ 10" over 8'-0" (= 9 or 10 bars per joint)
    bars_per_joint = math.floor(96.0 / 10.0) + 1  # 8'-0" / 10" + 1 = 10
    qty = n_joints * bars_per_joint

    # Bar length: 18'-0" per B3-1 Note 5
    bar_len = 18.0 * 12.0  # 216 in

    log.step(
        f"CW10 e-bars: {n_joints} joints x {bars_per_joint} bars = {qty} @ {fmt_inches(bar_len)}",
        source="CaltransRetWallRules",
    )
    log.result("CW10", f"#6 x {qty} @ {fmt_inches(bar_len)}",
               source="CaltransRetWallRules")

    return [BarRow(
        mark="CW10", size="#6", qty=qty, length_in=bar_len,
        shape="Str", notes=f"e-bars transverse @ exp joints (B3-1 Note 5)",
        source_rule="rule_ct_rw_e_bars",
    )]


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def rule_validate_ct_rw(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """Validate inputs against B3-1 limits."""
    h = p.design_h_ft
    if h < 4:
        log.warn(f"Design H = {h}' < 4' minimum per B3-1", source="CaltransRetWallRules")
    if h > 26:
        log.warn(f"Design H = {h}' > 26' -- exceeds B3-1 table, special design required",
                 source="CaltransRetWallRules")
    if p.wall_case != "case_1":
        log.warn(
            f"Loading case '{p.wall_case}' selected -- currently using Case 1 tables. "
            "Cases 2/3 have different bar sizes; verify with B3-1B/C.",
            source="CaltransRetWallRules",
        )
    return []
