"""
Rule functions for Straight Headwall template (D89A).

Dimensions looked up from the Caltrans D89A standard plan table by wall
height.  Bar sizes and spacings are hard-coded per the D89A standard.

Marks produced:
  D1  — top invert transverse bars   (#5 @ 8" oc)
  TF  — transverse footing bars      (#4 @ 12" oc)
  LI  — longitudinal invert bars     (#4 @ 8" oc, 2 layers)
  LW  — longitudinal wall bars       (#4 @ 12" oc, 2 faces)
  TW  — top-of-wall bars             (#5, 3 total)
  VW  — vertical wall bars           (#4 @ 12" oc)
  CB  — C-bar hairpin                (#4 @ 12" oc, shape_2, legs=14")
  WS  — wall spreaders               (#4, U-shape @ 24" oc)
  ST  — mat standees                 (#5, S-shape @ 12" oc)
"""

from __future__ import annotations

import math

from vistadetail.engine.hooks import bend_reduce
from vistadetail.engine.reasoning_logger import ReasoningLogger
from vistadetail.engine.schema import BarRow, Params, fmt_inches


# ---------------------------------------------------------------------------
# Caltrans D89A lookup table — keyed by row index, ordered by H.
# Source: Caltrans Standard Plan sheet D89A.
#
# H   = design wall height (in)
# T   = wall thickness (in)
# W   = footing width (in)
# C   = toe (front projection, in)
# B   = heel (back projection, in)
# F   = footing depth (in)
# c_s = "c" bar size (#4 or #5)
# c_p = "c" bar spacing (in)
# d_s = "d" bar size (#5 or #6)
# d_p = "d" bar spacing (in)
# ---------------------------------------------------------------------------

_D89A_ROWS: list[dict] = [
    # H   T    W   C   B   F  c_s   c_p  d_s   d_p    label
    {"H": 47, "T": 10, "W": 58, "C": 12, "B": 46, "F": 12, "c_s": "#4", "c_p": 12, "d_s": "#5", "d_p": 12},  # 3'-11"
    {"H": 50, "T": 10, "W": 58, "C": 12, "B": 46, "F": 12, "c_s": "#4", "c_p": 12, "d_s": "#5", "d_p": 12},  # 4'-2"
    {"H": 53, "T": 10, "W": 60, "C": 12, "B": 48, "F": 12, "c_s": "#4", "c_p": 12, "d_s": "#5", "d_p":  8},  # 4'-5"
    {"H": 56, "T": 10, "W": 64, "C": 16, "B": 48, "F": 12, "c_s": "#4", "c_p": 12, "d_s": "#5", "d_p":  8},  # 4'-8"
    {"H": 59, "T": 10, "W": 64, "C": 16, "B": 48, "F": 12, "c_s": "#4", "c_p": 12, "d_s": "#5", "d_p":  8},  # 4'-11"
    {"H": 62, "T": 10, "W": 64, "C": 16, "B": 48, "F": 12, "c_s": "#4", "c_p": 12, "d_s": "#5", "d_p":  8},  # 5'-2"
    {"H": 65, "T": 10, "W": 64, "C": 16, "B": 48, "F": 12, "c_s": "#4", "c_p": 12, "d_s": "#5", "d_p":  8},  # 5'-5"
    {"H": 68, "T": 10, "W": 64, "C": 16, "B": 48, "F": 12, "c_s": "#4", "c_p": 12, "d_s": "#6", "d_p":  8},  # 5'-8"
    {"H": 71, "T": 10, "W": 64, "C": 16, "B": 48, "F": 12, "c_s": "#5", "c_p": 12, "d_s": "#6", "d_p":  8},  # 5'-11"
    {"H": 74, "T": 12, "W": 64, "C": 16, "B": 48, "F": 14, "c_s": "#5", "c_p": 12, "d_s": "#6", "d_p":  8},  # 6'-2"
    {"H": 77, "T": 12, "W": 66, "C": 18, "B": 48, "F": 14, "c_s": "#5", "c_p": 12, "d_s": "#6", "d_p":  8},  # 6'-5"
    {"H": 80, "T": 12, "W": 69, "C": 18, "B": 51, "F": 14, "c_s": "#5", "c_p":  9, "d_s": "#6", "d_p":  6},  # 6'-8"
    {"H": 83, "T": 12, "W": 72, "C": 18, "B": 54, "F": 14, "c_s": "#5", "c_p":  9, "d_s": "#6", "d_p":  6},  # 6'-11"
]

_COVER_STEM = 2.0   # wall face cover (in)
_COVER_FTG  = 3.0   # footing bottom cover (in)


def _d89_by_height(h_in: float) -> dict:
    """Return first D89A row whose H >= h_in (round up for safety)."""
    for row in _D89A_ROWS:
        if row["H"] >= h_in:
            return row
    return _D89A_ROWS[-1]


# ---------------------------------------------------------------------------
# Rule functions
# ---------------------------------------------------------------------------

def rule_hw_d_bars(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """D1 — Top invert D-bars, transverse (#5 @ 8" oc)."""
    L   = p.wall_width_ft * 12
    H   = float(p.pipe_dia_in.replace('"', '')) + 11.0
    row = _d89_by_height(H)
    W   = row["W"]
    qty    = math.floor(L / 8) + 1
    length = W - 4.0

    log.step(f"D89A H={H:.0f}\" → W={W}\"  |  D1: ⌊{L}/8⌋+1={qty} @ {fmt_inches(length)}",
             source="HeadwallRules")
    log.result("D1", f"#5 × {qty} @ {fmt_inches(length)}", source="HeadwallRules")

    return [BarRow(
        mark="D1", size="#5", qty=qty, length_in=length, shape="Str",
        notes=f"Top invert trans @8\" oc  W={fmt_inches(W)}-4\"",
        source_rule="rule_hw_d_bars",
    )]


def rule_hw_trans_footing(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """TF — Transverse footing bars (#4 @ 12" oc)."""
    L   = p.wall_width_ft * 12
    H   = float(p.pipe_dia_in.replace('"', '')) + 11.0
    row = _d89_by_height(H)
    W   = row["W"]
    qty    = math.floor(L / 12) + 1
    length = W - 4.0

    log.step(f"TF: ⌊{L}/12⌋+1={qty} × #4 @ {fmt_inches(length)}", source="HeadwallRules")
    log.result("TF", f"#4 × {qty} @ {fmt_inches(length)}", source="HeadwallRules")

    return [BarRow(
        mark="TF", size="#4", qty=qty, length_in=length, shape="Str",
        notes=f"Trans footing @12\" oc  W={fmt_inches(W)}-4\"",
        source_rule="rule_hw_trans_footing",
    )]


def rule_hw_long_invert(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """LI — Longitudinal invert bars, 2 layers (#4 @ 8" oc)."""
    L   = p.wall_width_ft * 12
    H   = float(p.pipe_dia_in.replace('"', '')) + 11.0
    row = _d89_by_height(H)
    W   = row["W"]
    qty    = 2 * math.floor(W / 8)
    length = L - 6.0

    log.step(f"LI: 2×⌊{W}/8⌋={qty} × #4 @ {fmt_inches(length)}", source="HeadwallRules")
    log.result("LI", f"#4 × {qty} @ {fmt_inches(length)}", source="HeadwallRules")

    return [BarRow(
        mark="LI", size="#4", qty=qty, length_in=length, shape="Str",
        notes=f"Long invert 2-layer @8\" oc  W={fmt_inches(W)}",
        source_rule="rule_hw_long_invert",
    )]


def rule_hw_long_wall(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """LW — Longitudinal wall bars, 2 faces (#4 @ 12" oc).

    Qty based on actual wall height; length based on wall width.
    """
    L   = p.wall_width_ft * 12
    H_w = p.wall_height_ft * 12       # actual wall height for bar count
    H1  = H_w + 12.0                  # include 1'-0" extension per D89A note
    qty    = 2 * (math.floor(H1 / 12) + 1)
    length = L - 4.0

    log.step(f"LW: H_wall={H_w:.0f}\"  H1={H1:.0f}\"  2×(⌊{H1}/12⌋+1)={qty} × #4 @ {fmt_inches(length)}",
             source="HeadwallRules")
    log.result("LW", f"#4 × {qty} @ {fmt_inches(length)}", source="HeadwallRules")

    return [BarRow(
        mark="LW", size="#4", qty=qty, length_in=length, shape="Str",
        notes=f"Long wall 2-face @12\" oc  H1={fmt_inches(H1)}",
        source_rule="rule_hw_long_wall",
    )]


def rule_hw_top_wall(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """TW — Top-of-wall bars (#5, 3 total)."""
    L      = p.wall_width_ft * 12
    qty    = 3
    length = L - 4.0

    log.step(f"TW: 3 × #5 @ {fmt_inches(length)}", source="HeadwallRules")
    log.result("TW", f"#5 × 3 @ {fmt_inches(length)}", source="HeadwallRules")

    return [BarRow(
        mark="TW", size="#5", qty=qty, length_in=length, shape="Str",
        notes="Top of wall #5 Tot 3",
        source_rule="rule_hw_top_wall",
    )]


def rule_hw_vert_wall(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """VW — Vertical wall bars (#4 @ 12" oc)."""
    L  = p.wall_width_ft * 12
    H  = float(p.pipe_dia_in.replace('"', '')) + 11.0
    H1 = H + 12.0
    qty    = math.floor(L / 12) + 1
    length = H1 - 2 * _COVER_STEM

    log.step(f"VW: ⌊{L}/12⌋+1={qty} × #4 @ {fmt_inches(length)}  (H1={H1:.0f}\"-4\")",
             source="HeadwallRules")
    log.result("VW", f"#4 × {qty} @ {fmt_inches(length)}", source="HeadwallRules")

    return [BarRow(
        mark="VW", size="#4", qty=qty, length_in=length, shape="Str",
        notes=f"Vert wall @12\" oc  H1-2×cover={fmt_inches(length)}",
        source_rule="rule_hw_vert_wall",
    )]


def rule_hw_c_bars(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    CB — C-bar hairpin (#4 @ 12" oc).

    U/C hairpin spanning wall height H1 with two 14" horizontal legs.
    Body ("0") = H1 − 2 × 2" cover = H1 − 4".
    Inner ("d") = H (actual wall height input, between bend tangent points).
    Stock = body + 2 × leg − bend_reduce("shape_2", "#4").
    """
    L      = p.wall_width_ft * 12
    H      = float(p.pipe_dia_in.replace('"', '')) + 11.0
    H1     = H + 12.0
    c_cov  = 2.0          # 2" clear cover at each leg tip (standard)
    body   = H1 - 2 * c_cov   # outer span = "0" dimension in barlist sketch
    inner  = H            # inner dimension = wall height = "d" in barlist sketch
    leg    = 14.0
    R      = 9.0
    deduct = bend_reduce("shape_2", "#4")
    stock  = body + 2 * leg - deduct
    qty    = math.floor(L / 12) + 1

    log.step(
        f"CB: H1={H1:.0f}\"  body={fmt_inches(body)}  inner={fmt_inches(inner)}  "
        f"legs=1'-2\"×2  R=9\"  stock={fmt_inches(stock)}",
        source="HeadwallRules",
    )
    log.step(f"qty=⌊{L}/12⌋+1={qty}", source="HeadwallRules")
    log.result("CB", f"#4 × {qty} @ {fmt_inches(stock)}", source="HeadwallRules")

    return [BarRow(
        mark="CB", size="#4", qty=qty, length_in=stock, shape="C",
        leg_a_in=body, leg_b_in=leg, leg_c_in=leg, leg_d_in=inner,
        notes=f"C-bar @12\" oc  body={fmt_inches(body)}  inner={fmt_inches(inner)}  legs=1'-2\"×2  R=9\"",
        source_rule="rule_hw_c_bars",
    )]


def rule_hw_spreaders(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    WS — Wall spreaders (#4, U-shape, @ 24" oc).

    Body = 5", legs = 4.5" each.
    Stock = 5 + 2×4.5 − bend_reduce("shape_2", "#4").
    """
    L      = p.wall_width_ft * 12
    body   = 5.0
    leg    = 4.5
    deduct = bend_reduce("shape_2", "#4")
    stock  = body + 2 * leg - deduct
    qty    = math.floor(L / 24)

    log.step(
        f"WS: body=5\"  legs=4.5\"×2  stock={fmt_inches(stock)}  "
        f"qty=⌊{L}/24⌋={qty}",
        source="HeadwallRules",
    )
    log.result("WS", f"#4 × {qty} @ {fmt_inches(stock)}", source="HeadwallRules")

    return [BarRow(
        mark="WS", size="#4", qty=qty, length_in=stock, shape="U",
        leg_a_in=body, leg_b_in=leg, leg_c_in=leg,
        notes="Wall spreader U-shape  body=5\"  legs=4.5\"×2",
        source_rule="rule_hw_spreaders",
    )]


def rule_hw_standees(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    ST — Mat standees (#5, S-shape, @ 12" oc).

    Four segments: top=5.5", riser=6", seat=5.5", base=18".
    Stock = 5.5+6+5.5+18 − bend_reduce("shape_3", "#5").
    """
    L      = p.wall_width_ft * 12
    seg_a  = 5.5    # top hook
    seg_b  = 6.0    # riser
    seg_c  = 5.5    # seat
    seg_d  = 18.0   # base
    deduct = bend_reduce("shape_3", "#5")
    stock  = seg_a + seg_b + seg_c + seg_d - deduct
    qty    = math.floor(L / 12)

    log.step(
        f"ST: 5.5+6+5.5+18={seg_a+seg_b+seg_c+seg_d}\" − {deduct}={stock}\"  "
        f"qty=⌊{L}/12⌋={qty}",
        source="HeadwallRules",
    )
    log.result("ST", f"#5 × {qty} @ {fmt_inches(stock)}", source="HeadwallRules")

    return [BarRow(
        mark="ST", size="#5", qty=qty, length_in=stock, shape="S",
        leg_a_in=seg_a, leg_b_in=seg_b, leg_c_in=seg_c, leg_d_in=seg_d,
        notes="Mat standee S-shape  5.5\"+6\"+5.5\"+18\"",
        source_rule="rule_hw_standees",
    )]


def rule_validate_headwall(p: Params, log: ReasoningLogger) -> list[BarRow]:
    H = float(p.pipe_dia_in.replace('"', '')) + 11.0
    if H > 89:
        log.warn(
            f"Wall height {fmt_inches(H)} exceeds D89A table max 7'-5\" — "
            "using largest table row (54\" pipe)",
            source="HeadwallRules",
        )
    return []
