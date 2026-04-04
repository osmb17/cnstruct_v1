"""
caltrans_tables.py — Caltrans Standard Plan lookup tables.

Encoded from the following standard plans (2025 edition):
  Table C  — CIP Drainage Inlet Wall Reinforcement (Standard Plan D73A)
  D80      — CIP Reinforced Concrete Single Box Culvert
  D81      — CIP Reinforced Concrete Double Box Culvert
  D89B     — Pipe Culvert Headwalls, Straight and "L"
  D91B     — CIP Reinforced Concrete Junction Structure

Usage:
    from caltrans_tables import caltrans_lookup

    vals = caltrans_lookup("G2 Inlet", params_raw)
    # returns dict of {field_name: value} — auto-fills advanced inputs
"""

from __future__ import annotations


# ─────────────────────────────────────────────────────────────────────────────
# TABLE C — CIP Drainage Inlet Wall Reinforcement
# Source: Caltrans Standard Plan D73A / Table C
#
# Structure:
#   {inlet_type: {"low": {...}, "high": {...}}}
#   "low"  = H ≤ 8 ft (T = 6" UON unless overridden by type)
#   "high" = 8 ft < H ≤ 20 ft (T = 11" UON)
#
# Some types are limited to H ≤ 6'-6" (6.5 ft) — noted by max_H_ft.
# Types with no "high" entry are not valid above their max_H_ft.
# ─────────────────────────────────────────────────────────────────────────────

_LOW  = "low"
_HIGH = "high"

TABLE_C: dict[str, dict] = {
    "OS": {
        _LOW:  {"T_in": 6,  "horiz": ("#4", 8.0), "vert": ("#4", 6.0)},
        _HIGH: {"T_in": 11, "horiz": ("#5", 6.0), "vert": ("#6", 4.5)},
    },
    "OL": {
        _LOW:  {"T_in": 6,  "horiz": ("#4", 6.0), "vert": ("#4", 6.0)},
        _HIGH: {"T_in": 11, "horiz": ("#5", 6.0), "vert": ("#6", 4.5)},
    },
    "GOL": {
        _LOW:  {"T_in": 6,  "horiz": ("#5", 6.0), "vert": ("#5", 8.0)},
        _HIGH: {"T_in": 11, "horiz": ("#6", 5.0), "vert": ("#6", 4.5)},
    },
    "G1": {
        _LOW:  {"T_in": 6,  "horiz": ("#3", 6.0), "vert": ("#3", 6.0), "max_H_ft": 6.5},
    },
    "G2": {
        _LOW:  {"T_in": 9,  "horiz": ("#5", 5.0), "vert": ("#5", 5.0)},
        _HIGH: {"T_in": 11, "horiz": ("#6", 4.0), "vert": ("#6", 4.5)},
    },
    "G3": {
        _LOW:  {"T_in": 6,  "horiz": ("#3", 6.0), "vert": ("#3", 6.0), "max_H_ft": 6.5},
    },
    "G4": {
        _LOW:  {"T_in": 9,  "horiz": ("#5", 5.0), "vert": ("#5", 5.0)},
        _HIGH: {"T_in": 11, "horiz": ("#6", 4.0), "vert": ("#6", 4.5)},
    },
    "G5": {
        _LOW:  {"T_in": 6,  "horiz": ("#3", 6.0), "vert": ("#3", 6.0), "max_H_ft": 6.5},
    },
    "G6": {
        _LOW:  {"T_in": 6,  "horiz": ("#3", 6.0), "vert": ("#3", 6.0), "max_H_ft": 6.5},
    },
    "GT1": {
        _LOW:  {"T_in": 6,  "horiz": ("#5", 6.0), "vert": ("#5", 6.0), "max_H_ft": 6.5},
    },
    "GT2": {
        _LOW:  {"T_in": 8,  "horiz": ("#5", 6.0), "vert": ("#5", 6.0)},
        _HIGH: {"T_in": 11, "horiz": ("#6", 4.0), "vert": ("#6", 4.5)},
    },
    "GT3": {
        _LOW:  {"T_in": 6,  "horiz": ("#5", 6.0), "vert": ("#5", 6.0), "max_H_ft": 6.5},
    },
    "GT4": {
        _LOW:  {"T_in": 8,  "horiz": ("#5", 6.0), "vert": ("#5", 6.0)},
        _HIGH: {"T_in": 11, "horiz": ("#6", 4.0), "vert": ("#6", 4.5)},
    },
    "GO": {
        _LOW:  {"T_in": 6,  "horiz": ("#4", 9.0), "vert": ("#4", 6.0)},
        _HIGH: {"T_in": 11, "horiz": ("#4", 6.0), "vert": ("#6", 4.5)},
    },
    "GDO": {
        _LOW:  {"T_in": 6,  "horiz": ("#4", 6.0), "vert": ("#4", 6.0)},
        _HIGH: {"T_in": 11, "horiz": ("#5", 4.0), "vert": ("#6", 4.5)},
    },
}

# Maps CNSTRUCT template name → Table C key
# Both G2 Inlet and G2 Expanded Inlet use the G2 reinforcement standard.
_TEMPLATE_TO_C_TYPE: dict[str, str] = {
    "G2 Inlet":              "G2",
    "G2 Expanded Inlet":     "G2",
}


def _lookup_table_c(template_name: str, params_raw: dict) -> dict:
    """
    Return Caltrans Table C reinforcement values for the given inlet template.
    Fields returned: wall_thick_in, horiz_bar_size, horiz_spacing_in,
                     vert_bar_size, vert_spacing_in
    """
    inlet_type = _TEMPLATE_TO_C_TYPE.get(template_name)
    if not inlet_type or inlet_type not in TABLE_C:
        return {}

    H = float(params_raw.get("wall_height_ft", 0) or 0)
    if H <= 0:
        return {}

    entry = TABLE_C[inlet_type]
    max_H = entry.get(_LOW, {}).get("max_H_ft", 20.0)

    if H > max_H and _HIGH not in entry:
        # Height exceeds standard — no lookup available
        return {}

    row = entry[_HIGH] if H > 8.0 and _HIGH in entry else entry[_LOW]

    return {
        "wall_thick_in":   row["T_in"],
        "horiz_bar_size":  row["horiz"][0],
        "horiz_spacing_in": row["horiz"][1],
        "vert_bar_size":   row["vert"][0],
        "vert_spacing_in": row["vert"][1],
        "_source": f"Table C / {inlet_type} / {'H>8' if H > 8.0 else 'H≤8'}",
    }


# ─────────────────────────────────────────────────────────────────────────────
# TABLE D80 — Single Box Culvert Reinforcement
# Source: Caltrans Standard Plan D80 (2025)
#
# Key: (span_ft, height_ft, max_cover_ft)
# max_cover_ft is rounded to nearest 10 or 20 (10 = ≤10 ft, 20 = ≤20 ft)
#
# Values: T1_in (roof), T2_in (wall), T3_in (invert),
#         a_bar, a_spacing, b_bar, b_spacing, e_bar, e_spacing, dim_B_in
#
# NOTE: Values read from plan sheet D80. Verify against full-size drawings
# before use on permitted projects.
# ─────────────────────────────────────────────────────────────────────────────

# Format: (span_ft, height_ft): {10: {...}, 20: {...}}
TABLE_D80: dict[tuple, dict] = {
    # Span 4'
    (4, 2): {
        10: {"T1": 7,  "T2": 8,  "T3": 7,  "a": ("#4", 4.5), "b": ("#4", 4.5), "e": ("#4", 4.5), "B_in": 24},
        20: {"T1": 8,  "T2": 8,  "T3": 8,  "a": ("#4", 4.5), "b": ("#4", 4.5), "e": ("#4", 4.5), "B_in": 26},
    },
    (4, 3): {
        10: {"T1": 7,  "T2": 8,  "T3": 7,  "a": ("#5", 5.0), "b": ("#4", 5.0), "e": ("#4", 4.5), "B_in": 24},
        20: {"T1": 8,  "T2": 8,  "T3": 8,  "a": ("#5", 4.5), "b": ("#5", 4.5), "e": ("#4", 4.5), "B_in": 26},
    },
    (4, 4): {
        10: {"T1": 8,  "T2": 8,  "T3": 8,  "a": ("#5", 5.0), "b": ("#5", 5.0), "e": ("#4", 4.5), "B_in": 28},
        20: {"T1": 8,  "T2": 9,  "T3": 9,  "a": ("#5", 4.5), "b": ("#5", 4.5), "e": ("#5", 4.5), "B_in": 30},
    },
    (4, 5): {
        10: {"T1": 8,  "T2": 8,  "T3": 8,  "a": ("#5", 4.5), "b": ("#5", 4.5), "e": ("#4", 4.5), "B_in": 28},
        20: {"T1": 9,  "T2": 10, "T3": 9,  "a": ("#6", 4.5), "b": ("#5", 4.5), "e": ("#5", 4.5), "B_in": 32},
    },
    # Span 5'
    (5, 2): {
        10: {"T1": 7,  "T2": 8,  "T3": 7,  "a": ("#4", 4.5), "b": ("#4", 4.5), "e": ("#4", 4.5), "B_in": 28},
        20: {"T1": 8,  "T2": 8,  "T3": 8,  "a": ("#5", 4.5), "b": ("#4", 4.5), "e": ("#4", 4.5), "B_in": 30},
    },
    (5, 4): {
        10: {"T1": 8,  "T2": 9,  "T3": 8,  "a": ("#5", 5.0), "b": ("#5", 5.0), "e": ("#4", 4.5), "B_in": 30},
        20: {"T1": 9,  "T2": 10, "T3": 9,  "a": ("#6", 4.5), "b": ("#5", 4.5), "e": ("#5", 4.5), "B_in": 32},
    },
    (5, 5): {
        10: {"T1": 8,  "T2": 9,  "T3": 8,  "a": ("#5", 4.5), "b": ("#5", 4.5), "e": ("#4", 4.5), "B_in": 30},
        20: {"T1": 10, "T2": 11, "T3": 10, "a": ("#6", 4.5), "b": ("#6", 4.5), "e": ("#5", 4.5), "B_in": 34},
    },
    # Span 6'
    (6, 3): {
        10: {"T1": 8,  "T2": 9,  "T3": 8,  "a": ("#5", 5.0), "b": ("#5", 5.0), "e": ("#4", 4.5), "B_in": 32},
        20: {"T1": 9,  "T2": 10, "T3": 9,  "a": ("#6", 4.5), "b": ("#5", 4.5), "e": ("#5", 4.5), "B_in": 34},
    },
    (6, 4): {
        10: {"T1": 8,  "T2": 9,  "T3": 8,  "a": ("#5", 4.5), "b": ("#5", 4.5), "e": ("#4", 4.5), "B_in": 32},
        20: {"T1": 10, "T2": 11, "T3": 10, "a": ("#6", 4.5), "b": ("#6", 4.5), "e": ("#5", 4.5), "B_in": 36},
    },
    (6, 6): {
        10: {"T1": 9,  "T2": 10, "T3": 9,  "a": ("#6", 4.5), "b": ("#5", 4.5), "e": ("#5", 4.5), "B_in": 34},
        20: {"T1": 11, "T2": 12, "T3": 11, "a": ("#6", 4.5), "b": ("#6", 4.5), "e": ("#6", 4.5), "B_in": 38},
    },
    # Span 8'
    (8, 4): {
        10: {"T1": 9,  "T2": 10, "T3": 9,  "a": ("#6", 4.5), "b": ("#5", 4.5), "e": ("#5", 4.5), "B_in": 38},
        20: {"T1": 11, "T2": 12, "T3": 11, "a": ("#7", 4.5), "b": ("#6", 4.5), "e": ("#6", 4.5), "B_in": 42},
    },
    (8, 6): {
        10: {"T1": 10, "T2": 11, "T3": 10, "a": ("#6", 4.5), "b": ("#6", 4.5), "e": ("#5", 4.5), "B_in": 40},
        20: {"T1": 12, "T2": 14, "T3": 12, "a": ("#7", 4.5), "b": ("#7", 4.5), "e": ("#6", 4.5), "B_in": 46},
    },
    # Span 10'
    (10, 5): {
        10: {"T1": 10, "T2": 12, "T3": 10, "a": ("#6", 4.5), "b": ("#6", 4.5), "e": ("#5", 4.5), "B_in": 44},
        20: {"T1": 13, "T2": 15, "T3": 13, "a": ("#7", 4.5), "b": ("#7", 4.5), "e": ("#6", 4.5), "B_in": 50},
    },
    (10, 7): {
        10: {"T1": 11, "T2": 13, "T3": 11, "a": ("#7", 4.5), "b": ("#6", 4.5), "e": ("#6", 4.5), "B_in": 46},
        20: {"T1": 14, "T2": 16, "T3": 14, "a": ("#7", 4.5), "b": ("#7", 4.5), "e": ("#7", 4.5), "B_in": 54},
    },
    # Span 12'
    (12, 6): {
        10: {"T1": 12, "T2": 14, "T3": 12, "a": ("#7", 4.5), "b": ("#7", 4.5), "e": ("#6", 4.5), "B_in": 50},
        20: {"T1": 15, "T2": 18, "T3": 15, "a": ("#7", 4.5), "b": ("#7", 4.5), "e": ("#7", 4.5), "B_in": 58},
    },
    (12, 8): {
        10: {"T1": 13, "T2": 15, "T3": 13, "a": ("#7", 4.5), "b": ("#7", 4.5), "e": ("#6", 4.5), "B_in": 52},
        20: {"T1": 16, "T2": 20, "T3": 16, "a": ("#7", 4.5), "b": ("#7", 4.5), "e": ("#7", 4.5), "B_in": 60},
    },
}


def _nearest_key(table: dict, span: int, height: int) -> tuple | None:
    """Find the nearest (span, height) key in a table."""
    spans   = sorted({k[0] for k in table})
    heights = sorted({k[1] for k in table})

    def nearest(lst, val):
        return min(lst, key=lambda x: abs(x - val))

    s = nearest(spans, span)
    h = nearest(heights, height)
    key = (s, h)
    return key if key in table else None


def _lookup_table_d80(params_raw: dict) -> dict:
    span_ft   = int(round(float(params_raw.get("clear_span_ft", 0) or 0)))
    height_ft = int(round(float(params_raw.get("clear_rise_ft", 0) or 0)))
    cover_ft  = float(params_raw.get("earth_cover_ft", 10) or 10)

    if span_ft <= 0 or height_ft <= 0:
        return {}

    key = _nearest_key(TABLE_D80, span_ft, height_ft)
    if not key:
        return {}

    cover_key = 20 if cover_ft > 10 else 10
    row = TABLE_D80[key].get(cover_key, {})
    if not row:
        return {}

    return {
        "wall_thick_in":      row["T2"],
        "slab_bar_size":      row["a"][0],
        "slab_spacing_in":    row["a"][1],
        "bot_slab_bar_size":  row["a"][0],
        "bot_slab_spacing_in": row["a"][1],
        "wall_bar_size":      row["b"][0],
        "wall_spacing_in":    row["b"][1],
        "_source": f"D80 / S={key[0]}' H={key[1]}' cover≤{cover_key}'",
    }


# ─────────────────────────────────────────────────────────────────────────────
# TABLE D89B — Pipe Culvert Headwall (Straight and "L")
# Source: Caltrans Standard Plan D89B (2025)
#
# Key: design H in inches (wall stem height)
# Values: T (wall thickness), W, A, B, C dimensions — all in inches
# Reinforcement is standard #4@12 across all sizes per typical section.
# ─────────────────────────────────────────────────────────────────────────────

# H in ft-in string → (H_in, T_in, W_in)
TABLE_D89B: dict[float, dict] = {
    # H_ft : {T_in, W_in, horiz_bar, horiz_spacing, vert_bar, vert_spacing}
    2.67: {"T_in": 10, "W_in": 27,  "horiz": ("#4", 12.0), "vert": ("#4", 12.0)},  # 2'-8"
    2.92: {"T_in": 10, "W_in": 27,  "horiz": ("#4", 12.0), "vert": ("#4", 12.0)},  # 2'-11"
    3.17: {"T_in": 10, "W_in": 30,  "horiz": ("#4", 12.0), "vert": ("#4", 12.0)},  # 3'-2"
    3.42: {"T_in": 10, "W_in": 30,  "horiz": ("#4", 12.0), "vert": ("#4", 12.0)},  # 3'-5"
    3.67: {"T_in": 10, "W_in": 33,  "horiz": ("#4", 12.0), "vert": ("#4", 12.0)},  # 3'-8"
    3.92: {"T_in": 10, "W_in": 33,  "horiz": ("#4", 12.0), "vert": ("#4", 12.0)},  # 3'-11"
    4.17: {"T_in": 10, "W_in": 36,  "horiz": ("#4", 12.0), "vert": ("#4", 12.0)},  # 4'-2"
    4.67: {"T_in": 10, "W_in": 39,  "horiz": ("#4", 12.0), "vert": ("#5", 9.0)},   # 4'-8"
    4.92: {"T_in": 10, "W_in": 42,  "horiz": ("#4", 12.0), "vert": ("#5", 9.0)},   # 4'-11"
    5.17: {"T_in": 10, "W_in": 42,  "horiz": ("#5", 9.0),  "vert": ("#5", 9.0)},   # 5'-2"
    5.42: {"T_in": 10, "W_in": 45,  "horiz": ("#5", 9.0),  "vert": ("#5", 9.0)},   # 5'-5"
    5.67: {"T_in": 10, "W_in": 48,  "horiz": ("#5", 9.0),  "vert": ("#5", 9.0)},   # 5'-8"
    5.92: {"T_in": 10, "W_in": 48,  "horiz": ("#5", 9.0),  "vert": ("#5", 9.0)},   # 5'-11"
    6.17: {"T_in": 12, "W_in": 54,  "horiz": ("#5", 9.0),  "vert": ("#5", 9.0)},   # 6'-2"
    6.42: {"T_in": 12, "W_in": 57,  "horiz": ("#5", 9.0),  "vert": ("#5", 9.0)},   # 6'-5"
}


def _lookup_table_d89b(params_raw: dict) -> dict:
    H_ft = float(params_raw.get("wall_height_ft", 0) or 0)
    if H_ft <= 0:
        return {}

    # Find nearest H in table
    nearest_H = min(TABLE_D89B.keys(), key=lambda h: abs(h - H_ft))
    row = TABLE_D89B[nearest_H]

    return {
        "wall_thick_in":    row["T_in"],
        "horiz_bar_size":   row["horiz"][0],
        "horiz_spacing_in": row["horiz"][1],
        "vert_bar_size":    row["vert"][0],
        "vert_spacing_in":  row["vert"][1],
        "_source": f"D89B / H={nearest_H:.2f}ft",
    }


# ─────────────────────────────────────────────────────────────────────────────
# TABLE D91B — CIP Junction Structure Reinforcement
# Source: Caltrans Standard Plan D91B (2025)
#
# Key: (Hb_ft, span_ft, max_cover_ft)
# Hb = inside depth, span = inside width (larger dimension)
# max_cover: 10 or 20 ft
#
# Values: ts (top slab), t (wall), bs (bottom slab) — all in inches
#         a_bars (slabs top+bot), e_bars (wall ext), b_bars (wall int)
# ─────────────────────────────────────────────────────────────────────────────

# (Hb_ft, span_ft): {10: {...}, 20: {...}}
TABLE_D91B: dict[tuple, dict] = {
    (5.5, 4): {
        10: {"ts": 8,  "t": 8,  "bs": 8,  "a": ("#4", 10.0), "e": ("#4", 6.0), "b": ("#4", 10.0), "B_in": 28},
        20: {"ts": 8,  "t": 8,  "bs": 8,  "a": ("#4", 6.0),  "e": ("#4", 6.0), "b": ("#4", 6.0),  "B_in": 28},
    },
    (6.0, 5): {
        10: {"ts": 8,  "t": 8,  "bs": 8,  "a": ("#4", 6.0),  "e": ("#4", 6.0), "b": ("#4", 6.0),  "B_in": 31},
        20: {"ts": 8,  "t": 8,  "bs": 8,  "a": ("#4", 5.0),  "e": ("#4", 5.0), "b": ("#4", 6.0),  "B_in": 31},
    },
    (7.0, 6): {
        10: {"ts": 8,  "t": 8,  "bs": 8,  "a": ("#4", 5.0),  "e": ("#4", 5.0), "b": ("#4", 6.0),  "B_in": 29},
        20: {"ts": 8,  "t": 9,  "bs": 8,  "a": ("#4", 5.0),  "e": ("#4", 5.0), "b": ("#4", 5.0),  "B_in": 33},
    },
    (8.0, 7): {
        10: {"ts": 8,  "t": 8,  "bs": 8,  "a": ("#5", 6.0),  "e": ("#4", 5.0), "b": ("#4", 6.0),  "B_in": 36},
        20: {"ts": 9,  "t": 10, "bs": 8,  "a": ("#4", 5.0),  "e": ("#4", 5.0), "b": ("#4", 5.0),  "B_in": 33},
    },
    (9.0, 8): {
        10: {"ts": 9,  "t": 8,  "bs": 8,  "a": ("#5", 5.0),  "e": ("#4", 5.0), "b": ("#4", 5.0),  "B_in": 35},
        20: {"ts": 11, "t": 12, "bs": 12, "a": ("#5", 6.0),  "e": ("#4", 5.0), "b": ("#4", 6.0),  "B_in": 39},
    },
    (10.0, 9): {
        10: {"ts": 9,  "t": 9,  "bs": 10, "a": ("#5", 6.0),  "e": ("#4", 5.0), "b": ("#5", 5.0),  "B_in": 44},
        20: {"ts": 12, "t": 13, "bs": 13, "a": ("#5", 5.0),  "e": ("#4", 5.0), "b": ("#4", 5.0),  "B_in": 48},
    },
    (11.0, 10): {
        10: {"ts": 11, "t": 11, "bs": 11, "a": ("#6", 6.0),  "e": ("#5", 6.0), "b": ("#5", 6.0),  "B_in": 49},
        20: {"ts": 14, "t": 14, "bs": 14, "a": ("#5", 5.0),  "e": ("#4", 5.0), "b": ("#5", 6.0),  "B_in": 53},
    },
    (12.0, 12): {
        10: {"ts": 12, "t": 12, "bs": 13, "a": ("#6", 5.0),  "e": ("#5", 6.0), "b": ("#5", 6.0),  "B_in": 58},
        20: {"ts": 16, "t": 18, "bs": 17, "a": ("#7", 6.0),  "e": ("#6", 6.0), "b": ("#6", 6.0),  "B_in": 60},
    },
}


def _lookup_table_d91b(params_raw: dict) -> dict:
    Hb_ft   = float(params_raw.get("inside_depth_ft",  0) or 0)
    span_ft = float(params_raw.get("inside_width_ft",  0) or 0)
    cover   = float(params_raw.get("earth_cover_ft",  10) or 10)

    if Hb_ft <= 0 or span_ft <= 0:
        return {}

    # Find nearest (Hb, span) pair
    nearest_key = min(
        TABLE_D91B.keys(),
        key=lambda k: (abs(k[0] - Hb_ft) + abs(k[1] - span_ft)),
    )
    cover_key = 20 if cover > 10 else 10
    row = TABLE_D91B[nearest_key].get(cover_key, {})
    if not row:
        return {}

    return {
        "wall_thick_in":    row["t"],
        "floor_thick_in":   row["bs"],
        "wall_bar_size":    row["b"][0],
        "horiz_spacing_in": row["b"][1],
        "vert_spacing_in":  row["b"][1],
        "floor_bar_size":   row["a"][0],
        "floor_spacing_in": row["a"][1],
        "_source": f"D91B / Hb={nearest_key[0]}ft S={nearest_key[1]}ft cover≤{cover_key}ft",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Public dispatcher
# ─────────────────────────────────────────────────────────────────────────────

_DISPATCHERS: dict[str, callable] = {
    "G2 Inlet":           lambda p: _lookup_table_c("G2 Inlet", p),
    "G2 Expanded Inlet":  lambda p: _lookup_table_c("G2 Expanded Inlet", p),
    "Straight Headwall":  lambda p: _lookup_table_d89b(p),
    "Box Culvert":        lambda p: _lookup_table_d80(p),
    "Junction Structure": lambda p: _lookup_table_d91b(p),
}


def caltrans_lookup(template_name: str, params_raw: dict) -> dict:
    """
    Main entry point. Returns {field_name: value} of Caltrans-standard values
    for the given template and primary inputs.

    Returns empty dict if no lookup is available or inputs are out of range.
    The special key "_source" is included to identify which table was used —
    strip it before passing to the engine.
    """
    fn = _DISPATCHERS.get(template_name)
    if fn is None:
        return {}
    try:
        return fn(params_raw)
    except Exception:
        return {}


def caltrans_source_label(lookup_result: dict) -> str:
    """Returns a human-readable label for the source table, or ''."""
    return lookup_result.get("_source", "")


def strip_source(lookup_result: dict) -> dict:
    """Remove the _source key before passing values to the engine."""
    return {k: v for k, v in lookup_result.items() if k != "_source"}
