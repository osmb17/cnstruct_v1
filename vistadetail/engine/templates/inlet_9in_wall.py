"""
Template: G2 Inlet  (v4.0)

Caltrans G2 standard inlet box.  X (exterior width) is the primary driving
dimension.  Wall thickness T and grate opening L1 are auto-calculated.

Bar sizes and spacings are fixed per the Vista Steel G2 Inlet spreadsheet
(matches Caltrans Standard Plan D73A).
"""

from __future__ import annotations

from vistadetail.engine.schema import InputField, Params
from vistadetail.engine.templates.base import BaseTemplate


class InletWallTemplate(BaseTemplate):
    name: str = "G2 Inlet"
    version: str = "4.0"
    description: str = (
        "Caltrans G2 inlet — X/Y exterior dimensions drive all geometry. "
        "T auto-derives (9\" if interior X<=54\", 11\" otherwise). "
        "Bar sizes/spacings per Vista Steel spreadsheet."
    )

    def __init__(self):
        super().__init__()
        self.name = "G2 Inlet"
        self.version = "4.0"
        self.description = (
            "Caltrans G2 inlet — X/Y exterior dimensions drive all geometry. "
            "T auto-derives (9\" if interior X<=54\", 11\" otherwise). "
            "Bar sizes/spacings per Vista Steel spreadsheet."
        )

        self.inputs = [
            # ── Primary geometry ──────────────────────────────────────────────
            InputField(
                "x_dim_ft", float,
                label="X -- Exterior Width (ft)",
                min=2.5, max=20.0, default=5.5,
                hint="Primary driving dimension -- exterior face-to-face width in plan",
            ),
            InputField(
                "y_dim_ft", float,
                label="Y -- Exterior Depth (ft)",
                min=2.5, max=10.0, default=4.5,
                hint="Exterior depth in plan",
            ),
            InputField(
                "inside_x_in", float,
                label="Inside X Dimension (in)",
                min=0.0, max=120.0, default=0.0,
                hint="2'-11 3/8\" min or Pipe penetration diameter + 3\" min (90\" max). 0 = auto from exterior X.",
            ),
            InputField(
                "inside_y_in", float,
                label="Inside Y Dimension (in)",
                min=0.0, max=120.0, default=0.0,
                hint="2'-11 3/8\" min (Caltrans G2 minimum clear depth). 0 = auto from exterior Y.",
            ),
            InputField(
                "wall_height_ft", float,
                label="Wall Height (ft)",
                min=2.0, max=20.0, default=4.0,
                hint="Bottom of footing to top of wall",
            ),
            InputField(
                "wall_thick_in", int,
                label="Wall Thickness (in)",
                min=0, max=24, default=0,
                hint="0 = auto (9\" if interior X<=54\", 11\" otherwise)",
            ),
            InputField(
                "grate_type", str,
                label="Grate Type",
                choices=["Type 24", "Type 18"], default="Type 24",
                hint="Controls grate deduction: Type 24 = 24\", Type 18 = 18\"",
            ),
            InputField(
                "num_structures", int,
                label="Number of Structures",
                min=1, max=50, default=1,
                hint="Multiplier for quantities (bottom mat, right angle, hoops)",
            ),
        ]

        self.rules = [
            "rule_g2_geometry",
            "rule_g2_bottom_mat",
            "rule_g2_horizontals",
            "rule_g2_verticals",
            "rule_g2_ab_bars",
            "rule_g2_right_angle",
            "rule_g2_hoops",
        ]

    def evaluate_triggers(self, params: Params) -> list[str]:
        triggers: list[str] = []

        x_ft = getattr(params, "x_dim_ft", 5.5)
        y_ft = getattr(params, "y_dim_ft", 4.5)
        ratio = params.wall_height_ft / max(x_ft, 0.1)
        if ratio > 2.5:
            triggers.append("aspect_ratio_high")

        # Warn if Y is very close to minimum viable depth
        t_est = 9.0 / 12 if x_ft * 12 <= 54 else 11.0 / 12
        min_y = (35.375 / 12) + 2 * t_est
        if y_ft < min_y + 0.1:
            triggers.append("y_dim_near_minimum")

        return triggers


# ---------------------------------------------------------------------------
# Module-level singleton for TEMPLATE_REGISTRY
# ---------------------------------------------------------------------------

TEMPLATE = InletWallTemplate()
