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
# Caltrans D89A lookup table
# Key = pipe diameter (in) — used only for ordering; lookup is by H.
# Values: H  = minimum wall height (in)
#         T  = wall thickness (in)
#         F  = footing depth (in)
#         W  = footing width (in)
#         B  = back projection of footing from wall face (in)
#         C  = front projection of footing from wall face (in)
# ---------------------------------------------------------------------------

_D89_TABLE: dict[int, dict] = {
    12: {"H": 47, "T": 8, "F": 8, "W": 42, "B": 24, "C": 18},
    15: {"H": 50, "T": 8, "F": 8, "W": 44, "B": 26, "C": 18},
    18: {"H": 53, "T": 8, "F": 8, "W": 46, "B": 28, "C": 18},
    21: {"H": 56, "T": 8, "F": 8, "W": 50, "B": 30, "C": 20},
    24: {"H": 59, "T": 8, "F": 8, "W": 52, "B": 32, "C": 20},
    27: {"H": 62, "T": 8, "F": 8, "W": 56, "B": 34, "C": 22},
    30: {"H": 65, "T": 8, "F": 8, "W": 60, "B": 36, "C": 24},
    33: {"H": 68, "T": 8, "F": 8, "W": 64, "B": 38, "C": 26},
    36: {"H": 71, "T": 8, "F": 8, "W": 68, "B": 40, "C": 28},
    39: {"H": 74, "T": 8, "F": 8, "W": 72, "B": 42, "C": 30},
    42: {"H": 77, "T": 8, "F": 8, "W": 76, "B": 44, "C": 32},
    45: {"H": 80, "T": 8, "F": 8, "W": 80, "B": 46, "C": 34},
    48: {"H": 83, "T": 8, "F": 8, "W": 84, "B": 48, "C": 36},
    51: {"H": 86, "T": 8, "F": 8, "W": 88, "B": 50, "C": 38},
    54: {"H": 89, "T": 8, "F": 8, "W": 92, "B": 52, "C": 40},
}

_COVER_STEM = 2.0   # wall face cover (in)
_COVER_FTG  = 3.0   # footing bottom cover (in)


def _d89_by_height(h_in: float) -> dict:
    """Return first D89A row with H >= h_in (rounds up for safety)."""
    for dia in sorted(_D89_TABLE.keys()):
        row = _D89_TABLE[dia]
        if row["H"] >= h_in:
            return row
    return _D89_TABLE[54]


# ---------------------------------------------------------------------------
# Rule functions
# ---------------------------------------------------------------------------

def rule_hw_d_bars(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """D1 — Top invert D-bars, transverse (#5 @ 8" oc)."""
    L   = p.wall_width_ft * 12
    H   = p.wall_height_ft * 12
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
    H1 = H + 12.0
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
    Body = H1 − 2 × 1.5" (leg-tip cover at each end).
    Stock = body + 2 × leg − bend_reduce("shape_2", "#4").
    """
    L      = p.wall_width_ft * 12
    H      = p.wall_height_ft * 12
    H1     = H + 12.0
    c_cov  = 1.5
    body   = H1 - 2 * c_cov
    leg    = 14.0
    R      = 9.0
    deduct = bend_reduce("shape_2", "#4")
    stock  = body + 2 * leg - deduct
    qty    = math.floor(L / 12) + 1

    log.step(
        f"CB: H1={H1:.0f}\"  body={fmt_inches(body)}  legs=1'-2\"×2  R=9\"  "
        f"stock={fmt_inches(stock)}",
        source="HeadwallRules",
    )
    log.step(f"qty=⌊{L}/12⌋+1={qty}", source="HeadwallRules")
    log.result("CB", f"#4 × {qty} @ {fmt_inches(stock)}", source="HeadwallRules")

    return [BarRow(
        mark="CB", size="#4", qty=qty, length_in=stock, shape="C",
        leg_a_in=body, leg_b_in=leg, leg_c_in=leg,
        notes=f"C-bar @12\" oc  body={fmt_inches(body)}  legs=1'-2\"×2  R=9\"",
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
    H = p.wall_height_ft * 12
    if H > 89:
        log.warn(
            f"Wall height {fmt_inches(H)} exceeds D89A table max 7'-5\" — "
            "using largest table row (54\" pipe)",
            source="HeadwallRules",
        )
    return []
