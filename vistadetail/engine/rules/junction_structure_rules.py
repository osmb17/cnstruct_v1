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
      JA1S — top slab straight
      JA1U — top slab U-bar

    Geometry (from D91A and gold barlist):
      body  = S_in + 2×t − 6"          (3" cover at each outer wall face)
      leg   = _A_BAR_LEG_IN = 12"      (1'-0" tail — confirmed from gold)
      stock_u = 2×leg + body − bend_reduce(shape_2, a_s)

    Quantity — bars run across SPAN, counted along LENGTH:
      qty_bs = floor((L_in + 2t) / a_sp)
      qty_ts = floor((L_in + 2t + 2×_MH_SEAT_EXT_IN) / a_sp)  [if manhole]
               floor((L_in + 2t) / a_sp)                        [no manhole]

    Confirmed: Dane gold May-2026 (Span=5', Length=6', Hb=5.5', Cover=10'):
      body = 5'-10", qty = 14 each slab (no manhole).
    """
    hb_ft      = p.hb_ft
    span_ft    = p.span_ft
    length_ft  = float(getattr(p, "length_ft", span_ft))
    cover      = getattr(p, "max_earth_cover_ft", 10.0)
    no_manhole = str(getattr(p, "has_manhole", "yes")).lower() == "no"

    row  = _junc_lookup(hb_ft, span_ft, cover, log)
    a_s  = row["a_s"]
    a_sp = row["a_sp"]
    t    = row["t"]
    S_in = span_ft  * 12
    L_in = length_ft * 12

    body   = S_in + 2 * t - 6.0
    leg    = _A_BAR_LEG_IN                           # 12" = 1'-0"
    deduct = bend_reduce("shape_2", a_s)
    len_u  = 2 * leg + body - deduct                 # U-bar stock

    outer_L = L_in + 2 * t                           # length dimension (qty direction)
    qty_bs  = math.floor(outer_L / a_sp)
    if no_manhole:
        qty_ts = math.floor(outer_L / a_sp)          # same as bottom — no MH seat extension
        mh_note = " (no MH seat)"
    else:
        qty_ts = math.floor((outer_L + 2 * _MH_SEAT_EXT_IN) / a_sp)
        mh_note = f" (+2×{_MH_SEAT_EXT_IN}\" MH seat)"

    log.step(
        f"JA body=S+2t-6={S_in:.0f}+{2*t}-6={body:.1f}\"  "
        f"leg={leg}\"  deduct={deduct}\"  len_U={len_u:.1f}\"",
        source="JunctionRules",
    )
    log.step(
        f"JA2 bottom: outer_L={outer_L:.0f}\"  qty=floor({outer_L:.0f}/{a_sp})={qty_bs}  "
        f"JA1 top: qty={qty_ts}{mh_note}",
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

    Quantity — counts both wall pairs for rectangular plan:
      qty_span_walls   = floor((S_in + 2t) / e_sp)   (2 walls with outer width = S+2t)
      qty_length_walls = floor((L_in + 2t) / e_sp)   (2 walls with outer width = L+2t)
      qty_total        = qty_span_walls + qty_length_walls

    Confirmed: Dane gold May-2026 (Span=5', Length=6', t=8", e_sp=6"):
      floor(76/6) + floor(88/6) = 12 + 14 = 26 ✓
    """
    hb_ft     = p.hb_ft
    span_ft   = p.span_ft
    length_ft = float(getattr(p, "length_ft", span_ft))
    cover     = getattr(p, "max_earth_cover_ft", 10.0)

    row   = _junc_lookup(hb_ft, span_ft, cover, log)
    e_s   = row["e_s"]
    e_sp  = row["e_sp"]
    ts    = row["ts"]
    bs    = row["bs"]
    t     = row["t"]
    Hb_in = hb_ft   * 12
    S_in  = span_ft * 12
    L_in  = length_ft * 12

    bar_len     = ts + Hb_in + bs - 6.0
    outer_S     = S_in + 2 * t
    outer_L     = L_in + 2 * t
    qty_S       = math.floor(outer_S / e_sp)
    qty_L       = math.floor(outer_L / e_sp)
    qty         = qty_S + qty_L

    log.step(
        f"JE1 ({e_s}@{e_sp}\"): ts+Hb+bs-6={ts}+{Hb_in:.0f}+{bs}-6={bar_len:.1f}\"  "
        f"qty=floor({outer_S:.0f}/{e_sp})+floor({outer_L:.0f}/{e_sp})={qty_S}+{qty_L}={qty}",
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
      body    = ts + Hb_in + bs − 6"        (full height, same as E-bar)
      bar_len = body + 2×B − bend_reduce(shape_2, b_size)

    Quantity — counts both wall pairs for rectangular plan:
      qty_span_walls   = floor((S_in + 2t) / b_sp)
      qty_length_walls = floor((L_in + 2t) / b_sp)
      qty_total        = qty_span_walls + qty_length_walls

    Confirmed: Dane gold May-2026 (Span=5', Length=6', t=8", b_sp=6", B=31"):
      floor(76/6) + floor(88/6) = 12 + 14 = 26 ✓
    """
    hb_ft     = p.hb_ft
    span_ft   = p.span_ft
    length_ft = float(getattr(p, "length_ft", span_ft))
    cover     = getattr(p, "max_earth_cover_ft", 10.0)

    row   = _junc_lookup(hb_ft, span_ft, cover, log)
    b_s   = row["b_s"]
    b_sp  = row["b_sp"]
    B     = row["B"]
    ts    = row["ts"]
    bs    = row["bs"]
    t     = row["t"]
    Hb_in = hb_ft    * 12
    S_in  = span_ft  * 12
    L_in  = length_ft * 12

    body    = ts + Hb_in + bs - 6.0
    deduct  = bend_reduce("shape_2", b_s)
    bar_len = body + 2 * B - deduct
    outer_S = S_in + 2 * t
    outer_L = L_in + 2 * t
    qty_S   = math.floor(outer_S / b_sp)
    qty_L   = math.floor(outer_L / b_sp)
    qty     = qty_S + qty_L

    log.step(
        f"JB1 ({b_s}@{b_sp}\"): body=ts+Hb+bs-6={ts}+{Hb_in:.0f}+{bs}-6={body:.1f}\"  "
        f"bar_len=body+2B-deduct={body:.1f}+2×{B}-{deduct}={bar_len:.1f}\"  "
        f"qty=floor({outer_S:.0f}/{b_sp})+floor({outer_L:.0f}/{b_sp})={qty_S}+{qty_L}={qty}",
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
    Additional "a" bars at side pipe openings per D91A Note 12.

    Note 12: provide additional bars equal to half the interrupted main
    reinforcement, one each side of the opening.

    Applies only when side_pipe_dia_in != "None".  When there is no side
    pipe (or no manhole), these bars are not required (Dane gold May-2026).

    For the side pipe of diameter D_in:
      interrupted = floor(D_in / a_sp) + 1
      add_per_side = ceil(interrupted / 2)
      qty = add_per_side × 2 sides × 2 slabs

    Length = "a" bar body = S_in + 2×t − 6".
    """
    hb_ft    = p.hb_ft
    span_ft  = p.span_ft
    cover    = getattr(p, "max_earth_cover_ft", 10.0)
    side_pipe = str(getattr(p, "side_pipe_dia_in", "None")).strip()
    has_side  = side_pipe.lower() != "none" and side_pipe != "0"

    if not has_side:
        log.ok(
            "No side pipe — JX1 additional bars omitted (Note 12 n/a).",
            source="JunctionRules",
        )
        return []

    row  = _junc_lookup(hb_ft, span_ft, cover, log)
    t    = row["t"]
    a_sp = row["a_sp"]
    S_in = span_ft * 12

    bar_len   = S_in + 2 * t - 6.0
    D_in      = float(side_pipe)

    interrupted  = math.floor(D_in / a_sp) + 1
    add_per_side = math.ceil(interrupted / 2)
    qty          = add_per_side * 2 * 2   # 2 sides × 2 slabs

    log.step(
        f"JX1 side pipe D={fmt_inches(D_in)}: floor({D_in:.0f}/{a_sp})+1={interrupted} interrupted  "
        f"ceil({interrupted}/2)={add_per_side}/side × 2 sides × 2 slabs = {qty}",
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
        notes=f"Additional 'a' bars at side pipe opening D={fmt_inches(D_in)} (Note 12)",
        source_rule="rule_junc_add_bars",
    )]


# ---------------------------------------------------------------------------
# D91A plan constants (from Section C-C, plan details, and gold barlist)
# ---------------------------------------------------------------------------

_WALL_HORIZ_SP_IN  = 12   # vertical spacing of horizontal wall bars (@12" per gold/D91A)
_WALL_HORIZ_EXT_IN = 12   # wall horiz bars extend this far into top AND bottom slab (1'-0")
_TS_INNER_SP_IN    = 6    # top-slab inner-face longitudinal spacing (@6" oc — Dane gold May-2026)
_TS_OUTER_SP_IN    = 6    # top-slab outer-face longitudinal spacing (@6" oc — Dane gold May-2026)
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
    Longitudinal distribution bars running along the LENGTH dimension in both slabs.

    Bottom slab (JD1) — EF @12" oc:
      bar_len = L_in − 6"               (3" cover each end)
      qty     = 2 faces × (floor((L_in + 2t) / 12) + 1)

    Top slab inner (JL1) — @6" oc across outer span width:
      bar_len = L_in − 6"
      qty     = floor((S_in + 2t) / _TS_INNER_SP_IN)

    Top slab outer (JL2) — @6" oc across clear span:
      bar_len = L_in − 6"
      qty     = floor(S_in / _TS_OUTER_SP_IN)

    Confirmed: Dane gold May-2026 (Span=5', Length=6', t=8"):
      JD1: 2×(floor(88/12)+1)=16, len=5'-6" ✓
      JL1: floor(76/6)=12, len=5'-6" ✓
      JL2: floor(60/6)=10, len=5'-6" ✓
    """
    hb_ft     = p.hb_ft
    span_ft   = p.span_ft
    length_ft = float(getattr(p, "length_ft", span_ft))
    cover     = getattr(p, "max_earth_cover_ft", 10.0)

    row  = _junc_lookup(hb_ft, span_ft, cover, log)
    t    = row["t"]
    S_in = span_ft   * 12
    L_in = length_ft * 12

    outer_S  = S_in + 2 * t   # outer span dimension
    outer_L  = L_in + 2 * t   # outer length dimension

    long_len = L_in - 6.0     # 3" cover each end along LENGTH

    # Bottom slab EF @12" — qty counted across the LENGTH span
    qty_bs = 2 * (math.floor(outer_L / _SLAB_LONG_SP_IN) + 1)

    # Top slab inner face @6" — qty counted across the SPAN (outer_S)
    qty_ts_inner = math.floor(outer_S / _TS_INNER_SP_IN)

    # Top slab outer face @6" — qty counted across clear SPAN (S_in)
    qty_ts_outer = math.floor(S_in / _TS_OUTER_SP_IN)

    log.step(
        f"Slab longs: L={L_in:.0f}\" S={S_in:.0f}\" t={t}\"  long_len=L-6={long_len:.1f}\"",
        source="JunctionRules",
    )
    log.step(
        f"JD1 EF@{_SLAB_LONG_SP_IN}\": 2×(floor({outer_L:.0f}/{_SLAB_LONG_SP_IN})+1)={qty_bs}",
        source="JunctionRules",
    )
    log.step(
        f"JL1 inner@{_TS_INNER_SP_IN}\": floor({outer_S:.0f}/{_TS_INNER_SP_IN})={qty_ts_inner}  "
        f"JL2 outer@{_TS_OUTER_SP_IN}\": floor({S_in:.0f}/{_TS_OUTER_SP_IN})={qty_ts_outer}",
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
    Horizontal bars running along the LENGTH on the span-facing walls,
    and along the SPAN on the length-facing walls.  Listed as one row
    using the longer bar (L − 6") per Dane's gold (May-2026).

    Quantity formula (Dane gold May-2026, rectangular 5'×6' box, Hb=5'-6"):
      qty = floor((L+2t)/_WALL_HORIZ_SP_IN)+1 × 2 walls  (span walls, bars run along L)
          + floor((S+2t)/_WALL_HORIZ_SP_IN)+1 × 2 walls  (length walls, bars run along S)
      = (7+1)×2 + (6+1)×2 = 16+14 = 30 ✓

    NOTE: For the rectangular case, bars on length-facing walls are slightly
    shorter (S − 6") but are combined into a single row at L − 6" as
    Dane listed them.  This is conservative (uses the longer bar for all).
    """
    hb_ft     = p.hb_ft
    span_ft   = p.span_ft
    length_ft = float(getattr(p, "length_ft", span_ft))
    cover     = getattr(p, "max_earth_cover_ft", 10.0)

    row   = _junc_lookup(hb_ft, span_ft, cover, log)
    t     = row["t"]
    S_in  = span_ft   * 12
    L_in  = length_ft * 12
    Hb_in = hb_ft * 12

    long_len   = L_in - 6.0
    outer_S    = S_in + 2 * t
    outer_L    = L_in + 2 * t

    # Bars extend into top and bottom slabs; count using outer plan dimension of
    # the adjacent wall pair.
    qty_span_walls   = (math.floor(outer_L / _WALL_HORIZ_SP_IN) + 1) * 2
    qty_length_walls = (math.floor(outer_S / _WALL_HORIZ_SP_IN) + 1) * 2
    qty_total        = qty_span_walls + qty_length_walls

    log.step(
        f"JC1 wall horiz @{_WALL_HORIZ_SP_IN}\": "
        f"span walls=(floor({outer_L:.0f}/{_WALL_HORIZ_SP_IN})+1)×2={qty_span_walls}  "
        f"length walls=(floor({outer_S:.0f}/{_WALL_HORIZ_SP_IN})+1)×2={qty_length_walls}  "
        f"total={qty_total}  len=L-6={fmt_inches(long_len)}",
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
    Circular hoops and extra straight bars per D91A details.

    JMH — Manhole hoops (#6 circular):
      OD = 42" (36" MH cover + 3" each side)
      Qty = 2 (top and bottom of manhole seat per D91A plan)
      Stock = π × OD + 3'-0" lap
      Generated only when has_manhole = "yes".

    JPH — Pipe-opening hoops (#6 circular):
      OD = side_pipe_dia_in + 6" (3" clearance each side per D91A)
      Qty = 2
      Stock = π × OD + 3'-0" lap
      Generated only when side_pipe_dia_in != "None".

    JME — Extra bars adjacent to manhole at top slab (#6 straight):
      Qty = 4 (from D91A plan)
      Length = L_in − 6"
      Generated only when has_manhole = "yes".

    When has_manhole="no" and side_pipe_dia_in="None": returns [] (no hoops).
    """
    hb_ft      = p.hb_ft
    span_ft    = p.span_ft
    length_ft  = float(getattr(p, "length_ft", span_ft))
    cover      = getattr(p, "max_earth_cover_ft", 10.0)
    has_mh     = str(getattr(p, "has_manhole",      "yes")).lower() == "yes"
    side_pipe  = str(getattr(p, "side_pipe_dia_in", "None")).strip()
    has_side   = side_pipe.lower() != "none" and side_pipe != "0"

    _junc_lookup(hb_ft, span_ft, cover, log)
    L_in     = length_ft * 12
    long_len = L_in - 6.0

    rows: list[BarRow] = []

    if has_mh:
        mh_stock = math.pi * _MH_OD_IN + _MH_LAP_IN
        log.step(
            f"JMH manhole hoop: OD={fmt_inches(_MH_OD_IN)} Lap={fmt_inches(_MH_LAP_IN)}  "
            f"stock=π×{_MH_OD_IN:.0f}+{_MH_LAP_IN:.0f}={mh_stock:.1f}\" = {fmt_inches(mh_stock)}",
            source="JunctionRules",
        )
        log.result("JMH", f"#6 × 2 @ {fmt_inches(mh_stock)} (OD={fmt_inches(_MH_OD_IN)})",
                   source="JunctionRules")
        rows.append(BarRow(
            mark="JMH", size="#6", qty=2, length_in=mh_stock,
            shape="Rng",
            notes="Manhole hoops",
            source_rule="rule_junc_hoops",
        ))

    if has_side:
        pipe_d     = float(side_pipe)
        pipe_od    = pipe_d + _PIPE_HOO_CLEAR_IN
        pipe_stock = math.pi * pipe_od + _MH_LAP_IN
        log.step(
            f"JPH side pipe hoop: D={fmt_inches(pipe_d)} OD={fmt_inches(pipe_od)}  "
            f"stock=π×{pipe_od:.0f}+{_MH_LAP_IN:.0f}={pipe_stock:.1f}\" = {fmt_inches(pipe_stock)}",
            source="JunctionRules",
        )
        log.result("JPH", f"#6 × 2 @ {fmt_inches(pipe_stock)} (OD={fmt_inches(pipe_od)})",
                   source="JunctionRules")
        rows.append(BarRow(
            mark="JPH", size="#6", qty=2, length_in=pipe_stock,
            shape="Rng",
            notes=f"Side pipe-opening hoops (D={fmt_inches(pipe_d)})",
            source_rule="rule_junc_hoops",
        ))

    if has_mh:
        log.step(
            f"JME extra top-slab bars at manhole: 4 #6 × {fmt_inches(long_len)}",
            source="JunctionRules",
        )
        log.result("JME", f"#6 × 4 @ {fmt_inches(long_len)}", source="JunctionRules")
        rows.append(BarRow(
            mark="JME", size="#6", qty=4, length_in=long_len,
            shape="Str",
            notes="Extra #6 bars flanking manhole in top slab",
            source_rule="rule_junc_hoops",
        ))

    if not has_mh and not has_side:
        log.ok(
            "No manhole and no side pipe — JMH/JPH/JME omitted. Use Dobies for concrete cover.",
            source="JunctionRules",
        )

    return rows


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
