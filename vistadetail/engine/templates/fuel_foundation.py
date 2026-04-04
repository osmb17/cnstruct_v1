"""
Template: Fuel Foundation  (v1.0)

Rectangular concrete mat foundation for fuel tanks, fuel disconnect panels,
and similar utility equipment requiring a robust cast-against-earth base.

Single or double mat configuration:
  Single: F1 (long) + F2 (short)
  Double: F1 + F2 (bottom) + F3 + F4 (top)

Covers 2 PDFs in the clean_examples set:
  fueldisconnectfoundation.clean
  fueltankfoundationseamair.clean

Formulas (ACI 318-19 / ACI 360R-10):
  bar_length = span_dim_in - 2 × cover_in
  qty        = floor(perpendicular_dim_in / spacing_in)

Cover default: 3.0 in (cast against earth, ACI Table 20.6.1.3.1).
"""

from __future__ import annotations

from vistadetail.engine.schema import BAR_SIZES, InputField, Params
from vistadetail.engine.templates.base import BaseTemplate


class FuelFoundationTemplate(BaseTemplate):
    name: str = "Fuel Foundation"
    version: str = "1.0"
    description: str = (
        "Rectangular mat foundation for fuel tanks and disconnect panels. "
        "Single or double mat (F1/F2 bottom, F3/F4 top). "
        "Cover default 3 in per ACI cast-against-earth requirement."
    )

    def __init__(self):
        super().__init__()
        self.name        = "Fuel Foundation"
        self.version     = "1.0"
        self.description = (
            "Rectangular mat foundation for fuel tanks and disconnect panels. "
            "Single or double mat (F1/F2 bottom, F3/F4 top). "
            "Cover default 3 in per ACI cast-against-earth requirement."
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
            InputField(
                "bar_size", str,
                label="Bar Size  (bottom mat)",
                choices=BAR_SIZES, default="#5",
                hint="Bar size for bottom mat, both directions",
            ),
            InputField(
                "spacing_in", float,
                label="Spacing (in)  — bottom mat, both ways",
                min=6.0, max=18.0, default=12.0,
                hint="Center-to-center bar spacing EW, bottom mat",
            ),
            InputField(
                "cover_in", float,
                label="Clear Cover (in)",
                min=2.0, max=6.0, default=3.0,
                hint="3 in for cast against earth (ACI Table 20.6.1.3.1)",
            ),
            InputField(
                "has_top_mat", float,
                label="Top Mat? (0=No 1=Yes)",
                min=0.0, max=1.0, default=1.0,
                hint="1 = double mat with F3/F4 top bars (typical for fuel foundations)",
            ),
            InputField(
                "top_bar_size", str,
                label="Top Bar Size  (if double mat)",
                choices=BAR_SIZES, default="#5",
                hint="Bar size for top mat, both directions",
            ),
            InputField(
                "top_spacing_in", float,
                label="Top Spacing (in)  (if double mat)",
                min=6.0, max=18.0, default=12.0,
                hint="Center-to-center bar spacing EW, top mat",
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
        if bool(params.has_top_mat) and params.fdn_thickness_in < 8.0:
            triggers.append("thin_double_mat_fuel_foundation_verify_cover_clearance")
        return triggers


TEMPLATE = FuelFoundationTemplate()
