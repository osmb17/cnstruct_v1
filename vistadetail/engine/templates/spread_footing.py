"""
Template: Spread Footing  (v2.0)

Rectangular spread footing with bottom mat (transverse + longitudinal)
and vertical column/wall dowels. #5@12oc bottom mat, #5 dowels, 3\" cover.
"""

from __future__ import annotations

from vistadetail.engine.schema import InputField, Params
from vistadetail.engine.templates.base import BaseTemplate


class SpreadFootingTemplate(BaseTemplate):

    def __init__(self):
        super().__init__()
        self.name = "Spread Footing"
        self.version = "2.0"
        self.description = (
            "Spread footing. #5@12oc bottom mat, #5 dowels, 3\" cover."
        )

        self.inputs = [
            InputField("footing_length_ft", float, label="Footing Length (ft)",
                       min=2.0, max=40.0, default=8.0,
                       hint="Long dimension of footing plan"),
            InputField("footing_width_ft",  float, label="Footing Width (ft)",
                       min=2.0, max=40.0, default=6.0,
                       hint="Short dimension of footing plan"),
            InputField("footing_depth_in",  float, label="Footing Depth (in)",
                       min=12.0, max=60.0, default=18.0,
                       hint="Overall footing thickness"),
            InputField("dowel_qty",          int,   label="Dowel Qty",
                       min=0, max=50, default=4,
                       hint="Number of column/wall dowels (0 = none)"),
        ]

        self.rules = [
            "rule_bottom_transverse",
            "rule_bottom_longitudinal",
            "rule_dowels",
            "rule_validate_footing_cover",
        ]

    def evaluate_triggers(self, params: Params) -> list[str]:
        triggers: list[str] = []
        if params.footing_depth_in < 12.0:
            triggers.append("wall_height_exceeds_table")
        return triggers


TEMPLATE = SpreadFootingTemplate()
