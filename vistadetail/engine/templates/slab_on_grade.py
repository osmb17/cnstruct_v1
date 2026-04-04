"""
Template: Slab on Grade  (v1.0)

Rectangular concrete slab placed directly on compacted subgrade.
Single reinforcing mat — bars each way (EW).

Generates:
  G1 — long-direction bars
  G2 — short-direction bars
  G3 — perimeter thickened-edge bars (optional)

Covers 7 PDFs in the clean_examples set:
  slabongrade.20x10by31x8, slabongrade.25x10by22x10,
  slabongrade.15-41x2by8-1x4, slabongrade.gmz.lapc.parkinglot07, etc.

Formulas (ACI 360R-10 / ACI 318-19):
  bar_length = span_dim_in - 2 × cover_in
  qty        = floor(perpendicular_dim_in / spacing_in)

Cover default: 1.5 in (not exposed to weather, ACI Table 20.6.1.3.1).
"""

from __future__ import annotations

from vistadetail.engine.schema import BAR_SIZES, InputField, Params
from vistadetail.engine.templates.base import BaseTemplate


class SlabOnGradeTemplate(BaseTemplate):
    name: str = "Slab on Grade"
    version: str = "1.0"
    description: str = (
        "Rectangular slab on compacted subgrade. "
        "Single EW mat — G1 (long) and G2 (short) bars. "
        "Optional thickened perimeter edge beam (G3)."
    )

    def __init__(self):
        super().__init__()
        self.name        = "Slab on Grade"
        self.version     = "1.0"
        self.description = (
            "Rectangular slab on compacted subgrade. "
            "Single EW mat — G1 (long) and G2 (short) bars. "
            "Optional thickened perimeter edge beam (G3)."
        )

        self.inputs = [
            # ── Plan dimensions ───────────────────────────────────────────
            InputField(
                "slab_length_ft", float,
                label="Slab Length (ft)  — long side",
                min=2.0, max=500.0, default=20.0,
                hint="Longer plan dimension in feet",
            ),
            InputField(
                "slab_width_ft", float,
                label="Slab Width (ft)  — short side",
                min=2.0, max=500.0, default=10.0,
                hint="Shorter plan dimension in feet",
            ),
            InputField(
                "slab_thickness_in", float,
                label="Slab Thickness (in)",
                min=3.5, max=24.0, default=5.0,
                hint="Nominal slab thickness (used for ACI spacing check)",
            ),
            # ── Mat reinforcement ─────────────────────────────────────────
            InputField(
                "bar_size", str,
                label="Bar Size",
                choices=BAR_SIZES, default="#4",
                hint="Same bar size used both ways (EW)",
            ),
            InputField(
                "spacing_in", float,
                label="Spacing (in)  — both ways",
                min=6.0, max=18.0, default=12.0,
                hint="Center-to-center bar spacing EW",
            ),
            InputField(
                "cover_in", float,
                label="Clear Cover (in)",
                min=1.5, max=4.0, default=1.5,
                hint="1.5 in for interior slab not exposed to weather (ACI Table 20.6.1.3.1)",
            ),
            # ── Thickened edge beam (optional) ────────────────────────────
            InputField(
                "has_edge_beam", float,
                label="Thickened Edge Beam? (0=No 1=Yes)",
                min=0.0, max=1.0, default=0.0,
                hint="1 = add perimeter edge bars (G3) for thickened edge / haunch",
            ),
            InputField(
                "edge_bar_size", str,
                label="Edge Bar Size  (if edge beam)",
                choices=BAR_SIZES, default="#4",
                hint="Bar size for thickened perimeter edge",
            ),
            InputField(
                "edge_bars_per_side", float,
                label="Edge Bars per Side  (if edge beam)",
                min=1.0, max=8.0, default=2.0,
                hint="Number of bars per side in the thickened edge (e.g. 2 = top + bottom)",
            ),
        ]

        self.rules = [
            "rule_sog_long_bars",
            "rule_sog_short_bars",
            "rule_sog_edge_bars",
            "rule_validate_sog",
        ]

    def evaluate_triggers(self, params: Params) -> list[str]:
        triggers: list[str] = []
        if params.spacing_in > 15.0:
            triggers.append("sog_spacing_near_max")
        if bool(params.has_edge_beam):
            triggers.append("sog_thickened_edge_present")
        area = params.slab_length_ft * params.slab_width_ft
        if area > 2000.0:
            triggers.append("large_sog_contraction_joints_required")
        return triggers


TEMPLATE = SlabOnGradeTemplate()
