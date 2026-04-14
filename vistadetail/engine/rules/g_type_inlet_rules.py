"""
Rule functions for Caltrans D72 CIP Drainage Inlet Types G1, G3, G4, G5, G6.

Based on 2025 Standard Plans D72B, D72C, D72D.

Standard inner width W = 2'-11¾" (35.75") for all G-types (fixed per D72D).
Primary inputs:
  x_dim_ft  = L1, length of inlet box along roadway (ft)
  y_dim_ft  = H, depth from grate to flowline (ft)

Bar designations (D72C Table 2 top slab — same for all types):
  A bars  -- top slab bars spanning W direction  (#5 @ 5")
  B bars  -- top slab bars spanning L direction  (#5 @ 5")
  Hoops   -- perimeter ties at grate level       (#4 @ 5")

Wall bars by type (D72B section annotations):
  G1 -- #4 @ 12" all around    (simple box, no curb extension)
  G3 -- #4 @ 12" all around    (extended wall variant, +2ft ext bars)
  G4 -- #5 @ 12" all around    (concrete curb type)
  G5 -- #5 @ 12" all around    (detail A profile)
  G6 -- #4 @ 12" all around    (same-slope gutter, no depression)

Bottom mat (all types): #4 @ 12" each way
"""

from __future__ import annotations
import math
from vistadetail.engine.reasoning_logger import ReasoningLogger
from vistadetail.engine.schema import BarRow, Params, fmt_inches

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_STD_WIDTH_IN: float = 35.75   # 2'-11¾" standard box width (D72D)
_GRATE_DED: dict[str, float] = {"Type 24": 24.0, "Type 18": 18.0}


# ---------------------------------------------------------------------------
# Shared geometry helper
# ---------------------------------------------------------------------------

def _gt_geometry(p: Params, log: ReasoningLogger, label: str = "G-type") -> None:
    """
    Compute geometry for any G-type CIP inlet and store derived attrs on p.

    Derives:
      l_in, h_in, w_in, t_in
      l_bar, w_bar, h_adj
      gut_dim, n_struct, grate_ded
    """
    l_in = p.x_dim_ft * 12.0                           # box length (variable)
    h_in = p.y_dim_ft * 12.0                           # box depth H (variable)
    w_in = _STD_WIDTH_IN                               # fixed 2'-11¾"
    t_in = max(9.0, getattr(p, "wall_thick_in", 9.0))
    n    = int(getattr(p, "num_structures", 1)) or 1

    grate_type = str(getattr(p, "grate_type", "Type 24"))
    grate_ded  = _GRATE_DED.get(grate_type, 24.0)

    # Usable bar lengths (3" clear each end)
    l_bar = l_in - 6.0
    w_bar = w_in - 6.0
    h_adj = h_in + 4.0   # height + 4" development extension into slab

    # Gut dimension (clear grate opening after wall + grate deduction)
    int_l    = l_in - 2.0 * t_in
    gut_dim  = max(0.0, int_l - grate_ded - 5.0)

    setattr(p, "l_in",     l_in)
    setattr(p, "h_in",     h_in)
    setattr(p, "w_in",     w_in)
    setattr(p, "t_in",     t_in)
    setattr(p, "l_bar",    l_bar)
    setattr(p, "w_bar",    w_bar)
    setattr(p, "h_adj",    h_adj)
    setattr(p, "gut_dim",  gut_dim)
    setattr(p, "n_struct", n)
    setattr(p, "grate_ded", grate_ded)

    log.step(
        f"{label} Geometry: L={l_in/12:.2f}ft, H={h_in/12:.2f}ft, "
        f"W=2'-11¾\" (std), T={t_in:.0f}\"",
        source=f"{label}Geometry",
    )
    log.result(
        "GEOMETRY",
        f"L={l_in/12:.2f}ft, H={h_in/12:.2f}ft, W={w_in:.2f}\" std, "
        f"T={t_in:.0f}\", Gut={gut_dim:.2f}\"",
        source=f"{label}Geometry",
    )


# ---------------------------------------------------------------------------
# Shared wall bar helper
# ---------------------------------------------------------------------------

def _gt_wall_bars(
    p: Params, log: ReasoningLogger,
    bar_size: str, spacing: float, label: str, hook_in: float = 12.0,
) -> list[BarRow]:
    """
    Wall horizontal bars (both directions, both faces).

    Short bars (W-direction, 2 end walls × each face):
      qty = (floor(H/spacing)+1) × 2
      length = w_bar + 2×hook

    Long bars (L-direction, 2 side walls × each face):
      qty = (floor(H/spacing)+1) × 2
      length = l_bar + 2×hook
    """
    courses = math.floor(p.h_in / spacing) + 1
    qty_ws  = courses * 2
    len_ws  = p.w_bar + 2.0 * hook_in

    qty_wl  = courses * 2
    len_wl  = p.l_bar + 2.0 * hook_in

    log.step(
        f"{label} wall horiz {bar_size}@{spacing:.0f}\": "
        f"courses={courses}, W-bars qty={qty_ws} len={fmt_inches(len_ws)}, "
        f"L-bars qty={qty_wl} len={fmt_inches(len_wl)}",
        source=f"{label}WallBars",
    )
    log.result("W1", f"{bar_size} x {qty_ws} @ {fmt_inches(len_ws)}",
               "Wall horiz short (W-dir)", source=f"{label}WallBars")
    log.result("W2", f"{bar_size} x {qty_wl} @ {fmt_inches(len_wl)}",
               "Wall horiz long (L-dir)", source=f"{label}WallBars")

    return [
        BarRow(mark="W1", size=bar_size, qty=qty_ws,
               length_in=len_ws, shape="U",
               leg_a_in=hook_in, leg_b_in=p.w_bar, leg_c_in=hook_in,
               notes=f"Wall horiz short @{spacing:.0f}oc, 1ft hook EE",
               source_rule=f"rule_{label.lower()}_wall_bars"),
        BarRow(mark="W2", size=bar_size, qty=qty_wl,
               length_in=len_wl, shape="U",
               leg_a_in=hook_in, leg_b_in=p.l_bar, leg_c_in=hook_in,
               notes=f"Wall horiz long @{spacing:.0f}oc, 1ft hook EE",
               source_rule=f"rule_{label.lower()}_wall_bars"),
    ]


def _gt_vert_bars(
    p: Params, log: ReasoningLogger,
    bar_size: str, spacing: float, label: str, tail_in: float = 12.0,
) -> list[BarRow]:
    """
    Wall vertical bars (all walls, both faces).

    Short-wall verticals (W-direction walls):
      qty = (floor(w_bar/spacing)+1) × 2
    Long-wall verticals (L-direction walls):
      qty = (floor(l_bar/spacing)+1) × 2
    Length = h_adj + tail
    """
    qty_vs = (math.floor(p.w_bar / spacing) + 1) * 2
    qty_vl = (math.floor(p.l_bar / spacing) + 1) * 2
    length = p.h_adj + tail_in

    log.step(
        f"{label} wall vert {bar_size}@{spacing:.0f}\": "
        f"short-wall qty={qty_vs}, long-wall qty={qty_vl}, len={fmt_inches(length)}",
        source=f"{label}VertBars",
    )
    log.result("V1", f"{bar_size} x {qty_vs} @ {fmt_inches(length)}",
               "Wall vert short walls, 1ft tail", source=f"{label}VertBars")
    log.result("V2", f"{bar_size} x {qty_vl} @ {fmt_inches(length)}",
               "Wall vert long walls, 1ft tail", source=f"{label}VertBars")

    return [
        BarRow(mark="V1", size=bar_size, qty=qty_vs,
               length_in=length, shape="L",
               leg_a_in=p.h_adj, leg_b_in=tail_in,
               notes=f"Wall vert short walls @{spacing:.0f}oc, 1ft tail",
               source_rule=f"rule_{label.lower()}_wall_bars"),
        BarRow(mark="V2", size=bar_size, qty=qty_vl,
               length_in=length, shape="L",
               leg_a_in=p.h_adj, leg_b_in=tail_in,
               notes=f"Wall vert long walls @{spacing:.0f}oc, 1ft tail",
               source_rule=f"rule_{label.lower()}_wall_bars"),
    ]


# ---------------------------------------------------------------------------
# Shared top slab (Table 2, D72C — same for all G-types)
# ---------------------------------------------------------------------------

def _gt_top_slab(p: Params, log: ReasoningLogger, label: str) -> list[BarRow]:
    """
    Top slab A & B bars per D72C Table 2 (same for all G-types).

    A bars: #5@5" spanning across W (one bar per 5" along L)
    B bars: #5@5" spanning across L (one bar per 5" along W)
    """
    # A bars: qty along L, length = w_bar
    qty_a = max(2, math.ceil(p.l_bar / 5.0) + 1)
    len_a = p.w_bar

    # B bars: qty along W, length = l_bar
    qty_b = max(2, math.ceil(p.w_bar / 5.0) + 1)
    len_b = p.l_bar

    log.step(
        f"{label} top slab: A bars #5@5\" qty={qty_a} len={fmt_inches(len_a)}, "
        f"B bars #5@5\" qty={qty_b} len={fmt_inches(len_b)}",
        source=f"{label}TopSlab",
    )
    log.result("A1", f"#5 x {qty_a} @ {fmt_inches(len_a)}", "Top slab A bars @5oc",
               source=f"{label}TopSlab")
    log.result("B1", f"#5 x {qty_b} @ {fmt_inches(len_b)}", "Top slab B bars @5oc",
               source=f"{label}TopSlab")

    return [
        BarRow(mark="A1", size="#5", qty=qty_a,
               length_in=len_a, shape="Str",
               notes="Top slab A bars @5oc", source_rule=f"rule_{label.lower()}_top_slab"),
        BarRow(mark="B1", size="#5", qty=qty_b,
               length_in=len_b, shape="Str",
               notes="Top slab B bars @5oc", source_rule=f"rule_{label.lower()}_top_slab"),
    ]


# ---------------------------------------------------------------------------
# Shared hoops (Table 2, D72C — #4@5", same for all G-types)
# ---------------------------------------------------------------------------

def _gt_hoops(p: Params, log: ReasoningLogger, label: str) -> list[BarRow]:
    """
    Hoops per D72C Table 2: #4@5" rectangular, at grate level along L.
    Stock length = 2×(w + t) − bend_reduce(shape_4, #4) for 4-bend closed hoop.
    """
    from vistadetail.engine.hooks import bend_reduce

    qty    = math.ceil(p.l_bar / 5.0) + 1
    perim  = 2.0 * (p.w_bar + p.t_in)
    deduct = bend_reduce("shape_4", "#4")
    stock  = perim - deduct

    log.step(
        f"{label} hoops #4@5\": qty={qty}, perim={fmt_inches(perim)}, "
        f"−{deduct}\" bend deduction = {fmt_inches(stock)}",
        source=f"{label}Hoops",
    )
    log.result("HP", f"#4 x {qty} @ {fmt_inches(stock)}", "Hoops #4@5oc",
               source=f"{label}Hoops")

    return [
        BarRow(mark="HP", size="#4", qty=qty,
               length_in=stock, shape="Rect",
               leg_a_in=p.w_bar, leg_b_in=p.t_in,
               notes="#4 hoops @5oc", source_rule=f"rule_{label.lower()}_hoops"),
    ]


# ---------------------------------------------------------------------------
# Shared bottom mat (#4@12" each way — same for all G-types)
# ---------------------------------------------------------------------------

def _gt_bottom_mat(p: Params, log: ReasoningLogger, label: str) -> list[BarRow]:
    """Bottom mat: #4@12" each way."""
    qty_1 = math.ceil(p.l_bar / 12.0) + 1
    qty_2 = math.ceil(p.w_bar / 12.0) + 1

    log.step(
        f"{label} bottom mat #4@12\": "
        f"BM1={qty_1} len={fmt_inches(p.w_bar)}, BM2={qty_2} len={fmt_inches(p.l_bar)}",
        source=f"{label}BottomMat",
    )
    log.result("BM1", f"#4 x {qty_1} @ {fmt_inches(p.w_bar)}", "Bottom mat @12oc",
               source=f"{label}BottomMat")
    log.result("BM2", f"#4 x {qty_2} @ {fmt_inches(p.l_bar)}", "Bottom mat @12oc",
               source=f"{label}BottomMat")

    return [
        BarRow(mark="BM1", size="#4", qty=qty_1,
               length_in=p.w_bar, shape="Str",
               notes="Bottom mat W-dir @12oc", source_rule=f"rule_{label.lower()}_bottom_mat"),
        BarRow(mark="BM2", size="#4", qty=qty_2,
               length_in=p.l_bar, shape="Str",
               notes="Bottom mat L-dir @12oc", source_rule=f"rule_{label.lower()}_bottom_mat"),
    ]


# ===========================================================================
# G1  --  Simple box inlet, #4@12" all around  (D72B)
# ===========================================================================

def rule_g1_geometry(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """G1 CIP inlet geometry."""
    _gt_geometry(p, log, "G1")
    return []


def rule_g1_wall_bars(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """G1 wall bars: #4@12" all around (horizontal + vertical)."""
    horiz = _gt_wall_bars(p, log, "#4", 12.0, "G1")
    vert  = _gt_vert_bars(p, log, "#4", 12.0, "G1")
    return horiz + vert


def rule_g1_top_slab(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """G1 top slab A & B bars (Table 2, D72C)."""
    return _gt_top_slab(p, log, "G1")


def rule_g1_hoops(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """G1 hoops #4@5" (Table 2, D72C)."""
    return _gt_hoops(p, log, "G1")


def rule_g1_bottom_mat(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """G1 bottom mat #4@12" each way."""
    return _gt_bottom_mat(p, log, "G1")


def rule_g1_validate(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """Validate G1 inputs."""
    if p.x_dim_ft < 2.0:
        log.warn("L1 < 2ft -- minimum box length per D72.", source="G1Validate")
    if p.y_dim_ft < 2.0:
        log.warn("H < 2ft -- minimum box depth per D72.", source="G1Validate")
    if p.x_dim_ft > 20.0:
        log.warn(f"L1={p.x_dim_ft}ft is unusually long for a G1 inlet.", source="G1Validate")
    return []


# ===========================================================================
# G3  --  Extended wall variant, #4@12" all around + extension bars  (D72B)
# ===========================================================================

def rule_g3_geometry(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """G3 CIP inlet geometry (includes 2ft wall extension)."""
    _gt_geometry(p, log, "G3")
    # Extension wall adds 2ft (24") to one end
    ext_in = 24.0
    setattr(p, "ext_in", ext_in)
    log.step(f"G3 wall extension: {ext_in:.0f}\" (2ft per D72B EXTEND WALL note)",
             source="G3Geometry")
    return []


def rule_g3_wall_bars(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """G3 wall bars: #4@12" all around + extension wall bars."""
    horiz = _gt_wall_bars(p, log, "#4", 12.0, "G3")
    vert  = _gt_vert_bars(p, log, "#4", 12.0, "G3")

    # Extension wall bars (#4@12", 4 bars at top of extended wall section)
    ext_in = getattr(p, "ext_in", 24.0)
    hook   = 12.0
    qty_ew = 4
    len_ew = p.w_bar + 2.0 * hook

    log.step(f"G3 extension wall: {qty_ew} #4 bars, len={fmt_inches(len_ew)}",
             source="G3WallBars")
    log.result("EW", f"#4 x {qty_ew} @ {fmt_inches(len_ew)}", "Ext wall top bars",
               source="G3WallBars")

    ext_bars = [
        BarRow(mark="EW", size="#4", qty=qty_ew,
               length_in=len_ew, shape="U",
               leg_a_in=hook, leg_b_in=p.w_bar, leg_c_in=hook,
               notes="Extension wall top #4, 1ft hook EE",
               source_rule="rule_g3_wall_bars"),
    ]
    return horiz + vert + ext_bars


def rule_g3_top_slab(p: Params, log: ReasoningLogger) -> list[BarRow]:
    return _gt_top_slab(p, log, "G3")


def rule_g3_hoops(p: Params, log: ReasoningLogger) -> list[BarRow]:
    return _gt_hoops(p, log, "G3")


def rule_g3_bottom_mat(p: Params, log: ReasoningLogger) -> list[BarRow]:
    return _gt_bottom_mat(p, log, "G3")


def rule_g3_validate(p: Params, log: ReasoningLogger) -> list[BarRow]:
    if p.x_dim_ft < 2.0:
        log.warn("L1 < 2ft -- minimum box length per D72.", source="G3Validate")
    if p.y_dim_ft < 2.0:
        log.warn("H < 2ft -- minimum box depth per D72.", source="G3Validate")
    return []


# ===========================================================================
# G4  --  Concrete curb type, #5@12" all around  (D72B)
# ===========================================================================

def rule_g4_geometry(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """G4 CIP inlet geometry."""
    _gt_geometry(p, log, "G4")
    return []


def rule_g4_wall_bars(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """G4 wall bars: #5@12" all around (heavier than G1/G3)."""
    horiz = _gt_wall_bars(p, log, "#5", 12.0, "G4")
    vert  = _gt_vert_bars(p, log, "#5", 12.0, "G4")
    return horiz + vert


def rule_g4_top_slab(p: Params, log: ReasoningLogger) -> list[BarRow]:
    return _gt_top_slab(p, log, "G4")


def rule_g4_hoops(p: Params, log: ReasoningLogger) -> list[BarRow]:
    return _gt_hoops(p, log, "G4")


def rule_g4_bottom_mat(p: Params, log: ReasoningLogger) -> list[BarRow]:
    return _gt_bottom_mat(p, log, "G4")


def rule_g4_validate(p: Params, log: ReasoningLogger) -> list[BarRow]:
    if p.x_dim_ft < 2.0:
        log.warn("L1 < 2ft -- minimum box length per D72.", source="G4Validate")
    if p.y_dim_ft < 2.0:
        log.warn("H < 2ft -- minimum box depth per D72.", source="G4Validate")
    if p.x_dim_ft > 20.0:
        log.warn(f"L1={p.x_dim_ft}ft -- verify pipe penetration clearance (D72B Note 15).",
                 source="G4Validate")
    return []


# ===========================================================================
# G5  --  Detail A profile, #5@12" all around  (D72B)
# ===========================================================================

def rule_g5_geometry(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """G5 CIP inlet geometry."""
    _gt_geometry(p, log, "G5")
    return []


def rule_g5_wall_bars(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """G5 wall bars: #5@12" all around."""
    horiz = _gt_wall_bars(p, log, "#5", 12.0, "G5")
    vert  = _gt_vert_bars(p, log, "#5", 12.0, "G5")
    return horiz + vert


def rule_g5_top_slab(p: Params, log: ReasoningLogger) -> list[BarRow]:
    return _gt_top_slab(p, log, "G5")


def rule_g5_hoops(p: Params, log: ReasoningLogger) -> list[BarRow]:
    return _gt_hoops(p, log, "G5")


def rule_g5_bottom_mat(p: Params, log: ReasoningLogger) -> list[BarRow]:
    return _gt_bottom_mat(p, log, "G5")


def rule_g5_validate(p: Params, log: ReasoningLogger) -> list[BarRow]:
    if p.x_dim_ft < 2.0:
        log.warn("L1 < 2ft -- minimum box length per D72.", source="G5Validate")
    if p.y_dim_ft < 2.0:
        log.warn("H < 2ft -- minimum box depth per D72.", source="G5Validate")
    return []


# ===========================================================================
# G6  --  Same-slope gutter (no depression), #4@12" all around  (D72B)
# ===========================================================================

def rule_g6_geometry(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """G6 CIP inlet geometry -- flush with gutter, no depression."""
    _gt_geometry(p, log, "G6")
    log.step("G6: SAME SLOPE AS GUTTER -- no gutter depression.", source="G6Geometry")
    return []


def rule_g6_wall_bars(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """G6 wall bars: #4@12" all around (lightest G-type)."""
    horiz = _gt_wall_bars(p, log, "#4", 12.0, "G6")
    vert  = _gt_vert_bars(p, log, "#4", 12.0, "G6")
    return horiz + vert


def rule_g6_top_slab(p: Params, log: ReasoningLogger) -> list[BarRow]:
    return _gt_top_slab(p, log, "G6")


def rule_g6_hoops(p: Params, log: ReasoningLogger) -> list[BarRow]:
    return _gt_hoops(p, log, "G6")


def rule_g6_bottom_mat(p: Params, log: ReasoningLogger) -> list[BarRow]:
    return _gt_bottom_mat(p, log, "G6")


def rule_g6_validate(p: Params, log: ReasoningLogger) -> list[BarRow]:
    if p.x_dim_ft < 2.0:
        log.warn("L1 < 2ft -- minimum box length per D72.", source="G6Validate")
    if p.y_dim_ft < 2.0:
        log.warn("H < 2ft -- minimum box depth per D72.", source="G6Validate")
    return []
