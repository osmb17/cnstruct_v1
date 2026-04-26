"""Template: Box Culvert (D80) v3.0 — Caltrans D80 CIP single box culvert."""

from __future__ import annotations

from vistadetail.engine.schema import InputField, Params
from vistadetail.engine.templates.base import BaseTemplate


class BoxCulvertTemplate(BaseTemplate):

    def __init__(self):
        super().__init__()
        self.name = "Box Culvert"
        self.version = "3.0"
        self.description = (
            "Caltrans D80 CIP single box culvert. "
            "Bar sizes and concrete thicknesses looked up from the D80 table "
            "by (span, height, max earth cover)."
        )

        self.inputs = [
            InputField(
                "span_ft", int, label="Span (ft)",
                choices=["4", "5", "6", "7", "8", "10", "12", "14"],
                default="8",
                group="Geometry",
                hint="Inside horizontal span dimension — D80 standard sizes",
            ),
            InputField(
                "height_ft", float, label="Height (ft)",
                min=2.0, max=14.0, default=6.0,
                hint="Inside vertical height dimension",
            ),
            InputField(
                "barrel_length_ft", float, label="Barrel Length (ft)",
                min=4.0, max=200.0, default=20.0,
                hint="Total length along the culvert axis",
            ),
            InputField(
                "max_earth_cover_ft", int, label="Max Earth Cover (ft)",
                choices=["10", "20"],
                default="10",
                group="Loading",
                hint="Maximum earth cover over the roof slab — governs D80 table row selection",
            ),
        ]

        self.rules = [
            "rule_bc_a_bars",
            "rule_bc_b_bars",
            "rule_bc_e_bars",
            "rule_bc_i_bars",
            "rule_bc_hoops",
            "rule_bc_f_bars",
            "rule_bc_h_bars",
            "rule_bc_haunch_bars",
            "rule_bc_validate",
        ]

    def evaluate_triggers(self, params: Params) -> list[str]:
        triggers: list[str] = []
        span = int(params.span_ft)
        # All D80 standard spans (4-14) now have table data — no interpolation triggers
        if params.height_ft > 14.0:
            triggers.append("height_exceeds_d80_table")
        if span > 14:
            triggers.append("span_exceeds_d80_table")
        return triggers


TEMPLATE = BoxCulvertTemplate()
