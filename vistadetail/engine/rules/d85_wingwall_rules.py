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

Reinforcing table from D85 (Type E "TABLE OF REINFORCEMENT"):
  H(ft) | Bar No. | Spacing | Number Each Wall
    2   |   #4   |   12"   |   2
    3   |   #4   |   12"   |   3
    4   |   #4   |   12"   |   4
    5   |   #4   |   12"   |   5
    6   |   #4   |   12"   |   6
    7   |   #5   |   12"   |   7
    8   |   #5   |   12"   |   8
    9   |   #6   |   12"   |   9
   10   |   #6   |   12"   |  10
   12   |   #6   |   12"   |  12
   14   |   #8   |   12"   |  14

Bar marks:
  n1  -- "n" bars (inside face horizontal)
  n2  -- "n" bars (outside face horizontal)
  o1  -- "o" bars (inside face longitudinal)
  o2  -- "o" bars (outside face longitudinal)
  L1  -- "L" bars (longitudinal, stepped section)
  H1  -- #4 @ 12" hoops
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
# D85 reinforcement table (interpolate for fractional H)
# ---------------------------------------------------------------------------
_D85_TABLE = [
    (2,  "#4", 12, 2),
    (3,  "#4", 12, 3),
    (4,  "#4", 12, 4),
    (5,  "#4", 12, 5),
    (6,  "#4", 12, 6),
    (7,  "#5", 12, 7),
    (8,  "#5", 12, 8),
    (9,  "#6", 12, 9),
    (10, "#6", 12, 10),
    (12, "#6", 12, 12),
    (14, "#8", 12, 14),
]


def _lookup_d85(h_ft: float) -> tuple[str, int, int]:
    """Return (bar_size, spacing_in, qty_each_wall) from D85 table."""
    prev = _D85_TABLE[0]
    for row in _D85_TABLE:
        if h_ft <= row[0]:
            return row[1], row[2], row[3]
        prev = row
    return prev[1], prev[2], prev[3]


def rule_d85_geometry(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """Validate geometry and log."""
    size, spac, qty = _lookup_d85(p.wall_height_ft)
    log.step(
        f"D85 Geometry: H={p.wall_height_ft}ft, LOL={p.wall_length_ft}ft "
        f"→ table: {size} @{spac}\" x{qty} each wall",
        source="D85WingwallGeometry",
    )
    return []


def rule_d85_n_bars(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    'n' bars -- primary face bars from D85 table.
    Both faces, full LOL length.
    """
    h_ft   = p.wall_height_ft
    lol_in = p.wall_length_ft * 12
    size, spac, qty_each = _lookup_d85(h_ft)

    log.step(
        f"n-bars: H={h_ft}ft → {size} @{spac}\", qty={qty_each} each face, "
        f"len={lol_in/12:.2f}ft",
        source="D85nBars",
    )
    log.result("n1", f"{size} x {qty_each} @ {lol_in/12:.2f}ft",
               f"Inside face @{spac}oc", source="D85nBars")
    log.result("n2", f"{size} x {qty_each} @ {lol_in/12:.2f}ft",
               f"Outside face @{spac}oc", source="D85nBars")

    return [
        BarRow(mark="n1", size=size, qty=qty_each,
               length_in=lol_in, shape="Str",
               notes=f"Inside face @{spac}oc", source_rule="rule_d85_n_bars"),
        BarRow(mark="n2", size=size, qty=qty_each,
               length_in=lol_in, shape="Str",
               notes=f"Outside face @{spac}oc", source_rule="rule_d85_n_bars"),
    ]


def rule_d85_o_bars(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    'o' bars -- longitudinal bars running along wall height on each face.
    Length = H (wall height) + 2ft lap into box.
    Qty per face: 2 for H<=5, 3 for H<=9, 4 for taller.
    """
    h_in   = p.wall_height_ft * 12
    lap_in = 24.0  # 2'-0" into box wall
    length = h_in + lap_in

    if p.wall_height_ft <= 5.0:
        qty  = 2
        size = "#4"
    elif p.wall_height_ft <= 9.0:
        qty  = 3
        size = "#5"
    else:
        qty  = 4
        size = "#6"

    log.step(
        f"o-bars: H={p.wall_height_ft}ft → {size} x{qty} each face, "
        f"len={length/12:.2f}ft",
        source="D85oBars",
    )
    log.result("o1", f"{size} x {qty} @ {length/12:.2f}ft",
               "Inside long bars", source="D85oBars")
    log.result("o2", f"{size} x {qty} @ {length/12:.2f}ft",
               "Outside long bars", source="D85oBars")

    return [
        BarRow(mark="o1", size=size, qty=qty,
               length_in=length, shape="Str",
               notes="Inside long bars", source_rule="rule_d85_o_bars"),
        BarRow(mark="o2", size=size, qty=qty,
               length_in=length, shape="Str",
               notes="Outside long bars", source_rule="rule_d85_o_bars"),
    ]


def rule_d85_l_bars(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    'L' bars at stepped section (Type E) -- inside face longitudinals
    that continue from box into wingwall.
    Length = LOL + 2ft (extend into box).
    Qty = 2 (D85: 2-#5 additional bars).
    """
    lol_in = p.wall_length_ft * 12
    lap_in = 24.0
    length = lol_in + lap_in

    log.step(f"L-bars: 2 #5, len={length/12:.2f}ft", source="D85lBars")
    log.result("L1", f"#5 x 2 @ {length/12:.2f}ft",
               "2-#5 additional at step", source="D85lBars")

    return [
        BarRow(mark="L1", size="#5", qty=2,
               length_in=length, shape="Str",
               notes="2-#5 additional at step", source_rule="rule_d85_l_bars"),
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
