"""
Rule functions for Drilled Shaft Cage (Vertical Cylinder) template.

Geometry: circular cage for drilled pier / caisson.
  - Vertical bars running full depth + bottom embedment
  - Standard hoops at uniform spacing over full depth
  - Optional seismic confinement zone at top (closer hoop spacing)

Hardcoded constants (removed from user inputs):
  EMBED_IN   = 6.0"    bottom embedment
  RING_BAR   = "#4"    hoop bar size
  LAP_FT     = 3.0     hoop lap length
  COVER_IN   = 3.0"    clear cover (ACI cast-against-earth)
  CONF_SPC   = 3.0"    confinement hoop spacing
  CONF_DEP   = 6.0"    confinement zone depth

Verified formulas (from gold barlists):
  vert_length  = cage_depth_in + EMBED_IN
  ring_OD_in   = hole_diameter_in - 2 × COVER_IN
  ring_circ_in = π × ring_OD_in
  ring_len_in  = ring_circ_in + LAP_FT×12
  std_qty      = floor(cage_depth_in / ring_spacing_in) + 1
  conf_qty     = floor(CONF_DEP / CONF_SPC) + 1  (when enabled)
"""

from __future__ import annotations

import math

from vistadetail.engine.reasoning_logger import ReasoningLogger
from vistadetail.engine.schema import BarRow, Params, fmt_inches


_PI = math.pi

# Hardcoded constants
_EMBED_IN  = 6.0
_RING_BAR  = "#4"
_LAP_FT    = 3.0
_COVER_IN  = 3.0
_CONF_SPC  = 3.0
_CONF_DEP  = 6.0


# ---------------------------------------------------------------------------
# V1 — vertical bars
# ---------------------------------------------------------------------------

def rule_cage_verticals(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Longitudinal bars running the full cage depth + bottom embed.

    Length = cage_depth_in + EMBED_IN (6")
    Qty    = vert_count  (input directly — set by drilled shaft design)
    Mark   = V1
    """
    depth_in  = p.cage_depth_ft * 12
    bar_len   = depth_in + _EMBED_IN
    qty       = int(p.vert_count)

    log.step(
        f"Vert bars (V1): length = {depth_in:.1f} + {_EMBED_IN} embed = {bar_len:.1f} in"
        f" = {fmt_inches(bar_len)}",
        detail="cage_depth_ft×12 + 6in embed",
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
        notes=f"cage verticals, {_EMBED_IN:.0f}in bot. embed",
        source_rule="rule_cage_verticals",
    )]


# ---------------------------------------------------------------------------
# H1 — standard hoops (uniform spacing over full depth)
# ---------------------------------------------------------------------------

def rule_cage_hoops_standard(p: Params, log: ReasoningLogger) -> list[BarRow]:
    """
    Circular hoops (rings) at uniform spacing over the full cage depth.

    OD        = hole_diameter_in - 2 × COVER_IN (3")
    circ      = π × OD
    ring_len  = circ + LAP_FT×12 (36")
    qty       = floor(cage_depth_in / ring_spacing_in) + 1
    Mark      = H1
    """
    depth_in  = p.cage_depth_ft * 12
    hole_in   = p.hole_diameter_ft * 12
    OD_in     = hole_in - 2 * _COVER_IN
    circ_in   = _PI * OD_in
    ring_len  = circ_in + _LAP_FT * 12
    qty       = math.floor(depth_in / p.ring_spacing_in) + 1

    log.step(
        f"Hoop OD = {hole_in:.1f} − 2×{_COVER_IN} cover = {OD_in:.1f} in = {fmt_inches(OD_in)}",
        detail="hole_diameter_in − 2×3in cover",
        source="CageRules",
    )
    log.step(
        f"Circ = π × {OD_in:.2f} = {circ_in:.2f} in",
        detail="π × OD_in",
        source="CageRules",
    )
    log.step(
        f"Ring length = {circ_in:.2f} + {_LAP_FT * 12:.1f} lap = {ring_len:.2f} in"
        f" = {fmt_inches(ring_len)}",
        detail="circ_in + 36in lap",
        source="CageRules",
    )
    log.step(
        f"Qty H1 = ⌊{depth_in:.1f} ÷ {p.ring_spacing_in}⌋ + 1 = {qty}",
        detail="floor(cage_depth_in / ring_spacing_in) + 1",
        source="CageRules",
    )
    log.result("H1", f"{_RING_BAR} × {qty} @ {fmt_inches(ring_len)} [hoop]",
               detail=f"std hoops @{int(p.ring_spacing_in)}oc", source="CageRules")

    return [BarRow(
        mark="H1",
        size=_RING_BAR,
        qty=qty,
        length_in=ring_len,
        shape="Rng",
        notes=f"hoops @{int(p.ring_spacing_in)}oc, OD={fmt_inches(OD_in)}, lap={fmt_inches(_LAP_FT*12)}",
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
    qty = floor(CONF_DEP / CONF_SPC) + 1  (floor(6/3)+1 = 3)
    Mark = H2
    """
    if not bool(p.has_confinement_zone):
        log.step(
            "No confinement zone — H2 skipped",
            detail="has_confinement_zone = False",
            source="CageRules",
        )
        return []

    hole_in   = p.hole_diameter_ft * 12
    OD_in     = hole_in - 2 * _COVER_IN
    circ_in   = _PI * OD_in
    ring_len  = circ_in + _LAP_FT * 12
    conf_in   = _CONF_DEP
    qty       = math.floor(conf_in / _CONF_SPC) + 1

    log.step(
        f"Confinement zone H2: top {conf_in:.1f} in @ {_CONF_SPC} in oc",
        detail=f"seismic confinement zone: first {fmt_inches(conf_in)} of cage",
        source="CageRules",
    )
    log.step(
        f"Qty H2 = ⌊{conf_in} ÷ {_CONF_SPC}⌋ + 1 = {qty}",
        detail="floor(6in / 3in) + 1 = 3",
        source="CageRules",
    )
    log.result("H2", f"{_RING_BAR} × {qty} @ {fmt_inches(ring_len)} [conf. hoop]",
               detail=f"confinement hoops @{int(_CONF_SPC)}oc top {fmt_inches(conf_in)}",
               source="CageRules")

    return [BarRow(
        mark="H2",
        size=_RING_BAR,
        qty=qty,
        length_in=ring_len,
        shape="Rng",
        notes=(
            f"confinement hoops @{int(_CONF_SPC)}oc, "
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
      - Cover 3 in (hardcoded, cast against earth)
      - Hoop spacing ≤ 18 in max (general stirrup limit)
      - Vert count ≥ 4 (minimum cage redundancy)
      - OD ≥ 6 in (structurally unreasonable below this)
    """
    hole_in  = p.hole_diameter_ft * 12
    OD_in    = hole_in - 2 * _COVER_IN

    log.ok(
        f"Cover {_COVER_IN} in (standard, cast against earth)  [ACI Table 20.6.1.3.1]",
        detail="ACI 318-19 Table 20.6.1.3.1",
        source="Validator",
    )

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

    if OD_in < 6.0:
        log.warn(
            f"Ring OD {OD_in:.1f} in < 6 in — cage may be too small to build",
            detail="Practical cage limit — verify hole diameter and cover",
            source="Validator",
        )
    else:
        log.ok(
            f"Ring OD {OD_in:.1f} in = {fmt_inches(OD_in)}  [geometry OK]",
            detail="OD = hole_diameter_in − 2×3in cover",
            source="Validator",
        )

    return []
