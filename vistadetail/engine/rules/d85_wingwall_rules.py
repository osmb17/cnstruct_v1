"""
Rule functions for Caltrans D85 Box Culvert Wingwall (Types D, E).

Based on 2025 Standard Plan D85.

Types:
  D = Straight Wingwall (single box culvert)
  E = Stepped Wingwall (multiple span box culvert)

Key geometry:
  H   = wall height (ft) at box face
  LOL = length of wall (ft)
  S   = clear span of box (ft) -- used for Type E spacing

TABLE OF REINFORCEMENT FOR TYPE "E" WINGWALLS (confirmed from D85 2025):

  "k" BARS (primary face bars, outside face, spaced along wall height):
  H(ft)    3    4    5    6    7    8   10   12   14
  Bar No. #4   #4   #5   #5   #5   #5   #5   #5   #5
  Spacing @12  @12  @12  @10   @9   @8   @7   @5   @4

  "L" BARS (concentrated bars per wall, run full LOL length):
  H(ft)    3    4    5    6    7    8   10   12   14
  Bar No. #5   #5   #6   #6   #7   #7   #7   #7   #7
  Each Wl  2    2    3    3    3    3    3    3    3

  Note: "n" bars (inside face) match the adjacent RCB "a" bar size and spacing
  per D85 sections — coordinated from the box culvert design.

Bar marks:
  k1  -- "k" bars (outside face, primary face bars from table)
  L1  -- "L" bars (concentrated bars, total count per wall)
  H1  -- #4 @ 12 Max hoops
  T1  -- top bars (#4 @ 9" both faces)
  T2  -- top bars (#4 @ 9" outside face)
  B1  -- footing mat transverse
  B2  -- footing mat longitudinal
"""

from __future__ import annotations
import math
from vistadetail.engine.reasoning_logger import ReasoningLogger
from vistadetail.engine.schema import BarRow, Params


# ---------------------------------------------------------------------------
# D85 reinforcement tables — confirmed from 2025 Standard Plan D85
# ---------------------------------------------------------------------------

# "k" bars: primary outside-face bars, spaced along wall height.
# (H_ft, bar_size, spacing_in)
_D85_K_TABLE: list[tuple[int, str, int]] = [
    (3,  "#4", 12),
    (4,  "#4", 12),
    (5,  "#5", 12),
    (6,  "#5", 10),
    (7,  "#5",  9),
    (8,  "#5",  8),
    (10, "#5",  7),
    (12, "#5",  5),
    (14, "#5",  4),
]

# "L" bars: concentrated bars, fixed count per wall, run full LOL.
# (H_ft, bar_size, count_per_wall)
_D85_L_TABLE: list[tuple[int, str, int]] = [
    (3,  "#5", 2),
    (4,  "#5", 2),
    (5,  "#6", 3),
    (6,  "#6", 3),
    (7,  "#7", 3),
    (8,  "#7", 3),
    (10, "#7", 3),
    (12, "#7", 3),
    (14, "#7", 3),
]


def _lookup_k(h_ft: float) -> tuple[str, int]:
    """Return (bar_size, spacing_in) for 'k' bars from D85 table."""
    last = _D85_K_TABLE[-1]
    for row in _D85_K_TABLE:
        if h_ft <= row[0]:
            return row[1], row[2]
        last = row
    return last[1], last[2]


def _lookup_l(h_ft: float) -> tuple[str, int]:
    """Return (bar_size, count_per_wall) for 'L' bars from D85 table."""
    last = _D85_L_TABLE[-1]
    for row in _D85_L_TABLE:
        if h_ft <= row[0]:
            return row[1], row[2]
        last = row
    return last[1], last[2]


def rule_d85_geometry(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """Validate geometry and log key computed values."""
    k_size, k_sp = _lookup_k(p.wall_height_ft)
    l_size, l_cnt = _lookup_l(p.wall_height_ft)
    log.step(
        f"D85 Geometry: H={p.wall_height_ft}ft, LOL={p.wall_length_ft}ft  "
        f"k-bars: {k_size}@{k_sp}\"  L-bars: {l_size}×{l_cnt}/wall",
        source="D85WingwallGeometry",
    )
    return []


def rule_d85_k_bars(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    'k' bars — primary outside-face bars (D85 Table of Reinforcement).

    Run the full LOL length along the outside wall face, spaced vertically
    at the table spacing.  Length = LOL (+ 2'-0\" lap into box wall per D85).

    qty = floor(H_in / spacing) + 1
    """
    h_ft   = p.wall_height_ft
    h_in   = h_ft * 12
    lol_in = p.wall_length_ft * 12
    lap_in = 24.0   # 2'-0" into box wall per D85 detail
    size, spac = _lookup_k(h_ft)

    qty    = math.floor(h_in / spac) + 1
    length = lol_in + lap_in

    log.step(
        f"k-bars ({size}@{spac}\"): H={h_ft}ft → qty=floor({h_in}/{spac})+1={qty}  "
        f"len=LOL+2ft={length/12:.2f}ft",
        source="D85kBars",
    )
    log.result("k1", f"{size} x {qty} @ {length/12:.2f}ft",
               f"Outside face k-bars @{spac}\"oc", source="D85kBars")

    return [
        BarRow(mark="k1", size=size, qty=qty,
               length_in=length, shape="Str",
               notes=f"Outside face k-bars @{spac}\" oc, len incl 2'-0\" lap into box",
               source_rule="rule_d85_k_bars"),
    ]


def rule_d85_l_bars(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    'L' bars — concentrated bars per wall (D85 Table of Reinforcement).

    Fixed count (2 or 3 per wall) from the D85 table, running the full
    LOL length.  Length = LOL (+ 2'-0\" lap into box).
    """
    h_ft   = p.wall_height_ft
    lol_in = p.wall_length_ft * 12
    lap_in = 24.0
    size, cnt = _lookup_l(h_ft)
    length = lol_in + lap_in

    log.step(
        f"L-bars ({size}): H={h_ft}ft → {cnt} bars/wall  "
        f"len=LOL+2ft={length/12:.2f}ft",
        source="D85lBars",
    )
    log.result("L1", f"{size} x {cnt} @ {length/12:.2f}ft",
               f"Concentrated L-bars, {cnt}/wall", source="D85lBars")

    return [
        BarRow(mark="L1", size=size, qty=cnt,
               length_in=length, shape="Str",
               notes=f"Concentrated L-bars per D85 table, {cnt}/wall, len incl 2'-0\" lap",
               source_rule="rule_d85_l_bars"),
    ]


def rule_d85_hoops(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    #4 @ 12" hoops (rectangular ties) along wall length.
    Qty = floor(LOL*12 / 12) + 1.
    Hoop length = 2*(H + T) perimeter.
    """
    h_in   = p.wall_height_ft * 12
    lol_in = p.wall_length_ft * 12
    t_in   = max(9.0, getattr(p, "wall_thick_in", 9.0))
    spac   = 12.0

    qty    = math.floor(lol_in / spac) + 1
    hoop_l = 2 * (h_in + t_in)

    log.step(
        f"Hoops: #4 @12\", qty={qty}, perim={hoop_l/12:.2f}ft",
        source="D85Hoops",
    )
    log.result("H1", f"#4 x {qty} @ {hoop_l/12:.2f}ft",
               "#4 @12 hoops", source="D85Hoops")

    return [
        BarRow(mark="H1", size="#4", qty=qty,
               length_in=hoop_l, shape="Rect",
               leg_a_in=h_in, leg_b_in=t_in,
               notes="#4 @12 hoops", source_rule="rule_d85_hoops"),
    ]


def rule_d85_top_bars(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Top bars at wall crest -- #4 @ 9" both faces.
    Length = LOL.
    Qty = floor(LOL*12 / 9) + 1.
    """
    lol_in = p.wall_length_ft * 12
    spac   = 9.0
    qty    = math.floor(lol_in / spac) + 1

    log.step(f"Top bars: #4 @9\" both faces, qty={qty} per face",
             source="D85Top")
    log.result("T1", f"#4 x {qty} @ {lol_in/12:.2f}ft",
               "#4 @9 top inside face", source="D85Top")
    log.result("T2", f"#4 x {qty} @ {lol_in/12:.2f}ft",
               "#4 @9 top outside face", source="D85Top")

    return [
        BarRow(mark="T1", size="#4", qty=qty,
               length_in=lol_in, shape="Str",
               notes="#4 @9 top inside face", source_rule="rule_d85_top_bars"),
        BarRow(mark="T2", size="#4", qty=qty,
               length_in=lol_in, shape="Str",
               notes="#4 @9 top outside face", source_rule="rule_d85_top_bars"),
    ]


def rule_d85_footing_mat(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Footing mat -- #4 @ 12" each way.

    SOURCE: #4 @ 12" each way is per D85 standard plan.
    ASSUMPTION: Footing width = 0.55 × H when not specified by the user.
    This ratio is a conservative estimate — D85 does not publish a footing
    width formula. The actual footing width should come from the project plans
    or be designed by the PE for the specific loading condition.
    """
    lol_in   = p.wall_length_ft * 12
    ftg_w_in = getattr(p, "footing_width_ft", p.wall_height_ft * 0.55) * 12
    if ftg_w_in == 0:
        ftg_w_in = p.wall_height_ft * 0.55 * 12  # ASSUMPTION — see docstring
    spac     = 12.0  # per D85 standard plan

    qty_t = math.ceil(lol_in / spac) + 1
    qty_l = math.ceil(ftg_w_in / spac) + 1

    log.step(
        f"Footing mat: {ftg_w_in/12:.2f}ft x {lol_in/12:.2f}ft, "
        f"B1={qty_t} trans, B2={qty_l} long",
        source="D85Footing",
    )
    log.result("B1", f"#4 x {qty_t} @ {ftg_w_in/12:.2f}ft",
               "Ftg transverse #4@12", source="D85Footing")
    log.result("B2", f"#4 x {qty_l} @ {lol_in/12:.2f}ft",
               "Ftg longitudinal #4@12", source="D85Footing")

    return [
        BarRow(mark="B1", size="#4", qty=qty_t,
               length_in=ftg_w_in, shape="Str",
               notes="Ftg transverse #4@12", source_rule="rule_d85_footing_mat"),
        BarRow(mark="B2", size="#4", qty=qty_l,
               length_in=lol_in, shape="Str",
               notes="Ftg longitudinal #4@12", source_rule="rule_d85_footing_mat"),
    ]


def rule_d85_validate(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """Validate D85 inputs."""
    if p.wall_height_ft <= 0:
        log.warn("H must be > 0", source="D85Validate")
    if p.wall_length_ft <= 0:
        log.warn("LOL must be > 0", source="D85Validate")
    if p.wall_height_ft > 14.0:
        log.warn(
            f"H={p.wall_height_ft}ft exceeds D85 table max (14ft) -- extrapolating",
            source="D85Validate",
        )
    return []
