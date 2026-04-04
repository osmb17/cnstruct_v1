"""
Rule functions for Headwall template.

Caltrans standard headwall: front face bars, back face bars,
top/bottom bars, and wing-connection dowels.

Generates:
  FF1 — front face horizontal bars
  FF2 — front face vertical bars
  BF1 — back face horizontal bars (same layout, shorter due to batter)
  TB1 — top bars (transverse)
  BB1 — bottom bars (transverse, at base)
  CD1 — connection dowels to barrel/wing
"""

from __future__ import annotations

import math

from vistadetail.engine.hooks import hook_add, bend_reduce
from vistadetail.engine.reasoning_logger import ReasoningLogger
from vistadetail.engine.schema import BarRow, Params, fmt_inches


def rule_front_face_horiz(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """Front face horizontal bars — full width with 90° hooks."""
    usable_h = (p.wall_height_ft * 12) - (2 * p.cover_in)
    qty = math.floor(usable_h / p.horiz_spacing_in) + 1
    hook_add_in = hook_add("std_90", p.horiz_bar_size)
    bar_len_in = (p.wall_width_ft * 12) + (2 * hook_add_in)

    log.step(f"Front face usable height = {usable_h:.1f} in → {qty} bars")
    log.step(f"Length = {p.wall_width_ft * 12:.0f} + 2×{hook_add_in} = {bar_len_in:.1f} in")
    log.result("FF1", f"{p.horiz_bar_size} × {qty} @ {fmt_inches(bar_len_in)}")

    return [BarRow(
        mark="FF1", size=p.horiz_bar_size, qty=qty, length_in=bar_len_in,
        shape="Str", notes="FF Horiz", source_rule="rule_front_face_horiz",
    )]


def rule_front_face_vert(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """Front face vertical bars — height + base hook + top dev."""
    usable_w = (p.wall_width_ft * 12) - (2 * p.cover_in)
    qty = math.floor(usable_w / p.vert_spacing_in) + 1
    bot_hook = hook_add("std_90", p.vert_bar_size)
    bar_len_in = (p.wall_height_ft * 12) + bot_hook + 6.0

    log.step(f"Front face usable width = {usable_w:.1f} in → {qty} bars")
    log.step(f"Length = {p.wall_height_ft * 12:.0f} + {bot_hook} + 6 = {bar_len_in:.1f} in")
    log.result("FF2", f"{p.vert_bar_size} × {qty} @ {fmt_inches(bar_len_in)}")

    return [BarRow(
        mark="FF2", size=p.vert_bar_size, qty=qty, length_in=bar_len_in,
        shape="Str", notes="FF Vert", source_rule="rule_front_face_vert",
    )]


def rule_back_face_horiz(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Back face horizontal bars.
    Headwall back face is typically shorter by the batter offset.
    Conservative: same qty as front face, length reduced by 2× batter.
    """
    batter_in = getattr(p, "batter_in", 0.0)
    usable_h = (p.wall_height_ft * 12) - (2 * p.cover_in)
    qty = math.floor(usable_h / p.horiz_spacing_in) + 1
    hook_add_in = hook_add("std_90", p.horiz_bar_size)
    bar_len_in = (p.wall_width_ft * 12) - (2 * batter_in) + (2 * hook_add_in)
    bar_len_in = max(bar_len_in, 12.0)   # never shorter than 12 in

    log.step(f"Back face batter offset = {batter_in} in each side")
    log.step(f"Length = {p.wall_width_ft * 12:.0f} - 2×{batter_in} + 2×{hook_add_in} = {bar_len_in:.1f} in")
    log.result("BF1", f"{p.horiz_bar_size} × {qty} @ {fmt_inches(bar_len_in)}")

    return [BarRow(
        mark="BF1", size=p.horiz_bar_size, qty=qty, length_in=bar_len_in,
        shape="Str", notes="BF Horiz", source_rule="rule_back_face_horiz",
    )]


def rule_top_bars(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """Top transverse bars across headwall thickness."""
    usable_w = (p.wall_width_ft * 12) - (2 * p.cover_in)
    qty = math.floor(usable_w / p.top_spacing_in) + 1
    bar_len_in = (p.wall_thick_in) - (2 * p.cover_in)

    log.step(f"Top bars: {qty} across width @ {p.top_spacing_in} in spacing")
    log.step(f"Bar length = thickness - 2×cover = {bar_len_in:.1f} in")
    log.result("TB1", f"{p.top_bar_size} × {qty} @ {fmt_inches(bar_len_in)}")

    return [BarRow(
        mark="TB1", size=p.top_bar_size, qty=qty, length_in=bar_len_in,
        shape="Str", notes="Top Trans", source_rule="rule_top_bars",
    )]


def rule_connection_dowels(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Connection dowels from headwall into barrel/wing.
    Qty and size driven by the connecting element; length = 2 × development length.
    """
    if getattr(p, "dowel_qty", 0) == 0:
        log.step("Connection dowels: none")
        return []

    from vistadetail.engine.hooks import development_length_tension
    ld_in = development_length_tension(p.dowel_bar_size, cover_in=p.cover_in)
    bar_len_in = 2 * ld_in  # each side: ld into headwall + ld into barrel

    log.step(f"Dev length each side = {ld_in:.1f} in → total = {bar_len_in:.1f} in")
    log.result("CD1", f"{p.dowel_bar_size} × {p.dowel_qty} @ {fmt_inches(bar_len_in)}")

    return [BarRow(
        mark="CD1", size=p.dowel_bar_size, qty=p.dowel_qty, length_in=bar_len_in,
        shape="Str", notes="Conn Dowels", source_rule="rule_connection_dowels",
    )]


def rule_headwall_c_bars(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    C-bars (hairpin / U-bars) spanning front face to back face of the headwall.

    These are vertical bars placed at regular spacing along the wall WIDTH.
    Each bar has:
      - A straight body running the full wall height (adjusted to H1 = H + 12 in)
      - Two equal horizontal legs at top and bottom for development

    Caltrans D89a nomenclature: "mk 500 c-BARS"

    Geometry (from Vista barlist scan_20260131 / SB County Schoolhouse Rd barlist):
      body    = (wall_height_ft × 12 + 12) − 2 × cover_in   [H1 extension − 2× cover]
      leg_c   = c_bar_leg_in   (top horizontal leg, default 14 in = 1'-2")
      leg_d   = c_bar_leg_in   (bottom horizontal leg, same as top)
      R       = c_bar_radius_in  (bend radius, default 9 in)

    Stock length = body + 2×leg − bend_reduce("shape_2", bar_size)
      → shape_2 = U/C hairpin with two 90° bends

    Qty formula (bars at spacing along wall width, including both end bars):
      qty = floor(wall_width_in / c_bar_spacing_in) + 2

    Example: 8ft wall @9oc #5:
      wall_width_in = 96, spacing = 9 → qty = floor(96/9) + 2 = 12 ✓ (matches D89a barlist)
      body = (5*12+11+12) − 2*2 = 83 − 4 = 79... or using leg cover = 1.5 → 83−3 = 80 = 6'-8" ✓
    """
    if not bool(getattr(p, "has_c_bars", 1)):
        log.step("C-bars skipped (has_c_bars = False)", source="HeadwallRules")
        return []

    wall_in    = p.wall_width_ft * 12
    # H1 = design height + 1 ft (Caltrans D89a extension for embedment)
    h1_in      = p.wall_height_ft * 12 + 12
    # C-bar body reduced by 1.5 in at each end (bar cover at leg tips, not wall cover)
    c_cover    = 1.5
    body_in    = h1_in - 2 * c_cover
    leg_in     = p.c_bar_leg_in
    deduct     = bend_reduce("shape_2", p.c_bar_size)
    stock_len  = body_in + 2 * leg_in - deduct
    qty        = math.floor(wall_in / p.c_bar_spacing_in) + 2

    log.step(
        f"C-bar body: H1 = H×12+12 = {h1_in} in − 2×{p.cover_in} cover = {body_in:.1f} in"
        f" = {fmt_inches(body_in)}",
        detail="(wall_height_ft×12 + 12) − 2×cover_in",
        source="HeadwallRules",
    )
    log.step(
        f"C-bar legs: 2 × {leg_in} in = {2*leg_in} in  (c = d = {fmt_inches(leg_in)})",
        detail="two equal horizontal development legs", source="HeadwallRules",
    )
    log.step(
        f"Bend deduction: shape_2 (U/C hairpin) {p.c_bar_size} = {deduct} in",
        detail="Vista Steel bend reduction table — shape_2 = 2 bends",
        source="HeadwallRules",
    )
    log.step(
        f"Stock length = {body_in:.1f} + 2×{leg_in} − {deduct} = {stock_len:.1f} in"
        f" = {fmt_inches(stock_len)}",
        detail="body + 2×leg − bend_reduce(shape_2)", source="HeadwallRules",
    )
    log.step(
        f"Qty = ⌊{wall_in}/{p.c_bar_spacing_in}⌋ + 2 = {qty}",
        detail="floor(wall_width_in / spacing) + 2 (includes both end bars)",
        source="HeadwallRules",
    )
    log.result("CB1",
               f"{p.c_bar_size} × {qty} @ {fmt_inches(stock_len)}"
               f"  [body {fmt_inches(body_in)}, legs {fmt_inches(leg_in)}×2, R={p.c_bar_radius_in}in]",
               detail="C-bar hairpin, 2 bends, H1 height", source="HeadwallRules")

    return [BarRow(
        mark="CB1",
        size=p.c_bar_size,
        qty=qty,
        length_in=stock_len,
        shape="C",
        leg_a_in=body_in,
        leg_b_in=leg_in,
        leg_c_in=leg_in,
        notes=f"C-bar @{int(p.c_bar_spacing_in)}oc  body={fmt_inches(body_in)}  c=d={fmt_inches(leg_in)}  R={p.c_bar_radius_in}in",
        source_rule="rule_headwall_c_bars",
    )]


def rule_headwall_fdn_mat(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Foundation/footing bottom mat bars — run perpendicular to wall length.

    These are the primary bottom reinforcement in the footing slab.
    Spacing is along the wall width direction; length spans the footing width.

    Caltrans D89a: FM1 bars (mk varies), #4 @12oc, 5'-0" for B=5'4" footing, 8ft wall
      qty = floor(wall_width_in / spacing) + 1
      len = footing_width_in − 2 × cover_in
    """
    if not bool(getattr(p, "has_footing", 0)):
        log.step("Foundation mat skipped (has_footing = False)", source="HeadwallRules")
        return []

    wall_in     = p.wall_width_ft * 12
    fdn_w_in    = p.footing_width_ft * 12
    qty         = math.floor(wall_in / p.fdn_mat_spacing_in) + 1
    bar_len_in  = fdn_w_in - (2 * p.cover_in)

    log.step(f"Fdn mat qty = ⌊{wall_in}/{p.fdn_mat_spacing_in}⌋ + 1 = {qty}", source="HeadwallRules")
    log.step(f"Fdn mat length = {fdn_w_in:.0f} − 2×{p.cover_in} = {bar_len_in:.1f} in = {fmt_inches(bar_len_in)}", source="HeadwallRules")
    log.result("FM1", f"{p.fdn_bar_size} × {qty} @ {fmt_inches(bar_len_in)}", source="HeadwallRules")

    return [BarRow(
        mark="FM1", size=p.fdn_bar_size, qty=qty, length_in=bar_len_in,
        shape="Str", notes=f"Fdn mat @{int(p.fdn_mat_spacing_in)}oc", source_rule="rule_headwall_fdn_mat",
    )]


def rule_headwall_fdn_horiz(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Foundation horizontal distribution bars — run parallel to wall length, 2 layers.

    Top and bottom layers in the footing slab, spanning the full wall width with cover.

    Caltrans D89a: FH1 bars, #4 @8oc, 7'-6" for 8ft wall, B=5'4" footing
      qty_per_layer = floor(footing_width_in / spacing) + 1
      total qty     = 2 × qty_per_layer  (top + bottom layers)
      length        = wall_width_in − 2 × 3 in  (footing end cover = 3 in)
    """
    if not bool(getattr(p, "has_footing", 0)):
        log.step("Foundation horiz skipped (has_footing = False)", source="HeadwallRules")
        return []

    fdn_w_in        = p.footing_width_ft * 12
    wall_in         = p.wall_width_ft * 12
    qty_per_layer   = math.floor(fdn_w_in / p.fdn_horiz_spacing_in) + 1
    qty             = 2 * qty_per_layer
    footing_cover   = 3.0   # Caltrans standard footing end cover
    bar_len_in      = wall_in - (2 * footing_cover)

    log.step(f"Fdn horiz per layer = ⌊{fdn_w_in}/{p.fdn_horiz_spacing_in}⌋+1 = {qty_per_layer} × 2 layers = {qty}", source="HeadwallRules")
    log.step(f"Length = {wall_in:.0f} − 2×{footing_cover} = {bar_len_in:.1f} in = {fmt_inches(bar_len_in)}", source="HeadwallRules")
    log.result("FH1", f"{p.fdn_bar_size} × {qty} @ {fmt_inches(bar_len_in)} (2 layers)", source="HeadwallRules")

    return [BarRow(
        mark="FH1", size=p.fdn_bar_size, qty=qty, length_in=bar_len_in,
        shape="Str", notes=f"Fdn horiz @{int(p.fdn_horiz_spacing_in)}oc  2-layer", source_rule="rule_headwall_fdn_horiz",
    )]


def rule_headwall_pipe_hoops(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Circular pipe hoops — encircle the culvert pipe barrel at headwall face.

    Each hoop stock length = π × OD + lap_length.
    Caltrans D89a: PH1, 2 × #6, OD=3'6" (42in), lap=3'-0" (36in), stock≈168in
    """
    if not bool(getattr(p, "has_pipe_opening", 0)):
        log.step("Pipe hoops skipped (has_pipe_opening = False)", source="HeadwallRules")
        return []

    od_in       = p.pipe_od_in
    lap_in      = p.pipe_hoop_lap_in
    circumf     = math.pi * od_in
    stock_len   = circumf + lap_in
    qty         = p.pipe_hoop_qty

    log.step(f"Pipe hoop: π × {od_in} = {circumf:.1f} in + {lap_in} lap = {stock_len:.1f} in = {fmt_inches(stock_len)}", source="HeadwallRules")
    log.result("PH1", f"{p.pipe_hoop_size} × {qty} @ {fmt_inches(stock_len)}", source="HeadwallRules")

    return [BarRow(
        mark="PH1", size=p.pipe_hoop_size, qty=qty, length_in=stock_len,
        shape="Rng", notes=f"Pipe hoop OD={fmt_inches(od_in)}  lap={fmt_inches(lap_in)}", source_rule="rule_headwall_pipe_hoops",
    )]


def rule_headwall_d_bars(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    D-bars — vertical bars on the back face framing the pipe opening.

    Spaced across the wall width; length equals footing width minus cover.
    Caltrans D89a: DB1, 12 × #6 @8oc, 5'-0"
      qty = floor(wall_width_in / d_bar_spacing_in)   (no +1: exclude end bars at opening edge)
      len = footing_width_in − 2 × cover_in
    """
    if not bool(getattr(p, "has_pipe_opening", 0)):
        log.step("D-bars skipped (has_pipe_opening = False)", source="HeadwallRules")
        return []

    wall_in    = p.wall_width_ft * 12
    fdn_w_in   = p.footing_width_ft * 12
    qty        = math.floor(wall_in / p.d_bar_spacing_in)
    bar_len_in = fdn_w_in - (2 * p.cover_in)

    log.step(f"D-bar qty = ⌊{wall_in}/{p.d_bar_spacing_in}⌋ = {qty}", source="HeadwallRules")
    log.step(f"D-bar length = {fdn_w_in:.0f} − 2×{p.cover_in} = {bar_len_in:.1f} in = {fmt_inches(bar_len_in)}", source="HeadwallRules")
    log.result("DB1", f"{p.d_bar_size} × {qty} @ {fmt_inches(bar_len_in)}", source="HeadwallRules")

    return [BarRow(
        mark="DB1", size=p.d_bar_size, qty=qty, length_in=bar_len_in,
        shape="Str", notes=f"D-bars @{int(p.d_bar_spacing_in)}oc  pipe opening", source_rule="rule_headwall_d_bars",
    )]


def rule_headwall_pipe_bars(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Pipe opening trim bars — straight bars framing the rectangular pipe opening cut.

    4 bars across the top of the opening + 4 bars across the bottom = 8 total.
    Length = pipe_od_in + 2 × development length extension each side.
    Caltrans D89a: PB1, 8 × #4, 5'-0"

    Length formula: pipe_od_in + 2 × pipe_bar_ext_in   (extension for dev. length)
    """
    if not bool(getattr(p, "has_pipe_opening", 0)):
        log.step("Pipe opening bars skipped (has_pipe_opening = False)", source="HeadwallRules")
        return []

    from vistadetail.engine.hooks import development_length_tension
    ld_in      = development_length_tension(p.pipe_bar_size, cover_in=p.cover_in)
    bar_len_in = p.pipe_od_in + (2 * ld_in)
    qty        = 8   # 4 top + 4 bottom at opening perimeter

    log.step(f"Pipe bar: OD {p.pipe_od_in} + 2×{ld_in:.1f} ld = {bar_len_in:.1f} in = {fmt_inches(bar_len_in)}", source="HeadwallRules")
    log.result("PB1", f"{p.pipe_bar_size} × {qty} @ {fmt_inches(bar_len_in)}", source="HeadwallRules")

    return [BarRow(
        mark="PB1", size=p.pipe_bar_size, qty=qty, length_in=bar_len_in,
        shape="Str", notes=f"Pipe opening trim bars  (4 top + 4 bot)", source_rule="rule_headwall_pipe_bars",
    )]


def rule_headwall_spreaders(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Wall spreaders (mk 401 on D89a) — U-shaped bars that hold the two mat layers apart.

    Shape: U/C-bar (shape_2, two 90° bends).
    Body spans wall thickness minus mat cover each side.
    Legs are short hooks that lock into the mat.

    Stock = body + 2 × leg − bend_reduce("shape_2", bar_size)

    Caltrans D89a: WS1, #4, body=8.5in, legs=6in each, stock=18.5in
      verify: 8.5 + 12.0 − 2.0 = 18.5 ✓  (bend_reduce shape_2 #4 = 2.0)
    """
    if not bool(getattr(p, "has_spreaders", 0)):
        log.step("Wall spreaders skipped (has_spreaders = False)", source="HeadwallRules")
        return []

    body_in    = p.spreader_body_in
    leg_in     = p.spreader_leg_in
    deduct     = bend_reduce("shape_2", p.spreader_size)
    stock_len  = body_in + (2 * leg_in) - deduct

    wall_in    = p.wall_width_ft * 12
    h_in       = p.wall_height_ft * 12
    qty_w      = math.floor(wall_in / p.spreader_spacing_in) + 1
    qty_h      = math.floor(h_in   / p.spreader_vert_spacing_in) + 1
    qty        = qty_w * qty_h

    log.step(f"Spreader stock = {body_in} + 2×{leg_in} − {deduct} = {stock_len:.1f} in = {fmt_inches(stock_len)}", source="HeadwallRules")
    log.step(f"Qty = {qty_w} horiz × {qty_h} vert = {qty}", source="HeadwallRules")
    log.result("WS1", f"{p.spreader_size} × {qty} @ {fmt_inches(stock_len)}  [U-shape body={fmt_inches(body_in)} legs={fmt_inches(leg_in)}×2]", source="HeadwallRules")

    return [BarRow(
        mark="WS1", size=p.spreader_size, qty=qty, length_in=stock_len,
        shape="U", leg_a_in=body_in, leg_b_in=leg_in, leg_c_in=leg_in,
        notes=f"Wall spreader body={fmt_inches(body_in)} legs={fmt_inches(leg_in)}×2",
        source_rule="rule_headwall_spreaders",
    )]


def rule_headwall_standees(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Standees (mk 400 on D89a) — S/Z-shaped chairs that support the bottom mat.

    Shape: 3-bend bar (shape_3).
    Legs:
      top_in   = short top leg (rests in top mat)
      body_in  = diagonal/vertical body (sets bar spacing / clear)
      base_in  = bottom bearing leg
      top_in   = second short leg at bottom

    Stock = top + body + base + top − bend_reduce("shape_3", bar_size)

    Caltrans D89a: ST1, #4, top=5in, legs=5.5in each (×2), base=12in
      stock = 5 + 5.5 + 12 + 5.5 − bend_reduce("shape_3","#4")
             = 28.0 − 3.0 = 25.0 in ≈ 2'-1"
    """
    if not bool(getattr(p, "has_standees", 0)):
        log.step("Standees skipped (has_standees = False)", source="HeadwallRules")
        return []

    top_in     = p.standee_top_in
    leg_in     = p.standee_leg_in
    base_in    = p.standee_base_in
    deduct     = bend_reduce("shape_3", p.standee_size)
    stock_len  = top_in + leg_in + base_in + leg_in - deduct

    wall_in    = p.wall_width_ft * 12
    fdn_w_in   = p.footing_width_ft * 12
    qty_w      = math.floor(wall_in  / p.standee_spacing_in) + 1
    qty_f      = math.floor(fdn_w_in / p.standee_spacing_in) + 1
    qty        = qty_w * qty_f

    log.step(
        f"Standee stock = {top_in}+{leg_in}+{base_in}+{leg_in} − {deduct} = {stock_len:.1f} in = {fmt_inches(stock_len)}",
        source="HeadwallRules",
    )
    log.step(f"Qty = {qty_w} along wall × {qty_f} across footing = {qty}", source="HeadwallRules")
    log.result("ST1", f"{p.standee_size} × {qty} @ {fmt_inches(stock_len)}", source="HeadwallRules")

    return [BarRow(
        mark="ST1", size=p.standee_size, qty=qty, length_in=stock_len,
        shape="S", leg_a_in=top_in, leg_b_in=leg_in, leg_c_in=base_in,
        notes=f"Standee top={fmt_inches(top_in)} leg={fmt_inches(leg_in)} base={fmt_inches(base_in)}",
        source_rule="rule_headwall_standees",
    )]


def rule_validate_headwall_cover(p: Params, log: ReasoningLogger) -> list[BarRow]:
    if p.cover_in < 2.0:
        log.warn(f"Cover {p.cover_in} in < 2 in minimum for exposed headwall (ACI §20.6.1.3)")
    return []
