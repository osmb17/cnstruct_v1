"""
defaults.py -- Smart defaults layer for CNSTRUCT 1.0.

PRIMARY_INPUTS:   just X and Y (or equivalent pair) -- the only fields
                  visible by default.  Everything else is in Advanced.
DIAGRAM_LABELS:   human label for each field shown on the diagram.
"""

from __future__ import annotations

# -- Primary inputs: just X and Y (or equivalent) per template ----------------
# Only these 2 fields appear in the main panel.  Everything else is Advanced.

PRIMARY_INPUTS: dict[str, list[str]] = {
    "G2 Inlet":              ["x_dim_ft", "y_dim_ft"],
    "G2 Expanded Inlet":     ["x_dim_ft", "y_dim_ft"],
    "G2 Inlet Top":          ["x_dim_ft", "y_dim_ft"],
    "G2 Expanded Inlet Top": ["slab_length_ft", "slab_width_ft"],
    "Straight Headwall":     ["wall_width_ft", "wall_height_ft"],
    "Wing Wall":             ["wing_length_ft", "hw_height_ft"],
    "Spread Footing":        ["footing_length_ft", "footing_width_ft"],
    "Box Culvert":           ["clear_span_ft", "clear_rise_ft"],
    "Retaining Wall":        ["wall_length_ft", "stem_height_ft"],
    "Flat Slab":             ["slab_length_ft", "slab_width_ft"],
    "Drilled Shaft Cage":    ["hole_diameter_ft", "cage_depth_ft"],
    "Concrete Pipe Collar":  ["collar_length_ft", "collar_width_ft"],
    "Slab on Grade":         ["slab_length_ft", "slab_width_ft"],
    "Equipment Pad":         ["pad_length_ft", "pad_width_ft"],
    "Switchboard Pad":       ["pad_length_ft", "pad_width_ft"],
    "Seatwall":              ["wall_length_ft", "wall_height_in"],
    "Concrete Header":       ["header_length_ft", "header_height_in"],
    "Pipe Encasement":       ["encasement_length_ft", "encasement_width_in"],
    "Fuel Foundation":       ["fdn_length_ft", "fdn_width_ft"],
    "Dual Slab":             ["slab_a_length_ft", "slab_a_width_ft"],
    "Junction Structure":    ["inside_length_ft", "inside_width_ft"],
    "Sound Wall":            ["wall_height_ft", "wall_length_ft"],
    "Caltrans Retaining Wall": ["design_h_ft", "wall_length_ft"],
    "Caltrans Headwall":     ["pipe_dia_in", "wall_width_ft"],
    "D84 Wingwall":          ["wall_height_ft", "wall_length_ft"],
    "D85 Wingwall":          ["wall_height_ft", "wall_length_ft"],
}

# Legacy -- no longer used
OVERRIDEABLE: dict[str, str] = {}

# -- Diagram axis labels -------------------------------------------------------
DIAGRAM_LABELS: dict[str, dict[str, str]] = {
    "G2 Inlet":              {"x_dim_ft": "X", "y_dim_ft": "Y", "inside_x_in": "X_int", "inside_y_in": "Y_int", "wall_thick_in": "T"},
    "G2 Expanded Inlet":     {"x_dim_ft": "X", "y_dim_ft": "Y", "y_expanded_ft": "Y_exp", "wall_thick_in": "T"},
    "G2 Inlet Top":          {"x_dim_ft": "X", "y_dim_ft": "Y", "wall_thick_in": "T"},
    "G2 Expanded Inlet Top": {"slab_length_ft": "L", "slab_width_ft": "W"},
    "Straight Headwall":     {"wall_width_ft": "W", "wall_height_ft": "H", "wall_thick_in": "T"},
    "Wing Wall":             {"wing_length_ft": "L", "hw_height_ft": "H1", "tip_height_ft": "H2"},
    "Spread Footing":        {"footing_length_ft": "L", "footing_width_ft": "W", "footing_depth_in": "D"},
    "Box Culvert":           {"clear_span_ft": "S", "clear_rise_ft": "R", "barrel_length_ft": "B"},
    "Retaining Wall":        {"wall_length_ft": "L", "stem_height_ft": "H", "footing_length_ft": "W"},
    "Flat Slab":             {"slab_length_ft": "L", "slab_width_ft": "W"},
    "Drilled Shaft Cage":    {"hole_diameter_ft": "phi", "cage_depth_ft": "D"},
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
    "D84 Wingwall":          {"wall_height_ft": "H", "wall_length_ft": "LOL"},
    "D85 Wingwall":          {"wall_height_ft": "H", "wall_length_ft": "LOL"},
}


def get_primary_inputs(template) -> list:
    """Return the subset of template.inputs that are 'primary' (shown by default)."""
    primary_names = set(PRIMARY_INPUTS.get(template.name, []))
    return [f for f in template.inputs if f.name in primary_names]


def get_secondary_inputs(template) -> list:
    """Return the subset of template.inputs that are NOT primary (shown in Advanced)."""
    primary_names = set(PRIMARY_INPUTS.get(template.name, []))
    return [f for f in template.inputs if f.name not in primary_names]


def get_overrideable_field(template):
    """Legacy -- returns None."""
    return None
