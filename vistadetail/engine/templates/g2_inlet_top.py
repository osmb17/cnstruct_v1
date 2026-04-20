"""
Template: G2 Inlet Top  (v2.0)

Top extension / cover slab rebar for a Caltrans G2 standard inlet.
Uses the same X/Y base dimensions as the inlet below.

Bar sizes/spacings per Vista Steel spreadsheet
("G2 inlet Top 9in walls.xlsx").
"""

from __future__ import annotations

from vistadetail.engine.schema import InputField, Params
from vistadetail.engine.templates.base import BaseTemplate


class G2InletTopTemplate(BaseTemplate):

    def __init__(self):
        super().__init__()
        self.name = "G2 Inlet Top"
        self.version = "2.0"
        self.description = (
            "Top extension rebar for a G2 inlet -- horizontals, verticals, "
            "A&B bars, right angle, and hoops. "
            "Bar sizes/spacings per Vista Steel spreadsheet."
        )

        self.inputs = [
            InputField(
                "x_dim_ft", float,
                label="X -- Exterior Width (ft)",
                min=2.5, max=20.0, default=5.667,
                hint="Same exterior width as the inlet below",
                group="Geometry",
            ),
            InputField(
                "wall_thick_in", int,
                label="Wall Thickness (in)",
                min=0, max=24, default=0,
                hint="0 = auto (9\" if interior X<=54\", 11\" otherwise)",
            ),
            InputField(
                "wall_height_ft", float,
                label="Height",
                min=2.0, max=20.0, default=7.0,
                hint="Height from top of existing box to top of grade",
            ),
            InputField(
                "y_dim_ft", float,
                label="Y -- Exterior Depth (ft)",
                min=2.5, max=10.0, default=5.0,
                hint="Same exterior depth as the inlet below",
            ),
            InputField(
                "vert_extension_in", float,
                label="Vertical Extension (in)",
                min=6.0, max=60.0, default=20.0,
                hint="Height of vertical bars extending into top slab (inches)",
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
            "rule_g2top_geometry",
            "rule_g2_horizontals",      # shared with standard G2
            "rule_g2top_verticals",
            "rule_g2_ab_bars",          # shared with standard G2
            "rule_g2top_right_angle",
            "rule_g2_hoops",            # shared with standard G2
        ]

    def evaluate_triggers(self, params: Params) -> list[str]:
        triggers: list[str] = []
        x_ft = getattr(params, "x_dim_ft", 5.667)
        ratio = params.wall_height_ft / max(x_ft, 0.1)
        if ratio > 2.5:
            triggers.append("aspect_ratio_high")
        return triggers


TEMPLATE = G2InletTopTemplate()
