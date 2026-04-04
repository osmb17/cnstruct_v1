"""Template: Junction Structure — Caltrans cast-in-place drainage junction box."""

from __future__ import annotations

from vistadetail.engine.schema import BAR_SIZES, InputField, Params
from vistadetail.engine.templates.base import BaseTemplate


class JunctionStructureTemplate(BaseTemplate):

    def __init__(self):
        super().__init__()
        self.name = "Junction Structure"
        self.version = "1.0"
        self.description = (
            "Caltrans rectangular junction structure (drainage manhole/junction box). "
            "4 walls (long EF + short EF) and floor slab. "
            "Inside dimensions are clear; outside computed from wall thickness."
        )

        self.inputs = [
            # ── Box geometry ───────────────────────────────────────────────
            InputField("inside_length_ft",  float, label="Inside Length (ft)",  min=2.0,  max=40.0, default=6.0,
                       hint="Clear inside dimension, long direction"),
            InputField("inside_width_ft",   float, label="Inside Width (ft)",   min=2.0,  max=20.0, default=4.0,
                       hint="Clear inside dimension, short direction"),
            InputField("inside_depth_ft",   float, label="Inside Depth (ft)",   min=2.0,  max=20.0, default=5.0,
                       hint="Wall height from floor to top of walls"),
            InputField("wall_thick_in",     int,   label="Wall Thickness (in)", min=8,    max=24,   default=12),
            InputField("floor_thick_in",    int,   label="Floor Thickness (in)",min=8,    max=24,   default=12,
                       hint="Floor slab thickness"),
            InputField("cover_in",          float, label="Clear Cover (in)",    min=1.5,  max=4.0,  default=2.0),
            # ── Wall reinforcement ─────────────────────────────────────────
            InputField("wall_bar_size",     str,   label="Wall Bar Size",       choices=BAR_SIZES, default="#5",
                       hint="Used for all 4 walls, EF horiz and vert"),
            InputField("horiz_spacing_in",  float, label="Wall Horiz Spacing (in)", min=3.0, max=18.0, default=12.0),
            InputField("vert_spacing_in",   float, label="Wall Vert Spacing (in)",  min=3.0, max=18.0, default=12.0),
            # ── Floor reinforcement ────────────────────────────────────────
            InputField("floor_bar_size",    str,   label="Floor Bar Size",      choices=BAR_SIZES, default="#5"),
            InputField("floor_spacing_in",  float, label="Floor Spacing (in)",  min=3.0, max=18.0, default=12.0),
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
        if params.cover_in < 2.0:
            triggers.append("cover_unusual")
        wall_max = min(3 * params.wall_thick_in, 18.0)
        if params.horiz_spacing_in > wall_max or params.vert_spacing_in > wall_max:
            triggers.append("spacing_near_max")
        if params.inside_depth_ft < 3.0:
            triggers.append("shallow_box")
        return triggers


TEMPLATE = JunctionStructureTemplate()
