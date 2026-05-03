"""Template: Junction Structure (v4.0) — Caltrans D91A/D91B CIP junction structure."""

from __future__ import annotations

from vistadetail.engine.schema import InputField, Params
from vistadetail.engine.templates.base import BaseTemplate

_PIPE_SIZES = ["18", "24", "30", "36", "42", "48", "54", "60", "66", "72", "78", "84"]


class JunctionStructureTemplate(BaseTemplate):

    def __init__(self):
        super().__init__()
        self.name = "Junction Structure"
        self.version = "4.0"
        self.description = (
            "Caltrans 2025 Standard Plan D91A/D91B — CIP Reinforced Concrete "
            "Junction Structure. Wall/slab thicknesses and bar data from D91B table. "
            "Min Hb = 5'-6\". Standard Hb: 5.5, 6–12 ft (square plan)."
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
                       hint="Clear inside span — D91B standard: 4' or 5' (Hb=5.5'), 6–12' (square)"),
            InputField("hb_ft", float, label="Height HB (ft)",
                       min=5.5, max=12.0, default=5.5,
                       group="Box Geometry",
                       hint="Inside height from floor to top slab soffit — D91B range 5'-6\" to 12'"),
            InputField("max_earth_cover_ft", int, label="Max Earth Cover (ft)",
                       choices=["10", "20"], default="10",
                       group="Loading",
                       hint="Maximum earth cover over top slab — governs D91B table row (10 or 20 ft)"),
            InputField("num_structures", int, label="Number of Structures",
                       min=1, max=10, default=1,
                       group="Quantity",
                       hint="Multiply bar list by this count"),
        ]

        self.rules = [
            "rule_validate_junction",
            "rule_junc_a_bars",
            "rule_junc_e_bars",
            "rule_junc_b_bars",
            "rule_junc_add_bars",
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
