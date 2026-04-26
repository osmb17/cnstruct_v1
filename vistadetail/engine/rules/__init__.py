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
    # Vista Excel-matched G2 Inlet rules
    rule_g2_geometry,
    rule_g2_bottom_mat,
    rule_g2_horizontals,
    rule_g2_verticals,
    rule_g2_ab_bars,
    rule_g2_right_angle,
    rule_g2_hoops,
    # Vista Excel-matched G2 Expanded Inlet rules
    rule_g2exp_geometry,
    rule_g2exp_verticals,
    rule_g2exp_ab_bars,
    rule_g2exp_hoops,
    # Vista Excel-matched G2 Inlet Top rules
    rule_g2top_geometry,
    rule_g2top_verticals,
    rule_g2top_right_angle,
)
from vistadetail.engine.rules.footing_rules import (
    rule_bottom_transverse,
    rule_bottom_longitudinal,
    rule_dowels,
    rule_validate_footing_cover,
)
from vistadetail.engine.rules.headwall_rules import (
    rule_hw_d_bars,
    rule_hw_trans_footing,
    rule_hw_long_invert,
    rule_hw_long_wall,
    rule_hw_top_wall,
    rule_hw_vert_wall,
    rule_hw_c_bars,
    rule_hw_spreaders,
    rule_hw_standees,
    rule_validate_headwall,
)
from vistadetail.engine.rules.wing_wall_rules import (
    rule_wing_horiz,
    rule_wing_vert,
    rule_wing_corner,
    rule_validate_wing,
)
from vistadetail.engine.rules.box_culvert_rules import (
    rule_bc_a_bars,
    rule_bc_b_bars,
    rule_bc_e_bars,
    rule_bc_i_bars,
    rule_bc_hoops,
    rule_bc_validate,
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
    rule_swbd_top_long,
    rule_swbd_top_short,
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
from vistadetail.engine.rules.sound_wall_rules import (
    rule_sw_wall_verticals,
    rule_sw_wall_horizontals,
    rule_sw_footing_dowels,
    rule_sw_footing_bars,
    rule_sw_pile_cage,
    rule_sw_pile_cap_bars,
    rule_validate_sound_wall,
)
from vistadetail.engine.rules.caltrans_ret_wall_rules import (
    rule_ct_rw_stem_vert,
    rule_ct_rw_stem_horiz,
    rule_ct_rw_toe_heel,
    rule_ct_rw_dowels,
    rule_ct_rw_shear_key,
    rule_ct_rw_e_bars,
    rule_validate_ct_rw,
)
from vistadetail.engine.rules.d84_wingwall_rules import (
    rule_d84_validate,
    rule_d84_geometry,
    rule_d84_face_horiz,
    rule_d84_longitudinals,
    rule_d84_top_bars,
    rule_d84_footing_mat,
    rule_d84_cutoff_wall,
)
from vistadetail.engine.rules.d85_wingwall_rules import (
    rule_d85_validate,
    rule_d85_geometry,
    rule_d85_n_bars,
    rule_d85_o_bars,
    rule_d85_l_bars,
    rule_d85_hoops,
    rule_d85_top_bars,
    rule_d85_footing_mat,
)
from vistadetail.engine.rules.g_type_inlet_rules import (
    # G1
    rule_g1_geometry, rule_g1_wall_bars, rule_g1_top_slab,
    rule_g1_bottom_mat, rule_g1_hoops, rule_g1_validate,
    # G3
    rule_g3_geometry, rule_g3_wall_bars, rule_g3_top_slab,
    rule_g3_bottom_mat, rule_g3_hoops, rule_g3_validate,
    # G4
    rule_g4_geometry, rule_g4_wall_bars, rule_g4_top_slab,
    rule_g4_bottom_mat, rule_g4_hoops, rule_g4_validate,
    # G5
    rule_g5_geometry, rule_g5_wall_bars, rule_g5_top_slab,
    rule_g5_bottom_mat, rule_g5_hoops, rule_g5_validate,
    # G6
    rule_g6_geometry, rule_g6_wall_bars, rule_g6_top_slab,
    rule_g6_bottom_mat, rule_g6_hoops, rule_g6_validate,
)

RULE_REGISTRY: dict = {
    # G2 Inlet / G2 Expanded Inlet
    "rule_g2_inlet_geometry":         rule_g2_inlet_geometry,
    "rule_horizontal_bars_EF":       rule_horizontal_bars_EF,
    "rule_vertical_bars_EF":         rule_vertical_bars_EF,
    "rule_corner_L_bars":            rule_corner_L_bars,
    "rule_validate_min_cover":       rule_validate_min_cover,
    "rule_validate_max_spacing_ACI": rule_validate_max_spacing_ACI,
    # G2 Inlet — Vista Excel-matched
    "rule_g2_geometry":              rule_g2_geometry,
    "rule_g2_bottom_mat":            rule_g2_bottom_mat,
    "rule_g2_horizontals":           rule_g2_horizontals,
    "rule_g2_verticals":             rule_g2_verticals,
    "rule_g2_ab_bars":               rule_g2_ab_bars,
    "rule_g2_right_angle":           rule_g2_right_angle,
    "rule_g2_hoops":                 rule_g2_hoops,
    # G2 Expanded Inlet — Vista Excel-matched
    "rule_g2exp_geometry":           rule_g2exp_geometry,
    "rule_g2exp_verticals":          rule_g2exp_verticals,
    "rule_g2exp_ab_bars":            rule_g2exp_ab_bars,
    "rule_g2exp_hoops":              rule_g2exp_hoops,
    # G2 Inlet Top — Vista Excel-matched
    "rule_g2top_geometry":           rule_g2top_geometry,
    "rule_g2top_verticals":          rule_g2top_verticals,
    "rule_g2top_right_angle":        rule_g2top_right_angle,
    # Spread Footing
    "rule_bottom_transverse":        rule_bottom_transverse,
    "rule_bottom_longitudinal":      rule_bottom_longitudinal,
    "rule_dowels":                   rule_dowels,
    "rule_validate_footing_cover":   rule_validate_footing_cover,
    # Headwall (D89A)
    "rule_hw_d_bars":                rule_hw_d_bars,
    "rule_hw_trans_footing":         rule_hw_trans_footing,
    "rule_hw_long_invert":           rule_hw_long_invert,
    "rule_hw_long_wall":             rule_hw_long_wall,
    "rule_hw_top_wall":              rule_hw_top_wall,
    "rule_hw_vert_wall":             rule_hw_vert_wall,
    "rule_hw_c_bars":                rule_hw_c_bars,
    "rule_hw_spreaders":             rule_hw_spreaders,
    "rule_hw_standees":              rule_hw_standees,
    "rule_validate_headwall":        rule_validate_headwall,
    # Wing Wall
    "rule_wing_horiz":               rule_wing_horiz,
    "rule_wing_vert":                rule_wing_vert,
    "rule_wing_corner":              rule_wing_corner,
    "rule_validate_wing":            rule_validate_wing,
    # Box Culvert (D80)
    "rule_bc_a_bars":                rule_bc_a_bars,
    "rule_bc_b_bars":                rule_bc_b_bars,
    "rule_bc_e_bars":                rule_bc_e_bars,
    "rule_bc_i_bars":                rule_bc_i_bars,
    "rule_bc_hoops":                 rule_bc_hoops,
    "rule_bc_validate":              rule_bc_validate,
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
    "rule_swbd_top_long":            rule_swbd_top_long,
    "rule_swbd_top_short":           rule_swbd_top_short,
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
    # Sound Wall
    "rule_sw_wall_verticals":        rule_sw_wall_verticals,
    "rule_sw_wall_horizontals":      rule_sw_wall_horizontals,
    "rule_sw_footing_dowels":        rule_sw_footing_dowels,
    "rule_sw_footing_bars":          rule_sw_footing_bars,
    "rule_sw_pile_cage":             rule_sw_pile_cage,
    "rule_sw_pile_cap_bars":         rule_sw_pile_cap_bars,
    "rule_validate_sound_wall":      rule_validate_sound_wall,
    # Caltrans Retaining Wall Type 1
    "rule_ct_rw_stem_vert":          rule_ct_rw_stem_vert,
    "rule_ct_rw_stem_horiz":         rule_ct_rw_stem_horiz,
    "rule_ct_rw_toe_heel":           rule_ct_rw_toe_heel,
    "rule_ct_rw_dowels":             rule_ct_rw_dowels,
    "rule_ct_rw_shear_key":          rule_ct_rw_shear_key,
    "rule_ct_rw_e_bars":             rule_ct_rw_e_bars,
    "rule_validate_ct_rw":           rule_validate_ct_rw,
    # D84 Wingwall (Types A/B/C)
    "rule_d84_validate":             rule_d84_validate,
    "rule_d84_geometry":             rule_d84_geometry,
    "rule_d84_face_horiz":           rule_d84_face_horiz,
    "rule_d84_longitudinals":        rule_d84_longitudinals,
    "rule_d84_top_bars":             rule_d84_top_bars,
    "rule_d84_footing_mat":          rule_d84_footing_mat,
    "rule_d84_cutoff_wall":          rule_d84_cutoff_wall,
    # D85 Wingwall (Types D/E)
    "rule_d85_validate":             rule_d85_validate,
    "rule_d85_geometry":             rule_d85_geometry,
    "rule_d85_n_bars":               rule_d85_n_bars,
    "rule_d85_o_bars":               rule_d85_o_bars,
    "rule_d85_l_bars":               rule_d85_l_bars,
    "rule_d85_hoops":                rule_d85_hoops,
    "rule_d85_top_bars":             rule_d85_top_bars,
    "rule_d85_footing_mat":          rule_d85_footing_mat,
    # G1 Inlet (D72B)
    "rule_g1_validate":              rule_g1_validate,
    "rule_g1_geometry":              rule_g1_geometry,
    "rule_g1_wall_bars":             rule_g1_wall_bars,
    "rule_g1_top_slab":              rule_g1_top_slab,
    "rule_g1_bottom_mat":            rule_g1_bottom_mat,
    "rule_g1_hoops":                 rule_g1_hoops,
    # G3 Inlet (D72B)
    "rule_g3_validate":              rule_g3_validate,
    "rule_g3_geometry":              rule_g3_geometry,
    "rule_g3_wall_bars":             rule_g3_wall_bars,
    "rule_g3_top_slab":              rule_g3_top_slab,
    "rule_g3_bottom_mat":            rule_g3_bottom_mat,
    "rule_g3_hoops":                 rule_g3_hoops,
    # G4 Inlet (D72B)
    "rule_g4_validate":              rule_g4_validate,
    "rule_g4_geometry":              rule_g4_geometry,
    "rule_g4_wall_bars":             rule_g4_wall_bars,
    "rule_g4_top_slab":              rule_g4_top_slab,
    "rule_g4_bottom_mat":            rule_g4_bottom_mat,
    "rule_g4_hoops":                 rule_g4_hoops,
    # G5 Inlet (D72B)
    "rule_g5_validate":              rule_g5_validate,
    "rule_g5_geometry":              rule_g5_geometry,
    "rule_g5_wall_bars":             rule_g5_wall_bars,
    "rule_g5_top_slab":              rule_g5_top_slab,
    "rule_g5_bottom_mat":            rule_g5_bottom_mat,
    "rule_g5_hoops":                 rule_g5_hoops,
    # G6 Inlet (D72B)
    "rule_g6_validate":              rule_g6_validate,
    "rule_g6_geometry":              rule_g6_geometry,
    "rule_g6_wall_bars":             rule_g6_wall_bars,
    "rule_g6_top_slab":              rule_g6_top_slab,
    "rule_g6_bottom_mat":            rule_g6_bottom_mat,
    "rule_g6_hoops":                 rule_g6_hoops,
}
