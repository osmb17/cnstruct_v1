"""
Template: Fuel Foundation  (v2.0)

Rectangular concrete mat foundation for fuel tanks, fuel disconnect panels,
and similar utility equipment requiring a robust cast-against-earth base.

Always double mat: F1 + F2 (bottom) + F3 + F4 (top).
#5@12oc, 3\" cover.

Covers 2 PDFs in the clean_examples set:
  fueldisconnectfoundation.clean
  fueltankfoundationseamair.clean

Formulas (ACI 318-19 / ACI 360R-10):
  bar_length = span_dim_in - 2 × 3.0 (cover)
  qty        = floor(perpendicular_dim_in / 12.0 (spacing))
"""

from __future__ import annotations

from vistadetail.engine.schema import InputField, Params
from vistadetail.engine.templates.base import BaseTemplate


class FuelFoundationTemplate(BaseTemplate):
    name: str = "Fuel Foundation"
    version: str = "2.0"
    description: str = (
        "Fuel storage foundation. #5@12oc double mat (top + bottom), 3\" cover."
    )

    def __init__(self):
        super().__init__()
        self.name        = "Fuel Foundation"
        self.version     = "2.0"
        self.description = (
            "Fuel storage foundation. #5@12oc double mat (top + bottom), 3\" cover."
        )

        self.inputs = [
            InputField(
                "fdn_length_ft", float,
                label="Foundation Length (ft)  — long side",
                min=1.0, max=200.0, default=10.0,
                hint="Longer plan dimension in feet",
            ),
            InputField(
                "fdn_width_ft", float,
                label="Foundation Width (ft)  — short side",
                min=1.0, max=200.0, default=6.0,
                hint="Shorter plan dimension in feet",
            ),
            InputField(
                "fdn_thickness_in", float,
                label="Foundation Thickness (in)",
                min=6.0, max=36.0, default=10.0,
                hint="Typical fuel foundation: 8–12 in",
            ),
        ]

        self.rules = [
            "rule_fuel_bottom_long",
            "rule_fuel_bottom_short",
            "rule_fuel_top_long",
            "rule_fuel_top_short",
            "rule_validate_fuel_foundation",
        ]

    def evaluate_triggers(self, params: Params) -> list[str]:
        triggers: list[str] = []
        area = params.fdn_length_ft * params.fdn_width_ft
        if area > 300.0:
            triggers.append("large_fuel_foundation_verify_structural_design")
        return triggers


TEMPLATE = FuelFoundationTemplate()
