"""Template: Wing Wall  (v1.0) — tapered retaining wing."""

from __future__ import annotations

from vistadetail.engine.schema import BAR_SIZES, HOOK_TYPES, InputField, Params
from vistadetail.engine.templates.base import BaseTemplate


class WingWallTemplate(BaseTemplate):

    def __init__(self):
        super().__init__()
        self.name = "Wing Wall"
        self.version = "1.0"
        self.description = (
            "Tapered wing wall — horizontal EF, vertical EF (max length), "
            "corner L-bars at headwall junction."
        )

        self.inputs = [
            InputField("wing_length_ft",  float, label="Wing Length (ft)",   min=2.0,  max=50.0,  default=10.0),
            InputField("hw_height_ft",    float, label="Height at HW End (ft)", min=1.0, max=20.0, default=5.0),
            InputField("tip_height_ft",   float, label="Height at Tip (ft)",  min=0.0, max=10.0,  default=0.5,
                       hint="Typically small; 0 if wall tapers to grade"),
            InputField("wall_thick_in",   int,   label="Wall Thickness (in)", min=6,   max=24,    default=9),
            InputField("cover_in",        float, label="Clear Cover (in)",    min=1.5,  max=4.0,  default=2.0),
            InputField("horiz_bar_size",  str,   label="Horiz Bar Size",      choices=BAR_SIZES,  default="#4"),
            InputField("horiz_spacing_in",float, label="Horiz Spacing (in)",  min=6.0, max=18.0,  default=12.0),
            InputField("vert_bar_size",   str,   label="Vert Bar Size",       choices=BAR_SIZES,  default="#4"),
            InputField("vert_spacing_in", float, label="Vert Spacing (in)",   min=6.0, max=18.0,  default=12.0),
            InputField("hook_type",       str,   label="Hook Type",           choices=HOOK_TYPES, default="std_90"),
        ]

        self.rules = [
            "rule_wing_horiz",
            "rule_wing_vert",
            "rule_wing_corner",
            "rule_validate_wing",
        ]

    def evaluate_triggers(self, params: Params) -> list[str]:
        triggers: list[str] = []
        if params.cover_in < 2.0:
            triggers.append("cover_unusual")
        if params.horiz_spacing_in > 16.0 or params.vert_spacing_in > 16.0:
            triggers.append("spacing_near_max")
        return triggers


TEMPLATE = WingWallTemplate()
