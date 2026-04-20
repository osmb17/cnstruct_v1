"""Template: G2 Expanded Inlet Top (v2.0) — cover slab. #5@12oc both ways, 2\" cover."""

from __future__ import annotations

from vistadetail.engine.schema import InputField, Params
from vistadetail.engine.templates.base import BaseTemplate


class G2ExpandedInletTopTemplate(BaseTemplate):

    def __init__(self):
        super().__init__()
        self.name = "G2 Expanded Inlet Top"
        self.version = "2.0"
        self.description = (
            "Top/cover slab for a Caltrans G2 expanded inlet. "
            "#5@12oc both ways, 2\" cover."
        )

        self.inputs = [
            InputField("slab_length_ft", float, label="Slab Length (ft)",
                       min=2.0, max=60.0, default=14.0,
                       hint="Matches expanded inlet inside width (long direction)"),
            InputField("slab_width_ft",  float, label="Slab Width (ft)",
                       min=1.0, max=20.0, default=4.5,
                       hint="Inlet depth front-to-back"),
            InputField("slab_thick_in",  int,   label="Slab Thickness (in)",
                       min=6, max=24, default=10),
        ]

        self.rules = [
            "rule_inlet_top_long_bars",
            "rule_inlet_top_short_bars",
            "rule_validate_inlet_top",
        ]

    def evaluate_triggers(self, params: Params) -> list[str]:
        triggers: list[str] = []
        ratio = params.slab_length_ft / max(params.slab_width_ft, 0.1)
        if ratio > 5.0:
            triggers.append("aspect_ratio_high")
        return triggers


TEMPLATE = G2ExpandedInletTopTemplate()
