"""
Caltrans D72 CIP Drainage Inlet Type G4.

Concrete curb type -- #5 all around. Standard W = 2'-11¾".
Can accommodate pipe penetration (2'-11¾" min or 15° max diameter).
"""
from __future__ import annotations
from vistadetail.engine.schema import InputField
from vistadetail.engine.templates.base import BaseTemplate


class G4InletTemplate(BaseTemplate):
    def __init__(self):
        super().__init__()
        self.name = "G4 Inlet"
        self.version = "1.0"
        self.description = (
            "Caltrans D72B -- CIP Drainage Inlet Type G4. "
            "Concrete curb type, #5 all around, std W=2'-11¾\"."
        )
        self.inputs = [
            InputField("x_dim_ft", float, label="L1 -- Inlet Box Length (ft)",
                       min=2.0, max=30.0, default=4.0,
                       hint="Length of inlet box along roadway."),
            InputField("y_dim_ft", float, label="H -- Inlet Depth (ft)",
                       min=2.0, max=12.0, default=4.0,
                       hint="Depth from grate to flowline."),
            InputField("wall_thick_in", float, label="Wall Thickness (in)",
                       min=9.0, max=12.0, default=9.0,
                       hint="Standard 9\" per D72."),
            InputField("grate_type", str, label="Grate Type",
                       choices=["Type 24", "Type 18"], default="Type 24",
                       hint="Standard grate opening type."),
            InputField("num_structures", int, label="Number of Inlets",
                       min=1, max=20, default=1,
                       hint="Multiply barlist by this count."),
        ]
        self.rules = [
            "rule_g4_validate",
            "rule_g4_geometry",
            "rule_g4_wall_bars",
            "rule_g4_top_slab",
            "rule_g4_bottom_mat",
            "rule_g4_hoops",
        ]


TEMPLATE = G4InletTemplate()
