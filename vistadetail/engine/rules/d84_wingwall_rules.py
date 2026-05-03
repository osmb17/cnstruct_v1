"""
Rule functions for Caltrans D84 Box Culvert Wingwall (Types A, B, C).

2025 Standard Plan D84 — Box Culvert Wingwalls, Types A, B and C.

Reinforcement confirmed from Section A-A and End Elevation on D84 plan:

  Face bars (main wall body): #4 @ 12" each face           → F1, F2
  Face bars (parapet zone, 3'-0" top): #5 @ 8" each face  → P1
  Continuous longitudinal bars: #5 Cont Tot 4 (2 per face) → L1, L2
  Parapet heavy bars: #8 Tot 7 (parapet zone, both faces)  → T2
  Parapet cap/base bars: #4 Tot 2 (End Elevation)          → T1
  Lower zone face bars: #5 @ 6" (bottom zone, near footing)→ V1
  Footing bottom mat: #6 @ 4±" each way                   → B1, B2
  Box wall connection ties: #4 Tot 3 (Detail X)            → BO
  Cutoff wall: per footing plan (B3-5)

Bar marks follow D84 Section A-A and End Elevation labels.
"""

from __future__ import annotations
import math
from vistadetail.engine.reasoning_logger import ReasoningLogger
from vistadetail.engine.schema import BarRow, fmt_inches


# Parapet height per D84 End Elevation label — "HP 3'-0" Min"
_PARAPET_HT_IN = 36.0   # 3'-0"

# Lower zone height (near footing) where face bars tighten to #5@6
# D84 Section A-A shows this zone; using 2'-6" as read from section proportion
_LOWER_ZONE_HT_IN = 30.0  # 2'-6"


def rule_d84_validate(p, log: ReasoningLogger) -> list[BarRow]:
    """Validate D84 inputs."""
    if p.wall_height_ft <= 0:
        log.warn("Wall height H must be > 0", source="D84Validate")
    if p.wall_length_ft <= 0:
        log.warn("Wall length LOL must be > 0", source="D84Validate")
    if p.wall_height_ft > 20.0:
        log.warn(
            f"H={p.wall_height_ft}ft exceeds D84 max (~20ft) — verify with engineer",
            source="D84Validate",
        )
    return []


def rule_d84_geometry(p, log: ReasoningLogger) -> list[BarRow]:
    """Log key geometry values."""
    h_in   = p.wall_height_ft * 12
    lol_in = p.wall_length_ft * 12
    log.step(
        f"D84 Geometry: H={p.wall_height_ft}ft ({h_in:.0f}\")  "
        f"LOL={p.wall_length_ft}ft ({lol_in:.0f}\")",
        source="D84WingwallGeometry",
    )
    return []


def rule_d84_face_horiz(p, log: ReasoningLogger) -> list[BarRow]:
    """
    Main wall face horizontal bars — #4 @ 12" each face.
    Confirmed from Section A-A on D84 plan.

    Runs the full wall height minus the parapet zone (parapet has #5@8 instead).
    Qty per face = floor(main_wall_height_in / 12) + 1.
    Length = LOL (full wall length).
    """
    h_in     = p.wall_height_ft * 12
    lol_in   = p.wall_length_ft * 12
    spac     = 12.0   # D84 Section A-A: #4 @ 12"

    # Main wall zone = total H minus parapet (top) and lower zone (bottom)
    # Lower zone is only subtracted if wall is tall enough to have it
    lower = _LOWER_ZONE_HT_IN if h_in > _PARAPET_HT_IN + _LOWER_ZONE_HT_IN else 0.0
    main_ht = max(h_in - _PARAPET_HT_IN - lower, 0.0)
    qty_per_face = max(1, math.floor(main_ht / spac) + 1)

    log.step(
        f"F-bars (#4@12\"): main zone=H-parapet-lower={h_in:.0f}-{_PARAPET_HT_IN:.0f}-{lower:.0f}={main_ht:.0f}\"  "
        f"qty/face={qty_per_face}  len=LOL={fmt_inches(lol_in)}",
        source="D84FaceHoriz",
    )
    log.result("F1", f"#4 × {qty_per_face} @ {fmt_inches(lol_in)}", "Front face horiz @12\" oc",
               source="D84FaceHoriz")
    log.result("F2", f"#4 × {qty_per_face} @ {fmt_inches(lol_in)}", "Rear face horiz @12\" oc",
               source="D84FaceHoriz")

    return [
        BarRow(mark="F1", size="#4", qty=qty_per_face, length_in=lol_in, shape="Str",
               notes="Front face horiz @12\" oc  main wall body",
               source_rule="rule_d84_face_horiz"),
        BarRow(mark="F2", size="#4", qty=qty_per_face, length_in=lol_in, shape="Str",
               notes="Rear face horiz @12\" oc  main wall body",
               source_rule="rule_d84_face_horiz"),
    ]


def rule_d84_parapet_face(p, log: ReasoningLogger) -> list[BarRow]:
    """
    Parapet zone face bars — #5 @ 8" each face.
    Confirmed from Section A-A on D84 plan (top zone, HP=3'-0" min).

    Qty per face = floor(parapet_ht / 8) + 1 = floor(36/8) + 1 = 5.
    Length = LOL.
    """
    lol_in       = p.wall_length_ft * 12
    spac         = 8.0   # D84 Section A-A: #5 @ 8" in parapet zone
    qty_per_face = math.floor(_PARAPET_HT_IN / spac) + 1

    log.step(
        f"P1 parapet face bars (#5@8\"): zone={_PARAPET_HT_IN:.0f}\"  "
        f"qty/face=floor({_PARAPET_HT_IN:.0f}/{spac:.0f})+1={qty_per_face}  len={fmt_inches(lol_in)}",
        source="D84ParapetFace",
    )
    log.result("P1", f"#5 × {qty_per_face * 2} @ {fmt_inches(lol_in)}",
               "Parapet face bars #5@8\" EF", source="D84ParapetFace")

    total = qty_per_face * 2   # both faces
    return [BarRow(
        mark="P1", size="#5", qty=total, length_in=lol_in, shape="Str",
        notes=f"Parapet face bars @8\" oc EF  {_PARAPET_HT_IN:.0f}\" parapet zone  {qty_per_face}/face × 2",
        source_rule="rule_d84_parapet_face",
    )]


def rule_d84_lower_face(p, log: ReasoningLogger) -> list[BarRow]:
    """
    Lower zone face bars — #5 @ 6" each face near the footing (bottom zone).
    Confirmed from Section A-A on D84 plan.

    Zone height = 2'-6" (read from section proportion).
    Qty per face = floor(lower_zone_ht / 6) + 1 = floor(30/6) + 1 = 6.
    Length = LOL.
    """
    h_in   = p.wall_height_ft * 12
    lol_in = p.wall_length_ft * 12
    spac   = 6.0   # D84 Section A-A: #5 @ 6" near footing

    # Only add if wall is tall enough to have a distinct lower zone
    if h_in <= _PARAPET_HT_IN + _LOWER_ZONE_HT_IN:
        log.step(
            f"V1 lower zone: H={h_in:.0f}\" too short for separate lower zone — skipped",
            source="D84LowerFace",
        )
        return []

    qty_per_face = math.floor(_LOWER_ZONE_HT_IN / spac) + 1
    total = qty_per_face * 2

    log.step(
        f"V1 lower zone (#5@6\"): zone={_LOWER_ZONE_HT_IN:.0f}\"  "
        f"qty/face={qty_per_face}  total EF={total}  len={fmt_inches(lol_in)}",
        source="D84LowerFace",
    )
    log.result("V1", f"#5 × {total} @ {fmt_inches(lol_in)}",
               "Lower zone face bars #5@6\" EF", source="D84LowerFace")

    return [BarRow(
        mark="V1", size="#5", qty=total, length_in=lol_in, shape="Str",
        notes=f"Lower zone face bars @6\" oc EF  {_LOWER_ZONE_HT_IN:.0f}\" zone near footing",
        source_rule="rule_d84_lower_face",
    )]


def rule_d84_longitudinals(p, log: ReasoningLogger) -> list[BarRow]:
    """
    Continuous longitudinal bars — #5 Cont Tot 4 (2 per face, each face).
    Confirmed from Section A-A on D84 plan: "#5 Cont, Tot 4"

    Run full wall height on each face.
    Per D84 plan note: "EXTEND ALL LONGITUDINAL BARS IN BOX WALLS 2'-0"
    INTO WINGWALLS" — so bar length = LOL + 2'-0" extension into box wall.
    """
    lol_in    = p.wall_length_ft * 12
    lap_in    = 24.0   # 2'-0" lap extension into box wall per D84 plan note
    length_in = lol_in + lap_in
    qty_total = 4      # D84 Section A-A: #5 Cont Tot 4

    log.step(
        f"L-bars (#5 Cont Tot 4): LOL+2'={fmt_inches(lol_in)}+{lap_in:.0f}\"={fmt_inches(length_in)}  "
        f"total=4 (2 each face)",
        source="D84Longitudinals",
    )
    log.result("L1", f"#5 × 2 @ {fmt_inches(length_in)}", "Front longitudinal bars",
               source="D84Longitudinals")
    log.result("L2", f"#5 × 2 @ {fmt_inches(length_in)}", "Rear longitudinal bars",
               source="D84Longitudinals")

    return [
        BarRow(mark="L1", size="#5", qty=2, length_in=length_in, shape="Str",
               notes="Front longitudinal #5 Cont  incl 2'-0\" ext into box wall",
               source_rule="rule_d84_longitudinals"),
        BarRow(mark="L2", size="#5", qty=2, length_in=length_in, shape="Str",
               notes="Rear longitudinal #5 Cont  incl 2'-0\" ext into box wall",
               source_rule="rule_d84_longitudinals"),
    ]


def rule_d84_top_bars(p, log: ReasoningLogger) -> list[BarRow]:
    """
    Top/parapet bars — confirmed from Section A-A and End Elevation on D84 plan.

    T1: #4 Tot 2 — parapet cap bars (from End Elevation detail)
         Length = LOL (run along wall length at parapet top).
    T2: #8 Tot 7 — parapet heavy longitudinal bars (from Section A-A "#8 Tot 7")
         Length = LOL.
    """
    lol_in = p.wall_length_ft * 12

    log.step(
        f"Top bars: T1=#4 × 2, T2=#8 × 7  len=LOL={fmt_inches(lol_in)}",
        source="D84TopBars",
    )
    log.result("T1", f"#4 × 2 @ {fmt_inches(lol_in)}", "Parapet cap bars #4 Tot 2",
               source="D84TopBars")
    log.result("T2", f"#8 × 7 @ {fmt_inches(lol_in)}", "Parapet heavy bars #8 Tot 7",
               source="D84TopBars")

    return [
        BarRow(mark="T1", size="#4", qty=2, length_in=lol_in, shape="Str",
               notes="Parapet cap bars #4 Tot 2  (End Elevation)",
               source_rule="rule_d84_top_bars"),
        BarRow(mark="T2", size="#8", qty=7, length_in=lol_in, shape="Str",
               notes="Parapet heavy bars #8 Tot 7  (Section A-A)",
               source_rule="rule_d84_top_bars"),
    ]


def rule_d84_footing_mat(p, log: ReasoningLogger) -> list[BarRow]:
    """
    Footing bottom mat — #6 @ 4±" each way.
    Confirmed from Section A-A on D84 plan (bottom of section shows #6 @ 4±").

    Footing width B per D84 Typical Layout: total width = wall_thick + 2B.
    B is not tabulated on D84 (varies by project); defaults to 0.5×H each side.

    B1 = transverse bars (run across footing width), qty = floor(LOL/4) + 1
    B2 = longitudinal bars (run along footing length = LOL), qty = floor(ftg_w/4) + 1
    """
    lol_in   = p.wall_length_ft * 12
    t_in     = 9.0   # standard 9" wall thickness per D84
    B_in     = p.wall_height_ft * 0.5 * 12   # B each side = 0.5 × H (conservative default)
    ftg_w_in = t_in + 2 * B_in
    spac     = 4.5   # D84 Section A-A: #6 @ 4±" (using 4.5" as nominal)

    qty_trans = math.floor(lol_in / spac) + 1
    qty_long  = math.floor(ftg_w_in / spac) + 1

    log.step(
        f"Footing mat (#6@4±\"): B={fmt_inches(B_in)} each side  "
        f"ftg_w={fmt_inches(ftg_w_in)}  B1={qty_trans} trans  B2={qty_long} long",
        source="D84FootingMat",
    )
    log.result("B1", f"#6 × {qty_trans} @ {fmt_inches(ftg_w_in)}", "Footing transverse #6@4±",
               source="D84FootingMat")
    log.result("B2", f"#6 × {qty_long} @ {fmt_inches(lol_in)}", "Footing longitudinal #6@4±",
               source="D84FootingMat")

    return [
        BarRow(mark="B1", size="#6", qty=qty_trans, length_in=ftg_w_in, shape="Str",
               notes=f"Footing transverse #6@4±\" oc  ftg width={fmt_inches(ftg_w_in)}",
               source_rule="rule_d84_footing_mat"),
        BarRow(mark="B2", size="#6", qty=qty_long, length_in=lol_in, shape="Str",
               notes=f"Footing longitudinal #6@4±\" oc  len=LOL={fmt_inches(lol_in)}",
               source_rule="rule_d84_footing_mat"),
    ]


def rule_d84_box_ties(p, log: ReasoningLogger) -> list[BarRow]:
    """
    Box wall connection tie bars — #4 Tot 3 (Detail X on D84 plan).
    Hooked into box wall through neoprene strip at wall-to-box junction.
    Length = wall thickness + hook development = 9" wall + 12" hook = 21".
    """
    tie_len = 9.0 + 12.0   # wall thickness + hook development
    qty     = 3             # D84 Detail X: #4 Tot 3

    log.step(
        f"BO box ties (#4 Tot 3): len=wall_t+hook=9+12={tie_len:.0f}\"  Detail X",
        source="D84BoxTies",
    )
    log.result("BO", f"#4 × {qty} @ {fmt_inches(tie_len)}", "Box wall tie bars Detail X",
               source="D84BoxTies")

    return [BarRow(
        mark="BO", size="#4", qty=qty, length_in=tie_len, shape="L",
        notes="Box wall connection ties #4 Tot 3  (Detail X, neoprene strip junction)",
        source_rule="rule_d84_box_ties",
    )]


def rule_d84_cutoff_wall(p, log: ReasoningLogger) -> list[BarRow]:
    """
    Cutoff wall bars at toe of slope — #4 Tol 3 (per D84 detail and Section B-B).
    D84 Note 6: eliminate cutoff wall if channel is paved and skew ≤ 20°.
    Length = footing width.
    """
    t_in     = 9.0
    B_in     = p.wall_height_ft * 0.5 * 12
    ftg_w_in = t_in + 2 * B_in
    qty      = 3   # D84: #4 Tot 3 at cutoff wall

    log.step(
        f"CW cutoff wall (#4 Tot 3): len=ftg_w={fmt_inches(ftg_w_in)}",
        source="D84CutoffWall",
    )
    log.result("CW", f"#4 × {qty} @ {fmt_inches(ftg_w_in)}", "Cutoff wall #4 Tot 3",
               source="D84CutoffWall")

    return [BarRow(
        mark="CW", size="#4", qty=qty, length_in=ftg_w_in, shape="Str",
        notes="Cutoff wall #4 Tot 3  (D84 Note 6: eliminate if paved channel & skew ≤20°)",
        source_rule="rule_d84_cutoff_wall",
    )]
