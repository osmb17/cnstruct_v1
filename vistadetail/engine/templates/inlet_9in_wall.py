"""
Template: G2 Inlet  (v3.0)

Caltrans G2 standard inlet box.  X (exterior width) is the primary driving
dimension.  Wall thickness T and grate opening L1 are auto-calculated.

Caltrans Standard Plan D73A / AASHTO LRFD reference.
"""

from __future__ import annotations

from vistadetail.engine.schema import BAR_SIZES, HOOK_TYPES, InputField, Params
from vistadetail.engine.templates.base import BaseTemplate


class InletWallTemplate(BaseTemplate):
    name: str = "G2 Inlet"
    version: str = "3.0"
    description: str = (
        "Caltrans G2 inlet — X/Y exterior dimensions drive all geometry. "
        "T auto-derives (9\" if X≤54\", 11\" if X>54\"). "
        "L1 (grate opening) = interior width − grate deduction. "
        "Bar spacing auto-enforces ACI 318-19 §24.3.2."
    )

    def __init__(self):
        super().__init__()
        self.name = "G2 Inlet"
        self.version = "3.0"
        self.description = (
            "Caltrans G2 inlet — X/Y exterior dimensions drive all geometry. "
            "T auto-derives (9\" if X≤54\", 11\" if X>54\"). "
            "L1 (grate opening) = interior width − grate deduction. "
            "Bar spacing auto-enforces ACI 318-19 §24.3.2."
        )

        self.inputs = [
            # ── Primary geometry ──────────────────────────────────────────────
            InputField(
                "x_dim_ft", float,
                label="X — Exterior Width (ft)",
                min=2.5, max=20.0, default=5.5,
                hint="Primary driving dimension — exterior face-to-face width in plan",
            ),
            InputField(
                "y_dim_ft", float,
                label="Y — Exterior Depth (ft)",
                min=2.5, max=10.0, default=4.5,
                hint="Exterior depth in plan (constrained: min interior ≈ 2'-11 3/8\" + 2T)",
            ),
            InputField(
                "wall_height_ft", float,
                label="Wall Height (ft)",
                min=2.0, max=20.0, default=4.0,
                hint="Elevation height — bottom of footing to top of wall",
            ),
            InputField(
                "wall_thick_in", int,
                label="Wall Thickness (in)",
                min=0, max=24, default=0,
                hint="0 = auto (9\" if X≤54\", 11\" if X>54\") — override only if needed",
            ),
            InputField(
                "grate_type", str,
                label="Grate Type",
                choices=["Type 24", "Type 18"], default="Type 24",
                hint="Controls L1 deduction: Type 24 → −24\", Type 18 → −18\"",
            ),
            InputField(
                "pipe_diam_in", float,
                label="Pipe Diameter (in)",
                min=0.0, max=96.0, default=24.0,
                hint="Inlet pipe OD — used to check L1 clearance (0 = no pipe check)",
            ),
            # ── Cover & reinforcement ─────────────────────────────────────────
            InputField(
                "cover_in", float,
                label="Clear Cover (in)",
                min=1.5, max=4.0, default=2.0,
                hint="Clear cover to outermost bar — check exposure class",
            ),
            InputField(
                "horiz_bar_size", str,
                label="Horiz Bar Size",
                choices=BAR_SIZES, default="#5",
                hint="Horizontal bars, each face",
            ),
            InputField(
                "horiz_spacing_in", float,
                label="Horiz Spacing (in)",
                min=3.0, max=18.0, default=12.0,
                hint="Center-to-center spacing of horizontal bars",
            ),
            InputField(
                "vert_bar_size", str,
                label="Vert Bar Size",
                choices=BAR_SIZES, default="#5",
                hint="Vertical bars, each face",
            ),
            InputField(
                "vert_spacing_in", float,
                label="Vert Spacing (in)",
                min=3.0, max=18.0, default=12.0,
                hint="Center-to-center spacing of vertical bars",
            ),
            InputField(
                "hook_type", str,
                label="Hook Type",
                choices=HOOK_TYPES, default="std_90",
                hint="Hook type for horizontal bar ends",
            ),
            InputField(
                "corner_bars", str,
                label="Corner L-Bars",
                choices=["yes", "no"], default="yes",
                hint="Include corner L-bars at wall edges",
            ),
            InputField(
                "corner_bar_size", str,
                label="Corner Bar Size",
                choices=BAR_SIZES, default="#4",
                hint="Size for corner L-bars (if enabled)",
            ),
        ]

        self.rules = [
            "rule_g2_inlet_geometry",       # FIRST — derives T, L1, sets wall_length_ft alias
            "rule_horizontal_bars_EF",
            "rule_vertical_bars_EF",
            "rule_corner_L_bars",
            "rule_validate_min_cover",
            "rule_validate_max_spacing_ACI",
        ]

    def evaluate_triggers(self, params: Params) -> list[str]:
        triggers: list[str] = []

        cover = params.cover_in
        if cover < 1.5 or cover > 3.0:
            triggers.append("cover_unusual")
        if cover <= 2.0:
            triggers.append("thin_cover_soil")

        h_sp = params.horiz_spacing_in
        v_sp = params.vert_spacing_in
        if h_sp > 16.0 or v_sp > 16.0:
            triggers.append("spacing_near_max")

        # Use x_dim_ft; wall_length_ft alias set by geometry rule at runtime
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
