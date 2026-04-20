"""
Template: Box Culvert  (v1.0)

Cast-in-place or precast rectangular box culvert.
Generates reinforcement for top slab, bottom slab, exterior walls, and haunches.

Reference: Caltrans Standard Plans B3-1 through B3-6 / AASHTO LRFD §12.
"""

from __future__ import annotations

from vistadetail.engine.schema import InputField, Params
from vistadetail.engine.templates.base import BaseTemplate


class BoxCulvertTemplate(BaseTemplate):

    def __init__(self):
        super().__init__()
        self.name = "Box Culvert"
        self.version = "2.0"
        self.description = (
            "CIP box culvert. #5@12oc slab/wall, #5@9oc bot slab, 12\" haunch, 2\" cover."
        )

        self.inputs = [
            InputField("clear_span_ft",      float, label="Clear Span (ft)",
                       min=2.0, max=30.0, default=6.0,
                       hint="Inside horizontal dimension"),
            InputField("clear_rise_ft",       float, label="Clear Rise (ft)",
                       min=2.0, max=20.0, default=4.0,
                       hint="Inside vertical dimension"),
            InputField("barrel_length_ft",    float, label="Barrel Length (ft)",
                       min=4.0, max=200.0, default=20.0,
                       hint="Total length along the culvert axis"),
        ]

        self.rules = [
            "rule_top_slab_top",
            "rule_top_slab_bottom",
            "rule_wall_vertical",
            "rule_bottom_slab_top",
            "rule_bottom_slab_bottom",
            "rule_haunch_bars",
            "rule_validate_box_culvert",
        ]

    def evaluate_triggers(self, params: Params) -> list[str]:
        triggers: list[str] = []
        if params.clear_span_ft > 16.0:
            triggers.append("wall_height_exceeds_table")
        if params.clear_rise_ft / max(params.clear_span_ft, 0.1) > 1.5:
            triggers.append("aspect_ratio_high")
        return triggers


TEMPLATE = BoxCulvertTemplate()
