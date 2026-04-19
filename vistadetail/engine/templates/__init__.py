"""
TEMPLATE_REGISTRY — maps display names to template instances.

Add new templates here.
"""

from vistadetail.engine.templates.inlet_9in_wall import TEMPLATE as INLET_9IN_WALL
from vistadetail.engine.templates.spread_footing import TEMPLATE as SPREAD_FOOTING
from vistadetail.engine.templates.headwall import TEMPLATE as HEADWALL
from vistadetail.engine.templates.wing_wall import TEMPLATE as WING_WALL
from vistadetail.engine.templates.box_culvert import TEMPLATE as BOX_CULVERT
from vistadetail.engine.templates.retaining_wall import TEMPLATE as RETAINING_WALL
from vistadetail.engine.templates.flat_slab import TEMPLATE as FLAT_SLAB
from vistadetail.engine.templates.cage import TEMPLATE as CAGE
from vistadetail.engine.templates.collar import TEMPLATE as COLLAR
from vistadetail.engine.templates.slab_on_grade import TEMPLATE as SLAB_ON_GRADE
from vistadetail.engine.templates.equipment_pad import TEMPLATE as EQUIPMENT_PAD
from vistadetail.engine.templates.switchboard_pad import TEMPLATE as SWITCHBOARD_PAD
from vistadetail.engine.templates.seatwall import TEMPLATE as SEATWALL
from vistadetail.engine.templates.concrete_header import TEMPLATE as CONCRETE_HEADER
from vistadetail.engine.templates.pipe_encasement import TEMPLATE as PIPE_ENCASEMENT
from vistadetail.engine.templates.fuel_foundation import TEMPLATE as FUEL_FOUNDATION
from vistadetail.engine.templates.dual_slab import TEMPLATE as DUAL_SLAB
from vistadetail.engine.templates.g2_expanded_inlet import TEMPLATE as G2_EXPANDED_INLET
from vistadetail.engine.templates.g2_inlet_top import TEMPLATE as G2_INLET_TOP
from vistadetail.engine.templates.g2_expanded_inlet_top import TEMPLATE as G2_EXPANDED_INLET_TOP
from vistadetail.engine.templates.junction_structure import TEMPLATE as JUNCTION_STRUCTURE
from vistadetail.engine.templates.sound_wall import TEMPLATE as SOUND_WALL
from vistadetail.engine.templates.caltrans_ret_wall import TEMPLATE as CALTRANS_RET_WALL
from vistadetail.engine.templates.d84_wingwall import TEMPLATE as D84_WINGWALL
from vistadetail.engine.templates.d85_wingwall import TEMPLATE as D85_WINGWALL
from vistadetail.engine.templates.g1_inlet import TEMPLATE as G1_INLET
from vistadetail.engine.templates.g3_inlet import TEMPLATE as G3_INLET
from vistadetail.engine.templates.g4_inlet import TEMPLATE as G4_INLET
from vistadetail.engine.templates.g5_inlet import TEMPLATE as G5_INLET
from vistadetail.engine.templates.g6_inlet import TEMPLATE as G6_INLET

TEMPLATE_REGISTRY: dict = {
    # ── G-Type CIP Inlets (D72B) ──────────────────────────────────────────────
    INLET_9IN_WALL.name:         INLET_9IN_WALL,
    G2_EXPANDED_INLET.name:      G2_EXPANDED_INLET,
    G2_INLET_TOP.name:           G2_INLET_TOP,
    G2_EXPANDED_INLET_TOP.name:  G2_EXPANDED_INLET_TOP,
    G1_INLET.name:               G1_INLET,
    G3_INLET.name:               G3_INLET,
    G4_INLET.name:               G4_INLET,
    G5_INLET.name:               G5_INLET,
    G6_INLET.name:               G6_INLET,
    # ── Headwalls ─────────────────────────────────────────────────────────────
    HEADWALL.name:               HEADWALL,
    WING_WALL.name:              WING_WALL,
    # ── Junction & Pipe ───────────────────────────────────────────────────────
    JUNCTION_STRUCTURE.name:     JUNCTION_STRUCTURE,
    COLLAR.name:                 COLLAR,
    PIPE_ENCASEMENT.name:        PIPE_ENCASEMENT,
    # ── Culverts & Walls ──────────────────────────────────────────────────────
    BOX_CULVERT.name:            BOX_CULVERT,
    RETAINING_WALL.name:         RETAINING_WALL,
    CALTRANS_RET_WALL.name:      CALTRANS_RET_WALL,
    SOUND_WALL.name:             SOUND_WALL,
    # ── Caltrans D84/D85 Wingwalls ────────────────────────────────────────
    D84_WINGWALL.name:           D84_WINGWALL,
    D85_WINGWALL.name:           D85_WINGWALL,
    # ── Slabs & Pads ──────────────────────────────────────────────────────────
    FLAT_SLAB.name:              FLAT_SLAB,
    DUAL_SLAB.name:              DUAL_SLAB,
    SLAB_ON_GRADE.name:          SLAB_ON_GRADE,
    EQUIPMENT_PAD.name:          EQUIPMENT_PAD,
    SWITCHBOARD_PAD.name:        SWITCHBOARD_PAD,
    FUEL_FOUNDATION.name:        FUEL_FOUNDATION,
    # ── Misc Concrete ─────────────────────────────────────────────────────────
    SPREAD_FOOTING.name:         SPREAD_FOOTING,
    SEATWALL.name:               SEATWALL,
    CONCRETE_HEADER.name:        CONCRETE_HEADER,
    CAGE.name:                   CAGE,
}

TEMPLATE_NAMES: list[str] = list(TEMPLATE_REGISTRY.keys())
