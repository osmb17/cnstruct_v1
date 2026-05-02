"""
Caltrans D85 Box Culvert Wingwall template (Types D, E).

2025 Standard Plan D85 -- Straight and stepped wingwalls for multiple-span box culverts.
Inputs: wall height H, wall length LOL. Everything else defaults from table.
"""

from __future__ import annotations
from vistadetail.engine.schema import InputField
from vistadetail.engine.templates.base import BaseTemplate


class D85WingwallTemplate(BaseTemplate):

    def __init__(self):
        super().__init__()
        self.name = "D85 Wingwall"
        self.version = "2.0"
        self.description = (
            "Caltrans D85 -- Box Culvert Wingwall Types D/E. "
            "9\" wall, footing auto (0.55×H). "
            "Type D = straight (single span), Type E = stepped (multi-span)."
        )
        self.inputs = [
            InputField(
                "wall_height_ft", float,
                label="H -- Wall Height (ft)",
                min=2.0, max=14.0, default=6.0,
                hint="Height at box face. D85 table range 2-14 ft.",
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
            "rule_d85_validate",
            "rule_d85_geometry",
            "rule_d85_k_bars",
            "rule_d85_l_bars",
            "rule_d85_hoops",
            "rule_d85_top_bars",
            "rule_d85_footing_mat",
        ]


TEMPLATE = D85WingwallTemplate()
