"""
Rule functions for Straight Headwall template (D89A / D89B).

All formulas verified against three VistaSteel gold barlists:
  - SB County Schoolhouse Road: 8ft / D=36in / H=5'-11" (71in)
  - SB County Oak Valley:       10ft / D=48in / H=7'-6"  (90in, non-standard H)
  - No-pipe headwall:           8ft / no pipe  / H=5'-0"  (60in)

Reference: VistaProgram/src/caltrans_headwall.py (confirmed source).

Formula notes:
  ✓ = confirmed against gold barlists
  NO-PIPE = formula or value applies only to the no-pipe (pipe_qty=0) case
  TABLE = value comes from D89A bar-count table (not derivable from formula)

Marks produced:
  TF  — transverse footing bars      (#4 @ 12" oc, qty = L//12 + 1)                ✓
  D1  — top invert D-bars transverse (size from D89A/D89B table,
                                      qty = L//8 [pipe] or L//8+1 [no-pipe])        ✓
  LI  — longitudinal footing bars    (#4, qty = (H+12)//6+1 [pipe] or TABLE [no-pipe],
                                      length = L-6)                                  ✓
  LW  — longitudinal wall bars       (#4, qty = TABLE,
                                      length = L-6 [pipe] or L-4 [no-pipe])         ✓
  TW  — top-of-wall bars             (#5, qty = 3,
                                      length = L-6 [pipe] or L-4 [no-pipe])         ✓
  VW  — vertical wall bars           (#4, qty = TABLE, length = ceil((H+18)/6)*6)   ✓
  CB  — C-bar hairpin                (size = TABLE c_s, qty = TABLE,
                                      body = ceil((H+9)/2)*2, leg = T+4)            ✓
  WS  — wall spreaders (mk401)       (pipe:   #4, qty=L_ft, body=round((T-1.5)*2)/2,
                                               legs=D//6                             ✓
                                       no-pipe:#4, qty=L_ft//2, body=T//2,
                                               legs=T//2-0.5                        ✓)
  ST  — mat standees (mk400)         (pipe:   #4, qty=L_ft, legs=D/6-0.5, base=12"  ✓
                                       no-pipe:#5, qty=L_ft, legs=5.5",   base=18"  ✓)
  PH  — pipe hoops (mk600)           (#6, qty = 2 per pipe, OD = D+6, lap = 36")   ✓
  PO  — pipe opening bars            (size = TABLE, qty = L_ft, length = B+F)       ✓

Count-table marks (VW, LW, CB, LI for no-pipe):
  Confirmed cases:
    (D=36in, H=71in): vert=12, c_bar=12, wall_horz=22, li=14
    (D=48in, H=90in): vert=10, c_bar=14, wall_horz=28, li=18
    (D=0,    H=60in): vert= 9, c_bar= 9, wall_horz=14, li=16  [no-pipe gold]
  All other (D, H) combinations fall back to nearest-neighbour.
  ASSUMPTION: nearest-neighbour counts are approximate; confirm against
  additional gold barlists for each new (D, H) combination used on a job.
  For no-pipe, D=0 is used as the table key.
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
    {"H":  47, "T": 10, "W": 30, "C":  6, "B": 24, "F": 14, "c_s": "#4", "c_p": 12, "d_s": "#5", "d_p": 12},  # 3'-11"  confirmed D89B
    {"H":  50, "T": 10, "W": 36, "C":  9, "B": 27, "F": 14, "c_s": "#4", "c_p": 12, "d_s": "#5", "d_p": 12},  # 4'-2"
    {"H":  56, "T": 10, "W": 36, "C":  9, "B": 27, "F": 14, "c_s": "#5", "c_p": 12, "d_s": "#5", "d_p":  9},  # 4'-8"  confirmed D89B
    {"H":  59, "T": 10, "W": 39, "C":  9, "B": 30, "F": 14, "c_s": "#5", "c_p": 12, "d_s": "#5", "d_p":  9},  # 4'-11" confirmed D89B
    {"H":  62, "T": 10, "W": 45, "C": 12, "B": 33, "F": 14, "c_s": "#5", "c_p": 12, "d_s": "#5", "d_p":  9},  # 5'-2"
    {"H":  65, "T": 10, "W": 48, "C": 12, "B": 36, "F": 14, "c_s": "#5", "c_p": 12, "d_s": "#5", "d_p":  9},  # 5'-5"
    {"H":  68, "T": 10, "W": 50, "C": 12, "B": 38, "F": 14, "c_s": "#5", "c_p": 12, "d_s": "#6", "d_p": 12},  # 5'-8"  confirmed D89B
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
    # (D_in, H_in): {"vert": …, "c_bar": …, "wall_horz": …, "li": …}
    # "li" is the longitudinal footing bar count (only needed when formula fails,
    # i.e. the no-pipe case; for pipe cases li = (H+12)//6+1 which agrees ✓).
    (36, 71): {"vert": 12, "c_bar": 12, "wall_horz": 22, "li": 14},   # ✓ confirmed
    (48, 90): {"vert": 10, "c_bar": 14, "wall_horz": 28, "li": 18},   # ✓ confirmed (non-std H)
    # No-pipe entry: D=0 key used when pipe_qty=0.  All counts from gold barlist
    # (straight headwall 8ft / H=5'-0" / no pipe).
    (0,  60): {"vert":  9, "c_bar":  9, "wall_horz": 14, "li": 16},   # ✓ confirmed no-pipe
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


def _effective_D(p: "Params") -> int:
    """
    Return the pipe diameter to use for count-table lookups.
    When there is no pipe (pipe_qty=0) the key D=0 is used so that the
    no-pipe entry in _D89A_COUNT_TABLE is found exactly rather than falling
    back to the nearest pipe-based neighbour.
    """
    if int(getattr(p, "pipe_qty", 0)) < 1:
        return 0
    return _parse_dia(p)


def _count_lookup(D_in: int, H_in: int) -> dict[str, int]:
    """
    Return (vert, c_bar, wall_horz, li) from count table.
    If (D_in, H_in) is not in the confirmed table, fall back to
    nearest-neighbour by Euclidean distance in (D, H) space.
    ASSUMPTION for any (D, H) pair not in the confirmed table.

    For the no-pipe case pass D_in=0 (use _effective_D helper).
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

    qty    = L // 8         [pipe case, @8" oc, exclusive count]              ✓
             L // 8 + 1     [no-pipe case, @8" oc, inclusive — no pipe gap]   ✓
    length = B + F          (same span as TF)                                  ✓
    size   = d_s from D89A/D89B table

    Confirmed:
      Pipe   L=96" / D=36 / H=71: qty=96//8=12 ✓
      No-pipe L=96" / H=60:       qty=96//8+1=13 ✓
    """
    L      = p.wall_width_ft * 12
    H      = p.wall_height_ft * 12
    case   = getattr(p, "loading_case", "I")
    no_pipe = int(getattr(p, "pipe_qty", 0)) < 1
    row    = _d89_by_height(H, case)
    tbl    = "D89B" if case == "II / III" else "D89A"
    d_size = row["d_s"]
    qty    = int(L) // 8 + (1 if no_pipe else 0)
    length = row["B"] + row["F"]

    suffix = "+1 (no-pipe, inclusive)" if no_pipe else ""
    log.step(f"{tbl} H={H:.0f}\" → d_size={d_size}  D1: {L:.0f}//8{'='+str(qty) if not no_pipe else '+1='+str(qty)} @ {fmt_inches(length)}{suffix}",
             source="HeadwallRules")
    log.result("D1", f"{d_size} × {qty} @ {fmt_inches(length)}", source="HeadwallRules")

    return [BarRow(
        mark="D1", size=d_size, qty=qty, length_in=length, shape="Str",
        notes=f"D bars @8\" oc{'  no-pipe+1' if no_pipe else ''}  B+F={fmt_inches(length)}",
        source_rule="rule_hw_d_bars",
    )]


# ---------------------------------------------------------------------------
# LI — longitudinal footing bars (#4 along L, spaced @6" of total height H1)
# ---------------------------------------------------------------------------

def rule_hw_long_invert(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    LI — Longitudinal footing bars.

    PIPE case:
      qty    = (H_in + 12) // 6 + 1   (bars at 6" vertical spacing over H1=H+12)  ✓
      length = L - 6                  (3" cover each end)                           ✓

    NO-PIPE case:
      qty    = TABLE  (count-table "li" key, keyed by D=0 and H)                   ✓
      length = L - 6  (same 3" cover each end)                                     ✓
      Note: formula (H+12)//6+1 gives 13 for H=60 but gold says 16; cause unknown.
            The no-pipe bar layout differs from the pipe case; count is hard-coded.

    size   = #4 (constant)

    Confirmed:
      Pipe H=71:  (71+12)//6+1=14 ✓
      Pipe H=90:  (90+12)//6+1=18 ✓
      No-pipe H=60: TABLE=16 ✓
    """
    L       = p.wall_width_ft * 12
    H       = p.wall_height_ft * 12
    no_pipe = int(getattr(p, "pipe_qty", 0)) < 1
    length  = L - 6.0

    if no_pipe:
        D_eff = _effective_D(p)   # 0 for no-pipe
        cnts  = _count_lookup(D_eff, int(H))
        qty   = cnts.get("li", (int(H) + 12) // 6 + 1)
        log.step(
            f"LI no-pipe: (D=0, H={H:.0f}\") TABLE li={qty} × #4 @ {fmt_inches(length)}",
            source="HeadwallRules",
        )
    else:
        H1  = int(H) + 12
        qty = H1 // 6 + 1
        log.step(f"LI: H1=H+12={H1}  ⌊{H1}/6⌋+1={qty} × #4 @ {fmt_inches(length)}",
                 source="HeadwallRules")

    log.result("LI", f"#4 × {qty} @ {fmt_inches(length)}", source="HeadwallRules")

    if no_pipe:
        li_notes = "Long footing  TABLE (no-pipe)"
    else:
        H1_str = fmt_inches(float(int(H) + 12))
        li_notes = f'Long footing @6" oc  H1={H1_str}'
    return [BarRow(
        mark="LI", size="#4", qty=qty, length_in=length, shape="Str",
        notes=li_notes,
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

    qty    = TABLE  [pipe case, keyed by (D_in, H_in)]                          ✓
             L//12+1 [no-pipe case, bars @12\" oc along wall length]              ✓
    length = ceil((H+18)/6)*6  [pipe case — VistaProgram formula]               ✓
             H + F + 7\"        [no-pipe case — F from table, 7\"=hook]           ✓
    size   = #4 (constant)

    Confirmed:
      Pipe   H=71, D=36: qty=12 (TABLE), len=ceil(89/6)*6=90\"=7'-6\" ✓ (schoolhouse gold)
      Pipe   H=90, D=48: qty=10 (TABLE), len=ceil(108/6)*6=108\"=9'-0\" ✓ (vista gold)
      No-pipe H=60, F=12: qty=9=96//12+1, len=60+12+7=79\"=6'-7\" ✓ (no-pipe gold)
    """
    L       = p.wall_width_ft * 12
    H       = p.wall_height_ft * 12
    no_pipe = int(getattr(p, "pipe_qty", 0)) < 1
    D_in    = _effective_D(p)
    row     = _d89_by_height(H, getattr(p, "loading_case", "I"))

    if no_pipe:
        qty = math.floor(L / 12) + 1
        length = H + row["F"] + 7.0
        len_formula = f"H+F+7={H:.0f}+{row['F']}+7={length:.0f}\""
    else:
        cnts = _count_lookup(D_in, int(H))
        qty  = cnts["vert"]
        length = math.ceil((H + 18) / 6) * 6
        len_formula = f"ceil(({H:.0f}+18)/6)*6={length:.0f}\""

    log.step(f"VW: (D={D_in}\", H={H:.0f}\") → {'L//12+1' if no_pipe else 'TABLE'} qty={qty}  "
             f"len={len_formula}={fmt_inches(length)}",
             source="HeadwallRules")
    log.result("VW", f"#4 × {qty} @ {fmt_inches(length)}", source="HeadwallRules")

    if no_pipe:
        vw_notes = (
            f"H(={H:.0f}\") + F(={row['F']}\") + 7\"(hook) = {fmt_inches(length)}"
        )
    else:
        vw_notes = (
            f"ceil((H(={H:.0f}\")+18)/6)×6 = {fmt_inches(length)}"
        )
    return [BarRow(
        mark="VW", size="#4", qty=qty, length_in=length, shape="Str",
        notes=vw_notes,
        source_rule="rule_hw_vert_wall",
    )]


# ---------------------------------------------------------------------------
# CB — C-bar hairpin, qty from count table
# ---------------------------------------------------------------------------

def rule_hw_c_bars(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    CB — C-bar hairpin.

    qty    = L//12+1  [no-pipe case, @12\" oc along wall length]               ✓
             TABLE    [pipe case, count table keyed by (D_in, H_in)]           ✓
    body   = ceil((H_in + 9) / 2) * 2   (rounded up to next 2" increment)     ✓
             (= ceil((H1 - 3) / 2) * 2  where H1 = H + 12)
    leg    = T + 4   (T = wall thickness; 2\" cover each face)                 ✓
    size   = c_s from D89A/D89B table

    Confirmed:
      No-pipe 8ft/H=60: qty=96//12+1=9 ✓
      H=71, T=10: body=ceil(80/2)*2=80\"=6'-8\" ✓  leg=14\"=1'-2\" ✓
      H=90, T=12: body=ceil(99/2)*2=100\"=8'-4\" ✓  leg=16\"=1'-4\" ✓
    """
    L      = p.wall_width_ft * 12
    H      = p.wall_height_ft * 12
    D_in   = _effective_D(p)
    case   = getattr(p, "loading_case", "I")
    row    = _d89_by_height(H, case)
    tbl    = "D89B" if case == "II / III" else "D89A"
    c_size = row["c_s"]
    T      = row["T"]
    no_pipe = int(getattr(p, "pipe_qty", 0)) < 1
    if no_pipe:
        qty = math.floor(L / 12) + 1
    else:
        cnts = _count_lookup(D_in, int(H))
        qty  = cnts["c_bar"]
    body   = math.ceil((H + 9) / 2) * 2    # = ceil((H1-3)/2)*2 where H1=H+12
    leg    = float(T) + 4.0                  # 2" cover each face
    R      = 9.0
    deduct = bend_reduce("shape_2", c_size)
    stock  = body + 2 * leg - deduct

    log.step(
        f"{tbl} H={H:.0f}\" → c_size={c_size}  T={T}\"  "
        f"CB body=ceil(({H:.0f}+9)/2)*2={body}\"  leg=T+4={leg}\"  stock={fmt_inches(stock)}  "
        f"qty={'L//12+1' if no_pipe else 'TABLE'}={qty}",
        source="HeadwallRules",
    )
    log.result("CB", f"{c_size} × {qty} @ {fmt_inches(stock)}", source="HeadwallRules")

    return [BarRow(
        mark="CB", size=c_size, qty=qty, length_in=stock, shape="C", bend_type="11",
        leg_a_in=body, leg_b_in=float(T) + 2.0, leg_c_in=float(T) + 4.0, leg_d_in=H, leg_g_in=R,
        notes=(
            f"A(={fmt_inches(body)}) + B(=T+2={fmt_inches(float(T)+2.0)}) "
            f"+ C(=T+4={fmt_inches(float(T)+4.0)}) = {fmt_inches(stock)}"
        ),
        source_rule="rule_hw_c_bars",
    )]


# ---------------------------------------------------------------------------
# LW — longitudinal wall bars (#4, qty from count table, length = L-6)
# ---------------------------------------------------------------------------

def rule_hw_long_wall(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    LW — Longitudinal wall bars.

    qty    = TABLE  (count table keyed by (D_in, H_in))               ✓
             For no-pipe use D=0 as the table key.
    length = L - 6  [pipe case, 3\" cover each end]                    ✓
             L - 4  [no-pipe case, 2\" cover each end]                  ✓
    size   = #4 (constant)

    Confirmed:
      Pipe   8ft/D=36/H=71: qty=22 len=7'-6\" ✓
      Pipe  10ft/D=48/H=90: qty=28 len=9'-6\" ✓
      No-pipe 8ft/H=60:     qty=14 len=7'-8\" ✓
    """
    L       = p.wall_width_ft * 12
    H       = p.wall_height_ft * 12
    no_pipe = int(getattr(p, "pipe_qty", 0)) < 1
    D_in    = _effective_D(p)
    cnts    = _count_lookup(D_in, int(H))
    qty     = cnts["wall_horz"]
    length  = L - 4.0 if no_pipe else L - 6.0
    cover   = "2\"" if no_pipe else "3\""

    log.step(f"LW: (D={D_in}\", H={H:.0f}\") TABLE qty={qty}  len=L-{'4' if no_pipe else '6'}={fmt_inches(length)} ({cover} cover ea end)",
             source="HeadwallRules")
    log.result("LW", f"#4 × {qty} @ {fmt_inches(length)}", source="HeadwallRules")

    return [BarRow(
        mark="LW", size="#4", qty=qty, length_in=length, shape="Str",
        notes=f"Long wall  TABLE  len=L-{'4' if no_pipe else '6'}={fmt_inches(length)}",
        source_rule="rule_hw_long_wall",
    )]


# ---------------------------------------------------------------------------
# TW — top-of-wall bars (#5, 3 total, length = L-6)
# ---------------------------------------------------------------------------

def rule_hw_top_wall(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    TW — Top-of-wall bars (#5, 3 total).

    qty    = 3 (constant, per D89A plan)
    length = L - 6  [pipe case, 3\" cover each end]    ✓
             L - 4  [no-pipe case, 2\" cover each end]  ✓

    Confirmed:
      Pipe   8ft: L-6=7'-6\" ✓
      No-pipe 8ft: L-4=7'-8\" ✓
    """
    L       = p.wall_width_ft * 12
    no_pipe = int(getattr(p, "pipe_qty", 0)) < 1
    qty     = 3
    length  = L - 4.0 if no_pipe else L - 6.0

    log.step(f"TW: 3 × #5 @ {fmt_inches(length)}  (L-{'4' if no_pipe else '6'}={fmt_inches(length)})",
             source="HeadwallRules")
    log.result("TW", f"#5 × 3 @ {fmt_inches(length)}", source="HeadwallRules")

    return [BarRow(
        mark="TW", size="#5", qty=qty, length_in=length, shape="Str",
        notes=f"Top of wall #5 Tot 3  L-{'4' if no_pipe else '6'}={fmt_inches(length)}",
        source_rule="rule_hw_top_wall",
    )]


# ---------------------------------------------------------------------------
# WS — wall spreaders mk401 (#4, qty=L_ft, body=T-1.5", legs=D//6)
# ---------------------------------------------------------------------------

def rule_hw_spreaders(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    WS — Wall spreaders (mk401), U-shape.

    PIPE case:
      qty    = L_ft  (one per foot of wall width)                            ✓
      body   = round((T - 1.5) * 2) / 2   (nearest 0.5\", wall clear span)  ✓
      legs   = D_in // 6                                                     ✓
      Confirmed: T=10 D=36 → body=8.5\" legs=6\" ✓
                 T=12 D=48 → body=10\" legs=8\" ✓

    NO-PIPE case  (every 4ft, D=0):
      qty    = L_ft // 2   (every 4ft → 2 sets for 8ft wall → 4 bars)       ✓
      body   = T // 2      (= 5\" for T=10\")                                 ✓
      legs   = T // 2 - 0.5  (= 4.5\" for T=10\")                            ✓
      Confirmed: 8ft/H=60 → qty=4, body=5\", legs=4.5\" ✓

    size = #4 (both cases)
    """
    H       = p.wall_height_ft * 12
    no_pipe = int(getattr(p, "pipe_qty", 0)) < 1
    D_in    = _parse_dia(p)
    row     = _d89_by_height(H, getattr(p, "loading_case", "I"))
    T       = row["T"]
    deduct  = bend_reduce("shape_2", "#4")

    if no_pipe:
        qty  = int(p.wall_width_ft) // 2
        body = float(T // 2)
        leg  = float(T // 2) - 0.5
        log.step(
            f"WS no-pipe: T={T}\"  body=T//2={body}\"  legs=T//2-0.5={leg}\"  "
            f"stock={fmt_inches(body + 2*leg - deduct)}  qty=L_ft//2={qty}",
            source="HeadwallRules",
        )
    else:
        qty  = int(p.wall_width_ft)
        body = round((T - 1.5) * 2) / 2   # nearest 0.5"
        leg  = float(D_in // 6)
        log.step(
            f"WS: T={T}\" D={D_in}\"  body=round((T-1.5)*2)/2={body}\"  "
            f"legs=D//6={leg}\"  stock={fmt_inches(body + 2*leg - deduct)}  qty=L_ft={qty}",
            source="HeadwallRules",
        )

    stock = body + 2 * leg - deduct
    log.result("WS", f"#4 × {qty} @ {fmt_inches(stock)}", source="HeadwallRules")

    return [BarRow(
        mark="WS", size="#4", qty=qty, length_in=stock, shape="U",
        leg_a_in=body, leg_b_in=leg, leg_c_in=leg,
        notes=f"Wall spreader mk401  body={fmt_inches(body)}  legs={fmt_inches(leg)}",
        source_rule="rule_hw_spreaders",
    )]


# ---------------------------------------------------------------------------
# ST — mat standees mk400 (#4, qty=L_ft)
# ---------------------------------------------------------------------------

def rule_hw_standees(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    ST — Mat standees (mk400), S-shape.

    PIPE case:
      qty    = L_ft  (one per foot of wall width)             ✓
      size   = #4                                             ✓
      A      = 5.0\" (top hook, constant per both gold cases)  ✓
      leg    = D_in / 6 - 0.5  (riser/seat legs)             ✓
      base   = 12.0\" (bottom seat, constant)                  ✓
      Confirmed: D=36 → legs=5.5\" ✓;  D=48 → legs≈7\" ✓

    NO-PIPE case:
      qty    = L_ft  (one per foot, same as pipe)             ✓
      size   = #5                                             ✓
      A      = 5.0\" (top hook, constant)                      ✓
      leg    = 5.5\" (fixed, no pipe diameter)                 ✓
      base   = 18.0\" (larger base for solid footing mat)      ✓
      Confirmed: 8ft/H=60 → qty=8 #5 legs=5.5\" base=18\" ✓
    """
    D_in    = _parse_dia(p)
    no_pipe = int(getattr(p, "pipe_qty", 0)) < 1
    qty     = int(p.wall_width_ft)

    if no_pipe:
        size  = "#5"
        seg_a = 5.0
        seg_b = 5.5    # fixed for no-pipe
        seg_c = 5.5
        seg_d = 18.0   # larger base for solid footing mat
        deduct = bend_reduce("shape_3", "#5")
        log.step(
            f"ST no-pipe: #5  A=5\"  legs=5.5\" × 2  base=18\"  "
            f"stock={fmt_inches(seg_a+seg_b+seg_c+seg_d-deduct)}  qty=L_ft={qty}",
            source="HeadwallRules",
        )
    else:
        size  = "#4"
        seg_a = 5.0
        seg_b = D_in / 6 - 0.5
        seg_c = D_in / 6 - 0.5
        seg_d = 12.0
        deduct = bend_reduce("shape_3", "#4")
        log.step(
            f"ST: D={D_in}\"  A=5\"  legs=D/6-0.5={seg_b:.1f}\" × 2  base=12\"  "
            f"stock={fmt_inches(seg_a+seg_b+seg_c+seg_d-deduct)}  qty=L_ft={qty}",
            source="HeadwallRules",
        )

    stock = seg_a + seg_b + seg_c + seg_d - deduct
    log.result("ST", f"{size} × {qty} @ {fmt_inches(stock)}", source="HeadwallRules")

    return [BarRow(
        mark="ST", size=size, qty=qty, length_in=stock, shape="S",
        leg_a_in=seg_a, leg_b_in=seg_b, leg_c_in=seg_c, leg_d_in=seg_d,
        notes=f"Mat standee mk400  A=5\"  legs={fmt_inches(seg_b)}×2  base={fmt_inches(seg_d)}",
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
