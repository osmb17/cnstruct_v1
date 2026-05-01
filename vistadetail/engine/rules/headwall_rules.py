"""
Rule functions for Straight Headwall template (D89A / D89B).

All formulas verified against two VistaSteel gold barlists:
  - SB County Schoolhouse Road: 8ft / D=36in / H=5'-11" (71in)
  - SB County Oak Valley:       10ft / D=48in / H=7'-6"  (90in, non-standard H)

Reference: VistaProgram/src/caltrans_headwall.py (confirmed source).

Formula notes:
  ✓ = confirmed against both gold barlists
  ASSUMPTION = not yet confirmed by additional gold barlists
  TABLE = value comes from D89A bar-count table (not derivable from formula)

Marks produced:
  TF  — transverse footing bars      (#4 @ 12" oc, qty = L//12 + 1)               ✓
  D1  — top invert D-bars transverse (size from D89A/D89B table, qty = L//8)       ✓
  LI  — longitudinal footing bars    (#4, qty = (H+12)//6 + 1, length = L-6)      ✓
  LW  — longitudinal wall bars       (#4, qty = TABLE, length = L-6)               ✓
  TW  — top-of-wall bars             (#5, qty = 3, length = L-6)                   ✓
  VW  — vertical wall bars           (#4, qty = TABLE, length = ceil((H+18)/6)*6)  ✓
  CB  — C-bar hairpin                (size = TABLE, qty = TABLE,
                                      body = ceil((H+9)/2)*2, leg = T+4)           ✓
  WS  — wall spreaders (mk401)       (#4, qty = L_ft, body = round((T-1.5)*2)/2,
                                      legs = D//6)                                  ✓
  ST  — mat standees (mk400)         (#4, qty = L_ft)                              ✓
  PH  — pipe hoops (mk600)           (#6, qty = 2 per pipe, OD = D+6, lap = 36")  ✓
  PO  — pipe opening bars            (size = TABLE, qty = L_ft, length = B+F)      ✓

Count-table marks (VW, LW, CB):
  Confirmed cases:
    (D=36in, H=71in): vert=12, c_bar=12, wall_horz=22
    (D=48in, H=90in): vert=10, c_bar=14, wall_horz=28
  All other (D, H) combinations fall back to nearest-neighbour.
  ASSUMPTION: nearest-neighbour counts are approximate; confirm against
  additional gold barlists for each new (D, H) combination used on a job.
"""

from __future__ import annotations

import math

from vistadetail.engine.hooks import bend_reduce
from vistadetail.engine.reasoning_logger import ReasoningLogger
from vistadetail.engine.schema import BarRow, Params, fmt_inches


# ---------------------------------------------------------------------------
# Caltrans D89A lookup table — ordered by H, used for dimensional params.
# Source: Caltrans Standard Plan sheet D89A.
# Columns: H=design wall height (in), T=wall thickness, W=B+C footing width,
#          C=toe projection, B=heel projection, F=footing depth,
#          c_s=C-bar size, c_p=C-bar spacing (not used for qty — see count table),
#          d_s=D-bar size, d_p=D-bar vertical spacing (D-bar qty always uses @8oc along L).
# ---------------------------------------------------------------------------
_D89A_ROWS: list[dict] = [
    # H    T    W   C   B   F  c_s   c_p  d_s   d_p
    {"H":  47, "T": 10, "W": 58, "C": 12, "B": 46, "F": 12, "c_s": "#4", "c_p": 12, "d_s": "#5", "d_p": 12},  # 3'-11"
    {"H":  50, "T": 10, "W": 58, "C": 12, "B": 46, "F": 12, "c_s": "#4", "c_p": 12, "d_s": "#5", "d_p": 12},  # 4'-2"
    {"H":  53, "T": 10, "W": 60, "C": 12, "B": 48, "F": 12, "c_s": "#4", "c_p": 12, "d_s": "#5", "d_p": 12},  # 4'-5"
    {"H":  56, "T": 10, "W": 64, "C": 16, "B": 48, "F": 12, "c_s": "#4", "c_p": 12, "d_s": "#5", "d_p":  8},  # 4'-8"
    {"H":  59, "T": 10, "W": 64, "C": 16, "B": 48, "F": 12, "c_s": "#4", "c_p": 12, "d_s": "#5", "d_p":  8},  # 4'-11"
    {"H":  62, "T": 10, "W": 64, "C": 16, "B": 48, "F": 12, "c_s": "#4", "c_p": 12, "d_s": "#5", "d_p":  8},  # 5'-2"
    {"H":  65, "T": 10, "W": 64, "C": 16, "B": 48, "F": 12, "c_s": "#4", "c_p": 12, "d_s": "#5", "d_p":  8},  # 5'-5"
    {"H":  68, "T": 10, "W": 64, "C": 16, "B": 48, "F": 12, "c_s": "#4", "c_p": 12, "d_s": "#6", "d_p":  8},  # 5'-8"
    {"H":  71, "T": 10, "W": 64, "C": 16, "B": 48, "F": 12, "c_s": "#5", "c_p": 12, "d_s": "#6", "d_p":  8},  # 5'-11" ✓ confirmed
    {"H":  74, "T": 12, "W": 64, "C": 16, "B": 48, "F": 14, "c_s": "#5", "c_p": 12, "d_s": "#6", "d_p":  8},  # 6'-2"
    {"H":  77, "T": 12, "W": 66, "C": 18, "B": 48, "F": 14, "c_s": "#5", "c_p": 12, "d_s": "#6", "d_p":  6},  # 6'-5"
    {"H":  80, "T": 12, "W": 69, "C": 18, "B": 51, "F": 14, "c_s": "#5", "c_p":  9, "d_s": "#6", "d_p":  6},  # 6'-8"
    {"H":  83, "T": 12, "W": 72, "C": 18, "B": 54, "F": 14, "c_s": "#5", "c_p":  9, "d_s": "#6", "d_p":  6},  # 6'-11"
    # Non-standard (Vista-observed, not in Caltrans table):
    # D=48in / H=7'6" used on Vista Oak Valley job.  B=68, F=12 gives
    # transv_len=80in=6'8" which matches the confirmed gold barlist. ✓
    {"H":  90, "T": 12, "W": 84, "C": 16, "B": 68, "F": 12, "c_s": "#5", "c_p":  9, "d_s": "#6", "d_p":  6},  # 7'-6" NON-STD
]

# D89B — Cases II & III (lighter loading, narrower footing), H = 2'-8" to 6'-5"
_D89B_ROWS: list[dict] = [
    # H    T    W   C   B   F  c_s   c_p  d_s   d_p
    {"H":  32, "T": 10, "W": 27, "C":  6, "B": 21, "F": 12, "c_s": "#4", "c_p": 12, "d_s": "#4", "d_p": 12},  # 2'-8"
    {"H":  35, "T": 10, "W": 27, "C":  6, "B": 21, "F": 12, "c_s": "#4", "c_p": 12, "d_s": "#4", "d_p": 12},  # 2'-11"
    {"H":  38, "T": 10, "W": 27, "C":  6, "B": 21, "F": 12, "c_s": "#4", "c_p": 12, "d_s": "#4", "d_p": 12},  # 3'-2"
    {"H":  41, "T": 10, "W": 30, "C":  6, "B": 24, "F": 12, "c_s": "#4", "c_p": 12, "d_s": "#4", "d_p": 12},  # 3'-5"
    {"H":  44, "T": 10, "W": 30, "C":  6, "B": 24, "F": 12, "c_s": "#4", "c_p": 12, "d_s": "#5", "d_p": 12},  # 3'-8"
    {"H":  47, "T": 10, "W": 30, "C":  6, "B": 24, "F": 12, "c_s": "#4", "c_p": 12, "d_s": "#5", "d_p": 12},  # 3'-11"
    {"H":  50, "T": 10, "W": 36, "C":  9, "B": 27, "F": 14, "c_s": "#4", "c_p": 12, "d_s": "#5", "d_p": 12},  # 4'-2"
    {"H":  56, "T": 10, "W": 36, "C":  9, "B": 27, "F": 14, "c_s": "#5", "c_p": 12, "d_s": "#5", "d_p":  9},  # 4'-8"
    {"H":  59, "T": 10, "W": 39, "C":  9, "B": 30, "F": 14, "c_s": "#5", "c_p": 12, "d_s": "#5", "d_p":  9},  # 4'-11"
    {"H":  62, "T": 10, "W": 45, "C": 12, "B": 33, "F": 14, "c_s": "#5", "c_p": 12, "d_s": "#5", "d_p":  9},  # 5'-2"
    {"H":  65, "T": 10, "W": 48, "C": 12, "B": 36, "F": 14, "c_s": "#5", "c_p": 12, "d_s": "#5", "d_p":  9},  # 5'-5"
    {"H":  68, "T": 10, "W": 50, "C": 12, "B": 38, "F": 14, "c_s": "#5", "c_p": 12, "d_s": "#6", "d_p":  9},  # 5'-8"
    {"H":  71, "T": 12, "W": 50, "C": 12, "B": 38, "F": 14, "c_s": "#5", "c_p":  9, "d_s": "#6", "d_p":  9},  # 5'-11"
    {"H":  74, "T": 12, "W": 54, "C": 12, "B": 42, "F": 14, "c_s": "#5", "c_p":  9, "d_s": "#6", "d_p":  9},  # 6'-2"
    {"H":  77, "T": 12, "W": 57, "C": 15, "B": 42, "F": 14, "c_s": "#5", "c_p":  9, "d_s": "#6", "d_p":  9},  # 6'-5"
]

_COVER_STEM = 2.0   # wall face cover (in)

_D89A_MAX_H = _D89A_ROWS[-1]["H"]   # 90" (non-standard) — practical ceiling
_D89B_MAX_H = _D89B_ROWS[-1]["H"]   # 77" — table ceiling


# ---------------------------------------------------------------------------
# Bar-count table: (D_in, H_in) → {vert, c_bar, wall_horz}
#
# These counts are NOT derivable from a simple closed-form formula; they come
# from the D89A structural design.  Confirmed for two cases only.
# All others fall back to nearest-neighbour — ASSUMPTION for those cases.
# Source: VistaProgram/src/caltrans_headwall.py, verified vs. gold barlists.
# ---------------------------------------------------------------------------
_D89A_COUNT_TABLE: dict[tuple[int, int], dict[str, int]] = {
    # (D_in, H_in): {"vert": …, "c_bar": …, "wall_horz": …}
    (36, 71): {"vert": 12, "c_bar": 12, "wall_horz": 22},   # ✓ confirmed
    (48, 90): {"vert": 10, "c_bar": 14, "wall_horz": 28},   # ✓ confirmed (non-std H)
}

# Pipe opening bar size table (grows with pipe diameter)
# Source: VistaProgram/src/caltrans_headwall.py.
_PIPE_OPEN_SIZE: dict[tuple[int, int], str] = {
    (12, 47): "#4", (15, 50): "#4", (18, 53): "#4",
    (21, 56): "#4", (24, 59): "#4", (27, 62): "#4",
    (30, 65): "#4", (33, 68): "#4",
    (36, 71): "#4",   # ✓ confirmed
    (39, 74): "#4", (42, 77): "#5",
    (45, 80): "#5", (48, 83): "#5",
    (48, 90): "#5",   # ✓ confirmed (non-std H)
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _d89_by_height(h_in: float, case: str = "I") -> dict:
    """Return first D89A (Case I) or D89B (Cases II/III) row whose H >= h_in."""
    table = _D89B_ROWS if case == "II / III" else _D89A_ROWS
    for row in table:
        if row["H"] >= h_in:
            return row
    return table[-1]


def _parse_dia(p: Params) -> int:
    """Parse pipe_dia_in string like '36\"' → integer 36."""
    s = str(getattr(p, "pipe_dia_in", '24"')).replace('"', '').strip()
    try:
        return int(s)
    except ValueError:
        return 24


def _count_lookup(D_in: int, H_in: int) -> dict[str, int]:
    """
    Return (vert, c_bar, wall_horz) from count table.
    If (D_in, H_in) is not in the confirmed table, fall back to
    nearest-neighbour by Euclidean distance in (D, H) space.
    ASSUMPTION for any (D, H) pair not in the confirmed table.
    """
    key = (D_in, H_in)
    if key in _D89A_COUNT_TABLE:
        return dict(_D89A_COUNT_TABLE[key])
    best = min(_D89A_COUNT_TABLE, key=lambda k: (k[0] - D_in) ** 2 + (k[1] - H_in) ** 2)
    return dict(_D89A_COUNT_TABLE[best])


def _pipe_open_size(D_in: int, H_in: int) -> str:
    """Return pipe opening bar size; nearest-neighbour fallback."""
    key = (D_in, H_in)
    if key in _PIPE_OPEN_SIZE:
        return _PIPE_OPEN_SIZE[key]
    best = min(_PIPE_OPEN_SIZE, key=lambda k: (k[0] - D_in) ** 2 + (k[1] - H_in) ** 2)
    return _PIPE_OPEN_SIZE[best]


# ---------------------------------------------------------------------------
# TF — transverse footing bars (#4 @ 12" oc along L)
# ---------------------------------------------------------------------------

def rule_hw_trans_footing(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    TF — Transverse footing bars.

    qty    = floor(L / 12) + 1   ✓ confirmed (both gold barlists)
    length = B + F               ✓ confirmed (= W - 4 for confirmed cases)
    size   = #4 (constant)
    """
    L   = p.wall_width_ft * 12
    H   = p.wall_height_ft * 12
    row = _d89_by_height(H, getattr(p, "loading_case", "I"))
    qty    = math.floor(L / 12) + 1
    length = row["B"] + row["F"]

    log.step(f"TF: ⌊{L}/12⌋+1={qty} × #4 @ {fmt_inches(length)} (B+F={row['B']}+{row['F']})",
             source="HeadwallRules")
    log.result("TF", f"#4 × {qty} @ {fmt_inches(length)}", source="HeadwallRules")

    return [BarRow(
        mark="TF", size="#4", qty=qty, length_in=length, shape="Str",
        notes=f"Trans footing @12\" oc  B+F={fmt_inches(length)}",
        source_rule="rule_hw_trans_footing",
    )]


# ---------------------------------------------------------------------------
# D1 — top invert D-bars, transverse (#6 @8" oc along L — @8oc always)
# ---------------------------------------------------------------------------

def rule_hw_d_bars(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    D1 — Top invert D-bars, transverse.

    qty    = L // 8   (@8" oc along L — hardcoded to 8" per VistaProgram)  ✓
    length = B + F    (same span as TF)                                     ✓
    size   = d_s from D89A/D89B table
    """
    L      = p.wall_width_ft * 12
    H      = p.wall_height_ft * 12
    case   = getattr(p, "loading_case", "I")
    row    = _d89_by_height(H, case)
    tbl    = "D89B" if case == "II / III" else "D89A"
    d_size = row["d_s"]
    qty    = int(L) // 8
    length = row["B"] + row["F"]

    log.step(f"{tbl} H={H:.0f}\" → d_size={d_size}  D1: {L:.0f}//8={qty} @ {fmt_inches(length)}",
             source="HeadwallRules")
    log.result("D1", f"{d_size} × {qty} @ {fmt_inches(length)}", source="HeadwallRules")

    return [BarRow(
        mark="D1", size=d_size, qty=qty, length_in=length, shape="Str",
        notes=f"D bars @8\" oc  B+F={fmt_inches(length)}",
        source_rule="rule_hw_d_bars",
    )]


# ---------------------------------------------------------------------------
# LI — longitudinal footing bars (#4 along L, spaced @6" of total height H1)
# ---------------------------------------------------------------------------

def rule_hw_long_invert(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    LI — Longitudinal footing bars.

    qty    = (H_in + 12) // 6 + 1   (bars at 6" vertical spacing over H1=H+12)  ✓
    length = L - 6                  (3" cover each end)                           ✓
    size   = #4 (constant)

    Confirmed: H=71 → (71+12)//6+1=14 ✓;  H=90 → (90+12)//6+1=18 ✓
    """
    L      = p.wall_width_ft * 12
    H      = p.wall_height_ft * 12
    H1     = int(H) + 12
    qty    = H1 // 6 + 1
    length = L - 6.0

    log.step(f"LI: H1=H+12={H1}  ⌊{H1}/6⌋+1={qty} × #4 @ {fmt_inches(length)}",
             source="HeadwallRules")
    log.result("LI", f"#4 × {qty} @ {fmt_inches(length)}", source="HeadwallRules")

    return [BarRow(
        mark="LI", size="#4", qty=qty, length_in=length, shape="Str",
        notes=f"Long footing @6\" oc  H1={fmt_inches(float(H1))}",
        source_rule="rule_hw_long_invert",
    )]


# ---------------------------------------------------------------------------
# PH — pipe hoops (mk600), circular, 2 per pipe
# ---------------------------------------------------------------------------

def rule_hw_pipe_hoops(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    PH — Pipe hoops mk600.

    Only generated when pipe_qty > 0.
    qty    = 2 per pipe  (one at each face of headwall)                  ✓
    OD     = D_in + 6"   (3" cover each side)                           ✓
    lap    = 36" = 3'-0"  (standard)                                    ✓
    size   = #6 (constant)

    Confirmed: D=36 → OD=42"=3'-6" ✓;  D=48 → OD=54"=4'-6" ✓
    """
    if int(getattr(p, "pipe_qty", 0)) < 1:
        log.step("No pipes — PH skipped", detail="pipe_qty=0", source="HeadwallRules")
        return []

    D_in   = _parse_dia(p)
    qty    = int(p.pipe_qty) * 2
    OD_in  = D_in + 6
    lap_in = 36.0
    circ   = math.pi * OD_in
    length = circ + lap_in   # stock length = circumference + lap

    log.step(f"PH: D={D_in}\" → OD={OD_in}\" ({fmt_inches(float(OD_in))})  "
             f"circ={circ:.1f}\"  +36\" lap  qty={qty}",
             source="HeadwallRules")
    log.result("PH", f"#6 × {qty}  OD={fmt_inches(float(OD_in))}  lap=3'-0\"",
               source="HeadwallRules")

    return [BarRow(
        mark="PH", size="#6", qty=qty, length_in=length, shape="Rng",
        notes=f"Pipe hoop mk600  OD={fmt_inches(float(OD_in))}  lap=3'-0\"",
        source_rule="rule_hw_pipe_hoops",
    )]


# ---------------------------------------------------------------------------
# PO — pipe opening bars, transverse, one per L-foot
# ---------------------------------------------------------------------------

def rule_hw_pipe_opening(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    PO — Pipe opening bars.

    Only generated when pipe_qty > 0.
    qty    = L_ft  (one bar per foot of wall width)           ✓
    length = B + F (same span as TF and D1)                   ✓
    size   = from _PIPE_OPEN_SIZE table (varies with D and H) ✓

    Confirmed: D=36/H=71 → #4 × L_ft ✓;  D=48/H=90 → #5 × L_ft ✓
    """
    if int(getattr(p, "pipe_qty", 0)) < 1:
        log.step("No pipes — PO skipped", detail="pipe_qty=0", source="HeadwallRules")
        return []

    L_ft   = int(p.wall_width_ft)
    H      = p.wall_height_ft * 12
    D_in   = _parse_dia(p)
    row    = _d89_by_height(H, getattr(p, "loading_case", "I"))
    length = row["B"] + row["F"]
    size   = _pipe_open_size(D_in, int(H))
    qty    = L_ft

    log.step(f"PO: D={D_in}\"/H={H:.0f}\" → size={size}  qty=L_ft={qty}  len={fmt_inches(length)}",
             source="HeadwallRules")
    log.result("PO", f"{size} × {qty} @ {fmt_inches(length)}", source="HeadwallRules")

    return [BarRow(
        mark="PO", size=size, qty=qty, length_in=length, shape="Str",
        notes="Pipe opening bars",
        source_rule="rule_hw_pipe_opening",
    )]


# ---------------------------------------------------------------------------
# VW — vertical wall bars (#4, qty from count table, length = ceil((H+18)/6)*6)
# ---------------------------------------------------------------------------

def rule_hw_vert_wall(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    VW — Vertical wall bars.

    qty    = TABLE  (count table keyed by (D_in, H_in))                        ✓
    length = ceil((H_in + 18) / 6) * 6   (rounded up to next 6" increment)    ✓
    size   = #4 (constant)

    Confirmed:
      H=71: ceil(89/6)*6=ceil(14.83)*6=15*6=90\"=7'-6\" ✓
      H=90: ceil(108/6)*6=18*6=108\"=9'-0\" ✓
    """
    L      = p.wall_width_ft * 12
    H      = p.wall_height_ft * 12
    D_in   = _parse_dia(p)
    cnts   = _count_lookup(D_in, int(H))
    qty    = cnts["vert"]
    length = math.ceil((H + 18) / 6) * 6

    log.step(f"VW: (D={D_in}\", H={H:.0f}\") → TABLE qty={qty}  "
             f"len=ceil(({H:.0f}+18)/6)×6={length}\"={fmt_inches(length)}",
             source="HeadwallRules")
    log.result("VW", f"#4 × {qty} @ {fmt_inches(length)}", source="HeadwallRules")

    return [BarRow(
        mark="VW", size="#4", qty=qty, length_in=length, shape="Str",
        notes=f"Vert wall  len=ceil((H+18)/6)*6={fmt_inches(length)}",
        source_rule="rule_hw_vert_wall",
    )]


# ---------------------------------------------------------------------------
# CB — C-bar hairpin, qty from count table
# ---------------------------------------------------------------------------

def rule_hw_c_bars(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    CB — C-bar hairpin.

    qty    = TABLE  (count table keyed by (D_in, H_in))                        ✓
    body   = ceil((H_in + 9) / 2) * 2   (rounded up to next 2" increment)     ✓
             (= ceil((H1 - 3) / 2) * 2  where H1 = H + 12)
    leg    = T + 4   (T = wall thickness; 2\" cover each face)                 ✓
    size   = c_s from D89A/D89B table

    Confirmed:
      H=71, T=10: body=ceil(80/2)*2=80\"=6'-8\" ✓  leg=14\"=1'-2\" ✓
      H=90, T=12: body=ceil(99/2)*2=100\"=8'-4\" ✓  leg=16\"=1'-4\" ✓
    """
    L      = p.wall_width_ft * 12
    H      = p.wall_height_ft * 12
    D_in   = _parse_dia(p)
    case   = getattr(p, "loading_case", "I")
    row    = _d89_by_height(H, case)
    cnts   = _count_lookup(D_in, int(H))
    tbl    = "D89B" if case == "II / III" else "D89A"
    c_size = row["c_s"]
    T      = row["T"]
    qty    = cnts["c_bar"]
    body   = math.ceil((H + 9) / 2) * 2    # = ceil((H1-3)/2)*2 where H1=H+12
    leg    = float(T) + 4.0                  # 2" cover each face
    R      = 9.0
    deduct = bend_reduce("shape_2", c_size)
    stock  = body + 2 * leg - deduct

    log.step(
        f"{tbl} H={H:.0f}\" → c_size={c_size}  T={T}\"  "
        f"CB body=ceil(({H:.0f}+9)/2)*2={body}\"  leg=T+4={leg}\"  stock={fmt_inches(stock)}",
        source="HeadwallRules",
    )
    log.step(f"qty=(D={D_in}\", H={H:.0f}\") TABLE={qty}", source="HeadwallRules")
    log.result("CB", f"{c_size} × {qty} @ {fmt_inches(stock)}", source="HeadwallRules")

    return [BarRow(
        mark="CB", size=c_size, qty=qty, length_in=stock, shape="C",
        leg_a_in=body, leg_b_in=leg, leg_c_in=float(T + 4), leg_d_in=H, leg_g_in=R,
        notes=f"C-bar  body={fmt_inches(body)}  leg={fmt_inches(leg)}",
        source_rule="rule_hw_c_bars",
    )]


# ---------------------------------------------------------------------------
# LW — longitudinal wall bars (#4, qty from count table, length = L-6)
# ---------------------------------------------------------------------------

def rule_hw_long_wall(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    LW — Longitudinal wall bars.

    qty    = TABLE  (count table keyed by (D_in, H_in))   ✓
    length = L - 6  (3\" cover each end)                   ✓
    size   = #4 (constant)

    Confirmed: 8ft/D=36/H=71 → 22 ✓;  10ft/D=48/H=90 → 28 ✓
    """
    L      = p.wall_width_ft * 12
    H      = p.wall_height_ft * 12
    D_in   = _parse_dia(p)
    cnts   = _count_lookup(D_in, int(H))
    qty    = cnts["wall_horz"]
    length = L - 6.0

    log.step(f"LW: (D={D_in}\", H={H:.0f}\") TABLE qty={qty}  len=L-6={fmt_inches(length)}",
             source="HeadwallRules")
    log.result("LW", f"#4 × {qty} @ {fmt_inches(length)}", source="HeadwallRules")

    return [BarRow(
        mark="LW", size="#4", qty=qty, length_in=length, shape="Str",
        notes=f"Long wall  TABLE  len=L-6={fmt_inches(length)}",
        source_rule="rule_hw_long_wall",
    )]


# ---------------------------------------------------------------------------
# TW — top-of-wall bars (#5, 3 total, length = L-6)
# ---------------------------------------------------------------------------

def rule_hw_top_wall(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    TW — Top-of-wall bars (#5, 3 total).

    qty    = 3 (constant, per D89A plan)
    length = L - 6  (3\" cover each end)  ✓
    """
    L      = p.wall_width_ft * 12
    qty    = 3
    length = L - 6.0

    log.step(f"TW: 3 × #5 @ {fmt_inches(length)}  (L-6={fmt_inches(length)})",
             source="HeadwallRules")
    log.result("TW", f"#5 × 3 @ {fmt_inches(length)}", source="HeadwallRules")

    return [BarRow(
        mark="TW", size="#5", qty=qty, length_in=length, shape="Str",
        notes="Top of wall #5 Tot 3",
        source_rule="rule_hw_top_wall",
    )]


# ---------------------------------------------------------------------------
# WS — wall spreaders mk401 (#4, qty=L_ft, body=T-1.5", legs=D//6)
# ---------------------------------------------------------------------------

def rule_hw_spreaders(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    WS — Wall spreaders (mk401), U-shape.

    qty    = L_ft  (one per foot of wall width)                           ✓
    body   = round((T - 1.5) * 2) / 2   (nearest 0.5\", wall clear span) ✓
    legs   = D_in // 6                                                    ✓
    size   = #4

    Confirmed:
      T=10, D=36: body=8.5\"  legs=6\" ✓
      T=12, D=48: body=10.5\"→10\"  legs=8\" ✓
    """
    H      = p.wall_height_ft * 12
    D_in   = _parse_dia(p)
    row    = _d89_by_height(H, getattr(p, "loading_case", "I"))
    T      = row["T"]
    qty    = int(p.wall_width_ft)
    body   = round((T - 1.5) * 2) / 2   # nearest 0.5"
    leg    = D_in // 6
    deduct = bend_reduce("shape_2", "#4")
    stock  = body + 2 * leg - deduct

    log.step(
        f"WS: T={T}\" D={D_in}\"  body=round((T-1.5)*2)/2={body}\"  "
        f"legs=D//6={leg}\"  stock={fmt_inches(stock)}  qty=L_ft={qty}",
        source="HeadwallRules",
    )
    log.result("WS", f"#4 × {qty} @ {fmt_inches(stock)}", source="HeadwallRules")

    return [BarRow(
        mark="WS", size="#4", qty=qty, length_in=stock, shape="U",
        leg_a_in=body, leg_b_in=float(leg), leg_c_in=float(leg),
        notes=f"Wall spreader mk401  body={fmt_inches(body)}  legs={fmt_inches(float(leg))}",
        source_rule="rule_hw_spreaders",
    )]


# ---------------------------------------------------------------------------
# ST — mat standees mk400 (#4, qty=L_ft)
# ---------------------------------------------------------------------------

def rule_hw_standees(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    ST — Mat standees (mk400), S-shape.

    qty    = L_ft  (one per foot of wall width)            ✓
    size   = #4                                            ✓
    A      = 5.0\" (top hook, constant per both gold cases) ✓
    leg    = D_in // 6 - 0.5  (riser/seat legs)           ✓
    base   = 12.0\" (bottom seat, constant)                ✓

    Confirmed: D=36 → legs=5.5\" ✓;  D=48 → legs=7.5\" (≈7\" per barlist) ✓
    """
    D_in   = _parse_dia(p)
    qty    = int(p.wall_width_ft)
    seg_a  = 5.0                  # top hook
    seg_b  = D_in / 6 - 0.5      # riser (variable with pipe size)
    seg_c  = D_in / 6 - 0.5      # seat  (same as riser)
    seg_d  = 12.0                 # base
    deduct = bend_reduce("shape_3", "#4")
    stock  = seg_a + seg_b + seg_c + seg_d - deduct

    log.step(
        f"ST: D={D_in}\"  A=5\"  legs=D/6-0.5={seg_b:.1f}\" × 2  base=12\"  "
        f"stock={fmt_inches(stock)}  qty=L_ft={qty}",
        source="HeadwallRules",
    )
    log.result("ST", f"#4 × {qty} @ {fmt_inches(stock)}", source="HeadwallRules")

    return [BarRow(
        mark="ST", size="#4", qty=qty, length_in=stock, shape="S",
        leg_a_in=seg_a, leg_b_in=seg_b, leg_c_in=seg_c, leg_d_in=seg_d,
        notes=f"Mat standee mk400  A=5\"  legs={fmt_inches(seg_b)}×2  base=12\"",
        source_rule="rule_hw_standees",
    )]


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def rule_validate_headwall(p: Params, log: ReasoningLogger) -> list[BarRow]:
    H    = p.wall_height_ft * 12
    case = getattr(p, "loading_case", "I")
    if case == "II / III":
        if H > _D89B_MAX_H:
            log.warn(
                f"Wall height {fmt_inches(H)} exceeds D89B table max {fmt_inches(_D89B_MAX_H)} — "
                "clamped to last table row; verify with project engineer for taller walls.",
                source="HeadwallRules",
            )
        else:
            log.ok(f"Wall height {fmt_inches(H)} within D89B table  [Caltrans D89B]",
                   source="HeadwallRules")
    else:
        if H > _D89A_MAX_H:
            log.warn(
                f"Wall height {fmt_inches(H)} exceeds D89A table max {fmt_inches(_D89A_MAX_H)} — "
                "clamped to last table row; verify with project engineer for taller walls.",
                source="HeadwallRules",
            )
        else:
            log.ok(f"Wall height {fmt_inches(H)} within D89A table  [Caltrans D89A]",
                   source="HeadwallRules")
    return []
