"""Template: Straight Headwall (v3.0) — Caltrans D89A / D89B."""

from __future__ import annotations

from vistadetail.engine.schema import InputField, Params
from vistadetail.engine.templates.base import BaseTemplate


class HeadwallTemplate(BaseTemplate):

    def __init__(self):
        super().__init__()
        self.name = "Straight Headwall"
        self.version = "3.0"
        self.description = (
            "Caltrans straight headwall. "
            "Case I uses the D89A table (higher loading); Cases II/III use the D89B table (lighter loading). "
            "Bar sizes and footing dimensions are looked up by wall height."
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
                min=2.0, max=12.0, default=5.0,
                hint=(
                    "Wall height H above footing top. "
                    "Caltrans D89A table rounds up to the nearest standard row."
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
                         "30\"", "33\"", "36\"", "42\"", "48\"", "54\"",
                         "60\"", "66\"", "72\""],
                default="24\"",
                hint="Nominal RCP pipe diameter",
            ),
            InputField(
                "loading_case", str, label="Loading Case",
                choices=["D89A", "D89B"],
                default="D89A",
                group="Design",
                hint="D89A = higher loading (Case I); D89B = lighter loading (Cases II/III)",
            ),
        ]

        self.rules = [
            "rule_hw_trans_footing",
            "rule_hw_d_bars",
            "rule_hw_long_invert",
            "rule_hw_pipe_hoops",
            "rule_hw_pipe_opening",
            "rule_hw_vert_wall",
            "rule_hw_c_bars",
            "rule_hw_long_wall",
            "rule_hw_top_wall",
            "rule_hw_spreaders",
            "rule_hw_standees",
            "rule_validate_headwall",
        ]

    def evaluate_triggers(self, params: Params) -> list[str]:
        triggers: list[str] = []
        H = params.wall_height_ft * 12
        case = getattr(params, "loading_case", "D89A")
        max_h = 77 if case == "D89B" else 83
        if H > max_h:
            triggers.append("height_exceeds_d89_table")
        return triggers


TEMPLATE = HeadwallTemplate()
