"""
RULE_REGISTRY — maps rule function name strings to callables.

Add every new rule function here. The calculator looks up rules by name
so templates stay decoupled from imports.
"""

from vistadetail.engine.rules.inlet_wall_rules import (
    rule_g2_inlet_geometry,
    rule_corner_L_bars,
    rule_horizontal_bars_EF,
    rule_validate_max_spacing_ACI,
    rule_validate_min_cover,
    rule_vertical_bars_EF,
)
from vistadetail.engine.rules.footing_rules import (
    rule_bottom_transverse,
    rule_bottom_longitudinal,
    rule_dowels,
    rule_validate_footing_cover,
)
from vistadetail.engine.rules.headwall_rules import (
    rule_front_face_horiz,
    rule_front_face_vert,
    rule_back_face_horiz,
    rule_top_bars,
    rule_connection_dowels,
    rule_headwall_c_bars,
    rule_headwall_fdn_mat,
    rule_headwall_fdn_horiz,
    rule_headwall_pipe_hoops,
    rule_headwall_d_bars,
    rule_headwall_pipe_bars,
    rule_headwall_spreaders,
    rule_headwall_standees,
    rule_validate_headwall_cover,
)
from vistadetail.engine.rules.wing_wall_rules import (
    rule_wing_horiz,
    rule_wing_vert,
    rule_wing_corner,
    rule_validate_wing,
)
from vistadetail.engine.rules.box_culvert_rules import (
    rule_top_slab_top,
    rule_top_slab_bottom,
    rule_wall_vertical,
    rule_bottom_slab_top,
    rule_bottom_slab_bottom,
    rule_haunch_bars,
    rule_validate_box_culvert,
)
from vistadetail.engine.rules.retaining_wall_rules import (
    rule_stem_horiz,
    rule_stem_vert,
    rule_toe_bars,
    rule_heel_bars,
    rule_stem_dowels,
    rule_shear_key,
    rule_validate_retaining_wall,
)
from vistadetail.engine.rules.flat_slab_rules import (
    rule_slab_long_bars,
    rule_slab_short_bars,
    rule_validate_flat_slab,
)
from vistadetail.engine.rules.cage_rules import (
    rule_cage_verticals,
    rule_cage_hoops_standard,
    rule_cage_hoops_confinement,
    rule_validate_cage,
)
from vistadetail.engine.rules.collar_rules import (
    rule_collar_long_bars,
    rule_collar_short_bars,
    rule_validate_collar,
)
from vistadetail.engine.rules.slab_on_grade_rules import (
    rule_sog_long_bars,
    rule_sog_short_bars,
    rule_sog_edge_bars,
    rule_validate_sog,
)
from vistadetail.engine.rules.pipe_encasement_rules import (
    rule_encasement_hoops,
    rule_encasement_longitudinals,
    rule_validate_pipe_encasement,
)
from vistadetail.engine.rules.fuel_foundation_rules import (
    rule_fuel_bottom_long,
    rule_fuel_bottom_short,
    rule_fuel_top_long,
    rule_fuel_top_short,
    rule_validate_fuel_foundation,
)
from vistadetail.engine.rules.dual_slab_rules import (
    rule_dual_slab_A_long,
    rule_dual_slab_A_short,
    rule_dual_slab_B_long,
    rule_dual_slab_B_short,
    rule_validate_dual_slab,
)
from vistadetail.engine.rules.concrete_header_rules import (
    rule_header_top_long,
    rule_header_bot_long,
    rule_header_transverse,
    rule_validate_concrete_header,
)
from vistadetail.engine.rules.seatwall_rules import (
    rule_seatwall_top_long,
    rule_seatwall_bot_long,
    rule_seatwall_transverse,
    rule_validate_seatwall,
)
from vistadetail.engine.rules.equipment_pad_rules import (
    rule_pad_bottom_long,
    rule_pad_bottom_short,
    rule_pad_top_long,
    rule_pad_top_short,
    rule_pad_vertical_dowels,
    rule_validate_equipment_pad,
)
from vistadetail.engine.rules.inlet_top_rules import (
    rule_inlet_top_long_bars,
    rule_inlet_top_short_bars,
    rule_validate_inlet_top,
)
from vistadetail.engine.rules.junction_structure_rules import (
    rule_junction_long_wall_horiz,
    rule_junction_long_wall_vert,
    rule_junction_short_wall_horiz,
    rule_junction_short_wall_vert,
    rule_junction_floor_long,
    rule_junction_floor_short,
    rule_validate_junction,
)

RULE_REGISTRY: dict = {
    # G2 Inlet / G2 Expanded Inlet
    "rule_g2_inlet_geometry":         rule_g2_inlet_geometry,
    "rule_horizontal_bars_EF":       rule_horizontal_bars_EF,
    "rule_vertical_bars_EF":         rule_vertical_bars_EF,
    "rule_corner_L_bars":            rule_corner_L_bars,
    "rule_validate_min_cover":       rule_validate_min_cover,
    "rule_validate_max_spacing_ACI": rule_validate_max_spacing_ACI,
    # Spread Footing
    "rule_bottom_transverse":        rule_bottom_transverse,
    "rule_bottom_longitudinal":      rule_bottom_longitudinal,
    "rule_dowels":                   rule_dowels,
    "rule_validate_footing_cover":   rule_validate_footing_cover,
    # Headwall
    "rule_front_face_horiz":         rule_front_face_horiz,
    "rule_front_face_vert":          rule_front_face_vert,
    "rule_back_face_horiz":          rule_back_face_horiz,
    "rule_top_bars":                 rule_top_bars,
    "rule_connection_dowels":        rule_connection_dowels,
    "rule_headwall_c_bars":          rule_headwall_c_bars,
    "rule_headwall_fdn_mat":         rule_headwall_fdn_mat,
    "rule_headwall_fdn_horiz":       rule_headwall_fdn_horiz,
    "rule_headwall_pipe_hoops":      rule_headwall_pipe_hoops,
    "rule_headwall_d_bars":          rule_headwall_d_bars,
    "rule_headwall_pipe_bars":       rule_headwall_pipe_bars,
    "rule_headwall_spreaders":       rule_headwall_spreaders,
    "rule_headwall_standees":        rule_headwall_standees,
    "rule_validate_headwall_cover":  rule_validate_headwall_cover,
    # Wing Wall
    "rule_wing_horiz":               rule_wing_horiz,
    "rule_wing_vert":                rule_wing_vert,
    "rule_wing_corner":              rule_wing_corner,
    "rule_validate_wing":            rule_validate_wing,
    # Box Culvert
    "rule_top_slab_top":             rule_top_slab_top,
    "rule_top_slab_bottom":          rule_top_slab_bottom,
    "rule_wall_vertical":            rule_wall_vertical,
    "rule_bottom_slab_top":          rule_bottom_slab_top,
    "rule_bottom_slab_bottom":       rule_bottom_slab_bottom,
    "rule_haunch_bars":              rule_haunch_bars,
    "rule_validate_box_culvert":     rule_validate_box_culvert,
    # Flat Slab
    "rule_slab_long_bars":           rule_slab_long_bars,
    "rule_slab_short_bars":          rule_slab_short_bars,
    "rule_validate_flat_slab":       rule_validate_flat_slab,
    # Drilled Shaft Cage
    "rule_cage_verticals":           rule_cage_verticals,
    "rule_cage_hoops_standard":      rule_cage_hoops_standard,
    "rule_cage_hoops_confinement":   rule_cage_hoops_confinement,
    "rule_validate_cage":            rule_validate_cage,
    # Concrete Pipe Collar
    "rule_collar_long_bars":         rule_collar_long_bars,
    "rule_collar_short_bars":        rule_collar_short_bars,
    "rule_validate_collar":          rule_validate_collar,
    # Slab on Grade
    "rule_sog_long_bars":            rule_sog_long_bars,
    "rule_sog_short_bars":           rule_sog_short_bars,
    "rule_sog_edge_bars":            rule_sog_edge_bars,
    "rule_validate_sog":             rule_validate_sog,
    # Pipe Encasement
    "rule_encasement_hoops":           rule_encasement_hoops,
    "rule_encasement_longitudinals":   rule_encasement_longitudinals,
    "rule_validate_pipe_encasement":   rule_validate_pipe_encasement,
    # Fuel Foundation
    "rule_fuel_bottom_long":           rule_fuel_bottom_long,
    "rule_fuel_bottom_short":          rule_fuel_bottom_short,
    "rule_fuel_top_long":              rule_fuel_top_long,
    "rule_fuel_top_short":             rule_fuel_top_short,
    "rule_validate_fuel_foundation":   rule_validate_fuel_foundation,
    # Dual Slab
    "rule_dual_slab_A_long":           rule_dual_slab_A_long,
    "rule_dual_slab_A_short":          rule_dual_slab_A_short,
    "rule_dual_slab_B_long":           rule_dual_slab_B_long,
    "rule_dual_slab_B_short":          rule_dual_slab_B_short,
    "rule_validate_dual_slab":         rule_validate_dual_slab,
    # Concrete Header
    "rule_header_top_long":          rule_header_top_long,
    "rule_header_bot_long":          rule_header_bot_long,
    "rule_header_transverse":        rule_header_transverse,
    "rule_validate_concrete_header": rule_validate_concrete_header,
    # Seatwall
    "rule_seatwall_top_long":        rule_seatwall_top_long,
    "rule_seatwall_bot_long":        rule_seatwall_bot_long,
    "rule_seatwall_transverse":      rule_seatwall_transverse,
    "rule_validate_seatwall":        rule_validate_seatwall,
    # Equipment / Concrete Pad + Switchboard Pad
    "rule_pad_bottom_long":          rule_pad_bottom_long,
    "rule_pad_bottom_short":         rule_pad_bottom_short,
    "rule_pad_top_long":             rule_pad_top_long,
    "rule_pad_top_short":            rule_pad_top_short,
    "rule_pad_vertical_dowels":      rule_pad_vertical_dowels,
    "rule_validate_equipment_pad":   rule_validate_equipment_pad,
    # Retaining Wall
    "rule_stem_horiz":               rule_stem_horiz,
    "rule_stem_vert":                rule_stem_vert,
    "rule_toe_bars":                 rule_toe_bars,
    "rule_heel_bars":                rule_heel_bars,
    "rule_stem_dowels":              rule_stem_dowels,
    "rule_shear_key":                rule_shear_key,
    "rule_validate_retaining_wall":  rule_validate_retaining_wall,
    # G2 Inlet Top / G2 Expanded Inlet Top
    "rule_inlet_top_long_bars":      rule_inlet_top_long_bars,
    "rule_inlet_top_short_bars":     rule_inlet_top_short_bars,
    "rule_validate_inlet_top":       rule_validate_inlet_top,
    # Junction Structure
    "rule_junction_long_wall_horiz": rule_junction_long_wall_horiz,
    "rule_junction_long_wall_vert":  rule_junction_long_wall_vert,
    "rule_junction_short_wall_horiz":rule_junction_short_wall_horiz,
    "rule_junction_short_wall_vert": rule_junction_short_wall_vert,
    "rule_junction_floor_long":      rule_junction_floor_long,
    "rule_junction_floor_short":     rule_junction_floor_short,
    "rule_validate_junction":        rule_validate_junction,
}
