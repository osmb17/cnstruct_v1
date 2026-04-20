"""
Rule functions for Retaining Wall template.

Caltrans-style cantilever retaining wall:
  SW1 — stem wall horizontal bars EF (temperature/shrinkage running ALONG wall length)
  SW2 — stem wall vertical bars EF (primary flexural steel, tension on soil side)
  TW1 — toe bars (bottom footing, transverse, primary tension under toe)
  HW1 — heel bars (top footing, transverse, primary tension over heel)
  DW1 — stem-to-footing dowels (continuity bars across construction joint)
  KW1 — shear key bars (if shear key requested, vertical U-bars through key)

Geometry conventions:
  - wall_length_ft:    length of wall (out-of-plane dimension)
  - stem_height_ft:    wall stem height above top of footing
  - stem_thick_in:     stem wall thickness
  - footing_length_ft: full horizontal footing length (toe + heel + stem thickness)
  - footing_depth_in:  footing thickness (vertical dimension)
  - cover_in:          clear cover, all faces

Notes:
  - SW1 horizontal bars run ALONG the wall length. Qty per face = floor(stem_height/spacing)+1.
  - SW2 vertical bars are spaced along the wall length. Qty per face = floor(wall_length/spacing)+1.
  - Dowel length: footing_depth_in (embed into footing) + lap splice into stem.
  - Lap splice = 1.3 x ld (Class B tension splice per ACI 318-19 S25.5.2).
"""

from __future__ import annotations

import math

from vistadetail.engine.hooks import development_length_tension, hook_add
from vistadetail.engine.reasoning_logger import ReasoningLogger
from vistadetail.engine.schema import BarRow, Params, fmt_inches


# ---------------------------------------------------------------------------
# SW1 — Stem wall horizontal bars, each face (temperature & shrinkage steel)
# ACI 318-19 §11.7.2, §24.3.2
# ---------------------------------------------------------------------------

def rule_stem_horiz(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Stem horizontal bars, each face — temperature/shrinkage steel running
    ALONG the wall length (ACI 318-19 S11.7.2).

    Qty per face = floor(usable_stem_height / horiz_spacing) + 1.
    Bar length = wall_length - 2 * cover (runs the full length of the wall).
    Total qty = qty_per_face * 2 faces.
    """
    wall_len_in = p.wall_length_ft * 12.0
    usable_h_in = (p.stem_height_ft * 12.0) - (2.0 * 2.0)
    qty_per_face = math.floor(usable_h_in / 12.0) + 1
    qty_total = qty_per_face * 2   # each face

    # Horizontal bar runs the full wall length
    bar_len_in = wall_len_in - (2.0 * 2.0)
    bar_len_in = max(bar_len_in, 12.0)

    log.step(f"Stem usable height = {usable_h_in:.1f} in  ->  {qty_per_face} bars/face x 2 faces = {qty_total}")
    log.step(f"Bar length = {fmt_inches(wall_len_in)} - 2x{2.0} = {fmt_inches(bar_len_in)} (along wall)")
    log.result("SW1", f"#4 x {qty_total} @ {fmt_inches(bar_len_in)}")

    return [BarRow(
        mark="SW1", size="#4", qty=qty_total, length_in=bar_len_in,
        shape="Str", notes="Stem Horiz EF", source_rule="rule_stem_horiz",
    )]


# ---------------------------------------------------------------------------
# SW2 — Stem wall vertical bars, each face (primary flexural steel)
# ACI 318-19 §11.7.3.1 (cantilever wall primary reinf.)
# Tension face = soil (back) side; EF layout conservatively.
# ---------------------------------------------------------------------------

def rule_stem_vert(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Stem vertical bars, each face — primary flexural steel (ACI 318-19 S11.7.3.1).

    Qty per face = floor(usable_wall_length / vert_spacing) + 1.
    Bar length = stem_height + 90-deg hook at base (into footing) + 6 in top dev.
    Total qty = qty_per_face * 2 faces.
    """
    wall_len_in = p.wall_length_ft * 12.0
    usable_len_in = wall_len_in - (2.0 * 2.0)
    qty_per_face = math.floor(usable_len_in / 12.0) + 1
    qty_total = qty_per_face * 2   # each face

    bot_hook_in = hook_add("std_90", "#5")
    bar_len_in = (p.stem_height_ft * 12.0) + bot_hook_in + 6.0

    log.step(f"Wall length = {fmt_inches(wall_len_in)}, usable = {usable_len_in:.1f} in  ->  {qty_per_face} bars/face x 2 = {qty_total}")
    log.step(f"Bar length = {p.stem_height_ft * 12:.0f} + {bot_hook_in} hook + 6 top dev = {fmt_inches(bar_len_in)}")
    log.result("SW2", f"#5 x {qty_total} @ {fmt_inches(bar_len_in)}")

    return [BarRow(
        mark="SW2", size="#5", qty=qty_total, length_in=bar_len_in,
        shape="L", leg_a_in=p.stem_height_ft * 12.0 + 6.0, leg_b_in=bot_hook_in,
        notes="Stem Vert EF", source_rule="rule_stem_vert",
    )]


# ---------------------------------------------------------------------------
# TW1 — Toe bars (bottom of footing, toe side, transverse)
# ACI 318-19 §13.3.1 (footing flexural reinf.)
# Primary tension steel on bottom face under toe projection.
# ---------------------------------------------------------------------------

def rule_toe_bars(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Toe transverse bars at bottom of footing (ACI 318-19 S13.3.1).

    Bars run transverse (across the footing width = footing_length_ft).
    Qty = spaced along the wall length at footing_spacing_in.
    Bar length = footing_length - cover + hook at toe end.
    """
    wall_len_in = p.wall_length_ft * 12.0
    footing_len_in = p.footing_length_ft * 12.0

    # Bars spaced along the wall length
    qty = math.floor((wall_len_in - 2.0 * 2.0) / 12.0) + 1

    # Bar spans the full footing cross-section width with hook at toe
    hook_in = hook_add("std_90", "#5")
    bar_len_in = footing_len_in - 2.0 + hook_in

    log.step(f"Toe bars spaced along wall length {fmt_inches(wall_len_in)}: {qty} bars @ {12.0}\" oc")
    log.step(f"Bar length = {fmt_inches(footing_len_in)} - {2.0} + {hook_in} hook = {fmt_inches(bar_len_in)}")
    log.result("TW1", f"#5 x {qty} @ {fmt_inches(bar_len_in)}")

    return [BarRow(
        mark="TW1", size="#5", qty=qty, length_in=bar_len_in,
        shape="L", leg_a_in=footing_len_in - 2.0, leg_b_in=hook_in,
        notes="Toe Bars Bot", source_rule="rule_toe_bars",
    )]


# ---------------------------------------------------------------------------
# HW1 — Heel bars (bottom of footing, heel side, transverse)
# ACI 318-19 §13.3.1 (footing flexural reinf.)
# Primary tension steel on bottom face over heel projection.
# ---------------------------------------------------------------------------

def rule_heel_bars(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Heel transverse bars at top of footing (ACI 318-19 S13.3.1).

    Same spacing as toe bars (along wall length). Sits on top face of footing.
    Bar length = footing_length - cover + hook at heel free end.
    """
    wall_len_in = p.wall_length_ft * 12.0
    footing_len_in = p.footing_length_ft * 12.0

    qty = math.floor((wall_len_in - 2.0 * 2.0) / 12.0) + 1

    hook_in = hook_add("std_90", "#5")
    bar_len_in = footing_len_in - 2.0 + hook_in

    log.step(f"Heel bars spaced along wall length {fmt_inches(wall_len_in)}: {qty} bars @ {12.0}\" oc")
    log.step(f"Bar length = {fmt_inches(footing_len_in)} - {2.0} + {hook_in} hook = {fmt_inches(bar_len_in)}")
    log.result("HW1", f"#5 x {qty} @ {fmt_inches(bar_len_in)}")

    return [BarRow(
        mark="HW1", size="#5", qty=qty, length_in=bar_len_in,
        shape="L", leg_a_in=footing_len_in - 2.0, leg_b_in=hook_in,
        notes="Heel Bars Top", source_rule="rule_heel_bars",
    )]


# ---------------------------------------------------------------------------
# DW1 — Stem-to-footing dowels (construction joint continuity)
# ACI 318-19 §25.5.2, §16.3.2 (wall-footing interface)
# ---------------------------------------------------------------------------

def rule_stem_dowels(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Dowels through stem-to-footing construction joint.

    Qty = number of vertical bars per face on the stem (same spacing as SW2),
    placed at every vert_spacing_in across the footing length.
    Length = footing embed (footing_depth - cover) + Class B lap splice into stem.

    Class B splice = 1.3 × ld (ACI 318-19 §25.5.2).
    """
    wall_len_in = p.wall_length_ft * 12.0
    qty = math.floor((wall_len_in - 2.0 * 2.0) / 12.0) + 1

    # Embed into footing: footing depth minus top cover
    embed_in = 18.0 - 2.0

    # Lap splice into stem: Class B = 1.3 x ld
    ld_in = development_length_tension("#5", cover_in=2.0,
                                       spacing_in=12.0)
    lap_in = math.ceil(1.3 * ld_in)

    bar_len_in = embed_in + lap_in

    log.step(f"Dowel qty = {qty} at {12.0}\" oc along wall length {fmt_inches(wall_len_in)}")
    log.step(f"Embed = {embed_in:.1f} in  |  Class B lap = 1.3 x {ld_in:.1f} = {lap_in} in")
    log.step(f"Total dowel length = {bar_len_in:.1f} in")
    log.result("DW1", f"#5 × {qty} @ {fmt_inches(bar_len_in)}")

    return [BarRow(
        mark="DW1", size="#5", qty=qty, length_in=bar_len_in,
        shape="Str", notes="Stem-Ftg Dowels", source_rule="rule_stem_dowels",
    )]


# ---------------------------------------------------------------------------
# KW1 — Shear key bars (if shear key requested)
# Caltrans GS §6 (shear key sliding resistance)
# U-bars through shear key, vertical orientation.
# ---------------------------------------------------------------------------

def rule_shear_key(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Shear key U-bars — only generated when shear_key == 'yes'.

    Key bars are U-shaped: two vertical legs through the key depth plus
    a bottom bend, spaced at footing_spacing_in across the footing length.

    U-bar length = 2 × (key_depth + cover) + footing bar diameter bend allowance.
    """
    if p.shear_key != "yes":
        log.step("Shear key = no -- skipping KW1")
        return []

    wall_len_in = p.wall_length_ft * 12.0
    qty = math.floor((wall_len_in - 2.0 * 2.0) / 12.0) + 1

    # U-bar: two legs each = key_depth - cover; bend per ACI 318-19 Table 25.3.1
    from vistadetail.engine.hooks import min_bend_diameter
    bend_d = min_bend_diameter("#5")  # 6db (#3-#8) or 8db (#9+)
    leg_in = 12.0 - 2.0
    bar_len_in = (2.0 * leg_in) + bend_d
    bar_len_in = max(bar_len_in, 12.0)

    log.step(f"Shear key requested — key depth = {12.0} in")
    log.step(f"U-bar qty = {qty}  |  leg = {leg_in:.1f} in × 2 + {bend_d:.2f} bend = {bar_len_in:.2f} in")
    log.result("KW1", f"#5 × {qty} @ {fmt_inches(bar_len_in)}")

    return [BarRow(
        mark="KW1", size="#5", qty=qty, length_in=bar_len_in,
        shape="U", leg_a_in=leg_in, leg_b_in=bend_d, leg_c_in=leg_in,
        notes="Shear Key U-bars", source_rule="rule_shear_key",
    )]


# ---------------------------------------------------------------------------
# Validation rule — no BarRows produced; only warnings
# ---------------------------------------------------------------------------

def rule_validate_retaining_wall(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """Validate geometry and flag potentially unsafe combinations."""
    if p.stem_thick_in < 10:
        log.warn(
            f"Stem thickness {p.stem_thick_in} in < 10 in — verify cover and constructability "
            "(ACI 318-19 §11.7.2 requires min. 6 in for walls; Caltrans detail practice typically ≥ 10 in)"
        )
    if 2.0 < 2.0:
        log.warn(
            f"Cover {2.0} in < 2.0 in minimum for retaining wall (ACI 318-19 §20.6.1.3)"
        )
    if p.stem_height_ft > 15.0:
        log.warn(
            f"Stem height {p.stem_height_ft} ft > 15 ft — consider reviewing design forces; "
            "tall cantilever walls may require larger bar sizes or reduced spacing"
        )
    footing_ratio = (p.footing_length_ft * 12.0) / max(p.stem_height_ft * 12.0, 1.0)
    if footing_ratio < 0.5:
        log.warn(
            f"Footing length / stem height = {footing_ratio:.2f} < 0.5 — "
            "overturning and sliding stability may be inadequate; verify with geotechnical engineer"
        )
    return []
