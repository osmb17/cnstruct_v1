"""Template: Straight Headwall (v3.0) — Caltrans D89A."""

from __future__ import annotations

from vistadetail.engine.schema import InputField, Params
from vistadetail.engine.templates.base import BaseTemplate


class HeadwallTemplate(BaseTemplate):

    def __init__(self):
        super().__init__()
        self.name = "Straight Headwall"
        self.version = "3.0"
        self.description = (
            "Caltrans D89A straight headwall. "
            "Pipe diameter drives the D89A table lookup (H = pipe + 11\") "
            "for all bar sizes and lengths. Wall height controls bar counts."
        )

        self.inputs = [
            InputField(
                "wall_width_ft", float, label="Wall Width (ft)",
                min=4.0, max=30.0, default=8.0,
                group="Geometry",
                hint="Total wall length (parallel to pipe axis)",
            ),
            InputField(
                "wall_height_ft", float, label="Wall Height (ft)",
                min=2.0, max=12.0, default=5.0,
                hint="Actual wall height H above footing top — used for bar counts",
            ),
            InputField(
                "pipe_qty", int, label="Number of Pipes",
                min=0, max=4, default=1,
                group="Pipe",
                hint="Number of pipes through the headwall",
            ),
            InputField(
                "pipe_dia_in", str, label="Pipe Diameter",
                choices=["12\"", "15\"", "18\"", "21\"", "24\"", "27\"",
                         "30\"", "33\"", "36\"", "42\"", "48\"", "54\"",
                         "60\"", "66\"", "72\""],
                default="60\"",
                hint=(
                    "Nominal RCP pipe diameter. Drives D89A table lookup — "
                    "bar sizes, footing dimensions, and bar lengths. "
                    "H = pipe + 11\".  60\" pipe → VW = 6'-7\"."
                ),
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
        H = float(params.pipe_dia_in.replace('"', '')) + 11.0
        if H > 89:
            triggers.append("height_exceeds_d89_table")
        return triggers


TEMPLATE = HeadwallTemplate()
