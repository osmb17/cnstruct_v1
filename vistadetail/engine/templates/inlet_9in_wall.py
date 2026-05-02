"""
Template: G2 Inlet  (v5.0)

Caltrans G2 standard inlet box.

Geometry rules (Caltrans Standard Plan D73A):
  - Y interior is ALWAYS fixed at 3'-0" (36.0").
    Y exterior = Y_interior + 2 × T.  Y is never a free input.
  - X exterior is the primary user input.
    X interior = X_exterior − 2 × T.
  - Wall thickness T is always explicitly inputted (9" standard, 11" for
    larger spans).

If a non-standard Y interior is needed use the G2 Expanded Inlet template instead.
Bar sizes and spacings per Vista Steel G2 Inlet spreadsheet (D73A).
"""

from __future__ import annotations

from vistadetail.engine.schema import InputField, Params
from vistadetail.engine.templates.base import BaseTemplate


class InletWallTemplate(BaseTemplate):

    def __init__(self):
        super().__init__()
        self.name = "G2 Inlet"
        self.version = "5.0"
        self.description = (
            "Caltrans G2 inlet — Y interior fixed at 3'-0\" per D73A. "
            "X exterior and wall thickness T are the primary inputs. "
            "Bar sizes/spacings per Vista Steel spreadsheet."
        )

        self.inputs = [
            InputField(
                "x_dim_ft", float,
                label="X -- Exterior Width (ft)",
                min=2.5, max=20.0, default=5.5,
                hint="Exterior face-to-face width in plan. "
                     "Interior X = X − 2×T.",
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
                min=9, max=12, default=9,
                hint="9\" standard; 11\" for larger spans. "
                     "Y exterior = 2'-11 3/8\" + 2×T.",
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
        ratio = params.wall_height_ft / max(x_ft, 0.1)
        if ratio > 2.5:
            triggers.append("aspect_ratio_high")
        return triggers


# ---------------------------------------------------------------------------
# Module-level singleton for TEMPLATE_REGISTRY
# ---------------------------------------------------------------------------

TEMPLATE = InletWallTemplate()
