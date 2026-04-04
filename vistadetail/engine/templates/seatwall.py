"""
Template: Seatwall  (v1.0)

Low concrete bench wall used in playgrounds and landscape features.
Rectangular cross-section with top + bottom longitudinal bars and
transverse bars spanning the seat width.

Generates:
  S1 — top longitudinal bars (along full wall length)
  S2 — bottom longitudinal bars (along full wall length)
  S3 — transverse bars (across wall width, spaced along length)

Covers 5 PDFs in the clean_examples set:
  Portola.ES.Seatwall.clean
  Portola.ES.seatwall.31x2
  Portola.ES.seatwall31x2.clean
  detail.seatwall.portola.es.playground.pg1
  detail.seatwall.portola.es.playground.pg2

Formulas:
  long_length  = wall_length_in - 2 × cover_in
  trans_length = wall_width_in  - 2 × cover_in
  trans_qty    = floor(wall_length_in / tie_spacing_in)

Cover default: 1.5 in (exposed to weather, ACI Table 20.6.1.3.1).
"""

from __future__ import annotations

from vistadetail.engine.schema import BAR_SIZES, InputField, Params
from vistadetail.engine.templates.base import BaseTemplate


class SeatwallTemplate(BaseTemplate):
    name: str = "Seatwall"
    version: str = "1.0"
    description: str = (
        "Low concrete playground or landscape bench wall. "
        "S1/S2 longitudinal bars (top + bottom) + S3 transverse bars across seat width."
    )

    def __init__(self):
        super().__init__()
        self.name        = "Seatwall"
        self.version     = "1.0"
        self.description = (
            "Low concrete playground or landscape bench wall. "
            "S1/S2 longitudinal bars (top + bottom) + S3 transverse bars across seat width."
        )

        self.inputs = [
            # ── Wall geometry ─────────────────────────────────────────────
            InputField(
                "wall_length_ft", float,
                label="Wall Length (ft)",
                min=2.0, max=200.0, default=31.0,
                hint="Total seatwall length in feet",
            ),
            InputField(
                "wall_height_in", float,
                label="Wall Height (in)  — seat height",
                min=10.0, max=36.0, default=18.0,
                hint="Seat height from base to top; ADA comfortable range: 17–19 in",
            ),
            InputField(
                "wall_width_in", float,
                label="Wall Width (in)  — seat depth",
                min=8.0, max=36.0, default=14.0,
                hint="Seat depth / wall width (perpendicular to wall length)",
            ),
            # ── Top longitudinal reinforcement ────────────────────────────
            InputField(
                "top_bar_size", str,
                label="Top Bar Size",
                choices=BAR_SIZES, default="#4",
                hint="Bar size for top longitudinal reinforcement",
            ),
            InputField(
                "top_bar_count", float,
                label="Top Bar Count",
                min=1.0, max=8.0, default=2.0,
                hint="Number of longitudinal bars at top face (typically 2)",
            ),
            # ── Bottom longitudinal reinforcement ─────────────────────────
            InputField(
                "bot_bar_size", str,
                label="Bottom Bar Size",
                choices=BAR_SIZES, default="#4",
                hint="Bar size for bottom longitudinal reinforcement",
            ),
            InputField(
                "bot_bar_count", float,
                label="Bottom Bar Count",
                min=1.0, max=8.0, default=2.0,
                hint="Number of longitudinal bars at bottom face (typically 2)",
            ),
            # ── Transverse reinforcement ──────────────────────────────────
            InputField(
                "tie_bar_size", str,
                label="Transverse Bar Size",
                choices=BAR_SIZES, default="#3",
                hint="Bar size for transverse bars spanning the seat width",
            ),
            InputField(
                "tie_spacing_in", float,
                label="Transverse Spacing (in)",
                min=6.0, max=24.0, default=18.0,
                hint="Center-to-center spacing of transverse bars along wall length",
            ),
            # ── Cover ─────────────────────────────────────────────────────
            InputField(
                "cover_in", float,
                label="Clear Cover (in)",
                min=1.5, max=3.0, default=1.5,
                hint="1.5 in exposed to weather, ≤#5 bar (ACI Table 20.6.1.3.1)",
            ),
        ]

        self.rules = [
            "rule_seatwall_top_long",
            "rule_seatwall_bot_long",
            "rule_seatwall_transverse",
            "rule_validate_seatwall",
        ]

    def evaluate_triggers(self, params: Params) -> list[str]:
        triggers: list[str] = []
        if params.wall_height_in > 24.0:
            triggers.append("tall_seatwall_consider_retaining_wall_design")
        total_long = int(params.top_bar_count) + int(params.bot_bar_count)
        if total_long > 6:
            triggers.append("high_bar_count_verify_cover_clearance")
        return triggers


TEMPLATE = SeatwallTemplate()
