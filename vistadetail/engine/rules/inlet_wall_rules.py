"""
Rule functions for G2 Inlet / G2 Expanded Inlet templates.

Every rule function has the signature:
    def rule_xxx(p: Params, log: ReasoningLogger) -> list[BarRow]

Rules are pure: they read from p, write to log, return BarRow list.
rule_g2_inlet_geometry is intentionally run first — it derives wall_thick_in,
wall_length_ft, and l1_in from the X/Y primary inputs, then the downstream
bar rules (rule_horizontal_bars_EF etc.) work normally via those derived attrs.
"""

from __future__ import annotations

import math

from vistadetail.engine.hooks import hook_add
from vistadetail.engine.reasoning_logger import ReasoningLogger
from vistadetail.engine.schema import BarRow, Params, fmt_inches

# ---------------------------------------------------------------------------
# Grate-type deductions (inches subtracted from interior width to get L1)
# ---------------------------------------------------------------------------
_GRATE_DEDUCTION: dict[str, float] = {
    "Type 24": 24.0,
    "Type 18": 18.0,
}

_MIN_INTERIOR_Y_IN: float = 35.375   # 2'-11 3/8" — Caltrans G2 minimum clear depth


# ---------------------------------------------------------------------------
# G2 INLET GEOMETRY  — derives T, interior dims, L1 from X/Y primary inputs
# ---------------------------------------------------------------------------

def rule_g2_inlet_geometry(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Derive wall thickness (T) and grate clear opening (L1) from the X/Y
    primary exterior dimensions.

    Auto wall thickness rule (Caltrans standard):
      X ≤ 54 in  →  T = 9 in
      X >  54 in  →  T = 11 in
    If wall_thick_in is provided (> 0) by the user, that value is used as-is.

    L1 = Interior_X − grate_deduction
      grate_deduction: Type 24 = 24 in, Type 18 = 18 in

    Sets derived attributes on p so downstream rules work unchanged:
      p.wall_thick_in  (possibly auto-computed)
      p.wall_length_ft = p.x_dim_ft  (alias used by EF bar rules)
    Also stores:
      p.l1_in          (grate opening, inches)
      p.interior_x_in
      p.interior_y_in
    """
    x_in = getattr(p, "x_dim_ft", 5.5) * 12.0
    y_in = getattr(p, "y_dim_ft", 4.5) * 12.0

    # ── Wall thickness ──────────────────────────────────────────────────
    t_in = float(getattr(p, "wall_thick_in", 0))
    if t_in <= 0:
        t_in = 9.0 if x_in <= 54.0 else 11.0
        setattr(p, "wall_thick_in", t_in)
        log.step(
            f"Auto wall thickness: X = {fmt_inches(x_in)} "
            f"({'≤' if x_in <= 54.0 else '>'} 54\")  →  T = {t_in:.0f}\""
        )
    else:
        log.step(f"User-specified wall thickness T = {t_in:.0f}\"")

    # ── Alias for bar-count rules ───────────────────────────────────────
    setattr(p, "wall_length_ft", getattr(p, "x_dim_ft", x_in / 12))

    # ── Interior dimensions ─────────────────────────────────────────────
    int_x_in = x_in - 2.0 * t_in
    int_y_in = y_in - 2.0 * t_in
    setattr(p, "interior_x_in", int_x_in)
    setattr(p, "interior_y_in", int_y_in)

    log.step(f"X = {fmt_inches(x_in)}  →  interior width  = {fmt_inches(x_in)} − 2×{t_in:.0f}\" = {fmt_inches(int_x_in)}")
    log.step(f"Y = {fmt_inches(y_in)}  →  interior depth  = {fmt_inches(y_in)} − 2×{t_in:.0f}\" = {fmt_inches(int_y_in)}")

    if int_y_in < _MIN_INTERIOR_Y_IN:
        log.warn(
            f"Interior depth {fmt_inches(int_y_in)} < Caltrans G2 minimum "
            f"{fmt_inches(_MIN_INTERIOR_Y_IN)} (2'-11 3/8\")"
        )

    # ── Grate opening L1 ────────────────────────────────────────────────
    grate_type = getattr(p, "grate_type", "Type 24")
    grate_ded  = _GRATE_DEDUCTION.get(str(grate_type), 24.0)
    l1_in      = max(0.0, int_x_in - grate_ded)
    setattr(p, "l1_in", l1_in)

    log.step(
        f"Grate: {grate_type}  (deduction = {grate_ded:.0f}\")  →  "
        f"L1 = {fmt_inches(int_x_in)} − {grate_ded:.0f}\" = {fmt_inches(l1_in)}"
    )

    # ── Pipe clearance check ────────────────────────────────────────────
    pipe_diam = float(getattr(p, "pipe_diam_in", 0.0))
    if pipe_diam > 0 and l1_in < pipe_diam + 3.0:
        log.warn(
            f"L1 = {fmt_inches(l1_in)} may be tight for "
            f"{pipe_diam:.0f}\" pipe + 3\" min clearance "
            f"(need ≥ {fmt_inches(pipe_diam + 3.0)})"
        )

    log.result(
        "GEOMETRY",
        f"X={fmt_inches(x_in)}, Y={fmt_inches(y_in)}, "
        f"T={t_in:.0f}\", Interior={fmt_inches(int_x_in)}×{fmt_inches(int_y_in)}, "
        f"L1={fmt_inches(l1_in)}"
    )
    return []


def _aci_max_spacing(wall_thick_in: float) -> float:
    """ACI 318-19 §24.3.2: max spacing for walls/slabs = min(3×thickness, 18 in)."""
    return min(3.0 * wall_thick_in, 18.0)


def _effective_spacing(requested: float, wall_thick_in: float,
                       label: str, log: ReasoningLogger) -> float:
    """
    Return the spacing to use — clamped to ACI max if user input exceeds it.
    Logs a note when auto-correction occurs.
    """
    aci_max = _aci_max_spacing(wall_thick_in)
    if requested > aci_max:
        log.step(
            f"{label} spacing {requested}\" exceeds ACI §24.3.2 max "
            f"{aci_max:.0f}\" for {wall_thick_in}\" wall — auto-adjusted to {aci_max:.0f}\""
        )
        return aci_max
    return requested


# ---------------------------------------------------------------------------
# HORIZONTAL BARS — each face
# ---------------------------------------------------------------------------

def rule_horizontal_bars_EF(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Horizontal bars, each face, full wall length with standard hooks.

    Quantity: floor((usable_height / spacing) + 1) bars per face × 2 faces.
    Length:   wall_length + 2 × hook_add_per_end.
    Spacing auto-adjusted to ACI 318-19 §24.3.2 max if user input exceeds it.
    """
    spacing = _effective_spacing(p.horiz_spacing_in, p.wall_thick_in, "Horiz", log)
    usable_h_in = (p.wall_height_ft * 12) - (2 * p.cover_in)
    qty_per_face = math.floor(usable_h_in / spacing) + 1
    qty_total = qty_per_face * 2   # each face

    hook_add_in = hook_add(p.hook_type, p.horiz_bar_size)
    bar_len_in = (p.wall_length_ft * 12) + (2 * hook_add_in)

    log.step(f"Wall height = {p.wall_height_ft} ft = {p.wall_height_ft * 12:.0f} in")
    log.step(f"Cover each face = {p.cover_in} in  →  usable height = {usable_h_in:.2f} in")
    log.step(
        f"Spacing = {spacing} in  "
        f"→  courses = ⌊{usable_h_in:.2f}/{spacing}⌋ + 1 = {qty_per_face} bars/face"
    )
    log.step(
        f"Hook add = {hook_add_in} in/end ({p.hook_type})  "
        f"→  length = {p.wall_length_ft * 12:.0f} + 2×{hook_add_in} = {bar_len_in:.2f} in "
        f"= {fmt_inches(bar_len_in)}"
    )
    log.result(
        "H1",
        f"{p.horiz_bar_size} × {qty_total} @ {fmt_inches(bar_len_in)} [EF]",
    )

    return [BarRow(
        mark="H1",
        size=p.horiz_bar_size,
        qty=qty_total,
        length_in=bar_len_in,
        shape="Str",
        notes="Horiz EF",
        source_rule="rule_horizontal_bars_EF",
    )]


# ---------------------------------------------------------------------------
# VERTICAL BARS — each face
# ---------------------------------------------------------------------------

def rule_vertical_bars_EF(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Vertical bars, each face, from bottom hook to top development.

    Quantity: floor((usable_length / spacing) + 1) bars per face × 2 faces.
    Length:   wall_height + bottom_hook + top_dev_stub.
    Top development stub = 6 in (standard); bottom hook = std_90 add.
    Spacing auto-adjusted to ACI 318-19 §24.3.2 max if user input exceeds it.
    """
    spacing = _effective_spacing(p.vert_spacing_in, p.wall_thick_in, "Vert", log)
    usable_l_in = (p.wall_length_ft * 12) - (2 * p.cover_in)
    qty_per_face = math.floor(usable_l_in / spacing) + 1
    qty_total = qty_per_face * 2

    bottom_hook_in = hook_add("std_90", p.vert_bar_size)   # always 90° at base
    top_stub_in = 6.0   # standard top development stub into cap/footing

    bar_len_in = (p.wall_height_ft * 12) + bottom_hook_in + top_stub_in

    log.step(f"Wall length = {p.wall_length_ft} ft = {p.wall_length_ft * 12:.0f} in")
    log.step(f"Cover each face = {p.cover_in} in  →  usable length = {usable_l_in:.2f} in")
    log.step(
        f"Spacing = {spacing} in  "
        f"→  columns = ⌊{usable_l_in:.2f}/{spacing}⌋ + 1 = {qty_per_face} bars/face"
    )
    log.step(
        f"Bar length = {p.wall_height_ft * 12:.0f} (height) + {bottom_hook_in} (base hook) "
        f"+ {top_stub_in} (top dev) = {bar_len_in:.2f} in = {fmt_inches(bar_len_in)}"
    )
    log.result(
        "V1",
        f"{p.vert_bar_size} × {qty_total} @ {fmt_inches(bar_len_in)} [EF]",
    )

    return [BarRow(
        mark="V1",
        size=p.vert_bar_size,
        qty=qty_total,
        length_in=bar_len_in,
        shape="Str",
        notes="Vert EF",
        source_rule="rule_vertical_bars_EF",
    )]


# ---------------------------------------------------------------------------
# CORNER L-BARS
# ---------------------------------------------------------------------------

def rule_corner_L_bars(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Corner L-bars at each vertical edge of the wall (2 corners × 2 faces = 4 legs).

    One L-bar per wall face at each corner.
    Leg A (horizontal): min(wall_length/6, 24 in), min 18 in.
    Leg B (vertical):   same as Leg A for symmetry.
    Qty: 4 (one per corner per face side).
    """
    if getattr(p, "corner_bars", "yes") != "yes":
        log.step("Corner bars: disabled by user input")
        return []

    leg_a_in = max(18.0, min((p.wall_length_ft * 12) / 6.0, 24.0))
    leg_b_in = leg_a_in   # symmetric L
    qty = 4

    log.step(f"Corner L-bar leg = max(18, min(length/6, 24)) = {leg_a_in:.1f} in")
    log.step(f"Qty: {qty} (2 corners × 2 faces)")
    log.result(
        "C1",
        f"{p.corner_bar_size} × {qty}  L-bar: {fmt_inches(leg_a_in)} × {fmt_inches(leg_b_in)}",
    )

    return [BarRow(
        mark="C1",
        size=p.corner_bar_size,
        qty=qty,
        length_in=leg_a_in + leg_b_in,   # total bar length (both legs)
        shape="L",
        leg_a_in=leg_a_in,
        leg_b_in=leg_b_in,
        notes="Corner EF",
        source_rule="rule_corner_L_bars",
    )]


# ---------------------------------------------------------------------------
# VALIDATION rules — produce no bars but write warnings
# ---------------------------------------------------------------------------

def rule_validate_min_cover(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Flag if clear cover is below ACI 318-19 minimum for the inferred exposure.
    Soil-contact elements require ≥ 3 in (ACI Table 20.6.1.3.1).
    """
    if p.cover_in < 1.5:
        log.warn(
            f"Cover {p.cover_in} in < 1.5 in absolute minimum (ACI 318-19 §20.6.1.3)."
        )
    if p.cover_in < 2.0:
        log.warn(
            f"Cover {p.cover_in} in may be insufficient for soil-contact exposure. "
            "ACI 318-19 Table 20.6.1.3.1 requires 3 in cast-against-soil."
        )
    return []


def rule_validate_max_spacing_ACI(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Flag if bar spacing exceeds ACI 318-19 Section 24.3.2 maximum.
    Max spacing = min(3×slab_thickness, 18 in) for wall/slab.
    """
    t_in = p.wall_thick_in
    max_sp = min(3 * t_in, 18.0)

    if p.horiz_spacing_in > max_sp:
        log.warn(
            f"Horiz spacing {p.horiz_spacing_in} in > ACI max {max_sp} in "
            f"(= min(3×{t_in}, 18)) per §24.3.2"
        )
    if p.vert_spacing_in > max_sp:
        log.warn(
            f"Vert spacing {p.vert_spacing_in} in > ACI max {max_sp} in "
            f"(= min(3×{t_in}, 18)) per §24.3.2"
        )
    return []


# ═══════════════════════════════════════════════════════════════════════════════
# G2 INLET — Vista Excel-matched rules
#
# These rules reproduce the exact formulas from the Vista Steel G2 Inlet
# spreadsheet ("G2 inlet 9in walls.xlsx").  The old rule_horizontal_bars_EF /
# rule_vertical_bars_EF / rule_corner_L_bars are kept above for the Expanded
# Inlet template which still references them.
# ═══════════════════════════════════════════════════════════════════════════════

def rule_g2_geometry(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """Derive all G2 inlet dimensions matching the Vista Excel spreadsheet.

    Inputs expected on p:
      x_dim_ft     — exterior width  (ft)
      y_dim_ft     — exterior depth  (ft)
      wall_height_ft — wall height   (ft)
      wall_thick_in  — 0 = auto
      grate_type     — "Type 24" / "Type 18"
      num_structures — multiplier (default 1)
    """
    x_ext = p.x_dim_ft * 12.0
    y_ext = p.y_dim_ft * 12.0

    # ── Wall thickness auto-derive ──────────────────────────────────────
    t = float(getattr(p, "wall_thick_in", 0))
    if t <= 0:
        # Caltrans rule: interior X ≤ 54 → T=9, else T=11
        # Use tentative T=9 to compute trial interior X
        trial_inside = x_ext - 2 * 9.0
        t = 9.0 if trial_inside <= 54.0 else 11.0
        setattr(p, "wall_thick_in", t)
        log.step(f"Auto T: trial interior X = {fmt_inches(trial_inside)} → T = {t:.0f}\"")
    else:
        log.step(f"User T = {t:.0f}\"")

    x_inside = x_ext - 2 * t
    y_inside = y_ext - 2 * t
    n = int(getattr(p, "num_structures", 1)) or 1

    grate_type = str(getattr(p, "grate_type", "Type 24"))
    grate_ded = _GRATE_DEDUCTION.get(grate_type, 24.0)

    # ── Height adjustment (Excel adds 4" for development) ──────────────
    h_in = p.wall_height_ft * 12.0
    h_adj = h_in + 4.0

    # ── Bar lengths (clearance = 6" = 3" cover each end) ──────────────
    y_bar = y_ext - 6.0   # horizontal bar spanning Y direction
    x_bar = x_ext - 6.0   # horizontal bar spanning X direction

    # ── Gut dimension (Excel: X_inside + T - grate_ded - 5) ──────────
    gut_dim = x_inside + t - (grate_ded + 5.0)

    # ── A & B bar length (clearance = 4.5") ───────────────────────────
    ab_bar_len = x_ext - 4.5

    # ── Store derived values on params for downstream rules ───────────
    setattr(p, "x_ext_in", x_ext)
    setattr(p, "y_ext_in", y_ext)
    setattr(p, "x_inside_in", x_inside)
    setattr(p, "y_inside_in", y_inside)
    setattr(p, "h_adj", h_adj)
    setattr(p, "y_bar", y_bar)
    setattr(p, "x_bar", x_bar)
    setattr(p, "gut_dim", gut_dim)
    setattr(p, "ab_bar_len", ab_bar_len)
    setattr(p, "grate_ded", grate_ded)
    setattr(p, "n_struct", n)

    # ── Validation ────────────────────────────────────────────────────
    if y_inside < _MIN_INTERIOR_Y_IN:
        log.warn(
            f"Interior Y = {fmt_inches(y_inside)} < Caltrans minimum "
            f"{fmt_inches(_MIN_INTERIOR_Y_IN)} (2'-11 3/8\")"
        )
    if gut_dim <= 0:
        log.warn(f"Gut dimension = {fmt_inches(gut_dim)} ≤ 0 — check X dimension vs grate type")

    log.result("GEOMETRY",
        f"X={fmt_inches(x_ext)} (int {fmt_inches(x_inside)}), "
        f"Y={fmt_inches(y_ext)} (int {fmt_inches(y_inside)}), "
        f"T={t:.0f}\", H_adj={fmt_inches(h_adj)}, "
        f"Y_bar={fmt_inches(y_bar)}, X_bar={fmt_inches(x_bar)}, "
        f"Gut={fmt_inches(gut_dim)}")
    return []


def rule_g2_bottom_mat(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """Bottom mat: BM1 (Y-direction bars spaced across X), BM2 (X-direction)."""
    spacing = 5.0
    n = p.n_struct
    qty_bm1 = math.ceil(p.x_bar / spacing * n)
    qty_bm2 = math.ceil(p.y_bar / spacing * n)

    log.step(f"BM1: CEIL({fmt_inches(p.x_bar)}/{spacing}×{n}) = {qty_bm1} pcs, length {fmt_inches(p.y_bar)}")
    log.step(f"BM2: CEIL({fmt_inches(p.y_bar)}/{spacing}×{n}) = {qty_bm2} pcs, length {fmt_inches(p.x_bar)}")

    return [
        BarRow(mark="BM1", size="#5", qty=qty_bm1, length_in=p.y_bar,
               shape="Str", notes="Y Bottom Mat @5oc",
               source_rule="rule_g2_bottom_mat"),
        BarRow(mark="BM2", size="#5", qty=qty_bm2, length_in=p.x_bar,
               shape="Str", notes="X Bottom Mat @5oc",
               source_rule="rule_g2_bottom_mat"),
    ]


def rule_g2_horizontals(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """Horizontal wall bars — two zones per Excel:
    Top 2 ft:  #6 @ 4" oc (24/4 = 6 bars per wall-pair, ×2 = 12)
    Below 2 ft: #5 @ 5" oc
    """
    n = p.n_struct
    top_zone = 24.0      # 2 ft in inches
    top_spacing = 4.0
    below_spacing = 5.0

    qty_top = math.ceil(top_zone / top_spacing) * 2   # 6 × 2 walls = 12
    qty_below = math.ceil((p.h_adj - top_zone) / below_spacing + 2 * n)

    log.step(f"H1/H2 top 2ft: 24/{top_spacing}×2 = {qty_top} pcs, #6")
    log.step(f"H3/H4 below: CEIL(({fmt_inches(p.h_adj)}-24)/{below_spacing}+2×{n}) = {qty_below} pcs, #5")

    return [
        BarRow(mark="H1", size="#6", qty=qty_top, length_in=p.y_bar,
               shape="Str", notes="Y Horz Top 2ft @4oc",
               source_rule="rule_g2_horizontals"),
        BarRow(mark="H2", size="#6", qty=qty_top, length_in=p.x_bar,
               shape="Str", notes="X Horz Top 2ft @4oc",
               source_rule="rule_g2_horizontals"),
        BarRow(mark="H3", size="#5", qty=qty_below, length_in=p.y_bar,
               shape="Str", notes="Y Horz Below 2ft @5oc",
               source_rule="rule_g2_horizontals"),
        BarRow(mark="H4", size="#5", qty=qty_below, length_in=p.x_bar,
               shape="Str", notes="X Horz Below 2ft @5oc",
               source_rule="rule_g2_horizontals"),
    ]


def rule_g2_verticals(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """Vertical bars — non-grate walls + grate-side wall.

    Excel formulas (Type 24 grate):
      V1: CEIL((X_bar×2 − 2×grate_ded + Y_bar + 6) / 5)
      V2: CEIL((Y_bar + 2×grate_ded + 4) / 5)
    """
    spacing = 5.0
    gd2 = 2 * p.grate_ded   # 48 for Type 24, 36 for Type 18

    qty_v1 = math.ceil((p.x_bar * 2 - gd2 + p.y_bar + 6) / spacing)
    qty_v2 = math.ceil((p.y_bar + gd2 + 4) / spacing)

    log.step(f"V1: CEIL(({fmt_inches(p.x_bar)}×2 − {gd2:.0f} + {fmt_inches(p.y_bar)} + 6)/{spacing}) = {qty_v1}")
    log.step(f"V2: CEIL(({fmt_inches(p.y_bar)} + {gd2:.0f} + 4)/{spacing}) = {qty_v2}")

    return [
        BarRow(mark="V1", size="#5", qty=qty_v1, length_in=p.h_adj,
               shape="Str", notes="Verticals @5oc",
               source_rule="rule_g2_verticals"),
        BarRow(mark="V2", size="#5", qty=qty_v2, length_in=p.h_adj,
               shape="Str", notes="Verticals Grate Side @5oc",
               source_rule="rule_g2_verticals"),
    ]


def rule_g2_ab_bars(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """A and B bars (deck-level reinforcement at gut opening)."""
    if p.gut_dim <= 0:
        log.step("A/B bars: skipped (gut_dim ≤ 0)")
        return []

    qty_a = math.ceil(p.gut_dim / 5.0)
    qty_b = math.ceil(p.gut_dim / 6.0)

    log.step(f"A1: CEIL({fmt_inches(p.gut_dim)}/5) = {qty_a}, #5, length {fmt_inches(p.ab_bar_len)}")
    log.step(f"B1: CEIL({fmt_inches(p.gut_dim)}/6) = {qty_b}, #4, length {fmt_inches(p.ab_bar_len)}")

    return [
        BarRow(mark="A1", size="#5", qty=qty_a, length_in=p.ab_bar_len,
               shape="Str", notes="A Bars @5oc",
               source_rule="rule_g2_ab_bars"),
        BarRow(mark="B1", size="#4", qty=qty_b, length_in=p.ab_bar_len,
               shape="Str", notes="B Bars @6oc",
               source_rule="rule_g2_ab_bars"),
    ]


def rule_g2_right_angle(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """Outside right-angle L-bars at deck/wall junction.

    Deck leg = gut_dim, Vertical leg = 1.5 × gut_dim.
    Qty spaced along Y exterior at 6" oc.
    """
    if p.gut_dim <= 0:
        log.step("Right angle bars: skipped (gut_dim ≤ 0)")
        return []

    deck_leg = p.gut_dim
    vert_leg = round(deck_leg * 1.5, 2)
    qty = math.ceil(p.y_ext_in / 6.0 * p.n_struct)

    log.step(f"RA1: deck={fmt_inches(deck_leg)}, vert={fmt_inches(vert_leg)}, "
             f"qty=CEIL({fmt_inches(p.y_ext_in)}/6×{p.n_struct})={qty}")

    return [BarRow(
        mark="RA1", size="#5", qty=qty,
        length_in=deck_leg + vert_leg,
        shape="L", leg_a_in=deck_leg, leg_b_in=vert_leg,
        notes="Outside Right Angle @6oc",
        source_rule="rule_g2_right_angle",
    )]


def rule_g2_hoops(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """Hoops at grate level — spaced along Y exterior at 5" oc."""
    if p.gut_dim <= 0:
        log.step("Hoops: skipped (gut_dim ≤ 0)")
        return []

    qty = math.ceil(p.y_ext_in / 5.0 * p.n_struct)

    log.step(f"HP1: qty=CEIL({fmt_inches(p.y_ext_in)}/5×{p.n_struct})={qty}, "
             f"gut dim={fmt_inches(p.gut_dim)}")

    return [BarRow(
        mark="HP1", size="#5", qty=qty,
        length_in=p.gut_dim,
        shape="Rect", notes="Hoops @5oc",
        source_rule="rule_g2_hoops",
    )]
