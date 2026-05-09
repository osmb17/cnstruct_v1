"""
Rule functions for Junction Structure template (D91A/D91B).

Caltrans 2025 Standard Plans D91A (details) and D91B (design table) —
Cast-In-Place Reinforced Concrete Junction Structure.

CIP JUNCTION STRUCTURE TABLE (D91B, 2025):
  Key: (hb_ft, span_ft, max_cover_ft)
  Standard pairings — Hb=5'-6" accepts Span=4' or 5'; all other heights
  are square (Span = Hb numerically).

Bar marks:
  JA1 — "a" C-bars, top slab inside face
  JA2 — "a" C-bars, bottom slab inside face
  JE1 — "e" bars, wall exterior face (Str, vertical)
  JB1 — "b" bars, wall interior (U-bar, legs into top and bottom slab)
  JX1 — additional "a" bars at pipe openings (#4, 3 each side per D91A)

Geometry (all confirmed from D91A typical sections and D91B table):
  body(a) = Span + 2×t − 6"   (3" cover at each outer wall face)
  leg(a)  = slab_thick − 3"   (min 6") into slab from inside face
  len(e)  = ts + Hb + bs − 6" (3" cover top and bottom)
  len(b)  = Hb + 2×B − bend_reduce(shape_2)
             where B = table dimension (horizontal slab lap each end)
"""

from __future__ import annotations

import math

from vistadetail.engine.hooks import bend_reduce
from vistadetail.engine.reasoning_logger import ReasoningLogger
from vistadetail.engine.schema import BarRow, Params, fmt_inches


# ---------------------------------------------------------------------------
# D91B CIP Junction Structure Table — confirmed from 2025 Standard Plan
#
# Key: (hb_ft, span_ft, max_cover_ft)
# Values:
#   ts   = top slab thickness (in)
#   t    = wall thickness (in)
#   bs   = bottom slab thickness (in)
#   a_s  = "a" bar size          a_sp = "a" bar spacing (in)
#   e_s  = "e" bar size          e_sp = "e" bar spacing (in)
#   b_s  = "b" bar size          b_sp = "b" bar spacing (in)
#   B    = "b" bar slab lap (in) — horizontal arm into top AND bottom slab
# ---------------------------------------------------------------------------

_D91B: dict[tuple[float, int, int], dict] = {
    # Hb = 5'-6", Span = 4'
    (5.5, 4, 10): dict(ts=8,  t=8,  bs=8,  a_s="#4", a_sp=10, e_s="#4", e_sp=10, b_s="#4", b_sp=10, B=28),
    (5.5, 4, 20): dict(ts=8,  t=8,  bs=8,  a_s="#4", a_sp=6,  e_s="#4", e_sp=6,  b_s="#4", b_sp=6,  B=28),
    # Hb = 5'-6", Span = 5'
    (5.5, 5, 10): dict(ts=8,  t=8,  bs=8,  a_s="#4", a_sp=6,  e_s="#4", e_sp=6,  b_s="#4", b_sp=6,  B=31),
    (5.5, 5, 20): dict(ts=8,  t=8,  bs=8,  a_s="#4", a_sp=5,  e_s="#4", e_sp=5,  b_s="#4", b_sp=6,  B=27),
    # Hb = 6', Span = 6'
    (6.0, 6, 10): dict(ts=8,  t=8,  bs=8,  a_s="#4", a_sp=5,  e_s="#4", e_sp=5,  b_s="#4", b_sp=5,  B=31),
    (6.0, 6, 20): dict(ts=9,  t=9,  bs=9,  a_s="#5", a_sp=6,  e_s="#4", e_sp=6,  b_s="#4", b_sp=6,  B=29),
    # Hb = 7', Span = 7'
    (7.0, 7, 10): dict(ts=8,  t=8,  bs=8,  a_s="#4", a_sp=5,  e_s="#4", e_sp=5,  b_s="#4", b_sp=5,  B=36),
    (7.0, 7, 20): dict(ts=10, t=10, bs=10, a_s="#5", a_sp=5,  e_s="#4", e_sp=5,  b_s="#4", b_sp=5,  B=33),
    # Hb = 8', Span = 8'  (confirmed from D91B plan — gold barlist confirms e_sp=6)
    (8.0, 8, 10): dict(ts=8,  t=8,  bs=8,  a_s="#5", a_sp=6,  e_s="#4", e_sp=6,  b_s="#4", b_sp=6,  B=35),
    (8.0, 8, 20): dict(ts=11, t=12, bs=12, a_s="#5", a_sp=6,  e_s="#4", e_sp=6,  b_s="#4", b_sp=6,  B=39),
    # Hb = 9', Span = 9'
    (9.0, 9, 10): dict(ts=9,  t=9,  bs=10, a_s="#5", a_sp=5,  e_s="#4", e_sp=5,  b_s="#4", b_sp=5,  B=42),
    (9.0, 9, 20): dict(ts=12, t=13, bs=13, a_s="#5", a_sp=5,  e_s="#5", e_sp=5,  b_s="#5", b_sp=5,  B=44),
    # Hb = 10', Span = 10'
    (10.0, 10, 10): dict(ts=11, t=12, bs=11, a_s="#5", a_sp=5, e_s="#5", e_sp=5, b_s="#4", b_sp=5, B=48),
    (10.0, 10, 20): dict(ts=13, t=14, bs=14, a_s="#6", a_sp=6, e_s="#6", e_sp=6, b_s="#5", b_sp=6, B=49),
    # Hb = 11', Span = 11'
    (11.0, 11, 10): dict(ts=11, t=13, bs=12, a_s="#5", a_sp=5, e_s="#4", e_sp=5, b_s="#4", b_sp=5, B=52),
    (11.0, 11, 20): dict(ts=14, t=18, bs=15, a_s="#6", a_sp=6, e_s="#6", e_sp=6, b_s="#6", b_sp=6, B=53),
    # Hb = 12', Span = 12'
    (12.0, 12, 10): dict(ts=12, t=14, bs=13, a_s="#6", a_sp=6, e_s="#5", e_sp=6, b_s="#5", b_sp=6, B=58),
    (12.0, 12, 20): dict(ts=16, t=20, bs=17, a_s="#7", a_sp=6, e_s="#5", e_sp=6, b_s="#5", b_sp=6, B=60),
}

_KNOWN_HB   = sorted({k[0] for k in _D91B})
_KNOWN_SPAN = sorted({k[1] for k in _D91B})


# ---------------------------------------------------------------------------
# Lookup helper
# ---------------------------------------------------------------------------

def _junc_lookup(hb_ft: float, span_ft: float, cover_ft,
                 log: ReasoningLogger) -> dict:
    """
    Return D91B row for (hb_ft, span_ft, cover_ft).

    cover_key is 20 if cover_ft > 10, else 10.
    For non-standard (Hb, Span) pairs, the nearest tabulated Hb and the
    nearest tabulated Span are used with a warning logged.
    """
    cover_ft  = float(cover_ft)   # choices field returns str; cast once here
    cover_key = 20 if cover_ft > 10 else 10
    span_int  = int(round(span_ft))
    hb_round  = round(hb_ft * 2) / 2   # nearest 0.5-ft increment

    # Exact hit
    key = (hb_round, span_int, cover_key)
    if key in _D91B:
        return _D91B[key]

    # Find nearest Hb
    nearest_hb = min(_KNOWN_HB, key=lambda h: abs(h - hb_ft))
    # Find nearest Span (among those valid for the nearest Hb)
    valid_spans = sorted({k[1] for k in _D91B if k[0] == nearest_hb and k[2] == cover_key})
    nearest_sp  = min(valid_spans, key=lambda s: abs(s - span_ft))

    fallback_key = (nearest_hb, nearest_sp, cover_key)
    if fallback_key in _D91B:
        log.warn(
            f"D91B: no exact entry for Hb={hb_ft}' Span={span_ft}' Cover={cover_key}' — "
            f"using nearest Hb={nearest_hb}' Span={nearest_sp}'. "
            "Verify with D91B standard plan for non-standard geometry.",
            source="JunctionRules",
        )
        return _D91B[fallback_key]

    raise ValueError(
        f"D91B lookup failed for Hb={hb_ft} Span={span_ft} Cover={cover_key} "
        f"and fallback ({nearest_hb}, {nearest_sp}, {cover_key})."
    )


# ---------------------------------------------------------------------------
# Rule: "a" slab bars (JA1 = top slab, JA2 = bottom slab)
# ---------------------------------------------------------------------------

def rule_junc_a_bars(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    "a" bars in the top slab (JA1) and bottom slab (JA2) per D91B.

    Each slab gets TWO bar rows — one straight and one U-bar with 1'-0" tails:
      JA2S — bottom slab straight (body only)
      JA2U — bottom slab U-bar  (body + 1'-0" tails into wall each end)
      JA1S — top slab straight   (body only; extends 1'-6" past box edge for MH seat)
      JA1U — top slab U-bar      (body + 1'-0" tails into wall each end)

    Geometry (from D91A and gold barlist):
      body  = S_in + 2×t − 6"          (3" cover at each outer wall face)
      leg   = _A_BAR_LEG_IN = 12"      (1'-0" tail — confirmed from gold)
      stock_straight = body
      stock_u        = 2×leg + body − bend_reduce(shape_2, a_s)

    Quantity (transverse direction only — longitudinal handled by JD1/JL1/JL2):
      qty_bs = floor((S_in + 2t) / a_sp)                             (bottom slab)
      qty_ts = floor((S_in + 2t + 2×_MH_SEAT_EXT_IN) / a_sp)        (top slab, extends for MH seat)
    """
    hb_ft   = p.hb_ft
    span_ft = p.span_ft
    cover   = getattr(p, "max_earth_cover_ft", 10.0)

    row  = _junc_lookup(hb_ft, span_ft, cover, log)
    a_s  = row["a_s"]
    a_sp = row["a_sp"]
    t    = row["t"]
    S_in = span_ft * 12

    body   = S_in + 2 * t - 6.0
    leg    = _A_BAR_LEG_IN                           # 12" = 1'-0"
    deduct = bend_reduce("shape_2", a_s)
    len_u  = 2 * leg + body - deduct                 # U-bar stock

    outer_bs = S_in + 2 * t
    outer_ts = S_in + 2 * t + 2 * _MH_SEAT_EXT_IN

    qty_bs = math.floor(outer_bs / a_sp)             # bottom slab qty
    qty_ts = math.floor(outer_ts / a_sp)             # top slab qty (wider due to MH seat)

    log.step(
        f"JA body=S+2t-6={S_in:.0f}+{2*t}-6={body:.1f}\"  "
        f"leg={leg}\"  deduct={deduct}\"  len_U={len_u:.1f}\"",
        source="JunctionRules",
    )
    log.step(
        f"JA2 bottom: outer={outer_bs}\"  qty=floor({outer_bs}/{a_sp})={qty_bs}  "
        f"JA1 top: outer={outer_ts}\" (+2×{_MH_SEAT_EXT_IN}\" MH seat)  qty=floor({outer_ts}/{a_sp})={qty_ts}",
        source="JunctionRules",
    )
    log.result("JA2S", f"{a_s} × {qty_bs} straight @ {fmt_inches(body)}", source="JunctionRules")
    log.result("JA2U", f"{a_s} × {qty_bs} U-bar   @ {fmt_inches(len_u)}", source="JunctionRules")
    log.result("JA1S", f"{a_s} × {qty_ts} straight @ {fmt_inches(body)}", source="JunctionRules")
    log.result("JA1U", f"{a_s} × {qty_ts} U-bar   @ {fmt_inches(len_u)}", source="JunctionRules")

    return [
        # --- Bottom slab straight bars ---
        BarRow(
            mark="JA2S", size=a_s, qty=qty_bs, length_in=body,
            shape="Str",
            notes=f"Bottom slab 'a' bars @{a_sp}\" oc (straight)",
            source_rule="rule_junc_a_bars",
        ),
        # --- Bottom slab U-bars ---
        BarRow(
            mark="JA2U", size=a_s, qty=qty_bs, length_in=len_u,
            shape="U", bend_type="2",
            leg_a_in=leg,
            leg_b_in=body,
            leg_g_in=leg,
            notes=f"Bottom slab 'a' bars @{a_sp}\" oc (U-bar, 1'-0\" tails)",
            source_rule="rule_junc_a_bars",
        ),
        # --- Top slab straight bars ---
        BarRow(
            mark="JA1S", size=a_s, qty=qty_ts, length_in=body,
            shape="Str",
            notes=f"Top slab 'a' bars @{a_sp}\" oc (straight)",
            source_rule="rule_junc_a_bars",
        ),
        # --- Top slab U-bars ---
        BarRow(
            mark="JA1U", size=a_s, qty=qty_ts, length_in=len_u,
            shape="U", bend_type="2",
            leg_a_in=leg,
            leg_b_in=body,
            leg_g_in=leg,
            notes=f"Top slab 'a' bars @{a_sp}\" oc (U-bar, 1'-0\" tails)",
            source_rule="rule_junc_a_bars",
        ),
    ]


# ---------------------------------------------------------------------------
# Rule: "e" wall exterior bars (JE1)
# ---------------------------------------------------------------------------

def rule_junc_e_bars(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    "e" bars — straight vertical bars on all four wall exterior faces (D91B).

    Geometry (from D91A typical sections):
      len = ts + Hb_in + bs − 6"   (3" cover top and bottom)

    Quantity:
      qty_per_wall = floor(Span_in / e_sp) + 1
      qty_total    = 4 walls × qty_per_wall
    """
    hb_ft   = p.hb_ft
    span_ft = p.span_ft
    cover   = getattr(p, "max_earth_cover_ft", 10.0)

    row   = _junc_lookup(hb_ft, span_ft, cover, log)
    e_s   = row["e_s"]
    e_sp  = row["e_sp"]
    ts    = row["ts"]
    bs    = row["bs"]
    t     = row["t"]
    Hb_in = hb_ft * 12
    S_in  = span_ft * 12

    bar_len = ts + Hb_in + bs - 6.0
    outer   = S_in + 2 * t
    qty     = math.floor(outer / e_sp)

    log.step(
        f"JE1 ({e_s}@{e_sp}\"): ts+Hb+bs-6={ts}+{Hb_in:.0f}+{bs}-6={bar_len:.1f}\"  "
        f"qty=floor((S+2t)/{e_sp})=floor({outer:.0f}/{e_sp})={qty}",
        source="JunctionRules",
    )
    log.result("JE1", f"{e_s} × {qty} @ {fmt_inches(bar_len)}", source="JunctionRules")

    return [BarRow(
        mark="JE1", size=e_s, qty=qty, length_in=bar_len,
        shape="Str",
        notes=f"Wall exterior 'e' bars @{e_sp}\" oc",
        source_rule="rule_junc_e_bars",
    )]


# ---------------------------------------------------------------------------
# Rule: "b" wall interior bars (JB1)
# ---------------------------------------------------------------------------

def rule_junc_b_bars(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    "b" bars — U-shaped bars on all four wall interior faces (D91B).

    Each "b" bar runs vertically in the wall and laps "B" inches into both
    the top slab and the bottom slab (confirmed from D91A typical sections —
    "B" dimension visible at top AND bottom of each section).

    Geometry:
      len = Hb_in + 2×B − bend_reduce(shape_2, b_size)

    Quantity:
      qty_per_wall = floor(Span_in / b_sp) + 1
      qty_total    = 4 walls × qty_per_wall
    """
    hb_ft   = p.hb_ft
    span_ft = p.span_ft
    cover   = getattr(p, "max_earth_cover_ft", 10.0)

    row   = _junc_lookup(hb_ft, span_ft, cover, log)
    b_s   = row["b_s"]
    b_sp  = row["b_sp"]
    B     = row["B"]
    ts    = row["ts"]
    bs    = row["bs"]
    t     = row["t"]
    Hb_in = hb_ft * 12
    S_in  = span_ft * 12

    # body = full height from bottom cover to top cover (same as E-bar length)
    body   = ts + Hb_in + bs - 6.0
    deduct = bend_reduce("shape_2", b_s)
    bar_len = body + 2 * B - deduct          # body + 2 slab-lap tails − bend deduction
    outer  = S_in + 2 * t
    qty    = math.floor(outer / b_sp)

    log.step(
        f"JB1 ({b_s}@{b_sp}\"): body=ts+Hb+bs-6={ts}+{Hb_in:.0f}+{bs}-6={body:.1f}\"  "
        f"bar_len=body+2B-deduct={body:.1f}+2×{B}-{deduct}={bar_len:.1f}\"  "
        f"qty=floor((S+2t)/{b_sp})=floor({outer:.0f}/{b_sp})={qty}",
        source="JunctionRules",
    )
    log.result("JB1", f"{b_s} × {qty} @ {fmt_inches(bar_len)}", source="JunctionRules")

    return [BarRow(
        mark="JB1", size=b_s, qty=qty, length_in=bar_len,
        shape="U", bend_type="2",
        leg_a_in=float(B),   # A dim — slab lap into bottom slab
        leg_b_in=body,       # B dim — vertical body (ts+Hb+bs-6)
        leg_g_in=float(B),   # G dim — slab lap into top slab
        notes=f"Wall interior 'b' bars @{b_sp}\" oc",
        source_rule="rule_junc_b_bars",
    )]


# ---------------------------------------------------------------------------
# Rule: additional "a" bars at pipe openings (JX1)
# ---------------------------------------------------------------------------

def rule_junc_add_bars(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Additional "a" bars at pipe openings per D91A Note 12.

    Note 12: provide additional bars equal to half the interrupted main
    reinforcement, one each side of the opening.

    For each pipe of diameter D_in, "a" bars at spacing a_sp are interrupted
    over the pipe width:
      interrupted_per_slab = floor(D_in / a_sp) + 1
      add_per_side         = ceil(interrupted_per_slab / 2)
      qty_per_opening      = add_per_side × 2 sides × 2 slabs

    Total JX1 = qty(D1) + qty(D2).
    Length = "a" bar body = Span + 2×t − 6".
    """
    hb_ft   = p.hb_ft
    span_ft = p.span_ft
    cover   = getattr(p, "max_earth_cover_ft", 10.0)

    row   = _junc_lookup(hb_ft, span_ft, cover, log)
    t     = row["t"]
    a_sp  = row["a_sp"]
    S_in  = span_ft * 12

    bar_len = S_in + 2 * t - 6.0

    qty = 0
    pipe_details: list[str] = []
    for pipe_name, D_in in [("D1", int(p.d1_in)), ("D2", int(p.d2_in))]:
        interrupted   = math.floor(D_in / a_sp) + 1
        add_per_side  = math.ceil(interrupted / 2)
        qty_pipe      = add_per_side * 2 * 2   # 2 sides × 2 slabs
        qty          += qty_pipe
        pipe_details.append(
            f"{pipe_name}={D_in}\" → interrupted={interrupted}  "
            f"add/side={add_per_side}  ×2sides×2slabs={qty_pipe}"
        )
        log.step(
            f"JX1 {pipe_name}: floor({D_in}/{a_sp})+1={interrupted} interrupted  "
            f"ceil({interrupted}/2)={add_per_side}/side × 2 sides × 2 slabs = {qty_pipe}",
            source="JunctionRules",
        )

    log.step(
        f"JX1 body=S+2t-6={S_in:.0f}+{2*t}-6={bar_len:.1f}\"",
        source="JunctionRules",
    )
    log.result("JX1", f"#4 × {qty} @ {fmt_inches(bar_len)}", source="JunctionRules")

    return [BarRow(
        mark="JX1", size="#4", qty=qty, length_in=bar_len,
        shape="Str",
        notes="Additional 'a' bars at pipe openings (Note 12)",
        source_rule="rule_junc_add_bars",
    )]


# ---------------------------------------------------------------------------
# D91A plan constants (from Section C-C, plan details, and gold barlist)
# ---------------------------------------------------------------------------

_WALL_HORIZ_SP_IN  = 12   # vertical spacing of horizontal wall bars (@12" per gold/D91A)
_WALL_HORIZ_EXT_IN = 12   # wall horiz bars extend this far into top AND bottom slab (1'-0")
_TS_INNER_SP_IN    = 9    # top-slab inner-face longitudinal spacing (#4@9 per D91A)
_TS_OUTER_SP_IN    = 12   # top-slab outer-face longitudinal spacing (#4@12 per D91A)
_SLAB_LONG_SP_IN   = 12   # bottom-slab longitudinal bar spacing, EF (@12" per D91A)
_MH_SEAT_EXT_IN    = 18   # manhole seat extends 1'-6" each side of box on top slab
_MH_OD_IN          = 42.0 # manhole hoop OD = 36" manhole + 3" each side (D91A)
_MH_LAP_IN         = 36.0 # 3'-0" lap splice for #6 circular hoops
_PIPE_HOO_CLEAR_IN = 6.0  # clearance added each side of pipe for hoop OD
_A_BAR_LEG_IN      = 12.0 # A-bar U-bar tail = 1'-0" (per gold barlist)


# ---------------------------------------------------------------------------
# Rule: longitudinal bars in bottom slab (JD1) and top slab (JL1/JL2)
# ---------------------------------------------------------------------------

def rule_junc_slab_longs(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Longitudinal distribution bars running along the structure LENGTH
    (perpendicular to the transverse 'a' bars) in both slabs.

    From D91A Section C-C:
      '#4@9'  = inner face of top slab
      '#4@12' = outer face of both slabs

    Bottom slab (JD1) — EF (inner @a_sp + outer @12"):
      inner qty = floor(S_in / a_sp) + 1
      outer qty = floor((S_in + 2t) / 12) + 1
      total qty  = inner + outer

    Top slab inner (JL1) — '#4@9' across outer box width:
      qty = floor((S_in + 2t) / _TS_INNER_SP_IN)

    Top slab outer (JL2) — '#4@12' across outer box width:
      qty = floor((S_in + 2t) / _TS_OUTER_SP_IN) + 1

    Length for all = S_in - 6"  (3" cover at each end of the run).
    """
    hb_ft   = p.hb_ft
    span_ft = p.span_ft
    cover   = getattr(p, "max_earth_cover_ft", 10.0)

    row  = _junc_lookup(hb_ft, span_ft, cover, log)
    t    = row["t"]
    S_in = span_ft * 12
    outer = S_in + 2 * t     # outer box width = S + 2 walls

    long_len = S_in - 6.0   # 3" cover each end along structure length

    # Bottom slab — EF @12" oc across outer box width
    # qty = 2 faces × (floor(outer/12) + 1)
    qty_bs = 2 * (math.floor(outer / _SLAB_LONG_SP_IN) + 1)

    # Top slab inner face @9" oc
    qty_ts_inner = math.floor(outer / _TS_INNER_SP_IN)

    # Top slab outer face @12" oc
    qty_ts_outer = math.floor(outer / _TS_OUTER_SP_IN) + 1

    log.step(
        f"JD1 bottom slab longs EF @{_SLAB_LONG_SP_IN}\"oc: "
        f"2×(floor({outer:.0f}/{_SLAB_LONG_SP_IN})+1)={qty_bs}  len={fmt_inches(long_len)}",
        source="JunctionRules",
    )
    log.step(
        f"JL1 top slab inner@{_TS_INNER_SP_IN}\": floor({outer:.0f}/{_TS_INNER_SP_IN})={qty_ts_inner}  "
        f"JL2 top slab outer@{_TS_OUTER_SP_IN}\": floor({outer:.0f}/{_TS_OUTER_SP_IN})+1={qty_ts_outer}  "
        f"len={fmt_inches(long_len)}",
        source="JunctionRules",
    )
    log.result("JD1", f"#4 × {qty_bs} @ {fmt_inches(long_len)}", source="JunctionRules")
    log.result("JL1", f"#4 × {qty_ts_inner} @ {fmt_inches(long_len)}", source="JunctionRules")
    log.result("JL2", f"#4 × {qty_ts_outer} @ {fmt_inches(long_len)}", source="JunctionRules")

    return [
        BarRow(
            mark="JD1", size="#4", qty=qty_bs, length_in=long_len,
            shape="Str",
            notes=f"Bottom slab long. bars EF @{_SLAB_LONG_SP_IN}\" oc",
            source_rule="rule_junc_slab_longs",
        ),
        BarRow(
            mark="JL1", size="#4", qty=qty_ts_inner, length_in=long_len,
            shape="Str",
            notes=f"Top slab inner-face long. @{_TS_INNER_SP_IN}\" oc",
            source_rule="rule_junc_slab_longs",
        ),
        BarRow(
            mark="JL2", size="#4", qty=qty_ts_outer, length_in=long_len,
            shape="Str",
            notes=f"Top slab outer-face long. @{_TS_OUTER_SP_IN}\" oc",
            source_rule="rule_junc_slab_longs",
        ),
    ]


# ---------------------------------------------------------------------------
# Rule: horizontal longitudinal bars in walls — double curtain (JC1)
# ---------------------------------------------------------------------------

def rule_junc_wall_horiz(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Horizontal bars running longitudinally (along the structure length)
    on both faces of the two SOLID side walls (the walls without pipe
    openings — confirmed for 'no side pipes' case in gold barlist).

    From D91A plan analysis:
      Spacing = 9" oc vertically along the wall height
      Double curtain = inside face + outside face of each solid wall
      2 solid side walls × 2 curtains × (floor(Hb_in/9) + 1) = 44  [gold ✓]

    Length = S_in - 6"  (3" cover at each end of the run).
    """
    hb_ft   = p.hb_ft
    span_ft = p.span_ft
    cover   = getattr(p, "max_earth_cover_ft", 10.0)

    _junc_lookup(hb_ft, span_ft, cover, log)   # validate / log table row
    S_in  = span_ft * 12
    Hb_in = hb_ft * 12

    long_len         = S_in - 6.0
    # Bars extend _WALL_HORIZ_EXT_IN (12") into both top and bottom slabs
    horiz_span       = Hb_in + 2 * _WALL_HORIZ_EXT_IN
    qty_per_curtain  = math.floor(horiz_span / _WALL_HORIZ_SP_IN) + 1
    qty_total        = 2 * 2 * qty_per_curtain   # 2 solid walls × 2 curtains

    log.step(
        f"JC1 wall horiz: span=Hb+2×{_WALL_HORIZ_EXT_IN}\"={horiz_span}\"  "
        f"@{_WALL_HORIZ_SP_IN}\"oc → floor({horiz_span}/{_WALL_HORIZ_SP_IN})+1={qty_per_curtain}/curtain  "
        f"×4 (2 walls EF) = {qty_total}  len={fmt_inches(long_len)}",
        source="JunctionRules",
    )
    log.result("JC1", f"#4 × {qty_total} @ {fmt_inches(long_len)}", source="JunctionRules")

    return [BarRow(
        mark="JC1", size="#4", qty=qty_total, length_in=long_len,
        shape="Str",
        notes=f"Wall horiz. bars @{_WALL_HORIZ_SP_IN}\" oc EF",
        source_rule="rule_junc_wall_horiz",
    )]


# ---------------------------------------------------------------------------
# Rule: manhole hoops, pipe opening hoops, extra top-slab bars (JMH/JPH/JME)
# ---------------------------------------------------------------------------

def rule_junc_hoops(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Circular hoops and extra straight bars per D91A details:

    JMH — Manhole hoops (#6 circular):
      OD = 42" (36" MH cover + 3" each side)
      Qty = 2 (top and bottom of manhole seat per D91A plan)
      Stock = π × OD + 3'-0" lap

    JPH — Pipe-opening hoops (#6 circular):
      OD = max(D1, D2) + 6" (3" clearance each side per D91A)
      Qty = 2 (one ring per pipe opening, or two at each if D1=D2)
      Stock = π × OD + 3'-0" lap

    JME — Extra bars adjacent to manhole at top slab (#6 straight):
      Qty = 4 (from D91A plan — two pairs flanking the 36" MH opening)
      Length = S_in - 6" (same run as top-slab longs)
    """
    hb_ft   = p.hb_ft
    span_ft = p.span_ft
    cover   = getattr(p, "max_earth_cover_ft", 10.0)

    _junc_lookup(hb_ft, span_ft, cover, log)
    S_in = span_ft * 12

    long_len = S_in - 6.0   # JME length

    # Manhole hoop
    mh_stock = math.pi * _MH_OD_IN + _MH_LAP_IN

    # Pipe opening hoop
    d_max    = max(int(p.d1_in), int(p.d2_in))
    pipe_od  = float(d_max) + _PIPE_HOO_CLEAR_IN
    pipe_stock = math.pi * pipe_od + _MH_LAP_IN

    log.step(
        f"JMH manhole hoop: OD={fmt_inches(_MH_OD_IN)} Lap={fmt_inches(_MH_LAP_IN)}  "
        f"stock=π×{_MH_OD_IN:.0f}+{_MH_LAP_IN:.0f}={mh_stock:.1f}\" = {fmt_inches(mh_stock)}",
        source="JunctionRules",
    )
    log.step(
        f"JPH pipe hoop: OD={fmt_inches(pipe_od)} (D_max={d_max}+6)  "
        f"stock=π×{pipe_od:.0f}+{_MH_LAP_IN:.0f}={pipe_stock:.1f}\" = {fmt_inches(pipe_stock)}",
        source="JunctionRules",
    )
    log.step(
        f"JME extra top-slab bars at manhole: 4 #6 × {fmt_inches(long_len)}",
        source="JunctionRules",
    )
    log.result("JMH", f"#6 × 2 @ {fmt_inches(mh_stock)} (OD={fmt_inches(_MH_OD_IN)})", source="JunctionRules")
    log.result("JPH", f"#6 × 2 @ {fmt_inches(pipe_stock)} (OD={fmt_inches(pipe_od)})", source="JunctionRules")
    log.result("JME", f"#6 × 4 @ {fmt_inches(long_len)}", source="JunctionRules")

    return [
        BarRow(
            mark="JMH", size="#6", qty=2, length_in=mh_stock,
            shape="Rng",
            notes="Manhole hoops",
            source_rule="rule_junc_hoops",
        ),
        BarRow(
            mark="JPH", size="#6", qty=2, length_in=pipe_stock,
            shape="Rng",
            notes="Pipe-opening hoops",
            source_rule="rule_junc_hoops",
        ),
        BarRow(
            mark="JME", size="#6", qty=4, length_in=long_len,
            shape="Str",
            notes="Extra #6 bars flanking manhole in top slab",
            source_rule="rule_junc_hoops",
        ),
    ]


# ---------------------------------------------------------------------------
# Rule: validate
# ---------------------------------------------------------------------------

def rule_validate_junction(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Validate geometry against D91B table limits and log the table row used.
    """
    cover     = float(getattr(p, "max_earth_cover_ft", 10.0))
    cover_key = 20 if cover > 10 else 10

    row = _junc_lookup(p.hb_ft, p.span_ft, cover, log)
    log.ok(
        f"D91B table row: Hb={p.hb_ft}' Span={p.span_ft}' Cover={cover_key}'  "
        f"ts={row['ts']}\" t={row['t']}\" bs={row['bs']}\"",
        source="JunctionRules",
    )

    if p.hb_ft < 5.5:
        log.warn(
            f"Hb={p.hb_ft}' is below the D91B minimum of 5'-6\"",
            source="JunctionRules",
        )
    if p.hb_ft > 12.0:
        log.warn(
            f"Hb={p.hb_ft}' exceeds the D91B table maximum of 12' — "
            "structural analysis required.",
            source="JunctionRules",
        )
    if p.span_ft > 12.0:
        log.warn(
            f"Span={p.span_ft}' exceeds the D91B table maximum of 12' — "
            "structural analysis required.",
            source="JunctionRules",
        )

    d_max = max(int(p.d1_in), int(p.d2_in))
    if d_max / 12.0 > p.hb_ft - (row["ts"] + row["bs"]) / 12.0:
        log.warn(
            f"Largest pipe ({d_max}\") may not fit within Hb={p.hb_ft}' "
            f"after accounting for ts={row['ts']}\" and bs={row['bs']}\"",
            source="JunctionRules",
        )

    return []
