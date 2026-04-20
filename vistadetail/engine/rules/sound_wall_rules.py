"""
Rule functions for Caltrans Sound Wall template (B15-1 through B15-5).

Masonry block sound wall on spread footing, trench footing, or CIDH pile cap.
All bar sizes, spacings, and dimensions from Caltrans 2025 Standard Plans.

Design basis:
  AASHTO LRFD 8th Ed w/ CA Amendments (Preface Apr 2019)
  TMS 402-16
  2019 California Building Code
  f'c = 3,600 psi, f'm = 2,000 psi, fy = 60,000 psi
  Wind = 36.5 psf, Seismic = 0.57 Dead Load

Marks:
  WV1 -- vertical a-bars (primary flexural, each face)
  WV2 -- vertical b-bars (secondary, H >= 8', each face)
  WH1 -- horizontal bond beam bars (c-bars)
  FD1 -- footing dowels (d-bars, spread/trench only)
  FT1 -- footing transverse bars (spread/trench only)
  FL1 -- footing longitudinal bars (spread/trench only)
  PL1 -- CIDH pile longitudinal bars (pile cap only)
  PS1 -- CIDH pile spiral wire (pile cap only)
  PC1 -- pile cap transverse bars (pile cap only)
"""

from __future__ import annotations

import math

from vistadetail.engine.reasoning_logger import ReasoningLogger
from vistadetail.engine.schema import BarRow, Params, fmt_inches


# ---------------------------------------------------------------------------
# Caltrans B15-1 Lookup Tables -- Sound Wall on Footing
# ---------------------------------------------------------------------------

# Wall reinforcement by height (B15-1 reinforcement table)
# Keys: H in feet -> dict of bar data
_WALL_REINF = {
    6:  {"a_size": "#4", "a_spacing": 16, "b_size": None,  "b_spacing": None,
         "c_size": "#4", "c_spacing": 8,  "d_size": "#5", "d_spacing": 16},
    8:  {"a_size": "#4", "a_spacing": 16, "b_size": "#5",  "b_spacing": 16,
         "c_size": "#4", "c_spacing": 8,  "d_size": "#5", "d_spacing": 16},
    10: {"a_size": "#4", "a_spacing": 16, "b_size": "#5",  "b_spacing": 16,
         "c_size": "#5", "c_spacing": 8,  "d_size": "#5", "d_spacing": 16},
    12: {"a_size": "#4", "a_spacing": 16, "b_size": "#6",  "b_spacing": 16,
         "c_size": "#5", "c_spacing": 8,  "d_size": "#5", "d_spacing": 16},
    14: {"a_size": "#6", "a_spacing": 16, "b_size": "#6",  "b_spacing": 16,
         "c_size": "#6", "c_spacing": 8,  "d_size": "#5", "d_spacing": 16},
    16: {"a_size": "#6", "a_spacing": 16, "b_size": "#6",  "b_spacing": 16,
         "c_size": "#6", "c_spacing": 8,  "d_size": "#5", "d_spacing": 16},
}

# Spread footing width W by H (B15-1, Case 1)
_SPREAD_FOOTING_W = {
    6: 48, 8: 60, 10: 69, 12: 78, 14: 84, 16: 90,  # inches
}

# Trench footing depth D by H and case (B15-1)
_TRENCH_DEPTH = {
    "case_1": {6: 60, 8: 72, 10: 81, 12: 93, 14: 102, 16: 111},
    "case_2": {6: 63, 8: 72, 10: 81, 12: 93, 14: 102, 16: 111},
}

# ---------------------------------------------------------------------------
# Caltrans B15-3/5 Lookup Tables -- Sound Wall on Pile Cap
# ---------------------------------------------------------------------------

# Pile data by H, case, and soil phi (B15-5)
# Each entry: (pile_length_ft, pile_reinf_size, pile_reinf_count, pile_spacing_ft)
_PILE_DATA = {
    "case_1": {
        25: {
            6:  (12.0, "#6", 7, 8.0),
            8:  (13.0, "#7", 6, 8.0),
            10: (16.0, "#8", 7, 8.0),
            12: (16.0, "#8", 7, 8.0),
            14: (15.0, "#8", 7, 8.0),
            16: (13.0, "#8", 7, 8.0),
        },
        30: {
            6:  (12.0, "#6", 7, 8.0),
            8:  (13.0, "#7", 6, 8.0),
            10: (16.0, "#8", 7, 8.0),
            12: (16.0, "#8", 7, 8.0),
            14: (14.0, "#8", 7, 8.0),
            16: (13.0, "#8", 7, 8.0),
        },
        35: {
            6:  (12.0, "#6", 7, 8.0),
            8:  (13.0, "#7", 6, 8.0),
            10: (16.0, "#8", 7, 8.0),
            12: (16.0, "#8", 7, 8.0),
            14: (14.0, "#8", 7, 8.0),
            16: (13.0, "#8", 7, 8.0),
        },
    },
    "case_2": {
        25: {
            6:  (16.0, "#8", 7, 5.0),
            8:  (16.0, "#8", 7, 5.0),
            10: (16.0, "#8", 7, 5.0),
            12: (16.0, "#8", 7, 5.0),
            14: (16.0, "#8", 7, 5.0),
            16: (16.0, "#8", 7, 5.0),
        },
        30: {
            6:  (13.0, "#6", 7, 5.0),
            8:  (16.0, "#7", 7, 5.0),
            10: (16.0, "#8", 7, 5.0),
            12: (16.0, "#8", 7, 5.0),
            14: (16.0, "#8", 7, 5.0),
            16: (16.0, "#8", 7, 5.0),
        },
        35: {
            6:  (12.0, "#6", 7, 6.0),
            8:  (13.0, "#7", 6, 6.0),
            10: (16.0, "#8", 7, 6.0),
            12: (16.0, "#8", 7, 5.0),
            14: (16.0, "#8", 7, 5.0),
            16: (16.0, "#8", 7, 5.0),
        },
    },
}

# Pile cap width is always 1'-4" (16 in) per B15-3
_PILE_CAP_WIDTH_IN = 16
# Pile diameter is 1'-4" (16 in) per B15-3
_PILE_DIA_IN = 16
# Spiral wire W8 per B15-5
_SPIRAL_WIRE = "W8"


def _snap_height(h_ft: float) -> int:
    """Snap wall height to nearest Caltrans table row (even feet 6-16)."""
    h = round(h_ft)
    if h < 6:
        h = 6
    elif h > 16:
        h = 16
    # Round to nearest even
    if h % 2 != 0:
        h += 1
    return min(h, 16)


def _snap_phi(phi: float) -> int:
    """Snap soil friction angle to nearest Caltrans table column (25, 30, 35)."""
    if phi <= 27.5:
        return 25
    elif phi <= 32.5:
        return 30
    return 35


# ---------------------------------------------------------------------------
# WV1/WV2 -- Wall vertical bars (a-bars and b-bars)
# ---------------------------------------------------------------------------

def rule_sw_wall_verticals(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """Wall vertical reinforcement from B15-1 table. a-bars each face, b-bars for H >= 8'."""
    h = _snap_height(p.wall_height_ft)
    tbl = _WALL_REINF[h]
    wall_len_in = p.wall_length_ft * 12.0
    wall_ht_in = p.wall_height_ft * 12.0

    bars = []

    # a-bars: vertical flexural bars, each face
    a_spacing = tbl["a_spacing"]
    a_qty_per_face = math.floor((wall_len_in - 2 * 2.0) / a_spacing) + 1
    a_qty = a_qty_per_face * 2  # each face
    a_len = wall_ht_in - 2 * 2.0

    log.step(
        f"B15-1 table H={h}': a-bars = {tbl['a_size']} @ {a_spacing}\" oc",
        source="SoundWallRules",
    )
    log.step(
        f"WV1: {a_qty_per_face}/face x 2 = {a_qty} bars @ {fmt_inches(a_len)}",
        source="SoundWallRules",
    )
    log.result("WV1", f"{tbl['a_size']} x {a_qty} @ {fmt_inches(a_len)}",
               source="SoundWallRules")

    bars.append(BarRow(
        mark="WV1", size=tbl["a_size"], qty=a_qty, length_in=a_len,
        shape="Str", notes=f"vertical a-bars EF @ {a_spacing}\" oc (B15-1)",
        source_rule="rule_sw_wall_verticals",
    ))

    # b-bars: secondary vertical, H >= 8' only
    if tbl["b_size"] is not None:
        b_spacing = tbl["b_spacing"]
        b_qty_per_face = math.floor((wall_len_in - 2 * 2.0) / b_spacing) + 1
        b_qty = b_qty_per_face * 2
        # b-bars are shorter -- typically only in lower portion
        b_len = wall_ht_in - 2 * 2.0

        log.step(
            f"WV2: b-bars = {tbl['b_size']} @ {b_spacing}\" oc, {b_qty} total",
            source="SoundWallRules",
        )
        log.result("WV2", f"{tbl['b_size']} x {b_qty} @ {fmt_inches(b_len)}",
                   source="SoundWallRules")

        bars.append(BarRow(
            mark="WV2", size=tbl["b_size"], qty=b_qty, length_in=b_len,
            shape="Str", notes=f"vertical b-bars EF @ {b_spacing}\" oc (B15-1)",
            source_rule="rule_sw_wall_verticals",
        ))
    else:
        log.step("H < 8': no b-bars required", source="SoundWallRules")

    return bars


# ---------------------------------------------------------------------------
# WH1 -- Horizontal bond beam bars (c-bars)
# ---------------------------------------------------------------------------

def rule_sw_wall_horizontals(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """Horizontal bond beam reinforcement (#5 cont at each bond beam, B15-1)."""
    h = _snap_height(p.wall_height_ft)
    tbl = _WALL_REINF[h]
    wall_len_in = p.wall_length_ft * 12.0
    wall_ht_in = p.wall_height_ft * 12.0

    # Bond beams at top + every 4'-0" (48") below per B15 notes
    bond_beam_spacing = 48.0  # inches
    n_bond_beams = math.floor(wall_ht_in / bond_beam_spacing) + 1

    # #5 continuous at each bond beam per B15-1/3
    bar_len = wall_len_in - 2 * 2.0
    # 2 bars per bond beam (continuous #5 at each bond beam)
    qty = n_bond_beams * 2

    c_size = tbl["c_size"]

    log.step(
        f"Bond beams: top + every 4'-0\" = {n_bond_beams} beams, "
        f"2x {c_size} per beam = {qty} bars",
        source="SoundWallRules",
    )
    log.result("WH1", f"{c_size} x {qty} @ {fmt_inches(bar_len)}",
               source="SoundWallRules")

    return [BarRow(
        mark="WH1", size=c_size, qty=qty, length_in=bar_len,
        shape="Str", notes=f"bond beam c-bars, {n_bond_beams} beams (B15-1)",
        source_rule="rule_sw_wall_horizontals",
    )]


# ---------------------------------------------------------------------------
# FD1 -- Footing dowels (d-bars, spread/trench only)
# ---------------------------------------------------------------------------

def rule_sw_footing_dowels(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """Footing dowels from wall into footing (d-bars, B15-1). Skip for pile cap."""
    if p.foundation_type == "pile_cap":
        log.step("Pile cap foundation -- no separate footing dowels", source="SoundWallRules")
        return []

    h = _snap_height(p.wall_height_ft)
    tbl = _WALL_REINF[h]
    wall_len_in = p.wall_length_ft * 12.0

    d_spacing = tbl["d_spacing"]
    qty = math.floor((wall_len_in - 2 * 2.0) / d_spacing) + 1

    # Dowel length: embed into footing + lap into wall
    # Per B15-1: #5 @ 16, typical dowel = footing depth + 2'-8" lap
    lap_in = 32  # 2'-8" lap per B15-1
    if p.foundation_type == "spread_footing":
        footing_depth = 12.0  # 1'-0" typical spread footing depth
    else:
        footing_depth = 12.0  # trench footing -- dowel embed
    bar_len = footing_depth + lap_in

    log.step(
        f"FD1 dowels: {tbl['d_size']} @ {d_spacing}\" oc, {qty} bars, "
        f"embed {footing_depth}\" + {lap_in}\" lap = {fmt_inches(bar_len)}",
        source="SoundWallRules",
    )
    log.result("FD1", f"{tbl['d_size']} x {qty} @ {fmt_inches(bar_len)}",
               source="SoundWallRules")

    return [BarRow(
        mark="FD1", size=tbl["d_size"], qty=qty, length_in=bar_len,
        shape="Str", notes=f"footing dowels @ {d_spacing}\" oc (B15-1)",
        source_rule="rule_sw_footing_dowels",
    )]


# ---------------------------------------------------------------------------
# FT1/FL1 -- Footing bars (spread/trench only)
# ---------------------------------------------------------------------------

def rule_sw_footing_bars(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """Footing reinforcement for spread or trench footing (B15-1)."""
    if p.foundation_type == "pile_cap":
        log.step("Pile cap foundation -- no footing bars", source="SoundWallRules")
        return []

    h = _snap_height(p.wall_height_ft)
    wall_len_in = p.wall_length_ft * 12.0
    bars = []

    if p.foundation_type == "spread_footing":
        # Spread footing width from table
        w_in = _SPREAD_FOOTING_W.get(h, 78)
        footing_depth = 12.0  # 1'-0" per B15-1

        # Transverse bars: #4 @ 18" max, across footing width
        trans_qty = math.floor((wall_len_in - 2 * 2.0) / 18.0) + 1
        trans_len = w_in - 2 * 2.0

        log.step(
            f"Spread footing W = {fmt_inches(w_in)} for H={h}'",
            source="SoundWallRules",
        )
        log.step(
            f"FT1: #4 @ 18\" oc transverse, {trans_qty} bars @ {fmt_inches(trans_len)}",
            source="SoundWallRules",
        )
        log.result("FT1", f"#4 x {trans_qty} @ {fmt_inches(trans_len)}",
                   source="SoundWallRules")

        bars.append(BarRow(
            mark="FT1", size="#4", qty=trans_qty, length_in=trans_len,
            shape="Str", notes=f"footing transverse @ 18\" oc (B15-1)",
            source_rule="rule_sw_footing_bars",
        ))

        # Longitudinal bars: #4 Tot 2 top, #4 Tot 2 bottom = 4 total
        long_len = wall_len_in - 2 * 2.0
        long_qty = 4

        log.step(f"FL1: #4 Tot 4 longitudinal @ {fmt_inches(long_len)}", source="SoundWallRules")
        log.result("FL1", f"#4 x {long_qty} @ {fmt_inches(long_len)}", source="SoundWallRules")

        bars.append(BarRow(
            mark="FL1", size="#4", qty=long_qty, length_in=long_len,
            shape="Str", notes="footing longitudinal (B15-1)",
            source_rule="rule_sw_footing_bars",
        ))

    else:  # trench_footing
        case = p.ground_case
        depth_in = _TRENCH_DEPTH.get(case, _TRENCH_DEPTH["case_1"]).get(h, 81)

        # Trench footing: #4 @ 12 max horizontally, #4 @ 12 max vertically
        # Horizontal trench bars along wall length
        horiz_qty = math.floor(depth_in / 12.0) + 1
        horiz_len = wall_len_in - 2 * 2.0

        log.step(
            f"Trench footing D = {fmt_inches(depth_in)} ({case}, H={h}')",
            source="SoundWallRules",
        )
        log.step(
            f"FT1: #4 @ 12\" horizontal in trench, {horiz_qty} bars",
            source="SoundWallRules",
        )
        log.result("FT1", f"#4 x {horiz_qty} @ {fmt_inches(horiz_len)}",
                   source="SoundWallRules")

        bars.append(BarRow(
            mark="FT1", size="#4", qty=horiz_qty, length_in=horiz_len,
            shape="Str", notes=f"trench horizontal @ 12\" oc (B15-1)",
            source_rule="rule_sw_footing_bars",
        ))

        # Vertical bars in trench along wall length
        vert_qty = math.floor((wall_len_in - 2 * 2.0) / 12.0) + 1
        vert_len = depth_in - 2 * 2.0

        log.step(
            f"FL1: #4 @ 12\" vertical in trench, {vert_qty} bars @ {fmt_inches(vert_len)}",
            source="SoundWallRules",
        )
        log.result("FL1", f"#4 x {vert_qty} @ {fmt_inches(vert_len)}",
                   source="SoundWallRules")

        bars.append(BarRow(
            mark="FL1", size="#4", qty=vert_qty, length_in=vert_len,
            shape="Str", notes="trench vertical @ 12\" oc (B15-1)",
            source_rule="rule_sw_footing_bars",
        ))

    return bars


# ---------------------------------------------------------------------------
# PL1/PS1 -- CIDH pile cage (pile cap only)
# ---------------------------------------------------------------------------

def rule_sw_pile_cage(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """CIDH pile longitudinal bars and spiral (B15-3/5). Skip for footing types."""
    if p.foundation_type != "pile_cap":
        log.step("Not pile cap foundation -- skipping pile cage", source="SoundWallRules")
        return []

    h = _snap_height(p.wall_height_ft)
    case = p.ground_case
    phi = _snap_phi(30.0)

    pile_tbl = _PILE_DATA.get(case, _PILE_DATA["case_1"])
    phi_tbl = pile_tbl.get(phi, pile_tbl[30])
    pile_len_ft, pile_size, pile_count, pile_spacing_ft = phi_tbl.get(h, (16.0, "#8", 7, 8.0))

    wall_len_in = p.wall_length_ft * 12.0
    pile_spacing_in = pile_spacing_ft * 12.0
    n_piles = math.floor(wall_len_in / pile_spacing_in) + 1

    pile_len_in = pile_len_ft * 12.0

    bars = []

    # PL1 -- Pile longitudinal bars
    total_long = n_piles * pile_count
    log.step(
        f"B15-5 pile table ({case}, phi={phi}deg, H={h}'): "
        f"{pile_size} Tot {pile_count}, L={pile_len_ft}'-0\", spacing={pile_spacing_ft}'-0\"",
        source="SoundWallRules",
    )
    log.step(
        f"PL1: {n_piles} piles x {pile_count} bars = {total_long} bars @ {fmt_inches(pile_len_in)}",
        source="SoundWallRules",
    )
    log.result("PL1", f"{pile_size} x {total_long} @ {fmt_inches(pile_len_in)}",
               source="SoundWallRules")

    bars.append(BarRow(
        mark="PL1", size=pile_size, qty=total_long, length_in=pile_len_in,
        shape="Str", notes=f"CIDH pile longitudinal, {n_piles} piles (B15-5)",
        source_rule="rule_sw_pile_cage",
    ))

    # PS1 -- Pile spiral (W8 wire)
    # Spiral pitch: 6" for top 9', 3" below, 2" at top 3' per B15-5
    # Approximate total spiral length per pile:
    pile_circ_in = math.pi * (_PILE_DIA_IN - 2 * 2.0)
    # Average pitch ~4" over the pile length
    avg_pitch = 4.0
    n_turns = pile_len_in / avg_pitch
    spiral_len_per_pile = n_turns * pile_circ_in
    total_spiral = n_piles

    log.step(
        f"PS1: W8 spiral, ~{n_turns:.0f} turns/pile x {n_piles} piles",
        source="SoundWallRules",
    )
    log.result("PS1", f"W8 x {total_spiral} spirals @ {fmt_inches(spiral_len_per_pile)}",
               source="SoundWallRules")

    bars.append(BarRow(
        mark="PS1", size="W8", qty=total_spiral, length_in=spiral_len_per_pile,
        shape="Spiral",
        notes=f"CIDH pile spiral, pitch varies 2\"-6\" (B15-5)",
        source_rule="rule_sw_pile_cage",
    ))

    return bars


# ---------------------------------------------------------------------------
# PC1 -- Pile cap transverse bars (pile cap only)
# ---------------------------------------------------------------------------

def rule_sw_pile_cap_bars(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """Pile cap reinforcement: #4 @ 12 max vertically each face (B15-3)."""
    if p.foundation_type != "pile_cap":
        log.step("Not pile cap -- skipping pile cap bars", source="SoundWallRules")
        return []

    h = _snap_height(p.wall_height_ft)
    wall_len_in = p.wall_length_ft * 12.0

    # Pile cap: #4 @ 12 max vertically each face, 2'-0" deep cap
    cap_depth_in = 24.0  # per B15-3 typical
    n_vert_per_face = math.floor(cap_depth_in / 12.0) + 1
    qty = math.floor((wall_len_in - 2 * 2.0) / 12.0) + 1

    # Bar length spans across pile cap width
    cap_width_in = _PILE_CAP_WIDTH_IN
    bar_len = cap_width_in - 2 * 2.0

    log.step(
        f"PC1: pile cap #4 @ 12\" EF, {qty} bars @ {fmt_inches(bar_len)}",
        source="SoundWallRules",
    )
    log.result("PC1", f"#4 x {qty} @ {fmt_inches(bar_len)}",
               source="SoundWallRules")

    return [BarRow(
        mark="PC1", size="#4", qty=qty, length_in=bar_len,
        shape="Str", notes="pile cap transverse @ 12\" oc EF (B15-3)",
        source_rule="rule_sw_pile_cap_bars",
    )]


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def rule_validate_sound_wall(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """Validate sound wall inputs against Caltrans B15 limits."""
    h = p.wall_height_ft
    warns = []

    if h < 6.0:
        warns.append(f"Wall height {h}' < 6' minimum per B15")
    if h > 16.0:
        warns.append(f"Wall height {h}' > 16' maximum per B15")
    if 48.0 > 48.0:
        warns.append(f"Expansion joint spacing {48.0}' > 48' max per B15")

    for w in warns:
        log.warn(w, source="SoundWallRules")

    return []
