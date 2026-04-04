"""
Template: Equipment / Concrete Pad  (v1.0)

Rectangular concrete equipment pad placed on compacted earth.
Supports single mat and double mat reinforcing configurations.

Single mat:  P1 (long) + P2 (short)
Double mat:  P1 (bottom long) + P2 (bottom short) + P3 (top long) + P4 (top short)

Cover default: 3.0 in — concrete cast against and permanently exposed to earth
               (ACI 318-19 Table 20.6.1.3.1).

Covers 3 PDFs in the clean_examples set:
  1.s3.concrete.pad.plans       — 8'-6"×4'-1", 6"t, #4@12oc, single mat, 3" cover
  example.equipementfloor.detail — 43'-1"×24'-8.25", 12"t, #4 typ, double mat, 3" cover
  transformerpad.doublemat      — 4'-4"×4'-0", double mat explicit

Formulas (ACI 318-19 / ACI 360R-10):
  bar_length = span_dim_in - 2 × cover_in
  qty        = floor(perpendicular_dim_in / spacing_in)
"""

from __future__ import annotations

from vistadetail.engine.schema import BAR_SIZES, InputField, Params
from vistadetail.engine.templates.base import BaseTemplate


class EquipmentPadTemplate(BaseTemplate):
    name: str = "Equipment Pad"
    version: str = "1.0"
    description: str = (
        "Rectangular concrete equipment or transformer pad on compacted earth. "
        "Single or double reinforcing mat (P1/P2 bottom, P3/P4 top). "
        "Cover default 3 in per ACI cast-against-earth requirement."
    )

    def __init__(self):
        super().__init__()
        self.name        = "Equipment Pad"
        self.version     = "1.0"
        self.description = (
            "Rectangular concrete equipment or transformer pad on compacted earth. "
            "Single or double reinforcing mat (P1/P2 bottom, P3/P4 top). "
            "Cover default 3 in per ACI cast-against-earth requirement."
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
            # ── Bottom mat (always present) ───────────────────────────────
            InputField(
                "bar_size", str,
                label="Bar Size  (bottom mat)",
                choices=BAR_SIZES, default="#4",
                hint="Bar size for bottom mat — used both directions",
            ),
            InputField(
                "spacing_in", float,
                label="Spacing (in)  — bottom mat, both ways",
                min=6.0, max=18.0, default=12.0,
                hint="Center-to-center bar spacing EW for bottom mat",
            ),
            InputField(
                "cover_in", float,
                label="Clear Cover (in)",
                min=2.0, max=6.0, default=3.0,
                hint="3 in for concrete cast against earth (ACI Table 20.6.1.3.1)",
            ),
            # ── Double mat (optional) ─────────────────────────────────────
            InputField(
                "has_double_mat", float,
                label="Double Mat? (0=No 1=Yes)",
                min=0.0, max=1.0, default=0.0,
                hint="1 = add top mat (P3 and P4) for heavy equipment or thick pads",
            ),
            InputField(
                "top_bar_size", str,
                label="Top Bar Size  (if double mat)",
                choices=BAR_SIZES, default="#4",
                hint="Bar size for top mat — used both directions",
            ),
            InputField(
                "top_spacing_in", float,
                label="Top Spacing (in)  (if double mat)",
                min=6.0, max=18.0, default=12.0,
                hint="Center-to-center bar spacing EW for top mat",
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
        if bool(params.has_double_mat) and params.pad_thickness_in < 8.0:
            triggers.append("thin_double_mat_verify_cover_clearance")
        if params.spacing_in > 15.0:
            triggers.append("pad_spacing_near_max")
        return triggers


TEMPLATE = EquipmentPadTemplate()
