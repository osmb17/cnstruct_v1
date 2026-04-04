"""Template: Headwall  (v1.0) — Caltrans standard headwall."""

from __future__ import annotations

from vistadetail.engine.schema import BAR_SIZES, InputField, Params
from vistadetail.engine.templates.base import BaseTemplate


class HeadwallTemplate(BaseTemplate):

    def __init__(self):
        super().__init__()
        self.name = "Straight Headwall"
        self.version = "1.0"
        self.description = "Caltrans straight headwall (D89a) — front/back face, top bars, C-bars, footing, pipe opening, spreaders/standees."

        self.inputs = [
            # ── Geometry ──────────────────────────────────────────────────────
            InputField("wall_width_ft",    float, label="Wall Width (ft)",   min=2.0,  max=40.0,  default=8.0,
                       group="Geometry"),
            InputField("wall_height_ft",   float, label="Wall Height (ft)",  min=2.0,  max=20.0,  default=5.0),
            InputField("wall_thick_in",    int,   label="Wall Thickness (in)", min=8, max=36,     default=12),
            InputField("cover_in",         float, label="Clear Cover (in)",  min=1.5,  max=4.0,   default=2.0),
            InputField("batter_in",        float, label="Back Face Batter (in/side)", min=0.0, max=12.0, default=0.0,
                       hint="Horizontal batter offset each side of back face"),
            # ── Face Reinforcement ────────────────────────────────────────────
            InputField("horiz_bar_size",   str,   label="Horiz Bar Size",    choices=BAR_SIZES,   default="#5",
                       group="Face Reinforcement"),
            InputField("horiz_spacing_in", float, label="Horiz Spacing (in)", min=3.0, max=18.0,  default=12.0),
            InputField("vert_bar_size",    str,   label="Vert Bar Size",     choices=BAR_SIZES,   default="#5"),
            InputField("vert_spacing_in",  float, label="Vert Spacing (in)",  min=3.0, max=18.0,  default=12.0),
            InputField("top_bar_size",     str,   label="Top Bar Size",      choices=BAR_SIZES,   default="#4"),
            InputField("top_spacing_in",   float, label="Top Bar Spacing (in)", min=3.0, max=18.0, default=12.0),
            InputField("dowel_qty",        int,   label="Connection Dowel Qty", min=0, max=20,    default=4),
            InputField("dowel_bar_size",   str,   label="Connection Dowel Size", choices=BAR_SIZES, default="#5"),
            # ── C-bars (mk 500) ───────────────────────────────────────────────
            InputField("has_c_bars",       float, label="C-bars? (0=No 1=Yes)", min=0.0, max=1.0, default=1.0,
                       group="C-bars  (mk 500 — Caltrans D89a)",
                       hint="1 = generate C-bar (hairpin) vertical bars spanning wall depth"),
            InputField("c_bar_size",       str,   label="C-bar Size",          choices=BAR_SIZES, default="#5",
                       hint="Bar size for C-bars — #5 typical per Caltrans D89a"),
            InputField("c_bar_spacing_in", float, label="C-bar Spacing (in)",  min=3.0, max=18.0, default=9.0,
                       hint="C-to-C spacing along wall width — 9in per D89a standard"),
            InputField("c_bar_leg_in",     float, label="C-bar Leg Length (in)", min=6.0, max=24.0, default=14.0,
                       hint="Horizontal leg at each end — 1'-2\" (14in) per D89a"),
            InputField("c_bar_radius_in",  float, label="C-bar Bend Radius (in)", min=3.0, max=18.0, default=9.0,
                       hint="Bend radius at each corner — 9in per D89a barlist"),
            # ── Foundation / Footing ──────────────────────────────────────────
            InputField("has_footing",        float, label="Footing? (0=No 1=Yes)", min=0.0, max=1.0, default=0.0,
                       group="Foundation / Footing",
                       hint="1 = generate FM1 mat and FH1 distribution bars"),
            InputField("footing_width_ft",   float, label="Footing Width (ft)",    min=2.0, max=20.0, default=5.33,
                       hint="Perpendicular to wall — 5'-4\" (5.33ft) per D89a"),
            InputField("fdn_bar_size",       str,   label="Foundation Bar Size",   choices=BAR_SIZES, default="#4",
                       hint="Bar size for FM1 mat and FH1 distribution bars"),
            InputField("fdn_mat_spacing_in", float, label="Fdn Mat Spacing (in)",  min=3.0, max=18.0, default=12.0,
                       hint="Spacing of FM1 mat bars along wall width"),
            InputField("fdn_horiz_spacing_in", float, label="Fdn Horiz Spacing (in)", min=3.0, max=18.0, default=8.0,
                       hint="Spacing of FH1 distribution bars across footing width"),
            # ── Pipe Opening ──────────────────────────────────────────────────
            InputField("has_pipe_opening",   float, label="Pipe Opening? (0=No 1=Yes)", min=0.0, max=1.0, default=0.0,
                       group="Pipe Opening",
                       hint="1 = generate PH1 pipe hoops, DB1 D-bars, PB1 trim bars"),
            InputField("pipe_od_in",         float, label="Pipe OD (in)",           min=12.0, max=144.0, default=42.0,
                       hint="Pipe outer diameter — 42in (3'-6\") per D89a"),
            InputField("pipe_hoop_size",     str,   label="Pipe Hoop Bar Size",     choices=BAR_SIZES, default="#6"),
            InputField("pipe_hoop_qty",      int,   label="Pipe Hoop Qty",          min=1, max=10, default=2),
            InputField("pipe_hoop_lap_in",   float, label="Pipe Hoop Lap (in)",     min=12.0, max=72.0, default=36.0,
                       hint="Lap splice length for circular hoop — 3'-0\" per D89a"),
            InputField("d_bar_size",         str,   label="D-bar Size",             choices=BAR_SIZES, default="#6"),
            InputField("d_bar_spacing_in",   float, label="D-bar Spacing (in)",     min=3.0, max=18.0, default=8.0),
            InputField("pipe_bar_size",      str,   label="Pipe Trim Bar Size",     choices=BAR_SIZES, default="#4"),
            # ── Wall Spreaders (mk 401) ────────────────────────────────────────
            InputField("has_spreaders",      float, label="Spreaders? (0=No 1=Yes)", min=0.0, max=1.0, default=0.0,
                       group="Wall Spreaders  (mk 401 — U-shape)",
                       hint="1 = generate U-shape wall spreaders WS1"),
            InputField("spreader_size",      str,   label="Spreader Bar Size",      choices=BAR_SIZES, default="#4"),
            InputField("spreader_body_in",   float, label="Spreader Body (in)",     min=4.0, max=24.0, default=8.5,
                       hint="Body length — wall thick minus mat cover each side"),
            InputField("spreader_leg_in",    float, label="Spreader Leg (in)",      min=3.0, max=12.0, default=6.0),
            InputField("spreader_spacing_in",      float, label="Spreader H-Spacing (in)", min=12.0, max=48.0, default=24.0),
            InputField("spreader_vert_spacing_in", float, label="Spreader V-Spacing (in)", min=12.0, max=48.0, default=24.0),
            # ── Mat Standees (mk 400) ─────────────────────────────────────────
            InputField("has_standees",       float, label="Standees? (0=No 1=Yes)", min=0.0, max=1.0, default=0.0,
                       group="Mat Standees  (mk 400 — S-shape)",
                       hint="1 = generate S-shape mat standees ST1"),
            InputField("standee_size",       str,   label="Standee Bar Size",       choices=BAR_SIZES, default="#4"),
            InputField("standee_top_in",     float, label="Standee Top Leg (in)",   min=2.0, max=12.0, default=5.0),
            InputField("standee_leg_in",     float, label="Standee Side Leg (in)",  min=2.0, max=12.0, default=5.5),
            InputField("standee_base_in",    float, label="Standee Base (in)",      min=4.0, max=24.0, default=12.0),
            InputField("standee_spacing_in", float, label="Standee Spacing (in)",   min=12.0, max=48.0, default=24.0),
        ]

        self.rules = [
            "rule_front_face_horiz",
            "rule_front_face_vert",
            "rule_back_face_horiz",
            "rule_top_bars",
            "rule_connection_dowels",
            "rule_headwall_c_bars",
            "rule_headwall_fdn_mat",
            "rule_headwall_fdn_horiz",
            "rule_headwall_pipe_hoops",
            "rule_headwall_d_bars",
            "rule_headwall_pipe_bars",
            "rule_headwall_spreaders",
            "rule_headwall_standees",
            "rule_validate_headwall_cover",
        ]

    def evaluate_triggers(self, params: Params) -> list[str]:
        triggers: list[str] = []
        if params.cover_in < 2.0:
            triggers.append("cover_unusual")
        ratio = params.wall_height_ft / max(params.wall_width_ft, 0.1)
        if ratio > 2.5:
            triggers.append("aspect_ratio_high")
        return triggers


TEMPLATE = HeadwallTemplate()
