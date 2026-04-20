"""
Template: Pipe Encasement  (v2.0)

Rectangular concrete jacket cast around an underground pipe.
#5 hoops @9oc, 12 #4 longitudinal bars, 2\" cover — hardcoded standards.

Generates:
  E1 — transverse hoops encircling the cross-section
  E2 — longitudinal bars running along the full pipe length
"""

from __future__ import annotations

from vistadetail.engine.schema import BAR_SIZES, InputField, Params
from vistadetail.engine.templates.base import BaseTemplate


class PipeEncasementTemplate(BaseTemplate):

    def __init__(self):
        super().__init__()
        self.name        = "Pipe Encasement"
        self.version     = "2.0"
        self.description = (
            "Rectangular concrete jacket encasing an underground pipe. "
            "E1 hoops @9oc + E2 longitudinal bars (12 #4). 2\" cover."
        )

        self.inputs = [
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
                hint="Transverse outside width of the rectangular cross-section",
            ),
            InputField(
                "encasement_height_in", float,
                label="Encasement Height (in)  — outside face to outside face",
                min=8.0, max=120.0, default=44.0,
                hint="Vertical outside height of the rectangular cross-section",
            ),
            InputField(
                "hoop_bar_size", str,
                label="Hoop Bar Size",
                choices=BAR_SIZES, default="#5",
                hint="Bar size for transverse hoops — #5 typical for large pipe encasement",
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
        return triggers


TEMPLATE = PipeEncasementTemplate()
