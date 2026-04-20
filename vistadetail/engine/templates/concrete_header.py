"""
Template: Concrete Header  (v1.0)

Low rectangular concrete border beam used as a playground header, curb,
or landscape edge element. Reinforced with top + bottom longitudinal bars
and transverse bars spanning the cross-section width.

Generates:
  H1 — top longitudinal bars (along full header length)
  H2 — bottom longitudinal bars (along full header length)
  H3 — transverse bars (across header width, spaced along length)

Covers 4 PDFs in the clean_examples set:
  Portola.ES.header.67x3.clean    — 67'-0" × 36" section
  Portola.ES.header45x3.clean     — 45'-0" × 36" section
  detail.concrete.header.portola.es.playground.p1
  detail.concrete.header.portola.es.playground.p2

Formulas:
  long_length  = header_length_in - 2 × cover_in
  trans_length = header_width_in  - 2 × cover_in
  trans_qty    = floor(header_length_in / tie_spacing_in)

Cover default: 1.5 in (exposed to weather, ACI Table 20.6.1.3.1).
"""

from __future__ import annotations

from vistadetail.engine.schema import InputField, Params
from vistadetail.engine.templates.base import BaseTemplate


class ConcreteHeaderTemplate(BaseTemplate):
    name: str = "Concrete Header"
    version: str = "2.0"
    description: str = (
        "Concrete header/grade beam. #4 bars, #3 ties @18oc, 1.5\" cover."
    )

    def __init__(self):
        super().__init__()
        self.name        = "Concrete Header"
        self.version     = "2.0"
        self.description = (
            "Concrete header/grade beam. #4 bars, #3 ties @18oc, 1.5\" cover."
        )

        self.inputs = [
            # ── Header geometry ───────────────────────────────────────────
            InputField(
                "header_length_ft", float,
                label="Header Length (ft)",
                min=2.0, max=300.0, default=67.0,
                hint="Total header/curb length in feet",
            ),
            InputField(
                "header_height_in", float,
                label="Header Height (in)",
                min=6.0, max=48.0, default=24.0,
                hint="Cross-section height of the header (vertical dimension)",
            ),
            InputField(
                "header_width_in", float,
                label="Header Width (in)  — cross-section depth",
                min=4.0, max=36.0, default=12.0,
                hint="Cross-section width of the header (horizontal depth into playground)",
            ),
            # ── Top longitudinal reinforcement ────────────────────────────
            InputField(
                "top_bar_count", float,
                label="Top Bar Count",
                min=1.0, max=8.0, default=2.0,
                hint="Number of longitudinal bars at top (typically 2)",
            ),
            # ── Bottom longitudinal reinforcement ─────────────────────────
            InputField(
                "bot_bar_count", float,
                label="Bottom Bar Count",
                min=1.0, max=8.0, default=2.0,
                hint="Number of longitudinal bars at bottom (typically 2)",
            ),
        ]

        self.rules = [
            "rule_header_top_long",
            "rule_header_bot_long",
            "rule_header_transverse",
            "rule_validate_concrete_header",
        ]

    def evaluate_triggers(self, params: Params) -> list[str]:
        triggers: list[str] = []
        if params.header_height_in > 30.0:
            triggers.append("tall_header_consider_retaining_wall_design")
        if params.header_length_ft > 100.0:
            triggers.append("long_header_verify_expansion_joints")
        return triggers


TEMPLATE = ConcreteHeaderTemplate()
