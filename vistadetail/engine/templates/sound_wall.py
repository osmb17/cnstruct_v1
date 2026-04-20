"""
Template: Sound Wall (v2.0) -- Caltrans B15-1 through B15-5.

Masonry block sound wall on spread footing, trench footing, or CIDH pile cap.
2\" cover, phi=30 deg, exp joint @48ft — hardcoded standards.
"""

from __future__ import annotations

from vistadetail.engine.schema import InputField, Params
from vistadetail.engine.templates.base import BaseTemplate


class SoundWallTemplate(BaseTemplate):

    def __init__(self):
        super().__init__()
        self.name = "Sound Wall"
        self.version = "2.0"
        self.description = (
            "Caltrans B15 masonry block sound wall on spread footing, "
            "trench footing, or CIDH pile cap. Lookup tables by wall height. "
            "2\" cover, phi=30, exp joint @48ft."
        )

        self.inputs = [
            InputField("wall_height_ft", float, label="Wall Height H (ft)",
                       min=6.0, max=16.0, default=10.0,
                       hint="Design height per B15-1 tables: 6, 8, 10, 12, 14, or 16 ft"),
            InputField("wall_length_ft", float, label="Wall Length (ft)",
                       min=8.0, max=2000.0, default=200.0,
                       hint="Total wall length for qty calculations"),
            InputField("foundation_type", str, label="Foundation Type",
                       choices=["spread_footing", "trench_footing", "pile_cap"],
                       default="spread_footing",
                       hint="Per B15-1 (spread/trench) or B15-3 (pile cap)"),
            InputField("ground_case", str, label="Ground Case",
                       choices=["case_1", "case_2"],
                       default="case_1",
                       hint="Case 1: level both sides. Case 2: level one side, slope opposite"),
        ]

        self.rules = [
            "rule_sw_wall_verticals",
            "rule_sw_wall_horizontals",
            "rule_sw_footing_dowels",
            "rule_sw_footing_bars",
            "rule_sw_pile_cage",
            "rule_sw_pile_cap_bars",
            "rule_validate_sound_wall",
        ]

    def evaluate_triggers(self, params: Params) -> list[str]:
        triggers: list[str] = []
        if params.wall_height_ft > 14:
            triggers.append("tall_wall")
        return triggers


TEMPLATE = SoundWallTemplate()
