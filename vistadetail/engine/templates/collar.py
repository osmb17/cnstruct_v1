"""
Template: Concrete Pipe Collar  (v1.0)

Rectangular reinforced concrete collar block placed around a pipe penetration
(manhole, catch basin, utility penetration).  Orthogonal straight-bar mat in
two directions.

Generates:
  C1 — long-direction bars
  C2 — short-direction bars

Covers 3 PDFs in the clean_examples set:
  collar.example.pdf, collarexample.pdf, concrete.collar.layout.pdf

Formulas (verified against collar PDFs):
  bar_length = span_dim_in - 2 × cover_in
  qty        = floor(perpendicular_dim_in / spacing_in)
"""

from __future__ import annotations

from vistadetail.engine.schema import BAR_SIZES, InputField, Params
from vistadetail.engine.templates.base import BaseTemplate


class CollarTemplate(BaseTemplate):
    name: str = "Concrete Pipe Collar"
    version: str = "1.0"
    description: str = (
        "Rectangular concrete collar around a pipe opening. "
        "Orthogonal straight-bar mat (C1 long-way, C2 short-way). "
        "Same bar size and spacing each direction."
    )

    def __init__(self):
        super().__init__()
        self.name        = "Concrete Pipe Collar"
        self.version     = "1.0"
        self.description = (
            "Rectangular concrete collar around a pipe opening. "
            "Orthogonal straight-bar mat (C1 long-way, C2 short-way). "
            "Same bar size and spacing each direction."
        )

        self.inputs = [
            InputField(
                "collar_length_ft", float,
                label="Collar Length (ft)  — long side",
                min=1.0, max=40.0, default=5.167,   # 5'-2"
                hint="Outer long dimension of the collar block in feet",
            ),
            InputField(
                "collar_width_ft", float,
                label="Collar Width (ft)  — short side",
                min=1.0, max=40.0, default=4.396,   # 4'-4 3/4"
                hint="Outer short dimension of the collar block in feet",
            ),
            InputField(
                "bar_size", str,
                label="Bar Size",
                choices=BAR_SIZES, default="#4",
                hint="Bar size used both directions",
            ),
            InputField(
                "spacing_in", float,
                label="Spacing (in)  — both ways",
                min=6.0, max=18.0, default=9.0,
                hint="Center-to-center bar spacing",
            ),
            InputField(
                "cover_in", float,
                label="Clear Cover (in)",
                min=1.5, max=4.0, default=3.0,
                hint="Clear cover to bar face (ACI Table 20.6.1.3.1)",
            ),
        ]

        self.rules = [
            "rule_collar_long_bars",
            "rule_collar_short_bars",
            "rule_validate_collar",
        ]

    def evaluate_triggers(self, params: Params) -> list[str]:
        triggers: list[str] = []
        if params.spacing_in > 15.0:
            triggers.append("collar_spacing_near_max")
        ratio = params.collar_length_ft / max(params.collar_width_ft, 0.1)
        if ratio > 3.0:
            triggers.append("elongated_collar_check")
        return triggers


TEMPLATE = CollarTemplate()
