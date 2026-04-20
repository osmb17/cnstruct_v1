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
                "wall_height_ft", float, label="Wall Height H (ft)",
                min=2.0, max=12.0, default=5.917,
                hint=(
                    "Wall height H above footing top — "
                    "footing width W, thickness T, and all bar sizes "
                    "are looked up from the D89A table by this value. "
                    "H1 = H + 1'-0\" is shown automatically."
                ),
            ),
            InputField(
                "pipe_qty", int, label="Number of Pipes",
                min=0, max=4, default=1,
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
        if params.wall_height_ft * 12 > 89:
            triggers.append("height_exceeds_d89_table")
        return triggers


TEMPLATE = HeadwallTemplate()
