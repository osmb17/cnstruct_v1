"""
Template: Switchboard Pad  (v2.0)

Double-mat reinforced concrete pad for electrical switchboard panels,
transformer bases, and other heavy equipment requiring anchor dowels.

Always generates double mat (P1–P4) plus optional anchor dowels (D1).
#4@12oc double mat, #4 anchor dowels @12oc, 3\" cover.

Covers ~7 PDFs in the clean_examples set:
  Doublemat.verticaldowels.9.6x4.clean   — 9.6'×4', double mat + vert dowels
  swbd.school.doublemat                  — school switchboard pad, double mat
  swbd2a.school.doublemat                — school switchboard pad variant 2A
  swbd3a.school.doublemat                — school switchboard pad variant 3A
  Swbd4.school.doublemat                 — school switchboard pad variant 4
  swbd5a.school.doublemat                — school switchboard pad variant 5A
  swbd6a.school.doublemat                — school switchboard pad variant 6A

Formulas (ACI 318-19 / ACI 360R-10):
  bar_length  = span_dim_in - 2 × 3.0 (cover)
  qty         = floor(perpendicular_dim_in / 12.0 (spacing))
  dowel_len   = 12.0 (embed) + 18.0 (project) = 30 in
  dowel_qty   = floor(L/12) × floor(W/12)
"""

from __future__ import annotations

from vistadetail.engine.schema import InputField, Params
from vistadetail.engine.templates.base import BaseTemplate


class SwitchboardPadTemplate(BaseTemplate):
    name: str = "Switchboard Pad"
    version: str = "2.0"
    description: str = (
        "Switchboard pad. #4@12oc double mat, #4 anchor dowels @12oc, 3\" cover."
    )

    def __init__(self):
        super().__init__()
        self.name        = "Switchboard Pad"
        self.version     = "2.0"
        self.description = (
            "Switchboard pad. #4@12oc double mat, #4 anchor dowels @12oc, 3\" cover."
        )

        self.inputs = [
            # ── Plan dimensions ───────────────────────────────────────────
            InputField(
                "pad_length_ft", float,
                label="Pad Length (ft)  — long side",
                min=1.0, max=60.0, default=9.6,
                hint="Longer plan dimension in feet",
            ),
            InputField(
                "pad_width_ft", float,
                label="Pad Width (ft)  — short side",
                min=1.0, max=60.0, default=4.0,
                hint="Shorter plan dimension in feet",
            ),
            InputField(
                "pad_thickness_in", float,
                label="Pad Thickness (in)",
                min=6.0, max=36.0, default=8.0,
                hint="Typical switchboard pad: 8–12 in for double mat clearance",
            ),
            # ── Vertical dowels ───────────────────────────────────────────
            InputField(
                "has_vertical_dowels", float,
                label="Vertical Anchor Dowels? (0=No 1=Yes)",
                min=0.0, max=1.0, default=1.0,
                hint="1 = generate D1 anchor dowel grid projecting above pad",
            ),
        ]

        self.rules = [
            "rule_pad_bottom_long",
            "rule_pad_bottom_short",
            "rule_swbd_top_long",
            "rule_swbd_top_short",
            "rule_pad_vertical_dowels",
            "rule_validate_equipment_pad",
        ]

    def evaluate_triggers(self, params: Params) -> list[str]:
        triggers: list[str] = []
        area = params.pad_length_ft * params.pad_width_ft
        if area > 200.0:
            triggers.append("large_switchboard_pad_verify_structural_design")
        if params.pad_thickness_in < 8.0:
            triggers.append("thin_double_mat_verify_cover_clearance")
        return triggers


TEMPLATE = SwitchboardPadTemplate()
