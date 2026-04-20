"""
Template: Equipment / Concrete Pad  (v2.0)

Rectangular concrete equipment pad placed on compacted earth.
Single mat: P1 (long) + P2 (short). #4@12oc, 3\" cover.

Covers 3 PDFs in the clean_examples set:
  1.s3.concrete.pad.plans       — 8'-6"×4'-1", 6"t, #4@12oc, single mat, 3" cover
  example.equipementfloor.detail — 43'-1"×24'-8.25", 12"t, #4 typ, 3" cover
  transformerpad.doublemat      — 4'-4"×4'-0"

Formulas (ACI 318-19 / ACI 360R-10):
  bar_length = span_dim_in - 2 × 3.0 (cover)
  qty        = floor(perpendicular_dim_in / 12.0 (spacing))
"""

from __future__ import annotations

from vistadetail.engine.schema import InputField, Params
from vistadetail.engine.templates.base import BaseTemplate


class EquipmentPadTemplate(BaseTemplate):
    name: str = "Equipment Pad"
    version: str = "2.0"
    description: str = (
        "Concrete equipment pad. #4@12oc top and bottom, 3\" cover. "
        "Optional anchor dowels."
    )

    def __init__(self):
        super().__init__()
        self.name        = "Equipment Pad"
        self.version     = "2.0"
        self.description = (
            "Concrete equipment pad. #4@12oc top and bottom, 3\" cover. "
            "Optional anchor dowels."
        )

        self.inputs = [
            # ── Plan dimensions ───────────────────────────────────────────
            InputField(
                "pad_length_ft", float,
                label="Pad Length (ft)  — long side",
                min=1.0, max=300.0, default=8.5,
                hint="Longer plan dimension in feet",
            ),
            InputField(
                "pad_width_ft", float,
                label="Pad Width (ft)  — short side",
                min=1.0, max=300.0, default=4.0,
                hint="Shorter plan dimension in feet",
            ),
            InputField(
                "pad_thickness_in", float,
                label="Pad Thickness (in)",
                min=4.0, max=36.0, default=6.0,
                hint="Nominal pad thickness (typical: 6 in light equip, 12 in heavy equip)",
            ),
            InputField(
                "has_vertical_dowels", float,
                label="Vertical Anchor Dowels? (0=No 1=Yes)",
                min=0.0, max=1.0, default=0.0,
                hint="1 = generate D1 anchor dowel grid projecting above pad",
            ),
        ]

        self.rules = [
            "rule_pad_bottom_long",
            "rule_pad_bottom_short",
            "rule_pad_top_long",
            "rule_pad_top_short",
            "rule_validate_equipment_pad",
        ]

    def evaluate_triggers(self, params: Params) -> list[str]:
        triggers: list[str] = []
        area = params.pad_length_ft * params.pad_width_ft
        if area > 500.0:
            triggers.append("large_equipment_pad_contraction_joints_required")
        return triggers


TEMPLATE = EquipmentPadTemplate()
