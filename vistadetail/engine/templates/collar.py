"""
Template: Concrete Pipe Collar  (v2.0)

Rectangular reinforced concrete collar block placed around a pipe penetration
(manhole, catch basin, utility penetration).  Orthogonal straight-bar mat in
two directions. #4@9oc both ways, 3\" cover.

Generates:
  C1 — long-direction bars
  C2 — short-direction bars

Covers 3 PDFs in the clean_examples set:
  collar.example.pdf, collarexample.pdf, concrete.collar.layout.pdf

Formulas (verified against collar PDFs):
  bar_length = span_dim_in - 2 × 3.0 (cover)
  qty        = floor(perpendicular_dim_in / 9.0 (spacing))
"""

from __future__ import annotations

from vistadetail.engine.schema import InputField, Params
from vistadetail.engine.templates.base import BaseTemplate


class CollarTemplate(BaseTemplate):
    name: str = "Concrete Pipe Collar"
    version: str = "2.0"
    description: str = (
        "Concrete pipe collar. #4@9oc both ways, 3\" cover."
    )

    def __init__(self):
        super().__init__()
        self.name        = "Concrete Pipe Collar"
        self.version     = "2.0"
        self.description = (
            "Concrete pipe collar. #4@9oc both ways, 3\" cover."
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
        ]

        self.rules = [
            "rule_collar_long_bars",
            "rule_collar_short_bars",
            "rule_validate_collar",
        ]

    def evaluate_triggers(self, params: Params) -> list[str]:
        triggers: list[str] = []
        ratio = params.collar_length_ft / max(params.collar_width_ft, 0.1)
        if ratio > 3.0:
            triggers.append("elongated_collar_check")
        return triggers


TEMPLATE = CollarTemplate()
