"""
Template: Drilled Shaft Cage  (v1.0)

Circular rebar cage for a drilled pier / caisson.

Generates:
  V1 — vertical bars (longitudinal)
  H1 — standard hoops (full depth, uniform spacing)
  H2 — confinement hoops (optional seismic zone, top of cage, closer spacing)

Covers 24 PDFs in the clean_examples set:
  cage.5x3.*, cage.layout.6ft.tall.3ft.wide, ACI.cages, pacifictide.*.pdf, etc.

Formulas (verified against gold barlists):
  vert_length  = cage_depth_in + embed_in
  ring_OD      = hole_diameter_in - 2 × cover_in
  ring_length  = π × OD + lap_in
  std_hoop_qty = floor(cage_depth_in / ring_spacing_in) + 1
  conf_hoop_qty = floor(confinement_depth_in / conf_spacing_in) + 1  (when enabled)
"""

from __future__ import annotations

from vistadetail.engine.schema import BAR_SIZES, InputField, Params
from vistadetail.engine.templates.base import BaseTemplate


class CageTemplate(BaseTemplate):
    name: str = "Drilled Shaft Cage"
    version: str = "1.0"
    description: str = (
        "Circular drilled pier / caisson cage. "
        "Vertical bars + spiral/ring hoops. "
        "Optional seismic confinement zone at top."
    )

    def __init__(self):
        super().__init__()
        self.name        = "Drilled Shaft Cage"
        self.version     = "1.0"
        self.description = (
            "Circular drilled pier / caisson cage. "
            "Vertical bars + spiral/ring hoops. "
            "Optional seismic confinement zone at top."
        )

        self.inputs = [
            # ── Cage geometry ─────────────────────────────────────────────
            InputField(
                "cage_depth_ft", float,
                label="Cage Depth (ft)",
                min=2.0, max=200.0, default=5.0,
                hint="Total cage depth (length of vertical bars before embed add-on)",
            ),
            InputField(
                "hole_diameter_ft", float,
                label="Drilled Hole Diameter (ft)",
                min=0.5, max=12.0, default=3.0,
                hint="Nominal borehole diameter in feet (ring OD = this - 2×cover)",
            ),
            # ── Vertical bars ─────────────────────────────────────────────
            InputField(
                "vert_bar_size", str,
                label="Vertical Bar Size",
                choices=BAR_SIZES, default="#5",
                hint="Size of the longitudinal vertical bars",
            ),
            InputField(
                "vert_count", float,
                label="Number of Vertical Bars",
                min=4.0, max=40.0, default=4.0,
                hint="Count of vertical bars around cage perimeter (must be ≥ 4)",
            ),
            InputField(
                "embed_in", float,
                label="Bottom Embedment (in)",
                min=0.0, max=36.0, default=6.0,
                hint="Extra length added below cage depth for bottom embedment / splice",
            ),
            # ── Hoops ─────────────────────────────────────────────────────
            InputField(
                "ring_bar_size", str,
                label="Hoop / Ring Bar Size",
                choices=BAR_SIZES, default="#5",
                hint="Size of the circular hoop bars",
            ),
            InputField(
                "ring_spacing_in", float,
                label="Standard Hoop Spacing (in)",
                min=3.0, max=18.0, default=16.0,
                hint="Center-to-center spacing of standard hoops (full cage depth)",
            ),
            InputField(
                "lap_ft", float,
                label="Hoop Lap Length (ft)",
                min=1.0, max=6.0, default=3.0,
                hint="Lap length added to ring circumference for bar overlap",
            ),
            InputField(
                "cover_in", float,
                label="Clear Cover (in)",
                min=2.0, max=6.0, default=3.0,
                hint="3 in for drilled shafts cast against earth (ACI Table 20.6.1.3.1)",
            ),
            # ── Seismic confinement zone (optional) ───────────────────────
            InputField(
                "has_confinement_zone", float,    # stored as float 0/1 for Excel compat
                label="Seismic Confinement Zone? (0=No 1=Yes)",
                min=0.0, max=1.0, default=0.0,
                hint="1 = add closely-spaced hoops at top of cage (seismic requirement)",
            ),
            InputField(
                "conf_spacing_in", float,
                label="Confinement Hoop Spacing (in)",
                min=1.0, max=6.0, default=3.0,
                hint="Close hoop spacing within the seismic confinement zone",
            ),
            InputField(
                "confinement_depth_in", float,
                label="Confinement Zone Depth (in)",
                min=3.0, max=36.0, default=6.0,
                hint="Depth of the seismic confinement zone at the top of the cage",
            ),
        ]

        self.rules = [
            "rule_cage_verticals",
            "rule_cage_hoops_standard",
            "rule_cage_hoops_confinement",
            "rule_validate_cage",
        ]

    def evaluate_triggers(self, params: Params) -> list[str]:
        triggers: list[str] = []
        if params.cage_depth_ft > 50.0:
            triggers.append("deep_cage_splice_required")
        if bool(params.has_confinement_zone):
            triggers.append("seismic_confinement_zone_present")
        ratio = params.cage_depth_ft / max(params.hole_diameter_ft, 0.1)
        if ratio > 15.0:
            triggers.append("high_slenderness_cage")
        return triggers


TEMPLATE = CageTemplate()
