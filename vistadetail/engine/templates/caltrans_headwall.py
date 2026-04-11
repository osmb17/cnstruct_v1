"""
Template: Caltrans Pipe Culvert Headwall (v1.0) -- D89A/B.

Straight and "L" pipe culvert headwalls per Caltrans 2025 Standard Plans.
Dimensions and reinforcement looked up from tables by pipe diameter and
design H. Supports Cases I, II, and III.

Marks:
  HW1 -- c-bars: vertical face bars (each face)
  HW2 -- d-bars: horizontal face bars (each face)
  HW3 -- top-of-wall bars (#5 Tot 3)
  HW4 -- footing transverse bars
  HW5 -- footing longitudinal bars
  HW6 -- pipe hoop bars (2-#6 around opening)
"""

from __future__ import annotations

from vistadetail.engine.schema import InputField, Params
from vistadetail.engine.templates.base import BaseTemplate


class CaltransHeadwallTemplate(BaseTemplate):

    def __init__(self):
        super().__init__()
        self.name = "Caltrans Headwall"
        self.version = "1.0"
        self.description = (
            "Caltrans pipe culvert headwall (D89A/B). "
            "Bar sizes and dims from standard plan tables by pipe diameter."
        )

        self.inputs = [
            InputField("pipe_dia_in", float, label="Pipe Diameter (in)",
                       min=12.0, max=54.0, default=36.0,
                       hint="Circular pipe OD: 12 to 54 inches per D89"),
            InputField("wall_type", str, label="Wall Type",
                       choices=["straight", "L"],
                       default="straight",
                       hint="Straight or L-shaped headwall"),
            InputField("loading_case", str, label="Loading Case",
                       choices=["case_1", "case_2", "case_3"],
                       default="case_1",
                       hint="Case I: level. Case II: 1.5:1 slope. Case III: 2:1 slope"),
            InputField("wall_width_ft", float, label="Wall Width (ft)",
                       min=4.0, max=30.0, default=8.0,
                       hint="Total width of headwall face"),
        ]

        self.rules = [
            "rule_ct_hw_vert_bars",
            "rule_ct_hw_horiz_bars",
            "rule_ct_hw_top_bars",
            "rule_ct_hw_footing",
            "rule_ct_hw_pipe_hoops",
            "rule_validate_ct_hw",
        ]

    def evaluate_triggers(self, params: Params) -> list[str]:
        triggers: list[str] = []
        if params.pipe_dia_in >= 48:
            triggers.append("large_pipe")
        return triggers


TEMPLATE = CaltransHeadwallTemplate()
