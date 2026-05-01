"""
Rule functions for Caltrans D84 Box Culvert Wingwall (Types A, B, C).

Based on 2025 Standard Plan D84.

Key geometry:
  H   = wall height (ft) at box face
  LOL = length of wall (ft)
  T   = wall thickness (in) -- 9" min from D84 section details

Reinforcing (from D84 standard):
  Front/Rear face bars:
    #4 @ 12" each face (transverse / horizontal runs)
    Longitudinal "L" bars per table by H
  Footing:
    #4 @ 12" each way (bottom mat)
    #4 Tol 3 at cutoff wall
  Top bars:
    #4 Tol 2, #5 Tol 7 at parapet
  Wall-to-box tie:
    #4 @ 12" hooked into box wall (neoprene strip)

Bar marks follow D84 convention:
  F1  -- front face horizontal (transverse) #4 @ 12"
  F2  -- rear face horizontal #4 @ 12"
  L1  -- longitudinal front face
  L2  -- longitudinal rear face
  T1  -- top / parapet bars #4 x2
  T2  -- top / parapet bars #5 x7
  B1  -- bottom footing mat (transverse)
  B2  -- bottom footing mat (longitudinal)
  CW  -- cutoff wall bars
"""

from __future__ import annotations
import math
from vistadetail.engine.reasoning_logger import ReasoningLogger
from vistadetail.engine.schema import BarRow, Params


# ---------------------------------------------------------------------------
# Longitudinal bar table from D84 (H ft → size)
# D84 shows #4/#5/#6/#8 based on wall height
# ---------------------------------------------------------------------------
def _long_bar_size(h_ft: float) -> str:
    if h_ft <= 4.0:
        return "#4"
    elif h_ft <= 7.0:
        return "#5"
    elif h_ft <= 11.0:
        return "#6"
    else:
        return "#8"


def rule_d84_geometry(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """Validate geometry and log key computed values."""
    h_in   = p.wall_height_ft * 12
    lol_in = p.wall_length_ft * 12
    t_in   = max(9.0, getattr(p, "wall_thick_in", 9.0))

    log.step(
        f"D84 Geometry: H={h_in/12:.2f}ft, LOL={lol_in/12:.2f}ft, T={t_in}in",
        source="D84WingwallGeometry",
    )
    return []


def rule_d84_face_horiz(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Front and rear face horizontal bars -- #4 @ 12" each face.
    Length = LOL (full wall length).
    Qty each face = floor(H*12 / 12) + 1 = H + 1 bars.
    """
    h_in   = p.wall_height_ft * 12
    lol_in = p.wall_length_ft * 12
    cover  = getattr(p, "cover_in", 2.0)
    spac   = 12.0  # D84 standard: #4 @ 12"

    usable = h_in - 2 * cover
    qty_per_face = math.floor(usable / spac) + 1
    length_in    = lol_in

    log.step(
        f"F-bars: H={p.wall_height_ft}ft → {qty_per_face} bars each face @ 12\", "
        f"len={lol_in/12:.2f}ft",
        source="D84FaceHoriz",
    )
    log.result("F1", f"#4 x {qty_per_face} @ {lol_in/12:.2f}ft",
               "Front face horiz @12oc", source="D84FaceHoriz")
    log.result("F2", f"#4 x {qty_per_face} @ {lol_in/12:.2f}ft",
               "Rear face horiz @12oc", source="D84FaceHoriz")

    return [
        BarRow(mark="F1", size="#4", qty=qty_per_face,
               length_in=length_in, shape="Str",
               notes="Front face horiz @12oc", source_rule="rule_d84_face_horiz"),
        BarRow(mark="F2", size="#4", qty=qty_per_face,
               length_in=length_in, shape="Str",
               notes="Rear face horiz @12oc", source_rule="rule_d84_face_horiz"),
    ]


def rule_d84_longitudinals(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Longitudinal bars (L bars) -- run along the length of wall on each face.
    Size determined by wall height per D84 table.
    Qty = 2 per face (top and mid) for H <= 7, 3 per face for taller walls.
    Length = LOL + 2ft lap into box wall.
    """
    h_ft   = p.wall_height_ft
    lol_in = p.wall_length_ft * 12
    size   = _long_bar_size(h_ft)
    lap_in = 24.0  # 2'-0" lap into box wall (per D84 detail)

    if h_ft <= 5.0:
        qty_per_face = 2
    elif h_ft <= 9.0:
        qty_per_face = 3
    else:
        qty_per_face = 4

    length_in = lol_in + lap_in

    log.step(
        f"L-bars: H={h_ft}ft → {size}, {qty_per_face} bars each face, "
        f"len={length_in/12:.2f}ft (incl 2ft lap)",
        source="D84Longitudinals",
    )
    log.result("L1", f"{size} x {qty_per_face} @ {length_in/12:.2f}ft",
               f"Front long bars", source="D84Longitudinals")
    log.result("L2", f"{size} x {qty_per_face} @ {length_in/12:.2f}ft",
               f"Rear long bars", source="D84Longitudinals")

    return [
        BarRow(mark="L1", size=size, qty=qty_per_face,
               length_in=length_in, shape="Str",
               notes=f"Front long bars, {qty_per_face}ea", source_rule="rule_d84_longitudinals"),
        BarRow(mark="L2", size=size, qty=qty_per_face,
               length_in=length_in, shape="Str",
               notes=f"Rear long bars, {qty_per_face}ea", source_rule="rule_d84_longitudinals"),
    ]


def rule_d84_top_bars(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Top / parapet bars at wall top edge.
    D84 shows #4 Tol 2 and #5 Tol 7 at top of wall.
    Length = LOL.
    """
    lol_in = p.wall_length_ft * 12

    log.step(f"Top bars: LOL={p.wall_length_ft}ft → 2 #4 + 7 #5 at top",
             source="D84TopBars")
    log.result("T1", f"#4 x 2 @ {lol_in/12:.2f}ft", "Top parapet", source="D84TopBars")
    log.result("T2", f"#5 x 7 @ {lol_in/12:.2f}ft", "Top parapet", source="D84TopBars")

    return [
        BarRow(mark="T1", size="#4", qty=2,
               length_in=lol_in, shape="Str",
               notes="Top parapet #4 x2", source_rule="rule_d84_top_bars"),
        BarRow(mark="T2", size="#5", qty=7,
               length_in=lol_in, shape="Str",
               notes="Top parapet #5 x7", source_rule="rule_d84_top_bars"),
    ]


def rule_d84_footing_mat(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Footing bottom mat -- #4 @ 12" each way.
    Footing length = LOL.

    SOURCE: #4 @ 12" each way is per D84 standard plan.
    ASSUMPTION: Footing width = 0.55 × H when not specified by the user.
    This ratio is a conservative estimate — D84 does not publish a footing
    width formula. The actual footing width should come from the project plans
    or be designed by the PE for the specific loading condition.
    """
    lol_in   = p.wall_length_ft * 12
    ftg_w_in = getattr(p, "footing_width_ft", p.wall_height_ft * 0.55) * 12
    if ftg_w_in == 0:
        ftg_w_in = p.wall_height_ft * 0.55 * 12  # ASSUMPTION — see docstring
    spac     = 12.0  # per D84 standard plan

    qty_trans = math.ceil(lol_in / spac) + 1
    qty_long  = math.ceil(ftg_w_in / spac) + 1
    len_trans = ftg_w_in
    len_long  = lol_in

    log.step(
        f"Footing mat: {ftg_w_in/12:.2f}ft x {lol_in/12:.2f}ft, "
        f"B1={qty_trans} trans, B2={qty_long} long",
        source="D84FootingMat",
    )
    log.result("B1", f"#4 x {qty_trans} @ {len_trans/12:.2f}ft",
               "Ftg transverse #4@12", source="D84FootingMat")
    log.result("B2", f"#4 x {qty_long} @ {len_long/12:.2f}ft",
               "Ftg longitudinal #4@12", source="D84FootingMat")

    return [
        BarRow(mark="B1", size="#4", qty=qty_trans,
               length_in=len_trans, shape="Str",
               notes="Ftg transverse #4@12", source_rule="rule_d84_footing_mat"),
        BarRow(mark="B2", size="#4", qty=qty_long,
               length_in=len_long, shape="Str",
               notes="Ftg longitudinal #4@12", source_rule="rule_d84_footing_mat"),
    ]


def rule_d84_cutoff_wall(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Cutoff wall bars at toe of slope -- #4 Tol 3.
    Length = footing width (runs across footing).
    Qty = 3 (D84 standard detail).
    """
    ftg_w_in = getattr(p, "footing_width_ft", p.wall_height_ft * 0.55) * 12
    if ftg_w_in == 0:
        ftg_w_in = p.wall_height_ft * 0.55 * 12

    log.step(f"Cutoff wall: 3 #4 bars, len={ftg_w_in/12:.2f}ft",
             source="D84CutoffWall")
    log.result("CW", f"#4 x 3 @ {ftg_w_in/12:.2f}ft",
               "Cutoff wall #4 Tol3", source="D84CutoffWall")

    return [
        BarRow(mark="CW", size="#4", qty=3,
               length_in=ftg_w_in, shape="Str",
               notes="Cutoff wall #4 Tol3", source_rule="rule_d84_cutoff_wall"),
    ]


def rule_d84_validate(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """Validate D84 inputs."""
    if p.wall_height_ft <= 0:
        log.warn("Wall height H must be > 0", source="D84Validate")
    if p.wall_length_ft <= 0:
        log.warn("Wall length LOL must be > 0", source="D84Validate")
    if p.wall_height_ft > 20.0:
        log.warn(
            f"H={p.wall_height_ft}ft exceeds D84 max (~20ft) -- verify with engineer",
            source="D84Validate",
        )
    return []
