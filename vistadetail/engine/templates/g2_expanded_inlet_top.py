"""Template: G2 Expanded Inlet Top (v3.0) — top extension for G2 Expanded Inlet.

Same inputs as G2 Expanded Inlet plus wall_height_ft (H from top of existing
box to top of grade).  Y dimensions are fixed standard values per Caltrans
D73A (5'-0" main box, 8'-0" expanded section).

Bar marks produced:
  H1/H2/H3/H4  — horizontal wall bars (shared rule_g2_horizontals)
  V1/V2         — vertical bars (rule_g2exptop_verticals)
  A1/B1/A2/B2   — A&B bars (shared rule_g2exp_ab_bars)
  RA1           — right-angle bars (shared rule_g2top_right_angle)
  HP1/HP2       — hoops (shared rule_g2exp_hoops)
"""

from __future__ import annotations

from vistadetail.engine.schema import InputField, Params
from vistadetail.engine.templates.base import BaseTemplate


class G2ExpandedInletTopTemplate(BaseTemplate):

    def __init__(self):
        super().__init__()
        self.name = "G2 Expanded Inlet Top"
        self.version = "3.0"
        self.description = (
            "Top extension rebar for a G2 expanded inlet. "
            "Y dimensions fixed at 5'-0\" main / 8'-0\" expanded per D73A. "
            "Bar sizes/spacings per Vista Steel spreadsheet."
        )

        self.inputs = [
            InputField(
                "x_dim_ft", float,
                label="X -- Exterior Width (ft)",
                min=2.5, max=30.0, default=5.667,
                hint="Exterior face-to-face width. Interior X = X − 2×T.",
            ),
            InputField(
                "wall_thick_in", int,
                label="Wall Thickness (in)",
                min=9, max=12, default=9,
                hint="9\" standard; 11\" for larger spans.",
            ),
            InputField(
                "wall_height_ft", float,
                label="Height",
                min=2.0, max=20.0, default=5.917,
                hint="Height from top of existing box to top of grade",
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
            "rule_g2exptop_geometry",
            "rule_g2_horizontals",
            "rule_g2exptop_verticals",
            "rule_g2exp_ab_bars",
            "rule_g2top_right_angle",
            "rule_g2exp_hoops",
        ]

    def evaluate_triggers(self, params: Params) -> list[str]:
        triggers: list[str] = []
        x_ft = getattr(params, "x_dim_ft", 5.667)
        ratio = params.wall_height_ft / max(x_ft, 0.1)
        if ratio > 2.5:
            triggers.append("aspect_ratio_high")
        return triggers


TEMPLATE = G2ExpandedInletTopTemplate()
