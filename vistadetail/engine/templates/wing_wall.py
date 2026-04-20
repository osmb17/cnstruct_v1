"""Template: Wing Wall  (v2.0) — tapered retaining wing. #4@12oc EF, 2\" cover."""

from __future__ import annotations

from vistadetail.engine.schema import InputField, Params
from vistadetail.engine.templates.base import BaseTemplate


class WingWallTemplate(BaseTemplate):

    def __init__(self):
        super().__init__()
        self.name = "Wing Wall"
        self.version = "2.0"
        self.description = (
            "Tapered wing wall — #4@12oc horizontal EF, #4@12oc vertical EF, "
            "corner L-bars at headwall junction. 2\" cover."
        )

        self.inputs = [
            InputField("wing_length_ft", float, label="Wing Length (ft)",
                       min=2.0, max=50.0, default=10.0),
            InputField("hw_height_ft",   float, label="Height at HW End (ft)",
                       min=1.0, max=20.0, default=5.0),
            InputField("tip_height_ft",  float, label="Height at Tip (ft)",
                       min=0.0, max=10.0, default=0.5,
                       hint="Typically small; 0 if wall tapers to grade"),
            InputField("wall_thick_in",  int,   label="Wall Thickness (in)",
                       min=6, max=24, default=9),
        ]

        self.rules = [
            "rule_wing_horiz",
            "rule_wing_vert",
            "rule_wing_corner",
            "rule_validate_wing",
        ]

    def evaluate_triggers(self, params: Params) -> list[str]:
        triggers: list[str] = []
        if getattr(params, "tip_height_ft", 0.0) > params.hw_height_ft:
            triggers.append("tip_exceeds_hw_height")
        return triggers


TEMPLATE = WingWallTemplate()
