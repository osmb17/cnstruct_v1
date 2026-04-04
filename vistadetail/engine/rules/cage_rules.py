"""
Rule functions for Drilled Shaft Cage (Vertical Cylinder) template.

Geometry: circular cage for drilled pier / caisson.
  - Vertical bars running full depth + bottom embedment
  - Standard hoops at uniform spacing over full depth
  - Optional seismic confinement zone at top (closer hoop spacing)

Verified formulas (from gold barlists):
  vert_length  = cage_depth_in + embed_in
  ring_OD_in   = hole_diameter_in - 2 × cover_in
  ring_circ_in = π × ring_OD_in
  ring_len_in  = ring_circ_in + lap_in
  std_qty      = floor(cage_depth_in / ring_spacing_in) + 1
  conf_qty     = floor(confinement_depth_in / conf_spacing_in) + 1  (when enabled)

Examples confirmed from cage PDFs:
  5ft deep × 3ft hole, rings @16oc → 4 rings (floor(60/16)+1=4) ✓
  OD = 36 - 2×3 = 30in = 2'-6" ✓,  ring_len = π×30 + 36(lap) = 94.2+36 = 130.2in ✓
"""

from __future__ import annotations

import math

from vistadetail.engine.reasoning_logger import ReasoningLogger
from vistadetail.engine.schema import BarRow, Params, fmt_inches


_PI = math.pi


# ---------------------------------------------------------------------------
# V1 — vertical bars
# ---------------------------------------------------------------------------

def rule_cage_verticals(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Longitudinal bars running the full cage depth + bottom embed.

    Length = cage_depth_in + embed_in
    Qty    = vert_count  (input directly — set by drilled shaft design)
    Mark   = V1
    """
    depth_in  = p.cage_depth_ft * 12
    bar_len   = depth_in + p.embed_in
    qty       = int(p.vert_count)

    log.step(
        f"Vert bars (V1): length = {depth_in:.1f} + {p.embed_in} embed = {bar_len:.1f} in"
        f" = {fmt_inches(bar_len)}",
        detail="cage_depth_ft×12 + embed_in",
        source="CageRules",
    )
    log.step(
        f"Qty V1 = {qty}  (vert_count input)",
        detail="set by drilled shaft design / detailing standard",
        source="CageRules",
    )
    log.result("V1", f"{p.vert_bar_size} × {qty} @ {fmt_inches(bar_len)} [vert]",
               detail="longitudinal cage bars", source="CageRules")

    return [BarRow(
        mark="V1",
        size=p.vert_bar_size,
        qty=qty,
        length_in=bar_len,
        shape="Str",
        notes=f"cage verticals, {p.embed_in:.0f}in bot. embed",
        source_rule="rule_cage_verticals",
    )]


# ---------------------------------------------------------------------------
# H1 — standard hoops (uniform spacing over full depth)
# ---------------------------------------------------------------------------

def rule_cage_hoops_standard(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Circular hoops (rings) at uniform spacing over the full cage depth.

    OD        = hole_diameter_in - 2 × cover_in
    circ      = π × OD
    ring_len  = circ + lap_in
    qty       = floor(cage_depth_in / ring_spacing_in) + 1
    Mark      = H1
    """
    depth_in  = p.cage_depth_ft * 12
    hole_in   = p.hole_diameter_ft * 12
    OD_in     = hole_in - 2 * p.cover_in
    circ_in   = _PI * OD_in
    ring_len  = circ_in + p.lap_ft * 12
    qty       = math.floor(depth_in / p.ring_spacing_in) + 1

    log.step(
        f"Hoop OD = {hole_in:.1f} − 2×{p.cover_in} cover = {OD_in:.1f} in = {fmt_inches(OD_in)}",
        detail="hole_diameter_in − 2×cover_in",
        source="CageRules",
    )
    log.step(
        f"Circ = π × {OD_in:.2f} = {circ_in:.2f} in",
        detail="π × OD_in",
        source="CageRules",
    )
    log.step(
        f"Ring length = {circ_in:.2f} + {p.lap_ft * 12:.1f} lap = {ring_len:.2f} in"
        f" = {fmt_inches(ring_len)}",
        detail="circ_in + lap_ft×12",
        source="CageRules",
    )
    log.step(
        f"Qty H1 = ⌊{depth_in:.1f} ÷ {p.ring_spacing_in}⌋ + 1 = {qty}",
        detail="floor(cage_depth_in / ring_spacing_in) + 1",
        source="CageRules",
    )
    log.result("H1", f"{p.ring_bar_size} × {qty} @ {fmt_inches(ring_len)} [hoop]",
               detail=f"std hoops @{int(p.ring_spacing_in)}oc", source="CageRules")

    return [BarRow(
        mark="H1",
        size=p.ring_bar_size,
        qty=qty,
        length_in=ring_len,
        shape="Rng",
        notes=f"hoops @{int(p.ring_spacing_in)}oc, OD={fmt_inches(OD_in)}, lap={fmt_inches(p.lap_ft*12)}",
        source_rule="rule_cage_hoops_standard",
    )]


# ---------------------------------------------------------------------------
# H2 — confinement hoops (seismic zone, top of cage, closer spacing)
# ---------------------------------------------------------------------------

def rule_cage_hoops_confinement(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Extra close-spaced hoops within the seismic confinement zone at the top of the cage.
    Only generated when has_confinement_zone is True.

    Uses the same OD / ring length as H1.
    qty = floor(confinement_depth_in / conf_spacing_in) + 1
    Mark = H2

    These are IN ADDITION to the standard H1 hoops (the confinement zone gets
    the extra closely-spaced rings; H1 covers the full depth at standard spacing).
    """
    if not bool(p.has_confinement_zone):
        log.step(
            "No confinement zone — H2 skipped",
            detail="has_confinement_zone = False",
            source="CageRules",
        )
        return []

    hole_in   = p.hole_diameter_ft * 12
    OD_in     = hole_in - 2 * p.cover_in
    circ_in   = _PI * OD_in
    ring_len  = circ_in + p.lap_ft * 12
    conf_in   = p.confinement_depth_in
    qty       = math.floor(conf_in / p.conf_spacing_in) + 1

    log.step(
        f"Confinement zone H2: top {conf_in:.1f} in @ {p.conf_spacing_in} in oc",
        detail=f"seismic confinement zone: first {fmt_inches(conf_in)} of cage",
        source="CageRules",
    )
    log.step(
        f"Qty H2 = ⌊{conf_in} ÷ {p.conf_spacing_in}⌋ + 1 = {qty}",
        detail="floor(confinement_depth_in / conf_spacing_in) + 1",
        source="CageRules",
    )
    log.result("H2", f"{p.ring_bar_size} × {qty} @ {fmt_inches(ring_len)} [conf. hoop]",
               detail=f"confinement hoops @{int(p.conf_spacing_in)}oc top {fmt_inches(conf_in)}",
               source="CageRules")

    return [BarRow(
        mark="H2",
        size=p.ring_bar_size,
        qty=qty,
        length_in=ring_len,
        shape="Rng",
        notes=(
            f"confinement hoops @{int(p.conf_spacing_in)}oc, "
            f"top {fmt_inches(conf_in)}, OD={fmt_inches(OD_in)}"
        ),
        source_rule="rule_cage_hoops_confinement",
    )]


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def rule_validate_cage(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Checks:
      - ACI 318-19 §26.6.2.2  cover ≥ 3 in (cast against earth)
      - Hoop spacing ≤ 18 in max (general stirrup limit)
      - Vert count ≥ 4 (minimum cage redundancy)
      - OD ≥ 6 in (structurally unreasonable below this)
    """
    depth_in = p.cage_depth_ft * 12
    hole_in  = p.hole_diameter_ft * 12
    OD_in    = hole_in - 2 * p.cover_in

    # Cover check
    if p.cover_in < 3.0:
        log.warn(
            f"Cover {p.cover_in} in < 3 in — drilled shafts cast against earth require ≥ 3 in",
            detail="ACI 318-19 Table 20.6.1.3.1 (cast against earth)",
            source="Validator",
        )
    else:
        log.ok(
            f"Cover {p.cover_in} in ≥ 3 in  [ACI Table 20.6.1.3.1]",
            detail="ACI 318-19 Table 20.6.1.3.1",
            source="Validator",
        )

    # Hoop spacing check
    if p.ring_spacing_in > 18.0:
        log.warn(
            f"Ring spacing {p.ring_spacing_in} in > 18 in — check ACI §26.7.2",
            detail="ACI 318-19 §26.7.2 — stirrup/tie max spacing",
            source="Validator",
        )
    else:
        log.ok(
            f"Ring spacing {p.ring_spacing_in} in ≤ 18 in  [ACI §26.7.2]",
            detail="ACI 318-19 §26.7.2",
            source="Validator",
        )

    # Min vert count
    if int(p.vert_count) < 4:
        log.warn(
            f"Vert count {int(p.vert_count)} < 4 — practical cage minimum is 4 bars",
            detail="ACI 318-19 §18.8.5 (min bars for ductility)",
            source="Validator",
        )
    else:
        log.ok(
            f"Vert count {int(p.vert_count)} ≥ 4  [ACI §18.8.5]",
            detail="ACI 318-19 §18.8.5",
            source="Validator",
        )

    # OD sanity
    if OD_in < 6.0:
        log.warn(
            f"Ring OD {OD_in:.1f} in < 6 in — cage may be too small to build",
            detail="Practical cage limit — verify hole diameter and cover",
            source="Validator",
        )
    else:
        log.ok(
            f"Ring OD {OD_in:.1f} in = {fmt_inches(OD_in)}  [geometry OK]",
            detail="OD = hole_diameter_in − 2×cover_in",
            source="Validator",
        )

    return []
