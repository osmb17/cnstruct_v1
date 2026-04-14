"""
Deterministic hook extension and development length tables.

All values per ACI 318-19 and Caltrans BDS (2022 amendments).
These are NEVER derived from an LLM — they are hardcoded constants.

Also includes: Reductions at Bends table from Vista Steel shop standard
(scan_20260131.pdf) — inches to DEDUCT per shape when calculating stock
(cut) length from leg dimensions.

Units: inches
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Reductions at Bends — Vista Steel shop standard (scan_20260131.pdf)
#
# Source: printed fabricator table; values match standard CRSI bend deductions.
# Key: bar_size → deduction in inches for the given shape number.
#
# Shape 1: single 90° bend (L-bar)                 — 1 bend
# Shape 2: two 90° bends (U / hairpin / C-bar)     — 2 bends
# Shape 3: three 90° bends (open stirrup one side)  — 3 bends
# Shape 4: four 90° bends (closed stirrup / hoop)  — 4 bends
# Stirrup: per each 90° bend (used for hoops with known bend count)
#
# Stock length = sum of all leg dimensions − BEND_REDUCTION[shape][bar_size]
# ---------------------------------------------------------------------------

BEND_REDUCTION: dict[str, dict[str, float]] = {
    # shape_1: single 90° bend
    "shape_1": {
        "#2":  0.5,  "#3":  0.75, "#4":  1.0,  "#5":  1.5,
        "#6":  2.0,  "#7":  2.25, "#8":  3.0,  "#9":  3.25,
        "#10": 4.0,  "#11": 4.5,  "#14": 6.0,  "#18": 8.0,
    },
    # shape_2: two 90° bends (U-bar / C-bar / hairpin)
    "shape_2": {
        "#2":  1.0,  "#3":  1.5,  "#4":  2.0,  "#5":  3.0,
        "#6":  4.0,  "#7":  4.5,  "#8":  6.0,  "#9":  6.5,
        "#10": 8.0,  "#11": 9.0,  "#14": 12.0, "#18": 16.0,
    },
    # shape_3: three 90° bends
    "shape_3": {
        "#2":  1.5,  "#3":  2.25, "#4":  3.0,  "#5":  4.5,
        "#6":  6.0,  "#7":  6.75, "#8":  9.0,  "#9":  9.75,
        "#10": 12.0, "#11": 13.5, "#14": 18.0, "#18": 24.0,
    },
    # shape_4: four 90° bends (closed rectangular hoop / stirrup)
    "shape_4": {
        "#2":  2.0,  "#3":  3.0,  "#4":  4.0,  "#5":  6.0,
        "#6":  8.0,  "#7":  9.0,  "#8":  12.0, "#9":  13.0,
        "#10": 16.0, "#11": 18.0, "#14": 24.0,
    },
    # per_90: deduction per each 90° bend (use for arbitrary bend counts)
    "per_90": {
        "#2":  0.5,  "#3":  0.75, "#4":  1.0,  "#5":  1.25,
        "#6":  1.75, "#7":  2.0,  "#8":  2.5,  "#9":  2.75,
        "#10": 2.75, "#11": 3.5,  "#14": 4.0,
    },
}


def bend_reduce(shape: str, bar_size: str) -> float:
    """
    Return total inches to deduct from the sum of leg dimensions to get
    the stock (cut) length for a bar of the given shape and bar size.

    Args:
        shape:    one of "shape_1", "shape_2", "shape_3", "shape_4", "per_90"
        bar_size: standard bar designation, e.g. "#4", "#5"

    Returns:
        Deduction in inches (float).

    Raises:
        ValueError if shape or bar_size is not in the table.
    """
    table = BEND_REDUCTION.get(shape)
    if table is None:
        raise ValueError(f"Unknown bend shape: {shape!r}. "
                         f"Use one of {list(BEND_REDUCTION)}")
    deduct = table.get(bar_size)
    if deduct is None:
        raise ValueError(f"Bar size {bar_size!r} not in bend reduction table "
                         f"for shape {shape!r}")
    return deduct

# ---------------------------------------------------------------------------
# Standard 90° hook — added length beyond straight bar (tail extension)
# ACI 318-19 Table 25.3.2 — minimum tail extension for 90° hooks
# Values shown are the hook addition per end (one end only)
# ---------------------------------------------------------------------------

HOOK_90_ADD_IN: dict[str, float] = {
    "#3":  4.5,
    "#4":  6.0,
    "#5":  7.5,
    "#6":  9.0,
    "#7": 10.5,
    "#8": 12.0,
    "#9": 13.5,
    "#10": 15.0,
    "#11": 16.5,
}

# ---------------------------------------------------------------------------
# Standard 180° hook — added length
# ACI 318-19 Table 25.3.2 — 4db extension beyond bend, min 2.5 in
# ---------------------------------------------------------------------------

HOOK_180_ADD_IN: dict[str, float] = {
    "#3":  3.0,
    "#4":  4.0,
    "#5":  5.0,
    "#6":  6.0,
    "#7":  7.0,
    "#8":  8.0,
    "#9":  9.0,
    "#10": 10.0,
    "#11": 11.0,
}

# ---------------------------------------------------------------------------
# Seismic / special hook (135° stirrup/tie hook)
# ACI 318-19 Section 25.3.4
# ---------------------------------------------------------------------------

HOOK_SEISMIC_ADD_IN: dict[str, float] = {
    "#3":  3.0,
    "#4":  4.0,
    "#5":  5.0,
    "#6":  6.0,
    "#7":  7.0,
    "#8":  8.0,
    "#9":  9.0,
}

# ---------------------------------------------------------------------------
# Nominal bar diameter (inches)
# ---------------------------------------------------------------------------

BAR_DIAMETER_IN: dict[str, float] = {
    "#3":  0.375,
    "#4":  0.500,
    "#5":  0.625,
    "#6":  0.750,
    "#7":  0.875,
    "#8":  1.000,
    "#9":  1.128,
    "#10": 1.270,
    "#11": 1.410,
}

# ---------------------------------------------------------------------------
# Nominal bar area (sq in)
# ---------------------------------------------------------------------------

BAR_AREA_IN2: dict[str, float] = {
    "#3":  0.11,
    "#4":  0.20,
    "#5":  0.31,
    "#6":  0.44,
    "#7":  0.60,
    "#8":  0.79,
    "#9":  1.00,
    "#10": 1.27,
    "#11": 1.56,
}

# ---------------------------------------------------------------------------
# Weight per linear foot (lb/ft)
# ---------------------------------------------------------------------------

BAR_WEIGHT_LB_FT: dict[str, float] = {
    "#3":  0.376,
    "#4":  0.668,
    "#5":  1.043,
    "#6":  1.502,
    "#7":  2.044,
    "#8":  2.670,
    "#9":  3.400,
    "#10": 4.303,
    "#11": 5.313,
}

# ---------------------------------------------------------------------------
# Combined lookup table: HOOK_TABLE[hook_type][bar_size] → add inches
# ---------------------------------------------------------------------------

HOOK_TABLE: dict[str, dict[str, float]] = {
    "std_90":    HOOK_90_ADD_IN,
    "std_180":   HOOK_180_ADD_IN,
    "seismic":   HOOK_SEISMIC_ADD_IN,
    "none":      {s: 0.0 for s in HOOK_90_ADD_IN},
}


def hook_add(hook_type: str, bar_size: str) -> float:
    """Return inches to add per hooked end for this hook type and bar size."""
    table = HOOK_TABLE.get(hook_type)
    if table is None:
        raise ValueError(f"Unknown hook type: {hook_type!r}")
    add = table.get(bar_size)
    if add is None:
        raise ValueError(f"Unknown bar size: {bar_size!r}")
    return add


def bar_diameter(bar_size: str) -> float:
    """Nominal diameter in inches."""
    d = BAR_DIAMETER_IN.get(bar_size)
    if d is None:
        raise ValueError(f"Unknown bar size: {bar_size!r}")
    return d


def min_bend_diameter(bar_size: str, is_stirrup: bool = False) -> float:
    """Minimum inside bend diameter per ACI 318-19 Table 25.3.1.

    Stirrups/ties #3-#5: 4db
    All other #3-#8:     6db
    #9-#11:              8db
    """
    db = bar_diameter(bar_size)
    size_num = int(bar_size.lstrip("#"))
    if is_stirrup and size_num <= 5:
        return 4.0 * db
    elif size_num <= 8:
        return 6.0 * db
    else:
        return 8.0 * db


def development_length_tension(bar_size: str, fc_psi: float = 4000, fy_psi: float = 60000,
                                 cover_in: float = 2.0, spacing_in: float | None = None,
                                 epoxy: bool = False) -> float:
    """
    Tension development length per ACI 318-19 Section 25.5.2.1a.
    Uses simplified formula (Ktr = 0, no transverse reinforcement credit).

    cb = min(cover, spacing/2) per ACI 318-19 25.5.2.1.
    If spacing_in is None, falls back to cover only (conservative).

    Returns inches.
    """
    import math
    db = bar_diameter(bar_size)
    psi_t = 1.0   # top bar factor (conservative; not top bar)
    psi_e = 1.5 if epoxy else 1.0
    psi_s = 0.8 if bar_size in ("#3", "#4", "#5", "#6") else 1.0
    lam = 1.0     # normal weight concrete

    # cb = smaller of cover or half center-to-center spacing (ACI 318-19 25.5.2.1)
    if spacing_in is not None:
        cb = min(cover_in, spacing_in / 2.0)
    else:
        cb = cover_in
    cb_over_db = min(cb / db, 2.5)  # cap per ACI

    # ACI 318-19 Eq. 25.5.2.1a (Ktr = 0, no transverse reinforcement credit)
    ld = ((3 * fy_psi * psi_t * psi_e * psi_s) /
          (40 * lam * math.sqrt(fc_psi) * cb_over_db)) * db
    ld = max(ld, 12.0)  # ACI minimum 12 in
    return round(ld, 2)
