"""Template: G2 Inlet Top — cover/top slab for a standard G2 inlet."""

from __future__ import annotations

from vistadetail.engine.schema import BAR_SIZES, InputField, Params
from vistadetail.engine.templates.base import BaseTemplate


class G2InletTopTemplate(BaseTemplate):

    def __init__(self):
        super().__init__()
        self.name = "G2 Inlet Top"
        self.version = "1.0"
        self.description = (
            "Top/cover slab for a Caltrans G2 inlet. "
            "Bars each way; length matches inlet opening width, "
            "width matches inlet depth front-to-back."
        )

        self.inputs = [
            InputField("slab_length_ft",   float, label="Slab Length (ft)",    min=2.0, max=40.0, default=8.0,
                       hint="Matches inlet box inside width (long direction)"),
            InputField("slab_width_ft",    float, label="Slab Width (ft)",     min=1.0, max=20.0, default=4.0,
                       hint="Inlet depth front-to-back"),
            InputField("slab_thick_in",    int,   label="Slab Thickness (in)", min=6,   max=24,   default=9),
            InputField("cover_in",         float, label="Clear Cover (in)",    min=1.5, max=4.0,  default=2.0),
            InputField("long_bar_size",    str,   label="Long Bar Size",       choices=BAR_SIZES, default="#5"),
            InputField("long_spacing_in",  float, label="Long Spacing (in)",   min=6.0, max=18.0, default=12.0),
            InputField("short_bar_size",   str,   label="Short Bar Size",      choices=BAR_SIZES, default="#4"),
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


TEMPLATE = G2InletTopTemplate()
