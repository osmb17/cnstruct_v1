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

_MIN_INTERIOR_Y_IN: float = 36.0   # 3'-0" — Caltrans G2 standard interior Y (fixed)


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
            f"{fmt_inches(_MIN_INTERIOR_Y_IN)} (3'-0\")"
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
        shape="U", leg_a_in=hook_add_in, leg_b_in=p.wall_length_ft * 12, leg_c_in=hook_add_in,
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
        shape="L", leg_a_in=p.wall_height_ft * 12 + top_stub_in, leg_b_in=bottom_hook_in,
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

    Geometry rules (Caltrans D73A):
      - Y interior is ALWAYS fixed at 3'-0" (36.0") for standard G2.
        Y exterior = Y_interior + 2 × T.
      - X interior = X_exterior − 2 × T.
      - T (wall_thick_in) is always explicitly provided by the user.

    Inputs expected on p:
      x_dim_ft       — exterior width  (ft)
      wall_height_ft — wall height     (ft)
      wall_thick_in  — wall thickness  (in), must be > 0
      grate_type     — "Type 24" / "Type 18"
      num_structures — multiplier (default 1)
    """
    x_ext = p.x_dim_ft * 12.0
    t = float(getattr(p, "wall_thick_in", 9.0))
    if t <= 0:
        t = 9.0

    # ── X: interior derived from exterior and T ─────────────────────────
    x_inside = x_ext - 2.0 * t

    # ── Y: interior is FIXED per Caltrans D73A ──────────────────────────
    y_inside = _MIN_INTERIOR_Y_IN   # always 35.375" = 2'-11 3/8"
    y_ext = y_inside + 2.0 * t

    log.step(f"T = {t:.0f}\"  (user input)")
    log.step(f"X exterior = {fmt_inches(x_ext)}  →  X interior = {fmt_inches(x_ext)} − 2×{t:.0f}\" = {fmt_inches(x_inside)}")
    log.step(f"Y interior = {fmt_inches(y_inside)} (fixed 3'-0\", Caltrans D73A)  →  Y exterior = {fmt_inches(y_inside)} + 2×{t:.0f}\" = {fmt_inches(y_ext)}")

    n = int(getattr(p, "num_structures", 1)) or 1

    grate_type = str(getattr(p, "grate_type", "Type 24"))
    grate_ded = _GRATE_DEDUCTION.get(grate_type, 24.0)

    # ── Height adjustment (Excel adds 5" for development) ──────────────
    h_in = p.wall_height_ft * 12.0
    h_adj = h_in + 5.0

    # ── Bar lengths (clearance = 6" = 3" cover each end) ──────────────
    y_bar = y_ext - 6.0   # horizontal bar spanning Y direction
    x_bar = x_ext - 6.0   # horizontal bar spanning X direction

    # ── Gut dimension (Excel: X_inside + T - grate_ded - 5) ──────────
    gut_dim = x_inside + t - (grate_ded + 5.0)

    # ── A & B bar length: U-bars span Y direction, total = y_ext - 4.5 + 2×tail ──
    ab_bar_len = y_ext - 4.5 + 2.0 * _AB_TAIL_IN   # = y_ext + 11.5"

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
    if x_inside <= 0:
        log.warn(f"Interior X = {fmt_inches(x_inside)} ≤ 0 — X exterior too small for T={t:.0f}\"")
    if gut_dim <= 0:
        log.warn(f"Gut dimension = {fmt_inches(gut_dim)} ≤ 0 — check X dimension vs grate type")
    if 0 < gut_dim < 8.0:
        log.warn(f"Gut dimension = {fmt_inches(gut_dim)} < 8\" — tight grate opening, verify bar spacing")

    log.result("GEOMETRY",
        f"X={fmt_inches(x_ext)} (int {fmt_inches(x_inside)}), "
        f"Y={fmt_inches(y_ext)} (int {fmt_inches(y_inside)} fixed), "
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

    Each horizontal has a 12" (1 ft) hook at each end.
    """
    n = p.n_struct
    top_zone = 24.0      # 2 ft in inches
    top_spacing = 4.0
    below_spacing = 5.0
    hook_in = 12.0       # 1 ft hook each end

    qty_top = math.ceil(top_zone / top_spacing) * 2   # 6 × 2 walls = 12
    # Below zone: two wall faces, 5" oc, 14" base offset
    qty_below = math.ceil((p.wall_height_ft * 12.0 - 14.0) / below_spacing) * 2 * n

    # Bar length = straight span + 2 hooks
    h1_len = p.y_bar + 2 * hook_in
    h2_len = p.x_bar + 2 * hook_in
    h3_len = p.y_bar + 2 * hook_in
    h4_len = p.x_bar + 2 * hook_in

    log.step(f"H1/H2 top 2ft: 24/{top_spacing}×2 = {qty_top} pcs, #6, 12\" hook EE")
    log.step(f"H3/H4 below: CEIL((H×12−14)/{below_spacing})×2×{n} = "
             f"CEIL(({p.wall_height_ft * 12.0:.0f}−14)/{below_spacing})×2×{n} = {qty_below} pcs, #5, 12\" hook EE")

    return [
        BarRow(mark="H1", size="#6", qty=qty_top, length_in=h1_len,
               shape="U", leg_a_in=hook_in, leg_b_in=p.y_bar, leg_c_in=hook_in,
               notes="Y Horz Top 2ft @4oc, 1ft hook EE",
               source_rule="rule_g2_horizontals"),
        BarRow(mark="H2", size="#6", qty=qty_top, length_in=h2_len,
               shape="U", leg_a_in=hook_in, leg_b_in=p.x_bar, leg_c_in=hook_in,
               notes="X Horz Top 2ft @4oc, 1ft hook EE",
               source_rule="rule_g2_horizontals"),
        BarRow(mark="H3", size="#5", qty=qty_below, length_in=h3_len,
               shape="U", leg_a_in=hook_in, leg_b_in=p.y_bar, leg_c_in=hook_in,
               notes="Y Horz Below 2ft @5oc, 1ft hook EE",
               source_rule="rule_g2_horizontals"),
        BarRow(mark="H4", size="#5", qty=qty_below, length_in=h4_len,
               shape="U", leg_a_in=hook_in, leg_b_in=p.x_bar, leg_c_in=hook_in,
               notes="X Horz Below 2ft @5oc, 1ft hook EE",
               source_rule="rule_g2_horizontals"),
    ]


def rule_g2_verticals(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """Vertical bars — non-grate walls + grate-side wall.

    Excel formulas (Type 24 grate):
      V1: CEIL((X_bar×2 − 2×grate_ded + Y_bar + 6) / 5)
      V2: CEIL((Y_bar + 2×grate_ded + 4) / 5)

    V1 gets a 12" (1 ft) L-bend at the top: after the first pour the bar is
    bent horizontally to support the hoops and top deck.  Total = h_adj + 12".
    V2 (grate side) is a straight bar — no top extension.  Total = h_adj.
    """
    spacing = 5.0
    gd2 = 2 * p.grate_ded   # 48 for Type 24, 36 for Type 18
    v1_ext = 12.0            # 1 ft top extension on V1 for bending over hoops

    qty_v1 = math.ceil((p.x_bar * 2 - gd2 + p.y_bar + 6) / spacing)
    qty_v2 = math.ceil((p.y_bar + gd2 + 4) / spacing)

    # V1 is shape_1 (L-bar) #5: apply 2.0" bend deduction per Vista bend chart
    v1_len = p.h_adj + v1_ext - 2.0
    v2_len = p.h_adj

    log.step(f"V1: CEIL(({fmt_inches(p.x_bar)}×2 − {gd2:.0f} + {fmt_inches(p.y_bar)} + 6)/{spacing}) = {qty_v1}, "
             f"len={fmt_inches(v1_len)} (h_adj + 12\" top bend − 2\" shape_1 deduct)")
    log.step(f"V2: CEIL(({fmt_inches(p.y_bar)} + {gd2:.0f} + 4)/{spacing}) = {qty_v2}, "
             f"len={fmt_inches(v2_len)} (h_adj, straight)")

    return [
        BarRow(mark="V1", size="#5", qty=qty_v1, length_in=v1_len,
               shape="L", leg_a_in=p.h_adj, leg_b_in=v1_ext - 2.0,
               notes="Verticals @5oc, 1ft top bend for hoops",
               source_rule="rule_g2_verticals"),
        BarRow(mark="V2", size="#5", qty=qty_v2, length_in=v2_len,
               shape="Str",
               notes="Verticals Grate Side @5oc",
               source_rule="rule_g2_verticals"),
    ]


_AB_TAIL_IN = 8.0   # A and B bars are U-bars with 8" tails on each side


def rule_g2_ab_bars(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """A and B bars — U-bars with 8\" tails on each side over the gut opening."""
    if p.gut_dim <= 0:
        log.step("A/B bars: skipped (gut_dim ≤ 0)")
        return []

    qty_a = math.ceil(p.gut_dim / 5.0)
    qty_b = math.ceil(p.gut_dim / 6.0)

    # Total bar = 8" tail + span + 8" tail; span = ab_bar_len - 2 × 8"
    a_span = max(0.0, p.ab_bar_len - 2 * _AB_TAIL_IN)

    log.step(f"A1: CEIL({fmt_inches(p.gut_dim)}/5) = {qty_a}, #5, "
             f"total {fmt_inches(p.ab_bar_len)} (8\" U-tails, span {fmt_inches(a_span)})")
    log.step(f"B1: CEIL({fmt_inches(p.gut_dim)}/6) = {qty_b}, #5, "
             f"total {fmt_inches(p.ab_bar_len)} (8\" U-tails, span {fmt_inches(a_span)})")

    return [
        BarRow(mark="A1", size="#5", qty=qty_a, length_in=p.ab_bar_len,
               shape="U", leg_a_in=_AB_TAIL_IN, leg_b_in=a_span, leg_c_in=_AB_TAIL_IN,
               notes="A Bars @5oc, 8\" U-tails",
               source_rule="rule_g2_ab_bars"),
        BarRow(mark="B1", size="#5", qty=qty_b, length_in=p.ab_bar_len,
               shape="U", leg_a_in=_AB_TAIL_IN, leg_b_in=a_span, leg_c_in=_AB_TAIL_IN,
               notes="B Bars @6oc, 8\" U-tails",
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
    qty = (math.floor(p.y_ext_in / 6.0) + 1) * p.n_struct

    log.step(f"RA1: deck={fmt_inches(deck_leg)}, vert={fmt_inches(vert_leg)}, "
             f"qty=(FLOOR({fmt_inches(p.y_ext_in)}/6)+1)×{p.n_struct}={qty}")

    return [BarRow(
        mark="RA1", size="#5", qty=qty,
        length_in=deck_leg + vert_leg,
        shape="L", leg_a_in=deck_leg, leg_b_in=vert_leg,
        notes="Outside Right Angle @6oc",
        source_rule="rule_g2_right_angle",
    )]


_HP_TAIL_PLAIN = 6.5   # C: plain tail (bottom span of S6)
_HP_TAIL_HOOK  = 5.5   # A and G: hook tails (top extensions of S6)
_HP_BAR_SIZE   = "#5"


def _s6_total(gut: float) -> float:
    """Total developed (stock) length for an S6 hoop.

    S6 bar path: A(tail) → down B(gut) → across C(6.5\") → up D(gut) → G(tail)
    Sum of legs = A + B + C + D + G = 5.5 + gut + 6.5 + gut + 5.5 = 2×gut + 17.5
    Minus shape_4 bend deduction for #5 bar = 6.0\" (4 bends).
    Stock length = 2×gut + 11.5\"
    """
    from vistadetail.engine.hooks import bend_reduce
    legs_sum = _HP_TAIL_HOOK + gut + _HP_TAIL_PLAIN + gut + _HP_TAIL_HOOK
    return legs_sum - bend_reduce("shape_4", _HP_BAR_SIZE)


def rule_g2_hoops(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """Hoops at grate level — S6 bend type spanning gut_dim.

    Bend chart S6 (from Vista scan_20260131.pdf):
      A = 5.5\"  (hook tail, top-left)
      B = gut    (left side height, variable)
      C = 6.5\"  (bottom span)
      D = gut    (right side height, variable)
      G = 5.5\"  (hook tail, top-right)
    Stock = A+B+C+D+G − bend_reduce(shape_4,#5) = 2×gut + 11.5\"
    """
    if p.gut_dim <= 0:
        log.step("Hoops: skipped (gut_dim ≤ 0)")
        return []

    qty = math.ceil(p.y_bar / 5.0 * p.n_struct)
    hp_total = _s6_total(p.gut_dim)

    log.step(f"HP1: qty=CEIL({fmt_inches(p.y_bar)}/5×{p.n_struct})={qty}, "
             f"gut={fmt_inches(p.gut_dim)}, S6 stock=2×gut+11.5\"={fmt_inches(hp_total)}")

    return [BarRow(
        mark="HP1", size="#5", qty=qty,
        length_in=hp_total,
        shape="Hoop",
        leg_a_in=_HP_TAIL_HOOK,    # A = 5.5"
        leg_b_in=p.gut_dim,        # B = gut span (variable)
        leg_c_in=_HP_TAIL_PLAIN,   # C = 6.5"
        leg_d_in=p.gut_dim,        # D = gut span (variable)
        leg_g_in=_HP_TAIL_HOOK,    # G = 5.5"
        notes="Hoops @5oc, S6 bend",
        source_rule="rule_g2_hoops",
    )]


# ═══════════════════════════════════════════════════════════════════════════════
# G2 EXPANDED INLET — Vista Excel-matched rules
#
# Reproduces "expanded G2 inlet 9in walls.xlsx".
# Shares rule_g2_bottom_mat, rule_g2_horizontals, rule_g2_right_angle with
# the standard G2 Inlet.  Has different vertical formula and adds notched
# A&B bar and hoop variants for the expansion room.
# ═══════════════════════════════════════════════════════════════════════════════

def rule_g2exp_geometry(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """Derive expanded G2 inlet geometry.

    Y dimensions are user input (default: 5'-0" main, 8'-0" expanded per Caltrans D73A).
    Wall thickness T comes from explicit user input wall_thick_in.
    """
    x_ext = p.x_dim_ft * 12.0

    # Wall thickness — explicit user input
    t = float(p.wall_thick_in)
    log.step(f"T = {t:.0f}\"")

    # Y dimensions — user input (defaults to standard values)
    y_ext     = getattr(p, "y_dim_ft", 5.0) * 12.0       # main box exterior Y
    y_exp_ext = getattr(p, "y_expanded_ft", 8.0) * 12.0  # expanded section exterior Y
    log.step(f"Y main = {y_ext / 12.0:.2f}' ({y_ext:.0f}\")  Y expanded = {y_exp_ext / 12.0:.2f}' ({y_exp_ext:.0f}\")")

    x_inside = x_ext - 2 * t
    y_inside = y_ext - 2 * t
    y_exp_inside = y_exp_ext - 2 * t
    n = int(getattr(p, "num_structures", 1)) or 1

    grate_type = str(getattr(p, "grate_type", "Type 24"))
    grate_ded = _GRATE_DEDUCTION.get(grate_type, 24.0)

    h_adj = p.wall_height_ft * 12.0 + 4.0
    y_bar = y_ext - 6.0
    x_bar = x_ext - 6.0

    # ── Gut / notch dimensions (Excel formulas) ──────────────────────────
    gut_dim = x_inside + t - (grate_ded + 5.0)       # =F4+F5-29
    notch_dim = y_exp_ext / 2.0 - 23.0               # =(F3+2*F5)/2-23

    ab_bar_len_reg = x_ext - 4.5                      # =F4+2*F5-4.5
    ab_bar_len_notch = y_exp_ext - 4.5                # =F3+2*F5-4.5

    # ── Store on p ────────────────────────────────────────────────────────
    setattr(p, "x_ext_in", x_ext)
    setattr(p, "y_ext_in", y_ext)           # main box Y exterior
    setattr(p, "y_exp_ext_in", y_exp_ext)   # expanded Y exterior
    setattr(p, "x_inside_in", x_inside)
    setattr(p, "y_inside_in", y_inside)
    setattr(p, "y_exp_inside_in", y_exp_inside)
    setattr(p, "h_adj", h_adj)
    setattr(p, "y_bar", y_bar)
    setattr(p, "x_bar", x_bar)
    setattr(p, "gut_dim", gut_dim)
    setattr(p, "notch_dim", notch_dim)
    setattr(p, "ab_bar_len", ab_bar_len_reg)   # for reuse by shared rules
    setattr(p, "ab_bar_len_reg", ab_bar_len_reg)
    setattr(p, "ab_bar_len_notch", ab_bar_len_notch)
    setattr(p, "grate_ded", grate_ded)
    setattr(p, "n_struct", n)
    setattr(p, "t_in", t)

    if gut_dim <= 0:
        log.warn(f"Gut dimension = {fmt_inches(gut_dim)} <= 0")
    if 0 < gut_dim < 8.0:
        log.warn(f"Gut dimension = {fmt_inches(gut_dim)} < 8\" — tight grate opening, verify bar spacing")
    if notch_dim <= 0:
        log.warn(f"Notch dimension = {fmt_inches(notch_dim)} <= 0")
    if 0 < notch_dim < 8.0:
        log.warn(f"Notch dimension = {fmt_inches(notch_dim)} < 8\" — tight opening, verify bar spacing")

    log.result("GEOMETRY",
        f"X={fmt_inches(x_ext)} (int {fmt_inches(x_inside)}), "
        f"Y={fmt_inches(y_ext)} (int {fmt_inches(y_inside)}), "
        f"Y_exp={fmt_inches(y_exp_ext)} (int {fmt_inches(y_exp_inside)}), "
        f"T={t:.0f}\", H_adj={fmt_inches(h_adj)}, "
        f"Gut={fmt_inches(gut_dim)}, Notch={fmt_inches(notch_dim)}")
    return []


def rule_g2exp_verticals(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """Expanded G2 verticals -- uses T-based formula (not grate_ded).

    Excel formulas:
      V1: ROUNDUP((X_bar*2 + Y_bar + 6*T) / 5, 0)
      V2: ROUNDUP((Y_bar + 2*T) / 5, 0)

    V1 gets a 12" (1 ft) L-bend at the top: after the first pour the bar is
    bent horizontally to support the hoops and top deck.  Total = h_adj + 12".
    V2 (grate side) is a straight bar.  Total = h_adj.
    """
    t = p.t_in
    v1_ext = 12.0   # 1 ft top extension on V1 for bending over hoops

    qty_v1 = math.ceil((p.x_bar * 2 + p.y_bar + 6 * t) / 5.0)
    qty_v2 = math.ceil((p.y_bar + 2 * t) / 5.0)

    log.step(f"V1: CEIL(({fmt_inches(p.x_bar)}*2 + {fmt_inches(p.y_bar)} + 6*{t:.0f})/ 5) = {qty_v1}, "
             f"len={fmt_inches(p.h_adj + v1_ext)} (h_adj + 12\" top bend)")
    log.step(f"V2: CEIL(({fmt_inches(p.y_bar)} + 2*{t:.0f})/5) = {qty_v2}, "
             f"len={fmt_inches(p.h_adj)} (h_adj, straight)")

    return [
        BarRow(mark="V1", size="#5", qty=qty_v1, length_in=p.h_adj + v1_ext,
               shape="L", leg_a_in=p.h_adj, leg_b_in=v1_ext,
               notes="Verticals @5oc, 1ft top bend for hoops",
               source_rule="rule_g2exp_verticals"),
        BarRow(mark="V2", size="#5", qty=qty_v2, length_in=p.h_adj,
               shape="Str", notes="Verticals Grate Side @5oc",
               source_rule="rule_g2exp_verticals"),
    ]


def rule_g2exp_ab_bars(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """Expanded G2 A&B bars — U-bars with 8\" tails, regular + notched variants.

    Regular bars span X (over grate), notched bars span expanded Y.
    """
    bars: list[BarRow] = []

    if p.gut_dim > 0:
        qty_a_reg = math.ceil(p.gut_dim / 5.0)
        qty_b_reg = math.ceil(p.gut_dim / 6.0)
        span_reg = max(0.0, p.ab_bar_len_reg - 2 * _AB_TAIL_IN)
        log.step(f"A1 reg: CEIL({fmt_inches(p.gut_dim)}/5) = {qty_a_reg}, "
                 f"total {fmt_inches(p.ab_bar_len_reg)} (8\" U-tails, span {fmt_inches(span_reg)})")
        log.step(f"B1 reg: CEIL({fmt_inches(p.gut_dim)}/6) = {qty_b_reg}, "
                 f"total {fmt_inches(p.ab_bar_len_reg)} (8\" U-tails, span {fmt_inches(span_reg)})")
        bars += [
            BarRow(mark="A1", size="#5", qty=qty_a_reg, length_in=p.ab_bar_len_reg,
                   shape="U", leg_a_in=_AB_TAIL_IN, leg_b_in=span_reg, leg_c_in=_AB_TAIL_IN,
                   notes="A Bars Reg @5oc, 8\" U-tails",
                   source_rule="rule_g2exp_ab_bars"),
            BarRow(mark="B1", size="#4", qty=qty_b_reg, length_in=p.ab_bar_len_reg,
                   shape="U", leg_a_in=_AB_TAIL_IN, leg_b_in=span_reg, leg_c_in=_AB_TAIL_IN,
                   notes="B Bars Reg @6oc, 8\" U-tails",
                   source_rule="rule_g2exp_ab_bars"),
        ]
    else:
        log.step("A/B bars (reg): skipped (gut_dim <= 0)")

    if p.notch_dim > 0:
        qty_a_notch = math.ceil(p.notch_dim / 5.0)
        qty_b_notch = math.ceil(p.notch_dim / 6.0)
        span_notch = max(0.0, p.ab_bar_len_notch - 2 * _AB_TAIL_IN)
        log.step(f"A2 notch: CEIL({fmt_inches(p.notch_dim)}/5) = {qty_a_notch}, "
                 f"total {fmt_inches(p.ab_bar_len_notch)} (8\" U-tails, span {fmt_inches(span_notch)})")
        log.step(f"B2 notch: CEIL({fmt_inches(p.notch_dim)}/6) = {qty_b_notch}, "
                 f"total {fmt_inches(p.ab_bar_len_notch)} (8\" U-tails, span {fmt_inches(span_notch)})")
        bars += [
            BarRow(mark="A2", size="#5", qty=qty_a_notch, length_in=p.ab_bar_len_notch,
                   shape="U", leg_a_in=_AB_TAIL_IN, leg_b_in=span_notch, leg_c_in=_AB_TAIL_IN,
                   notes="A Bars Notched @5oc, 8\" U-tails",
                   source_rule="rule_g2exp_ab_bars"),
            BarRow(mark="B2", size="#4", qty=qty_b_notch, length_in=p.ab_bar_len_notch,
                   shape="U", leg_a_in=_AB_TAIL_IN, leg_b_in=span_notch, leg_c_in=_AB_TAIL_IN,
                   notes="B Bars Notched @6oc, 8\" U-tails",
                   source_rule="rule_g2exp_ab_bars"),
        ]
    else:
        log.step("A/B bars (notch): skipped (notch_dim <= 0)")

    return bars


def rule_g2exp_hoops(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """Expanded G2 hoops.

    HP1 (regular) — S6 bend type, unchanged from prior version.
      Excel:    ROUNDUP((Y_exp_ext) / 5 * n, 0)
      Span:     gut_dim
      Bend:     S6   A=5.5"  B=span  C=6.5"  D=span  G=5.5"

    HP2 (notch) — T14 bend type per Vista shop bend chart.
      T14 is a stepped / L-shaped closed hoop wrapping the expansion notch.
      Quantity formula unchanged (Excel match).
      Length formula treats the bar as a perimeter wrap of the notch-zone
      cross-section (notch_dim + tails); T14 leg breakdown left to shop
      drawings — review_flag set so the detailer can confirm A–G dims
      against the Vista T14 bend chart.
    """
    bars: list[BarRow] = []
    n = p.n_struct

    if p.gut_dim > 0:
        qty_reg = math.ceil(p.y_exp_ext_in / 5.0 * n)
        hp1_total = _s6_total(p.gut_dim)
        log.step(f"HP1 reg: CEIL({fmt_inches(p.y_exp_ext_in)}/5*{n}) = {qty_reg}, "
                 f"gut={fmt_inches(p.gut_dim)}, S6 stock=2×gut+11.5\"={fmt_inches(hp1_total)}")
        bars.append(BarRow(
            mark="HP1", size="#5", qty=qty_reg, length_in=hp1_total,
            shape="S6",
            leg_a_in=_HP_TAIL_HOOK,    # A = 5.5"
            leg_b_in=p.gut_dim,        # B = left side height
            leg_c_in=_HP_TAIL_PLAIN,   # C = 6.5" bottom span
            leg_d_in=p.gut_dim,        # D = right side height
            leg_g_in=_HP_TAIL_HOOK,    # G = 5.5"
            notes="Reg Hoops @5oc, S6 bend",
            source_rule="rule_g2exp_hoops",
        ))

    if p.notch_dim > 0:
        qty_notch = math.ceil(p.x_ext_in / 5.0 * 2 * n)
        hp2_total = _s6_total(p.notch_dim)
        log.step(f"HP2 notch: CEIL({fmt_inches(p.x_ext_in)}/5*2*{n}) = {qty_notch}, "
                 f"notch={fmt_inches(p.notch_dim)}, T14 stock≈2×notch+11.5\"={fmt_inches(hp2_total)}")
        bars.append(BarRow(
            mark="HP2", size="#5", qty=qty_notch, length_in=hp2_total,
            shape="T14",
            leg_a_in=_HP_TAIL_HOOK,    # A = 5.5" (inside step tail)
            leg_b_in=p.notch_dim,      # B = notch span
            leg_c_in=_HP_TAIL_PLAIN,   # C = 6.5"
            leg_d_in=p.notch_dim,      # D = notch span
            leg_g_in=_HP_TAIL_HOOK,    # G = 5.5"
            notes="Notched Hoops @5oc, T14 bend (Vista bend chart)",
            review_flag=(
                "T14 leg breakdown (A–G) per Vista shop bend chart. "
                "Verify A/B/C/D/E/F/G dimensions against bend chart at shop-drawing stage."
            ),
            source_rule="rule_g2exp_hoops",
        ))

    return bars


# ═══════════════════════════════════════════════════════════════════════════════
# G2 INLET TOP — Vista Excel-matched rules
#
# Reproduces "G2 inlet Top 9in walls.xlsx".
# Shares rule_g2_horizontals, rule_g2_ab_bars, rule_g2_hoops with the
# standard G2 Inlet.  Has different vertical length and right-angle formula.
# No bottom mat (top slab, not a box).
# ═══════════════════════════════════════════════════════════════════════════════

def rule_g2top_geometry(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """Derive G2 Inlet Top geometry.

    Same base X/Y/T as standard G2 inlet.  Two height parameters:
      wall_height_ft    — full wall height (for horizontal bar qty)
      vert_extension_in — top-slab extension (for vertical bar length & RA leg)
    """
    x_ext = p.x_dim_ft * 12.0
    y_ext = p.y_dim_ft * 12.0

    # ── Wall thickness auto-derive ──────────────────────────────────────
    t = float(getattr(p, "wall_thick_in", 0))
    if t <= 0:
        trial_inside = x_ext - 2 * 9.0
        t = 9.0 if trial_inside <= 54.0 else 11.0
        setattr(p, "wall_thick_in", t)
        log.step(f"Auto T: trial interior X = {fmt_inches(trial_inside)} -> T = {t:.0f}\"")
    else:
        log.step(f"User T = {t:.0f}\"")

    x_inside = x_ext - 2 * t
    y_inside = y_ext - 2 * t
    n = int(getattr(p, "num_structures", 1)) or 1

    grate_type = str(getattr(p, "grate_type", "Type 24"))
    grate_ded = _GRATE_DEDUCTION.get(grate_type, 24.0)

    h_adj = p.wall_height_ft * 12.0 + 4.0   # for horizontals

    vert_ext = float(getattr(p, "vert_extension_in", 20.0))
    vert_height = vert_ext + 10.0            # Excel: =D6*12+E6+10
    ra_vert_leg = vert_ext - 2.0             # Excel: =D6*12+E6-2

    y_bar = y_ext - 6.0
    x_bar = x_ext - 6.0

    gut_dim = x_inside + t - (grate_ded + 5.0)
    ab_bar_len = x_ext - 4.5

    # ── Store on p ────────────────────────────────────────────────────────
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
    setattr(p, "vert_height", vert_height)
    setattr(p, "ra_vert_leg", ra_vert_leg)

    if gut_dim <= 0:
        log.warn(f"Gut dimension = {fmt_inches(gut_dim)} <= 0")
    if 0 < gut_dim < 8.0:
        log.warn(f"Gut dimension = {fmt_inches(gut_dim)} < 8\" — tight grate opening, verify bar spacing")

    log.result("GEOMETRY",
        f"X={fmt_inches(x_ext)}, Y={fmt_inches(y_ext)}, T={t:.0f}\", "
        f"H_adj={fmt_inches(h_adj)}, Vert_ext={fmt_inches(vert_ext)}, "
        f"Vert_len={fmt_inches(vert_height)}, Gut={fmt_inches(gut_dim)}")
    return []


def rule_g2top_verticals(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """G2 Inlet Top verticals -- same qty formulas as standard, shorter length.

    Qty uses the standard -48/+52 constants (grate_ded parameterized).
    Length base = vert_extension_in + 10 (top-slab extension, NOT full wall H_adj).

    V1 gets a 12" (1 ft) L-bend at the top for supporting hoops and top deck.
    V2 (grate side) is a straight bar.
    """
    gd2 = 2 * p.grate_ded
    v1_ext = 12.0   # 1 ft top extension on V1 for bending over hoops

    qty_v1 = math.ceil((p.x_bar * 2 - gd2 + p.y_bar + 6) / 5.0)
    qty_v2 = math.ceil((p.y_bar + gd2 + 4) / 5.0)

    v1_len = p.vert_height + v1_ext
    v2_len = p.vert_height

    log.step(f"V1: CEIL(({fmt_inches(p.x_bar)}*2 - {gd2:.0f} + {fmt_inches(p.y_bar)} + 6)/5) = {qty_v1}, "
             f"len={fmt_inches(v1_len)} (vert_height + 12\" top bend)")
    log.step(f"V2: CEIL(({fmt_inches(p.y_bar)} + {gd2:.0f} + 4)/5) = {qty_v2}, "
             f"len={fmt_inches(v2_len)} (vert_height, straight)")

    return [
        BarRow(mark="V1", size="#5", qty=qty_v1, length_in=v1_len,
               shape="L", leg_a_in=p.vert_height, leg_b_in=v1_ext,
               notes="Verticals @5oc, 1ft top bend for hoops",
               source_rule="rule_g2top_verticals"),
        BarRow(mark="V2", size="#5", qty=qty_v2, length_in=v2_len,
               shape="Str", notes="Verticals Grate Side @5oc",
               source_rule="rule_g2top_verticals"),
    ]


def rule_g2top_right_angle(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """G2 Inlet Top right angle -- different vert leg and qty formula.

    Excel formulas:
      Deck leg  = gut_dim  (same as standard)
      Vert leg  = vert_extension_in - 2  (NOT gut*1.5)
      Qty       = ROUNDUP((Y_ext + 7) / 6 * n, 0)  (has +7 offset)
    """
    if p.gut_dim <= 0:
        log.step("Right angle bars: skipped (gut_dim <= 0)")
        return []

    deck_leg = p.gut_dim
    vert_leg = p.ra_vert_leg
    qty = math.ceil((p.y_ext_in + 7.0) / 6.0 * p.n_struct)

    log.step(f"RA1: deck={fmt_inches(deck_leg)}, vert={fmt_inches(vert_leg)}, "
             f"qty=CEIL(({fmt_inches(p.y_ext_in)}+7)/6*{p.n_struct})={qty}")

    return [BarRow(
        mark="RA1", size="#5", qty=qty,
        length_in=deck_leg + vert_leg,
        shape="L", leg_a_in=deck_leg, leg_b_in=vert_leg,
        notes="Outside Right Angle @6oc",
        source_rule="rule_g2top_right_angle",
    )]


# ═══════════════════════════════════════════════════════════════════════════════
# G2 EXPANDED INLET TOP — rules for the vertical extension over G2 Expanded Inlet
#
# Shares rule_g2_horizontals, rule_g2exp_ab_bars, rule_g2exp_hoops with G2
# Expanded Inlet.  Shares rule_g2top_right_angle with G2 Inlet Top.
# ═══════════════════════════════════════════════════════════════════════════════

def rule_g2exptop_geometry(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """Derive G2 Expanded Inlet Top geometry.

    Same base as rule_g2exp_geometry (Y fixed 5'-0" main / 8'-0" expanded).
    Adds vert_height and ra_vert_leg for the vertical extension bars:
    vert_ext = 20\" (fixed), vert_height = 30\", ra_vert_leg = 18\".
    """
    x_ext = p.x_dim_ft * 12.0

    t = float(getattr(p, "wall_thick_in", 9.0))
    log.step(f"T = {t:.0f}\"")

    y_ext     = 5.0 * 12.0   # 60"
    y_exp_ext = 8.0 * 12.0   # 96"
    setattr(p, "y_dim_ft",      y_ext / 12.0)
    setattr(p, "y_expanded_ft", y_exp_ext / 12.0)

    x_inside      = x_ext - 2 * t
    y_inside      = y_ext - 2 * t
    y_exp_inside  = y_exp_ext - 2 * t
    n = int(getattr(p, "num_structures", 1)) or 1

    grate_type = str(getattr(p, "grate_type", "Type 24"))
    grate_ded  = _GRATE_DEDUCTION.get(grate_type, 24.0)

    h_adj        = p.wall_height_ft * 12.0 + 4.0
    vert_ext     = 20.0
    vert_height  = vert_ext + 10.0    # 30"
    ra_vert_leg  = vert_ext - 2.0     # 18"

    y_bar = y_ext - 6.0
    x_bar = x_ext - 6.0

    gut_dim          = x_inside + t - (grate_ded + 5.0)
    notch_dim        = y_exp_ext / 2.0 - 23.0
    ab_bar_len_reg   = x_ext - 4.5
    ab_bar_len_notch = y_exp_ext - 4.5

    setattr(p, "x_ext_in",         x_ext)
    setattr(p, "y_ext_in",         y_ext)
    setattr(p, "y_exp_ext_in",     y_exp_ext)
    setattr(p, "x_inside_in",      x_inside)
    setattr(p, "y_inside_in",      y_inside)
    setattr(p, "y_exp_inside_in",  y_exp_inside)
    setattr(p, "h_adj",            h_adj)
    setattr(p, "y_bar",            y_bar)
    setattr(p, "x_bar",            x_bar)
    setattr(p, "gut_dim",          gut_dim)
    setattr(p, "notch_dim",        notch_dim)
    setattr(p, "ab_bar_len",       ab_bar_len_reg)
    setattr(p, "ab_bar_len_reg",   ab_bar_len_reg)
    setattr(p, "ab_bar_len_notch", ab_bar_len_notch)
    setattr(p, "grate_ded",        grate_ded)
    setattr(p, "n_struct",         n)
    setattr(p, "t_in",             t)
    setattr(p, "vert_height",      vert_height)
    setattr(p, "ra_vert_leg",      ra_vert_leg)

    if gut_dim <= 0:
        log.warn(f"Gut dimension = {fmt_inches(gut_dim)} <= 0")
    if 0 < gut_dim < 8.0:
        log.warn(f"Gut dimension = {fmt_inches(gut_dim)} < 8\" — tight grate opening, verify bar spacing")

    log.result("GEOMETRY",
        f"X={fmt_inches(x_ext)} (int {fmt_inches(x_inside)}), "
        f"Y_main={fmt_inches(y_ext)}, Y_exp={fmt_inches(y_exp_ext)}, T={t:.0f}\", "
        f"H_adj={fmt_inches(h_adj)}, vert_height={fmt_inches(vert_height)}, "
        f"Gut={fmt_inches(gut_dim)}, Notch={fmt_inches(notch_dim)}")
    return []


def rule_g2exptop_verticals(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """G2 Expanded Inlet Top verticals.

    Same T-based qty as rule_g2exp_verticals, but bar length uses
    vert_height (30\") instead of h_adj (full wall height).
    V1 gets a 12\" top bend; V2 is straight.
    """
    t      = p.t_in
    v1_ext = 12.0

    qty_v1 = math.ceil((p.x_bar * 2 + p.y_bar + 6 * t) / 5.0)
    qty_v2 = math.ceil((p.y_bar + 2 * t) / 5.0)

    v1_len = p.vert_height + v1_ext
    v2_len = p.vert_height

    log.step(f"V1: CEIL(({fmt_inches(p.x_bar)}*2 + {fmt_inches(p.y_bar)} + 6*{t:.0f})/5) = {qty_v1}, "
             f"len={fmt_inches(v1_len)} (vert_height + 12\" top bend)")
    log.step(f"V2: CEIL(({fmt_inches(p.y_bar)} + 2*{t:.0f})/5) = {qty_v2}, "
             f"len={fmt_inches(v2_len)} (vert_height, straight)")

    return [
        BarRow(mark="V1", size="#5", qty=qty_v1, length_in=v1_len,
               shape="L", leg_a_in=p.vert_height, leg_b_in=v1_ext,
               notes="Verticals @5oc, 1ft top bend for hoops",
               source_rule="rule_g2exptop_verticals"),
        BarRow(mark="V2", size="#5", qty=qty_v2, length_in=v2_len,
               shape="Str", notes="Verticals Grate Side @5oc",
               source_rule="rule_g2exptop_verticals"),
    ]
