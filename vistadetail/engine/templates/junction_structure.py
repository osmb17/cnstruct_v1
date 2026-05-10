"""Template: Junction Structure (v5.0) — Caltrans D91A/D91B CIP junction structure."""

from __future__ import annotations

from vistadetail.engine.schema import InputField, Params
from vistadetail.engine.templates.base import BaseTemplate

_PIPE_SIZES = ["18", "24", "30", "36", "42", "48", "54", "60", "66", "72", "78", "84"]


class JunctionStructureTemplate(BaseTemplate):

    def __init__(self):
        super().__init__()
        self.name = "Junction Structure"
        self.version = "5.0"
        self.description = (
            "Caltrans 2025 Standard Plan D91A/D91B — CIP Reinforced Concrete "
            "Junction Structure. Wall/slab thicknesses and bar data from D91B table. "
            "Min Hb = 5'-6\". Span governs D91B structural design; Length is the "
            "perpendicular plan dimension (may differ from Span for rectangular boxes)."
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
                       min=4.0, max=12.0, default=5.0,
                       group="Box Geometry",
                       hint="Clear inside span — governs D91B table (4' or 5' at Hb=5.5', 6–12' otherwise)"),
            InputField("length_ft", float, label="Length (ft)",
                       min=4.0, max=20.0, default=5.0,
                       group="Box Geometry",
                       hint="Inside plan length perpendicular to Span. Use same value as Span for square box."),
            InputField("hb_ft", float, label="Height HB (ft)",
                       min=5.5, max=12.0, default=5.5,
                       group="Box Geometry",
                       hint="Inside height from floor to top slab soffit — D91B range 5'-6\" to 12'"),
            InputField("max_earth_cover_ft", int, label="Max Earth Cover (ft)",
                       choices=["10", "20"], default="10",
                       group="Loading",
                       hint="Maximum earth cover over top slab — governs D91B table row (10 or 20 ft)"),
            InputField("has_manhole", str, label="Manhole",
                       choices=["yes", "no"], default="yes",
                       group="Openings",
                       hint="Include manhole in top slab (adds circular hoops and extra bars)"),
            InputField("side_pipe_dia_in", str, label="Side Pipe Diameter",
                       choices=["None"] + _PIPE_SIZES, default="None",
                       group="Openings",
                       hint="Diameter of pipe entering through side wall, or 'None' if no side pipe"),
            InputField("num_structures", int, label="Number of Structures",
                       min=1, max=10, default=1,
                       group="Quantity",
                       hint="Multiply bar list by this count"),
        ]

        self.rules = [
            "rule_validate_junction",
            "rule_junc_a_bars",       # JA1/JA2 — slab transverse U-bars
            "rule_junc_e_bars",       # JE1 — wall exterior vertical bars
            "rule_junc_b_bars",       # JB1 — wall interior U-bars
            "rule_junc_slab_longs",   # JD1/JL1/JL2 — longitudinal slab bars
            "rule_junc_wall_horiz",   # JC1 — horizontal wall bars (double curtain)
            "rule_junc_hoops",        # JMH/JPH/JME — manhole/pipe hoops + extra bars
            "rule_junc_add_bars",     # JX1 — additional bars at pipe openings
        ]

    def evaluate_triggers(self, params: Params) -> list[str]:
        triggers: list[str] = []
        if params.hb_ft < 5.5:
            triggers.append("height_below_minimum")
        length_ft = float(getattr(params, "length_ft", params.span_ft))
        d_max = max(int(params.d1_in), int(params.d2_in))
        # Pipe must fit within both horizontal plan dimensions
        if d_max / 12.0 > params.span_ft - 2.0:
            triggers.append("pipe_too_large_for_span")
        if d_max / 12.0 > length_ft - 2.0:
            triggers.append("pipe_too_large_for_length")
        return triggers


TEMPLATE = JunctionStructureTemplate()
