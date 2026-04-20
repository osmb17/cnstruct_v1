"""
Template: Flat Slab  (v2.0)

Rectangular flat slab with #5@12oc uniform spacing each way.
Two straight bar marks: S1 (long-way) and S2 (short-way).

Covers 20 PDFs in the clean_examples set:
  flatslab.10.2x3.6, flatslab.10.2x4.4, flatslab5x4, flatslab7x3, etc.

Formula (verified against gold barlists):
  bar_length = span_dim - 2 × 3.0 (cover)
  qty        = floor(perpendicular_dim / 12.0 (spacing))
"""

from __future__ import annotations

from vistadetail.engine.schema import InputField, Params
from vistadetail.engine.templates.base import BaseTemplate


class FlatSlabTemplate(BaseTemplate):
    name: str = "Flat Slab"
    version: str = "2.0"
    description: str = (
        "Rectangular flat slab with uniform #5@12oc rebar each way. "
        "Generates S1 (long-way) and S2 (short-way) marks."
    )

    def __init__(self):
        super().__init__()
        self.name        = "Flat Slab"
        self.version     = "2.0"
        self.description = (
            "Rectangular flat slab with uniform #5@12oc rebar each way. "
            "Generates S1 (long-way) and S2 (short-way) marks."
        )

        self.inputs = [
            InputField(
                "slab_length_ft", float,
                label="Slab Length (ft)  — long side",
                min=2.0, max=120.0, default=10.167,   # 10'-2"
                hint="Longer plan dimension in feet (decimals OK: 10.167 = 10'2\")",
            ),
            InputField(
                "slab_width_ft", float,
                label="Slab Width (ft)  — short side",
                min=2.0, max=120.0, default=3.5,       # 3'-6"
                hint="Shorter plan dimension in feet (decimals OK: 3.5 = 3'6\")",
            ),
        ]

        self.rules = [
            "rule_slab_long_bars",
            "rule_slab_short_bars",
            "rule_validate_flat_slab",
        ]

    def evaluate_triggers(self, params: Params) -> list[str]:
        triggers: list[str] = []
        ratio = params.slab_length_ft / max(params.slab_width_ft, 0.1)
        if ratio > 4.0:
            triggers.append("high_aspect_ratio_slab")
        return triggers


TEMPLATE = FlatSlabTemplate()
