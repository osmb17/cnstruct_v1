"""
Template: Flat Slab  (v1.0)

Rectangular slab-on-grade with a single bar size and uniform spacing each way.
Two straight bar marks: S1 (long-way) and S2 (short-way).

Covers 20 PDFs in the clean_examples set:
  flatslab.10.2x3.6, flatslab.10.2x4.4, flatslab5x4, flatslab7x3, etc.

Formula (verified against gold barlists):
  bar_length = span_dim - 2 × cover
  qty        = floor(perpendicular_dim / spacing)
"""

from __future__ import annotations

from vistadetail.engine.schema import BAR_SIZES, InputField, Params
from vistadetail.engine.templates.base import BaseTemplate


class FlatSlabTemplate(BaseTemplate):
    name: str = "Flat Slab"
    version: str = "1.0"
    description: str = (
        "Rectangular flat slab with uniform rebar each way. "
        "Straight bars only — no hooks. "
        "Generates S1 (long-way) and S2 (short-way) marks."
    )

    def __init__(self):
        super().__init__()
        self.name        = "Flat Slab"
        self.version     = "1.0"
        self.description = (
            "Rectangular flat slab with uniform rebar each way. "
            "Straight bars only — no hooks. "
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
            InputField(
                "bar_size", str,
                label="Bar Size",
                choices=BAR_SIZES, default="#5",
                hint="Same bar size used both ways (EW)",
            ),
            InputField(
                "spacing_in", float,
                label="Spacing (in) — both ways",
                min=6.0, max=18.0, default=12.0,
                hint="Center-to-center bar spacing, same each way",
            ),
            InputField(
                "cover_in", float,
                label="Clear Cover (in)",
                min=1.5, max=4.0, default=3.0,
                hint="3 in for concrete cast against earth (ACI Table 20.6.1.3.1)",
            ),
        ]

        self.rules = [
            "rule_slab_long_bars",
            "rule_slab_short_bars",
            "rule_validate_flat_slab",
        ]

    def evaluate_triggers(self, params: Params) -> list[str]:
        triggers: list[str] = []
        if params.spacing_in > 16.0:
            triggers.append("spacing_near_max_slab")
        if params.cover_in < 3.0:
            triggers.append("cover_below_earth_min")
        ratio = params.slab_length_ft / max(params.slab_width_ft, 0.1)
        if ratio > 4.0:
            triggers.append("high_aspect_ratio_slab")
        return triggers


TEMPLATE = FlatSlabTemplate()
