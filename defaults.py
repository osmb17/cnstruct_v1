"""
defaults.py -- Smart defaults layer for CNSTRUCT 1.0.

PRIMARY_INPUTS:   all fields shown inline in the input panel (no Advanced expander).
                  Every template lists its complete set of inputs here.
DIAGRAM_LABELS:   human label for each field shown on the diagram.
"""

from __future__ import annotations

# -- All inputs shown inline per template (no Advanced expander) ---------------

PRIMARY_INPUTS: dict[str, list[str]] = {
    "G1 Inlet":              ["x_dim_ft", "y_dim_ft",
                              "wall_thick_in", "grate_type", "num_structures"],
    "G2 Inlet":              ["x_dim_ft", "wall_thick_in", "wall_height_ft",
                              "grate_type", "num_structures"],
    "G3 Inlet":              ["x_dim_ft", "y_dim_ft",
                              "wall_thick_in", "grate_type", "num_structures"],
    "G4 Inlet":              ["x_dim_ft", "y_dim_ft",
                              "wall_thick_in", "grate_type", "num_structures"],
    "G5 Inlet":              ["x_dim_ft", "y_dim_ft",
                              "wall_thick_in", "grate_type", "num_structures"],
    "G6 Inlet":              ["x_dim_ft", "y_dim_ft",
                              "wall_thick_in", "grate_type", "num_structures"],
    "G2 Expanded Inlet":     ["x_dim_ft", "y_dim_ft", "y_expanded_ft",
                              "wall_height_ft", "wall_thick_in",
                              "grate_type", "num_structures"],
    "G2 Inlet Top":          ["x_dim_ft", "y_dim_ft", "wall_height_ft",
                              "vert_extension_in", "wall_thick_in",
                              "grate_type", "num_structures"],
    "G2 Expanded Inlet Top": ["slab_length_ft", "slab_width_ft",
                              "slab_thick_in", "cover_in",
                              "long_bar_size", "long_spacing_in",
                              "short_bar_size", "short_spacing_in"],
    "Straight Headwall":     ["wall_width_ft", "wall_height_ft",
                              "wall_thick_in", "cover_in", "batter_in",
                              "horiz_bar_size", "horiz_spacing_in",
                              "vert_bar_size", "vert_spacing_in",
                              "top_bar_size", "top_spacing_in",
                              "dowel_qty", "dowel_bar_size",
                              "has_c_bars", "c_bar_size", "c_bar_spacing_in",
                              "c_bar_leg_in", "c_bar_radius_in",
                              "has_footing", "footing_width_ft",
                              "fdn_bar_size", "fdn_mat_spacing_in", "fdn_horiz_spacing_in",
                              "has_pipe_opening", "pipe_od_in",
                              "pipe_hoop_size", "pipe_hoop_qty", "pipe_hoop_lap_in",
                              "d_bar_size", "d_bar_spacing_in", "pipe_bar_size",
                              "has_spreaders", "spreader_size",
                              "spreader_body_in", "spreader_leg_in",
                              "spreader_spacing_in", "spreader_vert_spacing_in",
                              "has_standees", "standee_size",
                              "standee_top_in", "standee_leg_in",
                              "standee_base_in", "standee_spacing_in"],
    "Wing Wall":             ["wing_length_ft", "hw_height_ft", "tip_height_ft",
                              "wall_thick_in", "cover_in",
                              "horiz_bar_size", "horiz_spacing_in",
                              "vert_bar_size", "vert_spacing_in", "hook_type"],
    "Spread Footing":        ["footing_length_ft", "footing_width_ft",
                              "footing_depth_in", "cover_in",
                              "bot_bar_size", "bot_spacing_in",
                              "dowel_qty", "dowel_bar_size"],
    "Box Culvert":           ["span_ft", "height_ft", "max_earth_cover_ft",
                              "barrel_length_ft"],
    "Retaining Wall":        ["wall_length_ft", "stem_height_ft",
                              "stem_thick_in", "footing_length_ft", "footing_depth_in",
                              "cover_in",
                              "vert_bar_size", "horiz_bar_size", "footing_bar_size",
                              "vert_spacing_in", "horiz_spacing_in", "footing_spacing_in",
                              "shear_key", "key_depth_in"],
    "Flat Slab":             ["slab_length_ft", "slab_width_ft",
                              "bar_size", "spacing_in", "cover_in"],
    "Drilled Shaft Cage":    ["hole_diameter_ft", "cage_depth_ft",
                              "vert_bar_size", "vert_count", "embed_in",
                              "ring_bar_size", "ring_spacing_in", "lap_ft", "cover_in",
                              "has_confinement_zone", "conf_spacing_in",
                              "confinement_depth_in"],
    "Concrete Pipe Collar":  ["collar_length_ft", "collar_width_ft",
                              "bar_size", "spacing_in", "cover_in"],
    "Slab on Grade":         ["slab_length_ft", "slab_width_ft", "slab_thickness_in",
                              "bar_size", "spacing_in", "cover_in",
                              "has_edge_beam", "edge_bar_size", "edge_bars_per_side"],
    "Equipment Pad":         ["pad_length_ft", "pad_width_ft", "pad_thickness_in",
                              "bar_size", "spacing_in", "cover_in",
                              "has_double_mat", "top_bar_size", "top_spacing_in"],
    "Switchboard Pad":       ["pad_length_ft", "pad_width_ft", "pad_thickness_in",
                              "bar_size", "spacing_in", "cover_in",
                              "top_bar_size", "top_spacing_in",
                              "has_vertical_dowels", "dowel_bar_size",
                              "dowel_spacing_in", "dowel_embed_in", "dowel_project_in",
                              "has_double_mat"],
    "Seatwall":              ["wall_length_ft", "wall_height_in", "wall_width_in",
                              "top_bar_size", "top_bar_count",
                              "bot_bar_size", "bot_bar_count",
                              "tie_bar_size", "tie_spacing_in", "cover_in"],
    "Concrete Header":       ["header_length_ft", "header_height_in", "header_width_in",
                              "top_bar_size", "top_bar_count",
                              "bot_bar_size", "bot_bar_count",
                              "tie_bar_size", "tie_spacing_in", "cover_in"],
    "Pipe Encasement":       ["encasement_length_ft", "encasement_width_in",
                              "encasement_height_in",
                              "hoop_bar_size", "hoop_spacing_in",
                              "long_bar_size", "n_long_bars", "cover_in"],
    "Fuel Foundation":       ["fdn_length_ft", "fdn_width_ft", "fdn_thickness_in",
                              "bar_size", "spacing_in", "cover_in",
                              "has_top_mat", "top_bar_size", "top_spacing_in"],
    "Dual Slab":             ["slab_a_length_ft", "slab_a_width_ft",
                              "slab_a_bar_size", "slab_a_spacing_in",
                              "slab_b_length_ft", "slab_b_width_ft",
                              "slab_b_bar_size", "slab_b_spacing_in", "cover_in"],
    "Junction Structure":    ["inside_length_ft", "inside_width_ft", "inside_depth_ft",
                              "wall_thick_in", "floor_thick_in", "cover_in",
                              "wall_bar_size", "horiz_spacing_in", "vert_spacing_in",
                              "floor_bar_size", "floor_spacing_in"],
    "Sound Wall":            ["wall_height_ft", "wall_length_ft",
                              "cover_in", "foundation_type", "ground_case",
                              "soil_phi_deg", "exp_joint_spacing_ft"],
    "Caltrans Retaining Wall": ["design_h_ft", "wall_length_ft",
                                "wall_case", "shear_key"],
    "Caltrans Headwall":     ["pipe_dia_in", "wall_width_ft",
                              "wall_type", "loading_case"],
    "D84 Wingwall":          ["wall_height_ft", "wall_length_ft",
                              "wall_thick_in", "footing_width_ft",
                              "cover_in", "num_structures"],
    "D85 Wingwall":          ["wall_height_ft", "wall_length_ft",
                              "wall_thick_in", "footing_width_ft",
                              "cover_in", "num_structures"],
}

# Legacy -- no longer used
OVERRIDEABLE: dict[str, str] = {}

# -- Diagram axis labels -------------------------------------------------------
DIAGRAM_LABELS: dict[str, dict[str, str]] = {
    "G1 Inlet":              {"x_dim_ft": "L1", "y_dim_ft": "H"},
    "G2 Inlet":              {"x_dim_ft": "X_ext", "wall_thick_in": "T"},
    "G3 Inlet":              {"x_dim_ft": "L1", "y_dim_ft": "H"},
    "G4 Inlet":              {"x_dim_ft": "L1", "y_dim_ft": "H"},
    "G5 Inlet":              {"x_dim_ft": "L1", "y_dim_ft": "H"},
    "G6 Inlet":              {"x_dim_ft": "L1", "y_dim_ft": "H"},
    "G2 Expanded Inlet":     {"x_dim_ft": "X", "y_dim_ft": "Y", "y_expanded_ft": "Y_exp", "wall_thick_in": "T"},
    "G2 Inlet Top":          {"x_dim_ft": "X", "y_dim_ft": "Y", "wall_thick_in": "T"},
    "G2 Expanded Inlet Top": {"slab_length_ft": "L", "slab_width_ft": "W"},
    "Straight Headwall":     {"wall_width_ft": "W", "wall_height_ft": "H", "wall_thick_in": "T"},
    "Wing Wall":             {"wing_length_ft": "L", "hw_height_ft": "H1", "tip_height_ft": "H2"},
    "Spread Footing":        {"footing_length_ft": "L", "footing_width_ft": "W", "footing_depth_in": "D"},
    "Box Culvert":           {"span_ft": "S", "height_ft": "H", "barrel_length_ft": "B"},
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
