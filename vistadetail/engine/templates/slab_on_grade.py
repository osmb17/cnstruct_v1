"""
Template: Slab on Grade  (v2.0)

Rectangular concrete slab placed directly on compacted subgrade.
#4@12oc EW mat. G1 (long) and G2 (short) bars.

Covers 7 PDFs in the clean_examples set:
  slabongrade.20x10by31x8, slabongrade.25x10by22x10,
  slabongrade.15-41x2by8-1x4, slabongrade.gmz.lapc.parkinglot07, etc.

Formulas (ACI 360R-10 / ACI 318-19):
  bar_length = span_dim_in - 2 × 1.5 (cover)
  qty        = floor(perpendicular_dim_in / 12.0 (spacing))
"""

from __future__ import annotations

from vistadetail.engine.schema import InputField, Params
from vistadetail.engine.templates.base import BaseTemplate


class SlabOnGradeTemplate(BaseTemplate):
    name: str = "Slab on Grade"
    version: str = "2.0"
    description: str = (
        "Rectangular slab on compacted subgrade. "
        "#4@12oc EW mat. G1 (long) and G2 (short) bars."
    )

    def __init__(self):
        super().__init__()
        self.name        = "Slab on Grade"
        self.version     = "2.0"
        self.description = (
            "Rectangular slab on compacted subgrade. "
            "#4@12oc EW mat. G1 (long) and G2 (short) bars."
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
        ]

        self.rules = [
            "rule_sog_long_bars",
            "rule_sog_short_bars",
            "rule_sog_edge_bars",
            "rule_validate_sog",
        ]

    def evaluate_triggers(self, params: Params) -> list[str]:
        triggers: list[str] = []
        area = params.slab_length_ft * params.slab_width_ft
        if area > 2000.0:
            triggers.append("large_sog_contraction_joints_required")
        return triggers


TEMPLATE = SlabOnGradeTemplate()
