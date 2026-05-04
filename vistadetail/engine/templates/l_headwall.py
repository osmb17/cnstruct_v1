"""Template: L Headwall (v1.0) — Caltrans D89A/D89B, one-sided footing."""

from __future__ import annotations

from vistadetail.engine.schema import InputField, Params
from vistadetail.engine.templates.base import BaseTemplate


class LHeadwallTemplate(BaseTemplate):

    def __init__(self):
        super().__init__()
        self.name = "L Headwall"
        self.version = "1.0"
        self.description = (
            "Caltrans D89A/D89B 'L' headwall — same wall geometry and table as the "
            "straight headwall but with a one-sided footing (heel only, no toe "
            "projection C).  Case I uses the D89A table (higher loading); "
            "Cases II/III use the D89B table (lighter loading)."
        )

        self.inputs = [
            InputField(
                "loading_case", str, label="Loading Case",
                choices=["I", "II / III"],
                default="I",
                group="Design",
                hint="Case I = D89A (higher loading); Cases II/III = D89B (lighter loading)",
            ),
            InputField(
                "wall_width_ft", float, label="Wall Width (ft)",
                min=4.0, max=30.0, default=8.0,
                group="Geometry",
                hint="Total wall length (parallel to pipe axis)",
            ),
            InputField(
                "wall_height_ft", float, label="Wall Height H (ft)",
                min=2.0, max=12.0, default=5.0,
                hint=(
                    "Wall height H above footing top. "
                    "Caltrans D89A/D89B table rounds up to the nearest standard row."
                ),
            ),
            InputField(
                "pipe_qty", int, label="Number of Pipes",
                min=0, max=4, default=0,
                group="Pipe",
                hint="Number of existing pipes through the headwall (0 = none)",
            ),
            InputField(
                "pipe_dia_in", str, label="Pipe Diameter",
                choices=["12\"", "15\"", "18\"", "21\"", "24\"", "27\"",
                         "30\"", "33\"", "36\"", "42\"", "48\"", "54\"",
                         "60\"", "66\"", "72\""],
                default="24\"",
                hint="Nominal RCP pipe diameter",
            ),
        ]

        # Reuses the same D89A/D89B rule functions as the straight headwall.
        #
        # ASSUMPTION: all bar lengths and quantities are identical to the
        # straight headwall because the existing formulas do not reference the
        # C (toe) dimension.  The CB (C-bar) toe leg and whether it becomes an
        # L-bar on this structure should be verified against a gold barlist.
        self.rules = [
            "rule_hw_trans_footing",   # TF  — transverse footing    (B+F, same as straight)
            "rule_hw_d_bars",          # D1  — top invert D-bars      (B+F)
            "rule_hw_long_invert",     # LI  — longitudinal footing   (L-6)
            "rule_hw_pipe_hoops",      # PH  — pipe hoops mk600       (pipe only)
            "rule_hw_pipe_opening",    # PO  — pipe opening bars      (pipe only)
            "rule_hw_vert_wall",       # VW  — vertical wall bars
            "rule_hw_c_bars",          # CB  — C-bar hairpin  ← ASSUMPTION: same leg formula
            "rule_hw_long_wall",       # LW  — longitudinal wall bars
            "rule_hw_top_wall",        # TW  — top-of-wall bars
            "rule_hw_spreaders",       # WS  — wall spreaders mk401
            "rule_hw_standees",        # ST  — mat standees mk400
            "rule_validate_headwall",  # validation / warnings
        ]

    def evaluate_triggers(self, params: Params) -> list[str]:
        triggers: list[str] = []
        H = params.wall_height_ft * 12
        case = getattr(params, "loading_case", "I")
        max_h = 77 if case == "II / III" else 83
        if H > max_h:
            triggers.append("height_exceeds_d89_table")
        return triggers


TEMPLATE = LHeadwallTemplate()
