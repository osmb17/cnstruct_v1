"""
Template: Sound Wall (v1.0) -- Caltrans B15-1 through B15-5.

Masonry block sound wall on spread footing, trench footing, or CIDH pile cap.
Rebar lookup tables from Caltrans 2025 Standard Plans.

Marks:
  WV1 -- vertical a-bars (each face of wall)
  WV2 -- vertical b-bars (each face, H >= 8')
  WH1 -- horizontal c-bars (bond beam reinf)
  FD1 -- footing d-bars (dowels into footing)
  FT1 -- footing transverse bars
  FL1 -- footing longitudinal bars
  PL1 -- pile longitudinal bars (pile cap variant)
  PS1 -- pile spiral (pile cap variant)
  PC1 -- pile cap transverse bars
"""

from __future__ import annotations

from vistadetail.engine.schema import BAR_SIZES, InputField, Params
from vistadetail.engine.templates.base import BaseTemplate


class SoundWallTemplate(BaseTemplate):

    def __init__(self):
        super().__init__()
        self.name = "Sound Wall"
        self.version = "1.0"
        self.description = (
            "Caltrans B15 masonry block sound wall on spread footing, "
            "trench footing, or CIDH pile cap. Lookup tables by wall height."
        )

        self.inputs = [
            # -- Geometry --
            InputField("wall_height_ft", float, label="Wall Height H (ft)",
                       min=6.0, max=16.0, default=10.0,
                       hint="Design height per B15-1 tables: 6, 8, 10, 12, 14, or 16 ft"),
            InputField("wall_length_ft", float, label="Wall Length (ft)",
                       min=8.0, max=2000.0, default=200.0,
                       hint="Total wall length for qty calculations"),
            InputField("cover_in", float, label="Clear Cover (in)",
                       min=1.5, max=4.0, default=2.0),
            # -- Foundation type --
            InputField("foundation_type", str, label="Foundation Type",
                       choices=["spread_footing", "trench_footing", "pile_cap"],
                       default="spread_footing",
                       hint="Per B15-1 (spread/trench) or B15-3 (pile cap)"),
            # -- Ground condition --
            InputField("ground_case", str, label="Ground Case",
                       choices=["case_1", "case_2"],
                       default="case_1",
                       hint="Case 1: level both sides. Case 2: level one side, slope opposite"),
            # -- Soil friction angle (for pile cap) --
            InputField("soil_phi_deg", float, label="Soil Friction Angle (deg)",
                       min=25.0, max=35.0, default=30.0,
                       hint="Phi for pile data table lookup: 25, 30, or 35 deg"),
            # -- Expansion joint spacing --
            InputField("exp_joint_spacing_ft", float, label="Expansion Joint Spacing (ft)",
                       min=24.0, max=48.0, default=48.0,
                       hint="Max 48 ft per B15 notes"),
        ]

        self.rules = [
            "rule_sw_wall_verticals",
            "rule_sw_wall_horizontals",
            "rule_sw_footing_dowels",
            "rule_sw_footing_bars",
            "rule_sw_pile_cage",
            "rule_sw_pile_cap_bars",
            "rule_validate_sound_wall",
        ]

    def evaluate_triggers(self, params: Params) -> list[str]:
        triggers: list[str] = []
        if params.wall_height_ft > 14:
            triggers.append("tall_wall")
        if params.foundation_type == "pile_cap" and params.soil_phi_deg < 30:
            triggers.append("soft_soil")
        return triggers


TEMPLATE = SoundWallTemplate()
