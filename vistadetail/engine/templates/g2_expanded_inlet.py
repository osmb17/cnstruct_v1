"""
Template: G2 Expanded Inlet  (v2.0)

Caltrans G2 expanded-size inlet box.  Wider than the standard G2 — typically
used where the drainage opening requires more flow area.

Same X/Y parametric geometry as G2 Inlet.  T auto-derives (9\" if X≤54\",
11\" if X>54\").  Expanded inlets typically have X > 54\" so T = 11\" in most
practical cases.
"""

from __future__ import annotations

from vistadetail.engine.schema import BAR_SIZES, HOOK_TYPES, InputField, Params
from vistadetail.engine.templates.base import BaseTemplate


class G2ExpandedInletTemplate(BaseTemplate):

    def __init__(self):
        super().__init__()
        self.name = "G2 Expanded Inlet"
        self.version = "2.0"
        self.description = (
            "Caltrans G2 expanded inlet — wider box than standard G2. "
            "X/Y exterior dimensions drive geometry; T auto-derives. "
            "Bar spacing auto-enforces ACI 318-19 §24.3.2."
        )

        self.inputs = [
            # ── Primary geometry ──────────────────────────────────────────────
            InputField(
                "x_dim_ft", float,
                label="X — Exterior Width (ft)",
                min=4.0, max=30.0, default=9.0,
                hint="Primary driving dimension — exterior face-to-face width in plan (typically >54\" → T=11\")",
            ),
            InputField(
                "y_dim_ft", float,
                label="Y — Exterior Depth (ft)",
                min=2.5, max=12.0, default=5.5,
                hint="Exterior depth in plan (constrained: min interior ≈ 2'-11 3/8\" + 2T)",
            ),
            InputField(
                "wall_height_ft", float,
                label="Wall Height (ft)",
                min=2.0, max=20.0, default=6.0,
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
                min=0.0, max=96.0, default=36.0,
                hint="Inlet pipe OD — used to check L1 clearance (0 = no pipe check)",
            ),
            # ── Cover & reinforcement ─────────────────────────────────────────
            InputField(
                "cover_in",         float, label="Clear Cover (in)",    min=1.5, max=4.0, default=2.0),
            InputField(
                "horiz_bar_size",   str,   label="Horiz Bar Size",      choices=BAR_SIZES,  default="#5"),
            InputField(
                "horiz_spacing_in", float, label="Horiz Spacing (in)",  min=6.0, max=18.0, default=12.0),
            InputField(
                "vert_bar_size",    str,   label="Vert Bar Size",       choices=BAR_SIZES,  default="#5"),
            InputField(
                "vert_spacing_in",  float, label="Vert Spacing (in)",   min=6.0, max=18.0, default=12.0),
            InputField(
                "hook_type",        str,   label="Hook Type",           choices=HOOK_TYPES, default="std_90"),
            InputField(
                "corner_bars",      str,   label="Corner L-Bars",       choices=["yes", "no"], default="yes"),
            InputField(
                "corner_bar_size",  str,   label="Corner Bar Size",     choices=BAR_SIZES,  default="#4"),
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
        if params.cover_in < 2.0:
            triggers.append("cover_unusual")
        if params.horiz_spacing_in > 16.0 or params.vert_spacing_in > 16.0:
            triggers.append("spacing_near_max")

        x_ft = getattr(params, "x_dim_ft", 9.0)
        ratio = params.wall_height_ft / max(x_ft, 0.1)
        if ratio > 2.5:
            triggers.append("aspect_ratio_high")

        return triggers


TEMPLATE = G2ExpandedInletTemplate()
