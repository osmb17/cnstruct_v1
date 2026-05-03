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
    # Hb = 8', Span = 8'  (confirmed from D91B plan — a_sp/e_sp order corrected)
    (8.0, 8, 10): dict(ts=8,  t=8,  bs=8,  a_s="#5", a_sp=6,  e_s="#4", e_sp=5,  b_s="#4", b_sp=6,  B=35),
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
    "a" C-bars in the top slab and bottom slab (inside face, per D91B).

    Geometry (from D91A typical sections):
      body    = Span_in + 2×t − 6"        (3" cover at each outer wall face)
      leg_top = max(6, ts − 3)            (into top slab from inside face)
      leg_bot = max(6, bs − 3)            (into bottom slab from inside face)
      stock   = 2×leg + body − bend_reduce(shape_2, a_size)

    Quantity (square structure — "a" bars run in BOTH plan directions):
      qty_per_dir  = floor(Span_in / a_sp) + 2   (one direction)
      qty_per_slab = 2 × qty_per_dir              (X and Y directions)
    """
    hb_ft   = p.hb_ft
    span_ft = p.span_ft
    cover   = getattr(p, "max_earth_cover_ft", 10.0)

    row    = _junc_lookup(hb_ft, span_ft, cover, log)
    a_s    = row["a_s"]
    a_sp   = row["a_sp"]
    ts     = row["ts"]
    t      = row["t"]
    bs     = row["bs"]
    S_in   = span_ft * 12

    body    = S_in + 2 * t - 6.0
    leg_top = max(6.0, ts - 3.0)
    leg_bot = max(6.0, bs - 3.0)
    deduct  = bend_reduce("shape_2", a_s)

    len_top = 2 * leg_top + body - deduct
    len_bot = 2 * leg_bot + body - deduct

    qty_per_dir  = math.floor(S_in / a_sp) + 2   # one plan direction
    qty_per_slab = 2 * qty_per_dir                # EF both plan directions (square in plan)

    log.step(
        f"JA bars ({a_s}@{a_sp}\"): body=S+2t-6={S_in:.0f}+{2*t}-6={body:.1f}\"  "
        f"deduct={deduct}\"  qty/dir=floor({S_in:.0f}/{a_sp})+2={qty_per_dir}  "
        f"qty/slab=2×{qty_per_dir}={qty_per_slab} (EF both plan directions)",
        source="JunctionRules",
    )
    log.step(
        f"JA1 top slab: leg={leg_top}\" → len={len_top:.1f}\"  "
        f"JA2 bot slab: leg={leg_bot}\" → len={len_bot:.1f}\"",
        source="JunctionRules",
    )
    log.result("JA1", f"{a_s} × {qty_per_slab} @ {fmt_inches(len_top)}", source="JunctionRules")
    log.result("JA2", f"{a_s} × {qty_per_slab} @ {fmt_inches(len_bot)}", source="JunctionRules")

    return [
        BarRow(
            mark="JA1", size=a_s, qty=qty_per_slab, length_in=len_top,
            shape="C",
            leg_a_in=leg_top, leg_b_in=leg_top, leg_c_in=body,
            notes=(
                f"Top slab 'a' bars @{a_sp}\" oc  EF both plan directions  "
                f"body={fmt_inches(body)}  leg={leg_top}\""
            ),
            source_rule="rule_junc_a_bars",
        ),
        BarRow(
            mark="JA2", size=a_s, qty=qty_per_slab, length_in=len_bot,
            shape="C",
            leg_a_in=leg_bot, leg_b_in=leg_bot, leg_c_in=body,
            notes=(
                f"Bottom slab 'a' bars @{a_sp}\" oc  EF both plan directions  "
                f"body={fmt_inches(body)}  leg={leg_bot}\""
            ),
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
    Hb_in = hb_ft * 12
    S_in  = span_ft * 12

    bar_len      = ts + Hb_in + bs - 6.0
    qty_per_wall = math.floor(S_in / e_sp) + 1
    qty_total    = 4 * qty_per_wall

    log.step(
        f"JE1 ({e_s}@{e_sp}\"): ts+Hb+bs-6={ts}+{Hb_in:.0f}+{bs}-6={bar_len:.1f}\"  "
        f"qty/wall=floor({S_in:.0f}/{e_sp})+1={qty_per_wall}  total=4×{qty_per_wall}={qty_total}",
        source="JunctionRules",
    )
    log.result("JE1", f"{e_s} × {qty_total} @ {fmt_inches(bar_len)}", source="JunctionRules")

    return [BarRow(
        mark="JE1", size=e_s, qty=qty_total, length_in=bar_len,
        shape="Str",
        notes=(
            f"Wall exterior 'e' bars @{e_sp}\" oc  "
            f"4 walls × {qty_per_wall}/wall  len=ts+Hb+bs-6={fmt_inches(bar_len)}"
        ),
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
    Hb_in = hb_ft * 12
    S_in  = span_ft * 12

    deduct       = bend_reduce("shape_2", b_s)
    bar_len      = Hb_in + 2 * B - deduct
    qty_per_wall = math.floor(S_in / b_sp) + 1
    qty_total    = 4 * qty_per_wall

    log.step(
        f"JB1 ({b_s}@{b_sp}\"): Hb+2B-deduct={Hb_in:.0f}+2×{B}-{deduct}={bar_len:.1f}\"  "
        f"qty/wall=floor({S_in:.0f}/{b_sp})+1={qty_per_wall}  total=4×{qty_per_wall}={qty_total}",
        source="JunctionRules",
    )
    log.result("JB1", f"{b_s} × {qty_total} @ {fmt_inches(bar_len)}", source="JunctionRules")

    return [BarRow(
        mark="JB1", size=b_s, qty=qty_total, length_in=bar_len,
        shape="U",
        leg_a_in=float(B), leg_b_in=Hb_in,
        notes=(
            f"Wall interior 'b' bars @{b_sp}\" oc  "
            f"4 walls × {qty_per_wall}/wall  "
            f"Hb+2B={fmt_inches(Hb_in)}+2×{B}\"  B={fmt_inches(B)}"
        ),
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
        notes=(
            f"Addl 'a' bars at pipe openings (Note 12)  "
            + "  |  ".join(pipe_details)
        ),
        source_rule="rule_junc_add_bars",
    )]


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
