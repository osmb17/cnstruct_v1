"""
Template: Box Culvert  (v1.0)

Cast-in-place or precast rectangular box culvert.
Generates reinforcement for top slab, bottom slab, exterior walls, and haunches.

Reference: Caltrans Standard Plans B3-1 through B3-6 / AASHTO LRFD §12.
"""

from __future__ import annotations

from vistadetail.engine.schema import BAR_SIZES, InputField, Params
from vistadetail.engine.templates.base import BaseTemplate


class BoxCulvertTemplate(BaseTemplate):

    def __init__(self):
        super().__init__()
        self.name = "Box Culvert"
        self.version = "1.0"
        self.description = (
            "Rectangular box culvert — top slab (T+B), walls (EF), "
            "bottom slab (T+B), and haunch/corner bars."
        )

        self.inputs = [
            InputField("clear_span_ft",      float, label="Clear Span (ft)",
                       min=2.0, max=30.0, default=6.0,
                       hint="Inside horizontal dimension"),
            InputField("clear_rise_ft",       float, label="Clear Rise (ft)",
                       min=2.0, max=20.0, default=4.0,
                       hint="Inside vertical dimension"),
            InputField("barrel_length_ft",    float, label="Barrel Length (ft)",
                       min=4.0, max=200.0, default=20.0,
                       hint="Total length along the culvert axis"),
            InputField("wall_thick_in",       int,   label="Wall/Slab Thickness (in)",
                       min=6, max=36, default=12,
                       hint="Applies to all four sides (uniform section)"),
            InputField("cover_in",            float, label="Clear Cover (in)",
                       min=1.5, max=4.0, default=2.0,
                       hint="Interior face; exterior soil face typically 2–3 in"),
            InputField("slab_bar_size",       str,   label="Slab/Wall Bar Size",
                       choices=BAR_SIZES, default="#5",
                       hint="Used for top slab, wall, and haunch bars"),
            InputField("slab_spacing_in",     float, label="Slab/Wall Bar Spacing (in)",
                       min=6.0, max=18.0, default=12.0),
            InputField("bot_slab_bar_size",   str,   label="Bot Slab Bar Size",
                       choices=BAR_SIZES, default="#5",
                       hint="Bottom slab bottom (primary tension) — often larger"),
            InputField("bot_slab_spacing_in", float, label="Bot Slab Spacing (in)",
                       min=6.0, max=18.0, default=9.0,
                       hint="Often tighter than top bars due to bearing pressure"),
            InputField("wall_bar_size",       str,   label="Wall Bar Size",
                       choices=BAR_SIZES, default="#5"),
            InputField("wall_spacing_in",     float, label="Wall Bar Spacing (in)",
                       min=6.0, max=18.0, default=12.0),
            InputField("haunch_size_in",      float, label="Haunch Size (in)",
                       min=0.0, max=24.0, default=12.0,
                       hint="Leg length of corner haunch (0 = no haunches)"),
        ]

        self.rules = [
            "rule_top_slab_top",
            "rule_top_slab_bottom",
            "rule_wall_vertical",
            "rule_bottom_slab_top",
            "rule_bottom_slab_bottom",
            "rule_haunch_bars",
            "rule_validate_box_culvert",
        ]

    def evaluate_triggers(self, params: Params) -> list[str]:
        triggers: list[str] = []
        if params.clear_span_ft > 16.0:
            triggers.append("wall_height_exceeds_table")
        if params.cover_in < 2.0:
            triggers.append("cover_unusual")
        if params.clear_rise_ft / max(params.clear_span_ft, 0.1) > 1.5:
            triggers.append("aspect_ratio_high")
        return triggers


TEMPLATE = BoxCulvertTemplate()
