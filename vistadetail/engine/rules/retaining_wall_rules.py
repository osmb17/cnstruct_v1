"""
Rule functions for Retaining Wall template.

Caltrans-style cantilever retaining wall:
  SW1 — stem wall horizontal bars EF (temperature/shrinkage + lateral distribution)
  SW2 — stem wall vertical bars EF (primary flexural steel, tension on soil side)
  TW1 — toe bars (bottom footing, toe side, transverse, primary tension under toe)
  HW1 — heel bars (bottom footing, heel side, transverse, primary tension over heel)
  DW1 — stem-to-footing dowels (continuity bars across construction joint)
  KW1 — shear key bars (if shear key requested, vertical U-bars through key)

Geometry conventions:
  - stem_height_ft:   wall stem height above top of footing
  - stem_thick_in:    stem wall thickness
  - footing_length_ft: full horizontal footing length (toe + heel + stem thickness)
  - footing_depth_in: footing thickness (vertical dimension)
  - cover_in:         clear cover, all faces

Notes:
  - SW1/SW2 are each-face (EF), so qty counts one face then caller understands EF.
    Here we compute EF directly as the total bar count for both faces combined
    on transverse (horiz) and track as a single EF mark.
  - SW2 vertical bars: total qty across footing length, spaced at vert_spacing_in.
  - Dowel length: footing_depth_in (embed into footing) + lap splice into stem.
  - Lap splice = 1.3 × ld (Class B tension splice per ACI 318-19 §25.5.2).
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
    Stem horizontal bars, each face.

    Qty = bars per face × 2 faces.
    One face: floor(usable_height / horiz_spacing) + 1 bars.
    Bar length = stem thickness - 2 × cover (transverse bar, no hooks).
    """
    usable_h_in = (p.stem_height_ft * 12.0) - (2.0 * p.cover_in)
    qty_per_face = math.floor(usable_h_in / p.horiz_spacing_in) + 1
    qty_total = qty_per_face * 2   # each face

    # Horizontal bar spans the stem thickness (transverse direction)
    bar_len_in = p.stem_thick_in - (2.0 * p.cover_in)
    bar_len_in = max(bar_len_in, 6.0)

    log.step(f"Stem usable height = {usable_h_in:.1f} in → {qty_per_face} bars/face × 2 faces = {qty_total}")
    log.step(f"Bar length = {p.stem_thick_in} - 2×{p.cover_in} = {bar_len_in:.1f} in (transverse)")
    log.result("SW1", f"{p.horiz_bar_size} × {qty_total} @ {fmt_inches(bar_len_in)}")

    return [BarRow(
        mark="SW1", size=p.horiz_bar_size, qty=qty_total, length_in=bar_len_in,
        shape="Str", notes="Stem Horiz EF", source_rule="rule_stem_horiz",
    )]


# ---------------------------------------------------------------------------
# SW2 — Stem wall vertical bars, each face (primary flexural steel)
# ACI 318-19 §11.7.3.1 (cantilever wall primary reinf.)
# Tension face = soil (back) side; EF layout conservatively.
# ---------------------------------------------------------------------------

def rule_stem_vert(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Stem vertical bars, each face.

    Qty = bars per face × 2 faces.
    One face: floor(usable_footing_length / vert_spacing) + 1 bars.
    Bar length = stem height + 90° hook at base (into footing) + 6 in top dev.
    """
    usable_len_in = (p.footing_length_ft * 12.0) - (2.0 * p.cover_in)
    qty_per_face = math.floor(usable_len_in / p.vert_spacing_in) + 1
    qty_total = qty_per_face * 2   # each face

    bot_hook_in = hook_add("std_90", p.vert_bar_size)
    bar_len_in = (p.stem_height_ft * 12.0) + bot_hook_in + 6.0

    log.step(f"Stem usable footing length = {usable_len_in:.1f} in → {qty_per_face} bars/face × 2 = {qty_total}")
    log.step(f"Bar length = {p.stem_height_ft * 12:.0f} + {bot_hook_in} hook + 6 top dev = {bar_len_in:.1f} in")
    log.result("SW2", f"{p.vert_bar_size} × {qty_total} @ {fmt_inches(bar_len_in)}")

    return [BarRow(
        mark="SW2", size=p.vert_bar_size, qty=qty_total, length_in=bar_len_in,
        shape="Str", notes="Stem Vert EF", source_rule="rule_stem_vert",
    )]


# ---------------------------------------------------------------------------
# TW1 — Toe bars (bottom of footing, toe side, transverse)
# ACI 318-19 §13.3.1 (footing flexural reinf.)
# Primary tension steel on bottom face under toe projection.
# ---------------------------------------------------------------------------

def rule_toe_bars(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Toe transverse bars at bottom of footing, toe side.

    Toe projection ≈ (footing_length - stem_thick) / 2 assuming equal toe/heel.
    Qty spans the footing length (longitudinal direction of wall).
    Bar length = toe projection + stem thickness + cover development.
    """
    footing_len_in = p.footing_length_ft * 12.0
    # Number of bars across the footing length at given spacing
    qty = math.floor((footing_len_in - 2.0 * p.cover_in) / p.footing_spacing_in) + 1

    # Toe bar spans from toe edge into and under the stem — full footing width
    # Hook at free end for development; straight at heel side
    hook_in = hook_add("std_90", p.footing_bar_size)
    bar_len_in = footing_len_in - p.cover_in + hook_in  # extend to toe edge with hook

    log.step(f"Footing length = {footing_len_in:.0f} in → {qty} bars at {p.footing_spacing_in} in spacing")
    log.step(f"Toe bar length = {footing_len_in:.0f} - {p.cover_in} + {hook_in} hook = {bar_len_in:.1f} in")
    log.result("TW1", f"{p.footing_bar_size} × {qty} @ {fmt_inches(bar_len_in)}")

    return [BarRow(
        mark="TW1", size=p.footing_bar_size, qty=qty, length_in=bar_len_in,
        shape="Str", notes="Toe Bars Bot", source_rule="rule_toe_bars",
    )]


# ---------------------------------------------------------------------------
# HW1 — Heel bars (bottom of footing, heel side, transverse)
# ACI 318-19 §13.3.1 (footing flexural reinf.)
# Primary tension steel on bottom face over heel projection.
# ---------------------------------------------------------------------------

def rule_heel_bars(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Heel transverse bars at bottom of footing, heel side.

    Same count as toe bars; heel bars are top face bars over heel projection.
    Bar length = footing depth - 2×cover (transverse through depth) + hooks.
    Conservative: same layout as toe bars, top of footing slab.
    """
    footing_len_in = p.footing_length_ft * 12.0
    qty = math.floor((footing_len_in - 2.0 * p.cover_in) / p.footing_spacing_in) + 1

    hook_in = hook_add("std_90", p.footing_bar_size)
    # Heel bar also runs footing length — sits on top face, hooks at heel free end
    bar_len_in = footing_len_in - p.cover_in + hook_in

    log.step(f"Heel bars: {qty} @ {p.footing_spacing_in} in spacing across footing length")
    log.step(f"Heel bar length = {footing_len_in:.0f} - {p.cover_in} + {hook_in} hook = {bar_len_in:.1f} in")
    log.result("HW1", f"{p.footing_bar_size} × {qty} @ {fmt_inches(bar_len_in)}")

    return [BarRow(
        mark="HW1", size=p.footing_bar_size, qty=qty, length_in=bar_len_in,
        shape="Str", notes="Heel Bars Top", source_rule="rule_heel_bars",
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
    footing_len_in = p.footing_length_ft * 12.0
    qty = math.floor((footing_len_in - 2.0 * p.cover_in) / p.vert_spacing_in) + 1

    # Embed into footing: footing depth minus top cover
    embed_in = p.footing_depth_in - p.cover_in

    # Lap splice into stem: Class B = 1.3 × ld
    ld_in = development_length_tension(p.vert_bar_size, cover_in=p.cover_in)
    lap_in = math.ceil(1.3 * ld_in)

    bar_len_in = embed_in + lap_in

    log.step(f"Dowel qty = {qty} at {p.vert_spacing_in} in spacing across footing {footing_len_in:.0f} in")
    log.step(f"Embed = {embed_in:.1f} in  |  Class B lap = 1.3×{ld_in:.1f} = {lap_in} in")
    log.step(f"Total dowel length = {bar_len_in:.1f} in")
    log.result("DW1", f"{p.vert_bar_size} × {qty} @ {fmt_inches(bar_len_in)}")

    return [BarRow(
        mark="DW1", size=p.vert_bar_size, qty=qty, length_in=bar_len_in,
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
        log.step("Shear key = no — skipping KW1")
        return []

    footing_len_in = p.footing_length_ft * 12.0
    qty = math.floor((footing_len_in - 2.0 * p.cover_in) / p.footing_spacing_in) + 1

    # U-bar: two legs each = key_depth_in + cover; bend at bottom adds ~4db
    from vistadetail.engine.hooks import bar_diameter
    db = bar_diameter(p.footing_bar_size)
    leg_in = p.key_depth_in - p.cover_in
    bend_add_in = 4.0 * db  # inside bend radius allowance
    bar_len_in = (2.0 * leg_in) + bend_add_in
    bar_len_in = max(bar_len_in, 12.0)

    log.step(f"Shear key requested — key depth = {p.key_depth_in} in")
    log.step(f"U-bar qty = {qty}  |  leg = {leg_in:.1f} in × 2 + {bend_add_in:.2f} bend = {bar_len_in:.2f} in")
    log.result("KW1", f"{p.footing_bar_size} × {qty} @ {fmt_inches(bar_len_in)}")

    return [BarRow(
        mark="KW1", size=p.footing_bar_size, qty=qty, length_in=bar_len_in,
        shape="U", notes="Shear Key U-bars", source_rule="rule_shear_key",
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
    if p.cover_in < 2.0:
        log.warn(
            f"Cover {p.cover_in} in < 2.0 in minimum for retaining wall (ACI 318-19 §20.6.1.3)"
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
