"""
Rule functions for Junction Structure template.

A Caltrans junction structure (junction box) is a cast-in-place rectangular
concrete box that connects drainage pipes of different sizes or orientations.

Components:
  JW1 — Long wall horizontal bars (EF, 2 long walls)
  JW2 — Long wall vertical bars (EF, 2 long walls)
  SW1 — Short wall horizontal bars (EF, 2 short walls)
  SW2 — Short wall vertical bars (EF, 2 short walls)
  JF1 — Floor long bars (bottom mat)
  JF2 — Floor short bars (bottom mat)

Geometry:
  - inside_length_ft × inside_width_ft × inside_depth_ft = inner clear dimensions
  - wall_thick_in = uniform wall thickness all 4 sides
  - floor_thick_in = floor slab thickness
  - Outside dimensions auto-computed: OL = inside_length + 2×wall_thick/12
"""

from __future__ import annotations

import math

from vistadetail.engine.hooks import hook_add
from vistadetail.engine.reasoning_logger import ReasoningLogger
from vistadetail.engine.schema import BarRow, Params, fmt_inches


def rule_junction_long_wall_horiz(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Horizontal bars in the two long walls, each face.

    2 long walls × 2 faces per wall.
    Length spans the full outside length of the structure minus cover each end.
    """
    outside_len_in = (p.inside_length_ft * 12) + (2 * p.wall_thick_in)
    bar_len_in     = outside_len_in - (2 * p.cover_in)
    usable_h_in    = (p.inside_depth_ft * 12) - (2 * p.cover_in)
    qty_per_face   = math.floor(usable_h_in / p.horiz_spacing_in) + 1
    qty            = qty_per_face * 2 * 2   # 2 faces × 2 long walls

    log.step(
        f"Long wall horiz: outside length = {outside_len_in:.0f} in  "
        f"bar length = {bar_len_in:.1f} in = {fmt_inches(bar_len_in)}",
        source="JunctionRules",
    )
    log.step(
        f"Qty = {qty_per_face} courses × 2 faces × 2 walls = {qty}",
        source="JunctionRules",
    )
    log.result("JW1", f"{p.wall_bar_size} × {qty} @ {fmt_inches(bar_len_in)}", source="JunctionRules")

    return [BarRow(
        mark="JW1", size=p.wall_bar_size, qty=qty, length_in=bar_len_in,
        shape="Str", notes="Long wall horiz EF (2 walls)",
        source_rule="rule_junction_long_wall_horiz",
    )]


def rule_junction_long_wall_vert(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Vertical bars in the two long walls, each face.

    Length = inside_depth + bottom hook + 6 in top development.
    """
    usable_len_in  = (p.inside_length_ft * 12) - (2 * p.cover_in)
    qty_per_face   = math.floor(usable_len_in / p.vert_spacing_in) + 1
    qty            = qty_per_face * 2 * 2   # 2 faces × 2 long walls
    bot_hook_in    = hook_add("std_90", p.wall_bar_size)
    bar_len_in     = (p.inside_depth_ft * 12) + bot_hook_in + 6.0

    log.step(
        f"Long wall vert: usable length = {usable_len_in:.1f} in  "
        f"→ {qty_per_face} cols/face × 2 faces × 2 walls = {qty}",
        source="JunctionRules",
    )
    log.step(
        f"Bar length = {p.inside_depth_ft * 12:.0f} + {bot_hook_in} hook + 6 stub "
        f"= {bar_len_in:.1f} in = {fmt_inches(bar_len_in)}",
        source="JunctionRules",
    )
    log.result("JW2", f"{p.wall_bar_size} × {qty} @ {fmt_inches(bar_len_in)}", source="JunctionRules")

    return [BarRow(
        mark="JW2", size=p.wall_bar_size, qty=qty, length_in=bar_len_in,
        shape="Str", notes="Long wall vert EF (2 walls)",
        source_rule="rule_junction_long_wall_vert",
    )]


def rule_junction_short_wall_horiz(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Horizontal bars in the two short walls, each face.

    Short walls fit between the long walls — bar length = inside_width minus cover.
    """
    bar_len_in   = (p.inside_width_ft * 12) - (2 * p.cover_in)
    usable_h_in  = (p.inside_depth_ft * 12) - (2 * p.cover_in)
    qty_per_face = math.floor(usable_h_in / p.horiz_spacing_in) + 1
    qty          = qty_per_face * 2 * 2   # 2 faces × 2 short walls

    log.step(
        f"Short wall horiz: bar length = {p.inside_width_ft * 12:.0f} − 2×{p.cover_in} "
        f"= {bar_len_in:.1f} in = {fmt_inches(bar_len_in)}",
        source="JunctionRules",
    )
    log.step(f"Qty = {qty_per_face} × 2 faces × 2 walls = {qty}", source="JunctionRules")
    log.result("SW1", f"{p.wall_bar_size} × {qty} @ {fmt_inches(bar_len_in)}", source="JunctionRules")

    return [BarRow(
        mark="SW1", size=p.wall_bar_size, qty=qty, length_in=bar_len_in,
        shape="Str", notes="Short wall horiz EF (2 walls)",
        source_rule="rule_junction_short_wall_horiz",
    )]


def rule_junction_short_wall_vert(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Vertical bars in the two short walls, each face.
    """
    usable_w_in  = (p.inside_width_ft * 12) - (2 * p.cover_in)
    qty_per_face = math.floor(usable_w_in / p.vert_spacing_in) + 1
    qty          = qty_per_face * 2 * 2   # 2 faces × 2 short walls
    bot_hook_in  = hook_add("std_90", p.wall_bar_size)
    bar_len_in   = (p.inside_depth_ft * 12) + bot_hook_in + 6.0

    log.step(
        f"Short wall vert: usable width = {usable_w_in:.1f} in  "
        f"→ {qty_per_face} cols/face × 2 faces × 2 walls = {qty}",
        source="JunctionRules",
    )
    log.result("SW2", f"{p.wall_bar_size} × {qty} @ {fmt_inches(bar_len_in)}", source="JunctionRules")

    return [BarRow(
        mark="SW2", size=p.wall_bar_size, qty=qty, length_in=bar_len_in,
        shape="Str", notes="Short wall vert EF (2 walls)",
        source_rule="rule_junction_short_wall_vert",
    )]


def rule_junction_floor_long(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Floor slab bars spanning the long direction.

    Run full outside length of structure minus cover each end.
    Qty spaced across the inside width.
    """
    outside_len_in = (p.inside_length_ft * 12) + (2 * p.wall_thick_in)
    bar_len_in     = outside_len_in - (2 * p.cover_in)
    qty            = math.floor((p.inside_width_ft * 12) / p.floor_spacing_in) + 1

    log.step(
        f"Floor long: outside length = {outside_len_in:.0f} in  "
        f"bar = {bar_len_in:.1f} in = {fmt_inches(bar_len_in)}",
        source="JunctionRules",
    )
    log.step(f"Qty = ⌊{p.inside_width_ft * 12:.0f}/{p.floor_spacing_in}⌋ + 1 = {qty}", source="JunctionRules")
    log.result("JF1", f"{p.floor_bar_size} × {qty} @ {fmt_inches(bar_len_in)}", source="JunctionRules")

    return [BarRow(
        mark="JF1", size=p.floor_bar_size, qty=qty, length_in=bar_len_in,
        shape="Str", notes="Floor long bars",
        source_rule="rule_junction_floor_long",
    )]


def rule_junction_floor_short(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Floor slab bars spanning the short direction.

    Length = inside_width minus cover.
    Qty spaced along inside length.
    """
    bar_len_in = (p.inside_width_ft * 12) - (2 * p.cover_in)
    qty        = math.floor((p.inside_length_ft * 12) / p.floor_spacing_in) + 1

    log.step(
        f"Floor short: length = {p.inside_width_ft * 12:.0f} − 2×{p.cover_in} "
        f"= {bar_len_in:.1f} in = {fmt_inches(bar_len_in)}",
        source="JunctionRules",
    )
    log.step(f"Qty = ⌊{p.inside_length_ft * 12:.0f}/{p.floor_spacing_in}⌋ + 1 = {qty}", source="JunctionRules")
    log.result("JF2", f"{p.floor_bar_size} × {qty} @ {fmt_inches(bar_len_in)}", source="JunctionRules")

    return [BarRow(
        mark="JF2", size=p.floor_bar_size, qty=qty, length_in=bar_len_in,
        shape="Str", notes="Floor short bars",
        source_rule="rule_junction_floor_short",
    )]


def rule_validate_junction(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """Validate junction structure geometry and cover."""
    if p.cover_in < 2.0:
        log.warn(f"Cover {p.cover_in} in < 2 in minimum for junction structure")
    wall_max_sp = min(3 * p.wall_thick_in, 18.0)
    if p.horiz_spacing_in > wall_max_sp:
        log.warn(
            f"Horiz spacing {p.horiz_spacing_in} in > ACI max {wall_max_sp} in "
            f"for {p.wall_thick_in} in wall (ACI §24.3.2)"
        )
    if p.inside_depth_ft < 2.0:
        log.warn("Inside depth < 2 ft — verify access requirements for maintenance")
    return []
