"""Template: Retaining Wall  (v2.0) — cantilever retaining wall. #5@12oc vert, #4@12oc horiz, 2\" cover."""

from __future__ import annotations

from vistadetail.engine.schema import InputField, Params
from vistadetail.engine.templates.base import BaseTemplate


class RetainingWallTemplate(BaseTemplate):

    def __init__(self):
        super().__init__()
        self.name = "Retaining Wall"
        self.version = "2.0"
        self.description = (
            "Cantilever retaining wall — #5@12oc vert/footing, #4@12oc horiz EF, "
            "18\" footing, 2\" cover. Optional shear key."
        )

        self.inputs = [
            InputField("wall_length_ft",    float, label="Wall Length (ft)",
                       min=4.0, max=200.0, default=20.0),
            InputField("stem_height_ft",    float, label="Stem Height (ft)",
                       min=2.0, max=30.0, default=10.0),
            InputField("stem_thick_in",     float, label="Stem Thickness (in)",
                       min=8.0, max=36.0, default=12.0),
            InputField("footing_length_ft", float, label="Footing Width (ft)",
                       min=4.0, max=30.0, default=8.0),
            InputField("shear_key",         str,   label="Shear Key",
                       choices=["yes", "no"], default="no"),
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
        return triggers


TEMPLATE = RetainingWallTemplate()
