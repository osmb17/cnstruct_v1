"""
Template: Spread Footing  (v1.0)

Rectangular spread footing with bottom mat (transverse + longitudinal)
and vertical column/wall dowels.
"""

from __future__ import annotations

from vistadetail.engine.schema import BAR_SIZES, InputField, Params
from vistadetail.engine.templates.base import BaseTemplate


class SpreadFootingTemplate(BaseTemplate):

    def __init__(self):
        super().__init__()
        self.name = "Spread Footing"
        self.version = "1.0"
        self.description = (
            "Rectangular spread footing — bottom mat (transverse + longitudinal) "
            "and vertical dowels."
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
            InputField("cover_in",           float, label="Clear Cover (in)",
                       min=2.0, max=6.0, default=3.0,
                       hint="Cast-against-soil: min 3 in per ACI 318-19"),
            InputField("bot_bar_size",       str,   label="Bottom Bar Size",
                       choices=BAR_SIZES, default="#5"),
            InputField("bot_spacing_in",     float, label="Bottom Bar Spacing (in)",
                       min=6.0, max=18.0, default=12.0),
            InputField("dowel_qty",          int,   label="Dowel Qty",
                       min=0, max=50, default=4,
                       hint="Number of column/wall dowels (0 = none)"),
            InputField("dowel_bar_size",     str,   label="Dowel Bar Size",
                       choices=BAR_SIZES, default="#5"),
        ]

        self.rules = [
            "rule_bottom_transverse",
            "rule_bottom_longitudinal",
            "rule_dowels",
            "rule_validate_footing_cover",
        ]

    def evaluate_triggers(self, params: Params) -> list[str]:
        triggers: list[str] = []
        if params.cover_in < 3.0:
            triggers.append("thin_cover_soil")
        if params.footing_depth_in < 12.0:
            triggers.append("wall_height_exceeds_table")
        return triggers


TEMPLATE = SpreadFootingTemplate()
