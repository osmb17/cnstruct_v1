"""Template: G2 Expanded Inlet Top — cover slab for the wider G2 expanded inlet."""

from __future__ import annotations

from vistadetail.engine.schema import BAR_SIZES, InputField, Params
from vistadetail.engine.templates.base import BaseTemplate


class G2ExpandedInletTopTemplate(BaseTemplate):

    def __init__(self):
        super().__init__()
        self.name = "G2 Expanded Inlet Top"
        self.version = "1.0"
        self.description = (
            "Top/cover slab for a Caltrans G2 expanded inlet. "
            "Wider than standard G2 Inlet Top; bars each way."
        )

        self.inputs = [
            InputField("slab_length_ft",   float, label="Slab Length (ft)",    min=2.0, max=60.0, default=14.0,
                       hint="Matches expanded inlet inside width (long direction)"),
            InputField("slab_width_ft",    float, label="Slab Width (ft)",     min=1.0, max=20.0, default=4.5,
                       hint="Inlet depth front-to-back (typically wider than standard)"),
            InputField("slab_thick_in",    int,   label="Slab Thickness (in)", min=6,   max=24,   default=10),
            InputField("cover_in",         float, label="Clear Cover (in)",    min=1.5, max=4.0,  default=2.0),
            InputField("long_bar_size",    str,   label="Long Bar Size",       choices=BAR_SIZES, default="#5"),
            InputField("long_spacing_in",  float, label="Long Spacing (in)",   min=6.0, max=18.0, default=12.0),
            InputField("short_bar_size",   str,   label="Short Bar Size",      choices=BAR_SIZES, default="#5",
                       hint="#5 typical for expanded (heavier loading)"),
            InputField("short_spacing_in", float, label="Short Spacing (in)",  min=6.0, max=18.0, default=12.0),
        ]

        self.rules = [
            "rule_inlet_top_long_bars",
            "rule_inlet_top_short_bars",
            "rule_validate_inlet_top",
        ]

    def evaluate_triggers(self, params: Params) -> list[str]:
        triggers: list[str] = []
        if params.cover_in < 2.0:
            triggers.append("cover_unusual")
        ratio = params.slab_length_ft / max(params.slab_width_ft, 0.1)
        if ratio > 5.0:
            triggers.append("aspect_ratio_high")
        return triggers


TEMPLATE = G2ExpandedInletTopTemplate()
