"""Template: Junction Structure (v3.0) — Caltrans CIP drainage junction box."""

from __future__ import annotations

from vistadetail.engine.schema import InputField, Params
from vistadetail.engine.templates.base import BaseTemplate

_PIPE_SIZES = ["18", "24", "30", "36", "42", "48", "54", "60", "66", "72", "78", "84"]


class JunctionStructureTemplate(BaseTemplate):

    def __init__(self):
        super().__init__()
        self.name = "Junction Structure"
        self.version = "3.0"
        self.description = (
            "Caltrans CIP rectangular junction structure connecting two circular pipes. "
            "#6 @ 6\" slab and wall reinforcement EF, 2\" cover. "
            "Min height HB = 5'-6\"."
        )

        self.inputs = [
            InputField("d1_in", int, label="D1 — Inlet Diameter (in)",
                       choices=_PIPE_SIZES, default="36",
                       group="Pipe Geometry",
                       hint="Diameter of the inlet (upper) pipe"),
            InputField("d2_in", int, label="D2 — Outlet Diameter (in)",
                       choices=_PIPE_SIZES, default="48",
                       group="Pipe Geometry",
                       hint="Diameter of the outlet (lower) pipe"),
            InputField("span_ft", float, label="Inside Span (ft)",
                       min=4.0, max=20.0, default=5.0,
                       group="Box Geometry",
                       hint="Clear inside dimension perpendicular to pipe flow"),
            InputField("length_ft", float, label="Inside Length (ft)",
                       min=4.0, max=30.0, default=6.0,
                       group="Box Geometry",
                       hint="Clear inside dimension along pipe flow direction"),
            InputField("hb_ft", float, label="Height HB (ft)",
                       min=5.5, max=20.0, default=5.5,
                       group="Box Geometry",
                       hint="Inside height from floor to top slab soffit — 5'-6\" minimum"),
            InputField("wall_thick_in", int, label="Wall Thickness T (in)",
                       min=9, max=24, default=12,
                       group="Box Geometry",
                       hint="Uniform wall and slab thickness all sides"),
        ]

        self.rules = [
            "rule_junction_top_slab_trans",
            "rule_junction_top_slab_long",
            "rule_junction_floor_trans",
            "rule_junction_floor_long",
            "rule_junction_long_wall_horiz",
            "rule_junction_long_wall_vert",
            "rule_junction_short_wall_horiz",
            "rule_junction_short_wall_vert",
            "rule_junction_a_bars",
            "rule_validate_junction",
        ]

    def evaluate_triggers(self, params: Params) -> list[str]:
        triggers: list[str] = []
        if params.hb_ft < 5.5:
            triggers.append("height_below_minimum")
        d_max = max(int(params.d1_in), int(params.d2_in))
        if d_max / 12.0 > params.span_ft - 2.0:
            triggers.append("pipe_too_large_for_span")
        return triggers


TEMPLATE = JunctionStructureTemplate()
