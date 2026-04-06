"""Template: Retaining Wall  (v1.0) — Caltrans-style cantilever retaining wall."""

from __future__ import annotations

from vistadetail.engine.schema import BAR_SIZES, InputField, Params
from vistadetail.engine.templates.base import BaseTemplate


class RetainingWallTemplate(BaseTemplate):

    def __init__(self):
        super().__init__()
        self.name = "Retaining Wall"
        self.version = "1.0"
        self.description = (
            "Caltrans-style cantilever retaining wall — stem horiz/vert EF, "
            "toe bars, heel bars, stem-to-footing dowels, optional shear key."
        )

        self.inputs = [
            InputField("wall_length_ft",     float, label="Wall Length (ft)",
                       min=4.0,  max=200.0, default=20.0),
            InputField("stem_height_ft",     float, label="Stem Height (ft)",
                       min=2.0,  max=30.0,  default=10.0),
            InputField("stem_thick_in",      float, label="Stem Thickness (in)",
                       min=8.0,  max=36.0,  default=12.0),
            InputField("footing_length_ft",  float, label="Footing Width (ft)",
                       min=4.0,  max=30.0,  default=8.0),
            InputField("footing_depth_in",   float, label="Footing Depth (in)",
                       min=12.0, max=48.0,  default=18.0),
            InputField("cover_in",           float, label="Cover (in)",
                       min=1.5,  max=4.0,   default=2.0),
            InputField("vert_bar_size",      str,   label="Vert Bar Size",
                       choices=BAR_SIZES,   default="#5"),
            InputField("horiz_bar_size",     str,   label="Horiz Bar Size",
                       choices=BAR_SIZES,   default="#4"),
            InputField("footing_bar_size",   str,   label="Footing Bar Size",
                       choices=BAR_SIZES,   default="#5"),
            InputField("vert_spacing_in",    float, label="Vert Spacing (in)",
                       min=6.0,  max=18.0,  default=12.0),
            InputField("horiz_spacing_in",   float, label="Horiz Spacing (in)",
                       min=6.0,  max=18.0,  default=12.0),
            InputField("footing_spacing_in", float, label="Footing Spacing (in)",
                       min=6.0,  max=18.0,  default=12.0),
            InputField("shear_key",          str,   label="Shear Key",
                       choices=["yes", "no"], default="no"),
            InputField("key_depth_in",       float, label="Key Depth (in)",
                       min=6.0,  max=24.0,  default=12.0),
        ]

        self.rules = [
            "rule_stem_horiz",
            "rule_stem_vert",
            "rule_toe_bars",
            "rule_heel_bars",
            "rule_stem_dowels",
            "rule_shear_key",
            "rule_validate_retaining_wall",
        ]

    def evaluate_triggers(self, params: Params) -> list[str]:
        triggers: list[str] = []
        if params.stem_thick_in < 10:
            triggers.append("thin_stem")
        if params.stem_height_ft > 15:
            triggers.append("tall_stem")
        if params.cover_in < 2.0 or params.cover_in > 3.5:
            triggers.append("cover_unusual")
        return triggers


TEMPLATE = RetainingWallTemplate()
