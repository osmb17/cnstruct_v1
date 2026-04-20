"""
Caltrans D84 Box Culvert Wingwall template (Types A, B, C).

2025 Standard Plan D84 -- Straight and warped wingwalls for box culverts.
Inputs: wall height H, wall length LOL. Everything else defaults from table.
"""

from __future__ import annotations
from vistadetail.engine.schema import InputField
from vistadetail.engine.templates.base import BaseTemplate


class D84WingwallTemplate(BaseTemplate):

    def __init__(self):
        super().__init__()
        self.name = "D84 Wingwall"
        self.version = "2.0"
        self.description = (
            "Caltrans D84 -- Box Culvert Wingwall Types A/B/C. "
            "9\" wall, footing auto (0.55×H), 2\" cover."
        )
        self.inputs = [
            InputField(
                "wall_height_ft", float,
                label="H -- Wall Height (ft)",
                min=1.0, max=20.0, default=6.0,
                hint="Height at box face. D84 range 1-20 ft.",
            ),
            InputField(
                "wall_length_ft", float,
                label="LOL -- Wall Length (ft)",
                min=1.0, max=60.0, default=10.0,
                hint="Length of wingwall from box face to toe of slope.",
            ),
            InputField(
                "num_structures", int,
                label="Number of Wingwalls",
                min=1, max=10, default=1,
                hint="Multiply barlist by this count.",
            ),
        ]
        self.rules = [
            "rule_d84_validate",
            "rule_d84_geometry",
            "rule_d84_face_horiz",
            "rule_d84_longitudinals",
            "rule_d84_top_bars",
            "rule_d84_footing_mat",
            "rule_d84_cutoff_wall",
        ]


TEMPLATE = D84WingwallTemplate()
