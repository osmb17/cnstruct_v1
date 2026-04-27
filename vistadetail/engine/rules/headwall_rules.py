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
  ST  — mat standees                 (#5, S-shape @ 4'-0" oc + 1)
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
    {"H": 53, "T": 10, "W": 60, "C": 12, "B": 48, "F": 12, "c_s": "#4", "c_p": 12, "d_s": "#5", "d_p": 12},  # 4'-5"
    {"H": 56, "T": 10, "W": 64, "C": 14, "B": 48, "F": 12, "c_s": "#4", "c_p": 12, "d_s": "#5", "d_p":  8},  # 4'-8"
    {"H": 59, "T": 10, "W": 64, "C": 14, "B": 48, "F": 12, "c_s": "#4", "c_p": 12, "d_s": "#5", "d_p":  8},  # 4'-11"
    {"H": 62, "T": 10, "W": 64, "C": 14, "B": 48, "F": 12, "c_s": "#4", "c_p": 12, "d_s": "#5", "d_p":  8},  # 5'-2"
    {"H": 65, "T": 10, "W": 64, "C": 14, "B": 48, "F": 12, "c_s": "#4", "c_p": 12, "d_s": "#5", "d_p":  8},  # 5'-5"
    {"H": 68, "T": 10, "W": 64, "C": 14, "B": 48, "F": 12, "c_s": "#4", "c_p": 12, "d_s": "#6", "d_p":  8},  # 5'-8"
    {"H": 71, "T": 10, "W": 64, "C": 14, "B": 48, "F": 12, "c_s": "#5", "c_p": 12, "d_s": "#6", "d_p":  8},  # 5'-11"
    {"H": 74, "T": 12, "W": 64, "C": 16, "B": 48, "F": 14, "c_s": "#5", "c_p": 12, "d_s": "#6", "d_p":  8},  # 6'-2"
    {"H": 77, "T": 12, "W": 66, "C": 18, "B": 48, "F": 14, "c_s": "#5", "c_p": 12, "d_s": "#6", "d_p":  6},  # 6'-5"
    {"H": 80, "T": 12, "W": 69, "C": 18, "B": 51, "F": 14, "c_s": "#5", "c_p":  9, "d_s": "#6", "d_p":  6},  # 6'-8"
    {"H": 83, "T": 12, "W": 72, "C": 18, "B": 54, "F": 14, "c_s": "#5", "c_p":  9, "d_s": "#6", "d_p":  6},  # 6'-11"
]

_COVER_STEM = 2.0   # wall face cover (in)
_COVER_FTG  = 2.0   # footing bottom/top cover (in) — "2" Clr" per D89A typical section


_D89A_MAX_H = _D89A_ROWS[-1]["H"]   # 83" — table ceiling


def _d89_by_height(h_in: float) -> dict:
    """Return first D89A row whose H >= h_in (round up for safety)."""
    for row in _D89A_ROWS:
        if row["H"] >= h_in:
            return row
    return _D89A_ROWS[-1]


def _h1(p: Params) -> float:
    """
    Total height from bottom of footing to top of wall (inches).
    H1 = wall_height_in + F, where F is the footing depth from the D89A row.
    """
    H_in = p.wall_height_ft * 12
    row  = _d89_by_height(H_in)
    return H_in + row["F"]


# ---------------------------------------------------------------------------
# Rule functions
# ---------------------------------------------------------------------------

def rule_hw_d_bars(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """D1 — Top invert D-bars, transverse (size and spacing from D89A table)."""
    L      = p.wall_width_ft * 12
    H      = p.wall_height_ft * 12
    row    = _d89_by_height(H)
    W      = row["W"]
    d_size = row["d_s"]          # "#5" or "#6" per D89A table
    d_sp   = int(row["d_p"])     # spacing in inches per D89A table
    qty    = math.floor(L / d_sp) + 1
    length = W - 4.0

    log.step(f"D89A H={H:.0f}\" → W={W}\"  |  D1: {d_size}@{d_sp}\"  ⌊{L}/{d_sp}⌋+1={qty} @ {fmt_inches(length)}",
             source="HeadwallRules")
    log.result("D1", f"{d_size} × {qty} @ {fmt_inches(length)}", source="HeadwallRules")

    return [BarRow(
        mark="D1", size=d_size, qty=qty, length_in=length, shape="Str",
        notes=f"D bars @{d_sp}\" oc  W={fmt_inches(W)}-4\"",
        source_rule="rule_hw_d_bars",
    )]


def rule_hw_trans_footing(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """TF — Transverse footing bars (#4 @ 12" oc)."""
    L   = p.wall_width_ft * 12
    H   = p.wall_height_ft * 12
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
    H   = p.wall_height_ft * 12
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
    """LW — Longitudinal wall bars, 2 faces (#4 @ 12" oc)."""
    L  = p.wall_width_ft * 12
    H  = p.wall_height_ft * 12
    H1 = _h1(p)
    qty    = 2 * (math.floor(H1 / 12) + 1)
    length = L - 4.0

    log.step(f"LW: H1={H1:.0f}\"  2×(⌊{H1}/12⌋+1)={qty} × #4 @ {fmt_inches(length)}",
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
    H  = p.wall_height_ft * 12
    H1 = _h1(p)
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
    CB — C-bar hairpin (size and spacing from D89A c_s/c_p columns).

    Body ("0") = H1 − 2 × 2" cover.
    Leg ("B")  = D89A C dimension − 2"  (toe projection minus 2" cover).
    Inner ("d") = H (design wall height).
    Stock = body + 2 × leg − bend_reduce("shape_2", c_size).
    """
    L      = p.wall_width_ft * 12
    H      = p.wall_height_ft * 12
    H1     = _h1(p)
    row    = _d89_by_height(H)
    c_size = row["c_s"]
    c_sp   = int(row["c_p"])
    c_cov  = 2.0
    body   = H1 - 2 * c_cov          # "0" dimension
    inner  = H                        # "d" dimension
    leg    = float(row["C"]) - 2.0    # D89A toe projection − 2" cover
    R      = 9.0
    deduct = bend_reduce("shape_2", c_size)
    stock  = body + 2 * leg - deduct
    qty    = math.floor(L / c_sp) + 1

    log.step(
        f"D89A H={H:.0f}\" → c_size={c_size} @{c_sp}\"  C={fmt_inches(row['C'])}  "
        f"CB: body={fmt_inches(body)}  leg=C-2\"={fmt_inches(leg)}  stock={fmt_inches(stock)}",
        source="HeadwallRules",
    )
    log.step(f"qty=⌊{L}/{c_sp}⌋+1={qty}", source="HeadwallRules")
    log.result("CB", f"{c_size} × {qty} @ {fmt_inches(stock)}", source="HeadwallRules")

    return [BarRow(
        mark="CB", size=c_size, qty=qty, length_in=stock, shape="C",
        leg_a_in=body, leg_b_in=leg, leg_c_in=float(row["C"]), leg_d_in=inner, leg_g_in=R,
        notes=f"C-bar @{c_sp}\" oc",
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
    ST — Mat standees (#5, S-shape, @ 4'-0" oc + 1 extra).

    Four segments: top=5.5", riser=6", seat=5.5", base=18".
    Stock = 5.5+6+5.5+18 − bend_reduce("shape_3", "#5").
    Qty = floor(L / 48) + 1 (one per 4 ft, plus one additional).
    """
    L      = p.wall_width_ft * 12
    seg_a  = 5.5    # top hook
    seg_b  = 6.0    # riser
    seg_c  = 5.5    # seat
    seg_d  = 18.0   # base
    deduct = bend_reduce("shape_3", "#5")
    stock  = seg_a + seg_b + seg_c + seg_d - deduct
    qty    = math.floor(L / 48) + 1

    log.step(
        f"ST: 5.5+6+5.5+18={seg_a+seg_b+seg_c+seg_d}\" − {deduct}={stock}\"  "
        f"qty=⌊{L}/48⌋+1={qty}",
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
    H = p.wall_height_ft * 12
    if H > _D89A_MAX_H:
        log.warn(
            f"Wall height {fmt_inches(H)} exceeds D89A table max {fmt_inches(_D89A_MAX_H)} — "
            "clamped to last table row; verify with project engineer for taller walls.",
            source="HeadwallRules",
        )
    return []
