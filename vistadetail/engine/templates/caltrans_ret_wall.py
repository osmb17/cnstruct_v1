"""
Template: Caltrans Retaining Wall Type 1 (v1.0) -- B3-1A (Case 1).

Cantilever retaining wall with level backfill, vertical exterior face.
All bar sizes, spacings, and footing dims looked up from Caltrans 2025
Standard Plans B3-1A tables by Design H.

User only needs to specify: Design H, wall length, and case.
Everything else comes from the table.
"""

from __future__ import annotations

from vistadetail.engine.schema import InputField, Params
from vistadetail.engine.templates.base import BaseTemplate


class CaltransRetWallTemplate(BaseTemplate):

    def __init__(self):
        super().__init__()
        self.name = "Caltrans Retaining Wall"
        self.version = "1.0"
        self.description = (
            "Caltrans Type 1 cantilever retaining wall (B3-1A/B/C). "
            "Bar sizes and footing dims from standard plan tables by Design H."
        )

        self.inputs = [
            InputField("design_h_ft", float, label="Design H (ft)",
                       min=4.0, max=26.0, default=10.0,
                       hint="Design height per B3-1 table: 4 to 26 ft (even increments)"),
            InputField("wall_length_ft", float, label="Wall Length (ft)",
                       min=4.0, max=500.0, default=50.0,
                       hint="Total wall length for qty calculations"),
            InputField("wall_case", str, label="Loading Case",
                       choices=["case_1", "case_2", "case_3"],
                       default="case_1",
                       hint="Case 1: level backfill. Case 2: sloped at top. Case 3: sloped backfill"),
            InputField("shear_key", str, label="Shear Key",
                       choices=["yes", "no"], default="no"),
        ]

        self.rules = [
            "rule_ct_rw_stem_vert",
            "rule_ct_rw_stem_horiz",
            "rule_ct_rw_toe_heel",
            "rule_ct_rw_dowels",
            "rule_ct_rw_shear_key",
            "rule_ct_rw_e_bars",
            "rule_validate_ct_rw",
        ]

    def evaluate_triggers(self, params: Params) -> list[str]:
        triggers: list[str] = []
        if params.design_h_ft > 20:
            triggers.append("tall_wall")
        return triggers


TEMPLATE = CaltransRetWallTemplate()
