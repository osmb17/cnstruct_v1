"""
Template: Pipe Encasement  (v1.0)

Rectangular concrete jacket cast around an underground pipe.

Generates:
  E1 — transverse hoops encircling the cross-section
  E2 — longitudinal bars running along the full pipe length

Covers 2 PDFs in the clean_examples set:
  Route118SandCanyontoBalcomCanyon.pipe.encasement  — 234 linear ft, #5@9oc, 165 #4 long
  pipe.encasement.balcom.canyon.layout              — 234 linear ft layout

Formulas:
  hoop_length  = 2×(W − 2c) + 2×(H − 2c)    rectangular hoop perimeter
  hoop_qty     = floor(encasement_length_in / hoop_spacing_in)
  long_length  = encasement_length_in − 2×cover_in
  long_qty     = n_long_bars  (user-specified)

Cover default: 2.0 in — buried, exposed to earth, not cast against earth
               (ACI 318-19 Table 20.6.1.3.1).

Verified against Route 118 encasement:
  234 ft × #5@9oc → E1 qty = floor(2808/9) = 312 (drawing shows 315 with overrun)
"""

from __future__ import annotations

from vistadetail.engine.schema import BAR_SIZES, InputField, Params
from vistadetail.engine.templates.base import BaseTemplate


class PipeEncasementTemplate(BaseTemplate):
    name: str = "Pipe Encasement"
    version: str = "1.0"
    description: str = (
        "Rectangular concrete jacket encasing an underground pipe. "
        "E1 transverse hoops + E2 longitudinal bars."
    )

    def __init__(self):
        super().__init__()
        self.name        = "Pipe Encasement"
        self.version     = "1.0"
        self.description = (
            "Rectangular concrete jacket encasing an underground pipe. "
            "E1 transverse hoops + E2 longitudinal bars."
        )

        self.inputs = [
            # ── Encasement geometry ───────────────────────────────────────
            InputField(
                "encasement_length_ft", float,
                label="Encasement Length (ft)  — along pipe",
                min=2.0, max=2000.0, default=234.0,
                hint="Total linear footage of pipe encasement",
            ),
            InputField(
                "encasement_width_in", float,
                label="Encasement Width (in)  — outside face to outside face",
                min=8.0, max=120.0, default=44.0,
                hint="Transverse outside width of the rectangular encasement cross-section",
            ),
            InputField(
                "encasement_height_in", float,
                label="Encasement Height (in)  — outside face to outside face",
                min=8.0, max=120.0, default=44.0,
                hint="Vertical outside height of the rectangular encasement cross-section",
            ),
            # ── Transverse (hoop) reinforcement ───────────────────────────
            InputField(
                "hoop_bar_size", str,
                label="Hoop Bar Size",
                choices=BAR_SIZES, default="#5",
                hint="Bar size for transverse hoops — #5 typical for large pipe encasement",
            ),
            InputField(
                "hoop_spacing_in", float,
                label="Hoop Spacing (in)",
                min=3.0, max=18.0, default=9.0,
                hint="Center-to-center hoop spacing along the pipe length",
            ),
            # ── Longitudinal reinforcement ────────────────────────────────
            InputField(
                "long_bar_size", str,
                label="Longitudinal Bar Size",
                choices=BAR_SIZES, default="#4",
                hint="Bar size for longitudinal bars running along pipe",
            ),
            InputField(
                "n_long_bars", float,
                label="Number of Longitudinal Bars",
                min=2.0, max=32.0, default=12.0,
                hint="Count of longitudinal bars in cross-section (typically 8–16 for large pipe)",
            ),
            # ── Cover ─────────────────────────────────────────────────────
            InputField(
                "cover_in", float,
                label="Clear Cover (in)",
                min=1.5, max=4.0, default=2.0,
                hint="2 in for buried concrete not cast against earth (ACI Table 20.6.1.3.1)",
            ),
        ]

        self.rules = [
            "rule_encasement_hoops",
            "rule_encasement_longitudinals",
            "rule_validate_pipe_encasement",
        ]

    def evaluate_triggers(self, params: Params) -> list[str]:
        triggers: list[str] = []
        if params.encasement_length_ft > 500.0:
            triggers.append("long_encasement_expansion_joints_and_construction_joints_required")
        if params.hoop_spacing_in < 6.0:
            triggers.append("tight_hoop_spacing_verify_concrete_placement_clearance")
        return triggers


TEMPLATE = PipeEncasementTemplate()
