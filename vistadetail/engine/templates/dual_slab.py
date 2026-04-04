"""
Template: Dual Slab  (v1.0)

Two adjacent rectangular slabs on compacted earth, each with an independent
EW mat. Used for AT&T / telecom equipment foundations and similar split-pad designs.

Generates:
  A1 — Slab A long bars
  A2 — Slab A short bars
  B1 — Slab B long bars
  B2 — Slab B short bars

Covers 3 PDFs in the clean_examples set:
  2slab.at.and.t      — AT&T dual slab (2 pages)
  2slab.at.andt(A)    — AT&T slab variant A
  2slab.at.and.t(B)   — AT&T slab variant B

Formulas (ACI 318-19 / ACI 360R-10):
  bar_length = span_dim_in - 2 × cover_in
  qty        = floor(perpendicular_dim_in / spacing_in)

Cover default: 3.0 in (cast against earth, ACI Table 20.6.1.3.1).
"""

from __future__ import annotations

from vistadetail.engine.schema import BAR_SIZES, InputField, Params
from vistadetail.engine.templates.base import BaseTemplate


class DualSlabTemplate(BaseTemplate):
    name: str = "Dual Slab"
    version: str = "1.0"
    description: str = (
        "Two adjacent slabs on compacted earth (AT&T / telecom equipment pads). "
        "Slab A → A1/A2; Slab B → B1/B2. Independent sizes and spacing."
    )

    def __init__(self):
        super().__init__()
        self.name        = "Dual Slab"
        self.version     = "1.0"
        self.description = (
            "Two adjacent slabs on compacted earth (AT&T / telecom equipment pads). "
            "Slab A → A1/A2; Slab B → B1/B2. Independent sizes and spacing."
        )

        self.inputs = [
            # ── Slab A ────────────────────────────────────────────────────
            InputField("slab_a_length_ft", float,
                       label="Slab A Length (ft)", min=1.0, max=200.0, default=8.0,
                       hint="Longer plan dimension of Slab A in feet"),
            InputField("slab_a_width_ft", float,
                       label="Slab A Width (ft)",  min=1.0, max=200.0, default=5.0,
                       hint="Shorter plan dimension of Slab A in feet"),
            InputField("slab_a_bar_size", str,
                       label="Slab A Bar Size", choices=BAR_SIZES, default="#4",
                       hint="Bar size for Slab A, both directions"),
            InputField("slab_a_spacing_in", float,
                       label="Slab A Spacing (in)", min=6.0, max=18.0, default=12.0,
                       hint="Center-to-center bar spacing EW for Slab A"),
            # ── Slab B ────────────────────────────────────────────────────
            InputField("slab_b_length_ft", float,
                       label="Slab B Length (ft)", min=1.0, max=200.0, default=6.0,
                       hint="Longer plan dimension of Slab B in feet"),
            InputField("slab_b_width_ft", float,
                       label="Slab B Width (ft)",  min=1.0, max=200.0, default=4.0,
                       hint="Shorter plan dimension of Slab B in feet"),
            InputField("slab_b_bar_size", str,
                       label="Slab B Bar Size", choices=BAR_SIZES, default="#4",
                       hint="Bar size for Slab B, both directions"),
            InputField("slab_b_spacing_in", float,
                       label="Slab B Spacing (in)", min=6.0, max=18.0, default=12.0,
                       hint="Center-to-center bar spacing EW for Slab B"),
            # ── Shared cover ──────────────────────────────────────────────
            InputField("cover_in", float,
                       label="Clear Cover (in)", min=2.0, max=6.0, default=3.0,
                       hint="3 in for cast against earth (ACI Table 20.6.1.3.1)"),
        ]

        self.rules = [
            "rule_dual_slab_A_long",
            "rule_dual_slab_A_short",
            "rule_dual_slab_B_long",
            "rule_dual_slab_B_short",
            "rule_validate_dual_slab",
        ]

    def evaluate_triggers(self, params: Params) -> list[str]:
        triggers: list[str] = []
        total_area = (params.slab_a_length_ft * params.slab_a_width_ft
                      + params.slab_b_length_ft * params.slab_b_width_ft)
        if total_area > 500.0:
            triggers.append("large_dual_slab_verify_expansion_joints")
        return triggers


TEMPLATE = DualSlabTemplate()
