"""Template: Junction Structure (v2.0) — Caltrans CIP drainage junction box."""

from __future__ import annotations

from vistadetail.engine.schema import InputField, Params
from vistadetail.engine.templates.base import BaseTemplate


class JunctionStructureTemplate(BaseTemplate):

    def __init__(self):
        super().__init__()
        self.name = "Junction Structure"
        self.version = "2.0"
        self.description = (
            "Caltrans rectangular junction structure (drainage manhole/junction box). "
            "#5@12oc walls and floor EF, 2\" cover. Floor thickness = wall thickness."
        )

        self.inputs = [
            InputField("inside_length_ft", float, label="Inside Length (ft)",
                       min=2.0, max=40.0, default=6.0,
                       hint="Clear inside dimension, long direction"),
            InputField("inside_width_ft",  float, label="Inside Width (ft)",
                       min=2.0, max=20.0, default=4.0,
                       hint="Clear inside dimension, short direction"),
            InputField("inside_depth_ft",  float, label="Inside Depth (ft)",
                       min=2.0, max=20.0, default=5.0,
                       hint="Wall height from floor to top of walls"),
            InputField("wall_thick_in",    int,   label="Wall Thickness (in)",
                       min=8, max=24, default=12,
                       hint="Floor slab uses the same thickness"),
        ]

        self.rules = [
            "rule_junction_long_wall_horiz",
            "rule_junction_long_wall_vert",
            "rule_junction_short_wall_horiz",
            "rule_junction_short_wall_vert",
            "rule_junction_floor_long",
            "rule_junction_floor_short",
            "rule_validate_junction",
        ]

    def evaluate_triggers(self, params: Params) -> list[str]:
        triggers: list[str] = []
        if params.inside_depth_ft < 3.0:
            triggers.append("shallow_box")
        return triggers


TEMPLATE = JunctionStructureTemplate()
