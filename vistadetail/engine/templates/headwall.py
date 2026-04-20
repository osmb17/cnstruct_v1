"""Template: Straight Headwall (v2.0) — Caltrans D89A."""

from __future__ import annotations

from vistadetail.engine.schema import InputField, Params
from vistadetail.engine.templates.base import BaseTemplate


class HeadwallTemplate(BaseTemplate):

    def __init__(self):
        super().__init__()
        self.name = "Straight Headwall"
        self.version = "2.0"
        self.description = (
            "Caltrans D89A straight headwall. "
            "Bar sizes and footing dimensions looked up from the D89A table by wall height."
        )

        self.inputs = [
            InputField(
                "wall_width_ft", float, label="Wall Width (ft)",
                min=4.0, max=30.0, default=8.0,
                group="Geometry",
                hint="Total wall length (parallel to pipe axis)",
            ),
            InputField(
                "design_pipe_dia_in", str, label="Design Pipe Diameter (in)",
                choices=["36", "42", "48", "54", "60", "66", "72"],
                default="60",
                hint=(
                    "Nominal RCP diameter. Determines D89A table row — "
                    "wall height H, footing width W/depth F, and all bar sizes. "
                    "H = pipe + 11\". Example: 60\" pipe → H = 71\" = 5'-11\"."
                ),
            ),
            InputField(
                "pipe_qty", int, label="Number of Pipes",
                min=0, max=4, default=0,
                group="Pipe",
                hint="Number of existing pipes through the headwall (0 = none)",
            ),
            InputField(
                "pipe_dia_in", str, label="Pipe Diameter",
                choices=["12\"", "15\"", "18\"", "21\"", "24\"", "27\"",
                         "30\"", "33\"", "36\"", "42\"", "48\"", "54\""],
                default="24\"",
                hint="Nominal RCP pipe diameter",
            ),
        ]

        self.rules = [
            "rule_hw_d_bars",
            "rule_hw_trans_footing",
            "rule_hw_long_invert",
            "rule_hw_long_wall",
            "rule_hw_top_wall",
            "rule_hw_vert_wall",
            "rule_hw_c_bars",
            "rule_hw_spreaders",
            "rule_hw_standees",
            "rule_validate_headwall",
        ]

    def evaluate_triggers(self, params: Params) -> list[str]:
        triggers: list[str] = []
        H = float(params.design_pipe_dia_in) + 11.0
        if H > 89:
            triggers.append("height_exceeds_d89_table")
        return triggers


TEMPLATE = HeadwallTemplate()
