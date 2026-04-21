"""
Template: G2 Expanded Inlet  (v5.0)

Caltrans G2 expanded inlet box.  Has an expansion room on one side.
Y dimensions are fixed standard values (5'-0" main, 8'-0" expanded).

Bar sizes/spacings per Vista Steel spreadsheet
("expanded G2 inlet 9in walls.xlsx").
"""

from __future__ import annotations

from vistadetail.engine.schema import InputField, Params
from vistadetail.engine.templates.base import BaseTemplate


class G2ExpandedInletTemplate(BaseTemplate):

    def __init__(self):
        super().__init__()
        self.name = "G2 Expanded Inlet"
        self.version = "5.0"
        self.description = (
            "Caltrans G2 expanded inlet -- main box + expansion room. "
            "Y dimensions are fixed standard values (5'-0\" main, 8'-0\" expanded). "
            "Bar sizes/spacings per Vista Steel spreadsheet."
        )

        self.inputs = [
            InputField(
                "x_dim_ft", float,
                label="X -- Exterior Width (ft)",
                min=2.5, max=30.0, default=5.667,
                hint="Exterior face-to-face width in plan. Interior X = X − 2×T.",
            ),
            InputField(
                "wall_height_ft", float,
                label="Wall Height (ft)",
                min=2.0, max=20.0, default=5.0,
                hint="Bottom of footing to top of wall",
            ),
            InputField(
                "wall_thick_in", int,
                label="Wall Thickness (in)",
                min=9, max=12, default=9,
                hint="9\" standard; 11\" for larger spans.",
            ),
            InputField(
                "grate_type", str,
                label="Grate Type",
                choices=["Type 24", "Type 18"], default="Type 24",
                hint="Controls grate deduction: Type 24 = 24\", Type 18 = 18\"",
            ),
            InputField(
                "num_structures", int,
                label="Number of Structures",
                min=1, max=50, default=1,
                hint="Multiplier for quantities",
            ),
        ]

        self.rules = [
            "rule_g2exp_geometry",
            "rule_g2_bottom_mat",       # shared with standard G2
            "rule_g2_horizontals",      # shared with standard G2
            "rule_g2exp_verticals",
            "rule_g2exp_ab_bars",
            "rule_g2_right_angle",      # shared with standard G2
            "rule_g2exp_hoops",
        ]

    def evaluate_triggers(self, params: Params) -> list[str]:
        triggers: list[str] = []
        x_ft = getattr(params, "x_dim_ft", 5.667)
        ratio = params.wall_height_ft / max(x_ft, 0.1)
        if ratio > 2.5:
            triggers.append("aspect_ratio_high")
        return triggers


TEMPLATE = G2ExpandedInletTemplate()
