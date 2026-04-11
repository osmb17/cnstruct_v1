"""
defaults.py — Smart defaults layer for CNSTRUCT 1.0.

PRIMARY_INPUTS:   the 2–4 fields shown by default (X, Y, key dims).
OVERRIDEABLE:     field that is auto-computed but user can unlock (usually wall_thick_in).
DIAGRAM_LABELS:   human label for each primary field shown on the diagram.
"""

from __future__ import annotations

# ── Primary inputs shown by default ──────────────────────────────────────────
# Only these appear in the main panel; everything else is in "Advanced".

PRIMARY_INPUTS: dict[str, list[str]] = {
    "G2 Inlet":              ["x_dim_ft", "y_dim_ft", "inside_x_in", "inside_y_in", "wall_height_ft", "grate_type"],
    "G2 Expanded Inlet":     ["x_dim_ft", "y_dim_ft", "y_expanded_ft", "wall_height_ft", "grate_type"],
    "G2 Inlet Top":          ["x_dim_ft", "y_dim_ft", "wall_height_ft", "grate_type"],
    "G2 Expanded Inlet Top": ["slab_length_ft", "slab_width_ft"],
    "Straight Headwall":     ["wall_width_ft", "wall_height_ft"],
    "Wing Wall":             ["wing_length_ft", "hw_height_ft", "tip_height_ft"],
    "Spread Footing":        ["footing_length_ft", "footing_width_ft", "footing_depth_in"],
    "Box Culvert":           ["clear_span_ft", "clear_rise_ft", "barrel_length_ft"],
    "Retaining Wall":        ["wall_length_ft", "stem_height_ft", "footing_length_ft"],
    "Flat Slab":             ["slab_length_ft", "slab_width_ft"],
    "Drilled Shaft Cage":    ["hole_diameter_ft", "cage_depth_ft", "vert_count"],
    "Concrete Pipe Collar":  ["collar_length_ft", "collar_width_ft"],
    "Slab on Grade":         ["slab_length_ft", "slab_width_ft", "slab_thickness_in"],
    "Equipment Pad":         ["pad_length_ft", "pad_width_ft", "pad_thickness_in"],
    "Switchboard Pad":       ["pad_length_ft", "pad_width_ft", "pad_thickness_in"],
    "Seatwall":              ["wall_length_ft", "wall_height_in", "wall_width_in"],
    "Concrete Header":       ["header_length_ft", "header_height_in", "header_width_in"],
    "Pipe Encasement":       ["encasement_length_ft", "encasement_width_in", "encasement_height_in"],
    "Fuel Foundation":       ["fdn_length_ft", "fdn_width_ft", "fdn_thickness_in"],
    "Dual Slab":             ["slab_a_length_ft", "slab_a_width_ft", "slab_b_length_ft", "slab_b_width_ft"],
    "Junction Structure":    ["inside_length_ft", "inside_width_ft", "inside_depth_ft"],
    "Sound Wall":            ["wall_height_ft", "wall_length_ft", "foundation_type"],
    "Caltrans Retaining Wall": ["design_h_ft", "wall_length_ft", "wall_case"],
    "Caltrans Headwall":     ["pipe_dia_in", "wall_width_ft", "wall_type"],
}

# ── Auto-computed field (shown as read-only, unlockable via checkbox) ─────────
OVERRIDEABLE: dict[str, str] = {
    "G2 Inlet":              "wall_thick_in",
    "G2 Expanded Inlet":     "wall_thick_in",
    "G2 Inlet Top":          "wall_thick_in",
    "Straight Headwall":     "wall_thick_in",
    "Box Culvert":           "wall_thick_in",
    "Junction Structure":    "wall_thick_in",
}

# ── Diagram axis labels (what each primary field represents on the diagram) ───
DIAGRAM_LABELS: dict[str, dict[str, str]] = {
    "G2 Inlet":              {"x_dim_ft": "X", "y_dim_ft": "Y", "inside_x_in": "X_int", "inside_y_in": "Y_int", "wall_thick_in": "T"},
    "G2 Expanded Inlet":     {"x_dim_ft": "X", "y_dim_ft": "Y", "y_expanded_ft": "Y_exp", "wall_thick_in": "T"},
    "G2 Inlet Top":          {"x_dim_ft": "X", "y_dim_ft": "Y", "wall_thick_in": "T"},
    "G2 Expanded Inlet Top": {"slab_length_ft": "L", "slab_width_ft": "W"},
    "Straight Headwall":     {"wall_width_ft": "W", "wall_height_ft": "H", "wall_thick_in": "T"},
    "Wing Wall":             {"wing_length_ft": "L", "hw_height_ft": "H₁", "tip_height_ft": "H₂"},
    "Spread Footing":        {"footing_length_ft": "L", "footing_width_ft": "W", "footing_depth_in": "D"},
    "Box Culvert":           {"clear_span_ft": "S", "clear_rise_ft": "R", "barrel_length_ft": "B"},
    "Retaining Wall":        {"wall_length_ft": "L", "stem_height_ft": "H", "footing_length_ft": "W"},
    "Flat Slab":             {"slab_length_ft": "L", "slab_width_ft": "W"},
    "Drilled Shaft Cage":    {"hole_diameter_ft": "φ", "cage_depth_ft": "D"},
    "Concrete Pipe Collar":  {"collar_length_ft": "L", "collar_width_ft": "W"},
    "Slab on Grade":         {"slab_length_ft": "L", "slab_width_ft": "W", "slab_thickness_in": "T"},
    "Equipment Pad":         {"pad_length_ft": "L", "pad_width_ft": "W", "pad_thickness_in": "T"},
    "Switchboard Pad":       {"pad_length_ft": "L", "pad_width_ft": "W", "pad_thickness_in": "T"},
    "Seatwall":              {"wall_length_ft": "L", "wall_height_in": "H", "wall_width_in": "W"},
    "Concrete Header":       {"header_length_ft": "L", "header_height_in": "H", "header_width_in": "W"},
    "Pipe Encasement":       {"encasement_length_ft": "L", "encasement_width_in": "W", "encasement_height_in": "H"},
    "Fuel Foundation":       {"fdn_length_ft": "L", "fdn_width_ft": "W", "fdn_thickness_in": "T"},
    "Dual Slab":             {"slab_a_length_ft": "A-L", "slab_a_width_ft": "A-W",
                              "slab_b_length_ft": "B-L", "slab_b_width_ft": "B-W"},
    "Junction Structure":    {"inside_length_ft": "L", "inside_width_ft": "W", "inside_depth_ft": "D"},
    "Sound Wall":            {"wall_height_ft": "H", "wall_length_ft": "L"},
    "Caltrans Retaining Wall": {"design_h_ft": "H", "wall_length_ft": "L"},
    "Caltrans Headwall":     {"pipe_dia_in": "D", "wall_width_ft": "W"},
}


def get_primary_inputs(template) -> list:
    """Return the subset of template.inputs that are 'primary' (shown by default)."""
    primary_names = set(PRIMARY_INPUTS.get(template.name, []))
    return [f for f in template.inputs if f.name in primary_names]


def get_secondary_inputs(template) -> list:
    """Return the subset of template.inputs that are 'advanced' (shown in expander)."""
    primary_names = set(PRIMARY_INPUTS.get(template.name, []))
    override_name = OVERRIDEABLE.get(template.name)
    return [
        f for f in template.inputs
        if f.name not in primary_names and f.name != override_name
    ]


def get_overrideable_field(template):
    """Return the InputField for the auto-computed/overrideable field, or None."""
    name = OVERRIDEABLE.get(template.name)
    if not name:
        return None
    for f in template.inputs:
        if f.name == name:
            return f
    return None
