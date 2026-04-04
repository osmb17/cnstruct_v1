"""
Template: Switchboard Pad  (v1.0)

Double-mat reinforced concrete pad for electrical switchboard panels,
transformer bases, and other heavy equipment requiring anchor dowels.

Always generates double mat (P1–P4) plus optional anchor dowels (D1).
Cover default: 3.0 in — cast against earth (ACI 318-19 Table 20.6.1.3.1).

Covers ~7 PDFs in the clean_examples set:
  Doublemat.verticaldowels.9.6x4.clean   — 9.6'×4', double mat + vert dowels
  swbd.school.doublemat                  — school switchboard pad, double mat
  swbd2a.school.doublemat                — school switchboard pad variant 2A
  swbd3a.school.doublemat                — school switchboard pad variant 3A
  Swbd4.school.doublemat                 — school switchboard pad variant 4
  swbd5a.school.doublemat                — school switchboard pad variant 5A
  swbd6a.school.doublemat                — school switchboard pad variant 6A

Formulas (ACI 318-19 / ACI 360R-10):
  bar_length  = span_dim_in - 2 × cover_in
  qty         = floor(perpendicular_dim_in / spacing_in)
  dowel_len   = dowel_embed_in + dowel_project_in
  dowel_qty   = floor(L/ds) × floor(W/ds)
"""

from __future__ import annotations

from vistadetail.engine.schema import BAR_SIZES, InputField, Params
from vistadetail.engine.templates.base import BaseTemplate


class SwitchboardPadTemplate(BaseTemplate):
    name: str = "Switchboard Pad"
    version: str = "1.0"
    description: str = (
        "Double-mat concrete pad for switchboard / transformer equipment. "
        "Always double mat (P1–P4 bottom+top EW). "
        "Optional vertical anchor dowels (D1) projecting above pad top."
    )

    def __init__(self):
        super().__init__()
        self.name        = "Switchboard Pad"
        self.version     = "1.0"
        self.description = (
            "Double-mat concrete pad for switchboard / transformer equipment. "
            "Always double mat (P1–P4 bottom+top EW). "
            "Optional vertical anchor dowels (D1) projecting above pad top."
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
            # ── Bottom mat ────────────────────────────────────────────────
            InputField(
                "bar_size", str,
                label="Bar Size  (bottom mat)",
                choices=BAR_SIZES, default="#4",
                hint="Bar size for bottom mat — both directions",
            ),
            InputField(
                "spacing_in", float,
                label="Spacing (in)  — bottom mat",
                min=6.0, max=18.0, default=12.0,
                hint="Center-to-center bar spacing EW for bottom mat",
            ),
            InputField(
                "cover_in", float,
                label="Clear Cover (in)",
                min=2.0, max=6.0, default=3.0,
                hint="3 in for concrete cast against earth (ACI Table 20.6.1.3.1)",
            ),
            # ── Top mat ───────────────────────────────────────────────────
            InputField(
                "top_bar_size", str,
                label="Top Bar Size",
                choices=BAR_SIZES, default="#4",
                hint="Bar size for top mat — both directions",
            ),
            InputField(
                "top_spacing_in", float,
                label="Top Spacing (in)",
                min=6.0, max=18.0, default=12.0,
                hint="Center-to-center bar spacing EW for top mat",
            ),
            # ── Vertical dowels ───────────────────────────────────────────
            InputField(
                "has_vertical_dowels", float,
                label="Vertical Anchor Dowels? (0=No 1=Yes)",
                min=0.0, max=1.0, default=1.0,
                hint="1 = generate D1 anchor dowel grid projecting above pad",
            ),
            InputField(
                "dowel_bar_size", str,
                label="Dowel Bar Size",
                choices=BAR_SIZES, default="#4",
                hint="Bar size for vertical anchor dowels",
            ),
            InputField(
                "dowel_spacing_in", float,
                label="Dowel Grid Spacing (in)",
                min=6.0, max=24.0, default=12.0,
                hint="Center-to-center spacing of dowel grid EW",
            ),
            InputField(
                "dowel_embed_in", float,
                label="Dowel Embed into Pad (in)",
                min=6.0, max=24.0, default=12.0,
                hint="Embedment length into pad ≥ development length (12 in min for #4-#5)",
            ),
            InputField(
                "dowel_project_in", float,
                label="Dowel Projection above Pad (in)",
                min=6.0, max=36.0, default=18.0,
                hint="Height of dowel stub projecting above top of pad to anchor equipment",
            ),
            # ── Hidden fixed field — always double mat ────────────────────
            InputField(
                "has_double_mat", float,
                label="Double Mat (always 1 for switchboard pad)",
                min=1.0, max=1.0, default=1.0,
                hint="Fixed at 1 — switchboard pads always use double mat",
            ),
        ]

        self.rules = [
            "rule_pad_bottom_long",
            "rule_pad_bottom_short",
            "rule_pad_top_long",
            "rule_pad_top_short",
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
        if bool(params.has_vertical_dowels) and params.dowel_embed_in < 12.0:
            triggers.append("short_dowel_embed_verify_development_length")
        return triggers


TEMPLATE = SwitchboardPadTemplate()
