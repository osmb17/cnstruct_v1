"""
Rule functions for Box Culvert template (D80).

Caltrans D80 CIP single box culvert.
Bar sizes, spacings, and concrete thicknesses looked up from the D80 standard
plan table keyed by (span_ft, height_ft, max_earth_cover_ft).

Marks produced:
  A1  — transverse a-bars  (C/U-shape, wrapping inside of box)
  B1  — transverse b-bars  (outside straight U-shape)
  E1  — longitudinal e-bars (distribution bars along barrel)
  I1  — longitudinal i-bars (count from i-bar table or #4@12")
  HP1 — #4 hoops @ 12" max (per D82 miscellaneous details)

Reference: Caltrans Standard Plan D80 (bar and dimension tables) and
           D82 (miscellaneous details — hoop requirement).

Cover: 2" typical, 1" interior surfaces
       (D82 Note 9: "2" concrete cover are typical except as shown").
"""

from __future__ import annotations

import logging
import math

from vistadetail.engine.hooks import bend_reduce, hook_add
from vistadetail.engine.reasoning_logger import ReasoningLogger
from vistadetail.engine.schema import BarRow, Params, fmt_inches

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# D80 lookup table
#
# Key:    (span_ft, height_ft, max_cover_ft)
# Values: T1  = roof thickness (in)
#         T2  = wall thickness (in)
#         T3  = invert thickness (in)
#         a_s = a-bar size,  a_sp = a-bar spacing (in)
#         b_s = b-bar size,  b_sp = b-bar spacing (in)
#         e_s = e-bar size,  e_sp = e-bar spacing (in)
#         B   = B dimension (in) — nominal hook-engagement dimension
#         lblf = reinforcement lb per linear foot (for validation only)
# ---------------------------------------------------------------------------

_D80: dict[tuple[int, int, int], dict] = {

    # --- SPAN 4' ---
    (4, 2, 10): dict(T1=7.5, T2=6,   T3=7,   a_s="#5", a_sp=6,   b_s="#4", b_sp=5.5, e_s="#4", e_sp=13.5, B=28, lblf=79),
    (4, 2, 20): dict(T1=7,   T2=6,   T3=7,   a_s="#5", a_sp=5,   b_s="#5", b_sp=6,   e_s="#4", e_sp=13.5, B=24, lblf=84),
    (4, 3, 10): dict(T1=8,   T2=6,   T3=7,   a_s="#5", a_sp=6,   b_s="#4", b_sp=6,   e_s="#4", e_sp=13.5, B=28, lblf=84),
    (4, 3, 20): dict(T1=7,   T2=6,   T3=7.5, a_s="#5", a_sp=5,   b_s="#5", b_sp=6,   e_s="#4", e_sp=13.5, B=25, lblf=96),
    (4, 4, 10): dict(T1=8,   T2=7,   T3=7,   a_s="#4", a_sp=5,   b_s="#5", b_sp=6,   e_s="#4", e_sp=9,    B=28, lblf=104),
    (4, 4, 20): dict(T1=7,   T2=7,   T3=7.5, a_s="#5", a_sp=5,   b_s="#5", b_sp=4.5, e_s="#4", e_sp=7,    B=30, lblf=127),

    # --- SPAN 5' ---
    (5, 2, 10): dict(T1=8,   T2=6,   T3=7.5, a_s="#5", a_sp=5.5, b_s="#5", b_sp=5,   e_s="#4", e_sp=13.5, B=30, lblf=107),
    (5, 2, 20): dict(T1=8,   T2=6,   T3=8,   a_s="#5", a_sp=4.5, b_s="#5", b_sp=4.5, e_s="#4", e_sp=13.5, B=25, lblf=110),
    (5, 3, 10): dict(T1=8,   T2=6.5, T3=7.5, a_s="#5", a_sp=5,   b_s="#5", b_sp=6,   e_s="#4", e_sp=13.5, B=31, lblf=112),
    (5, 3, 20): dict(T1=8,   T2=6.5, T3=8,   a_s="#5", a_sp=4.5, b_s="#5", b_sp=5.5, e_s="#4", e_sp=13.5, B=28, lblf=114),
    (5, 4, 10): dict(T1=7.5, T2=7,   T3=7.5, a_s="#5", a_sp=5,   b_s="#5", b_sp=6,   e_s="#4", e_sp=12,   B=33, lblf=123),
    (5, 4, 20): dict(T1=8,   T2=7.5, T3=9,   a_s="#5", a_sp=4.5, b_s="#5", b_sp=5.5, e_s="#4", e_sp=11,   B=32, lblf=128),
    (5, 5, 10): dict(T1=8,   T2=7,   T3=7.5, a_s="#5", a_sp=5,   b_s="#5", b_sp=4.5, e_s="#4", e_sp=6.5,  B=33, lblf=154),
    (5, 5, 20): dict(T1=8,   T2=9,   T3=9.5, a_s="#5", a_sp=5,   b_s="#5", b_sp=5.5, e_s="#4", e_sp=7.5,  B=34, lblf=140),

    # --- SPAN 6' ---
    (6, 3, 10): dict(T1=7.5,  T2=6.5,  T3=8.5,  a_s="#5", a_sp=5.5, b_s="#5", b_sp=5.5, e_s="#4", e_sp=13.5, B=33, lblf=268),
    (6, 3, 20): dict(T1=12.0, T2=7.5,  T3=12.5, a_s="#4", a_sp=5.0, b_s="#4", b_sp=6.0, e_s="#4", e_sp=11.0, B=31, lblf=209),
    (6, 4, 10): dict(T1=7.5,  T2=7.0,  T3=8.5,  a_s="#5", a_sp=5.5, b_s="#4", b_sp=5.0, e_s="#4", e_sp=12.5, B=34, lblf=287),
    (6, 4, 20): dict(T1=11.5, T2=8.5,  T3=12.5, a_s="#4", a_sp=5.0, b_s="#4", b_sp=5.5, e_s="#4", e_sp=9.5,  B=32, lblf=232),
    (6, 5, 10): dict(T1=8.0,  T2=7.5,  T3=8.5,  a_s="#5", a_sp=5.0, b_s="#5", b_sp=5.0, e_s="#4", e_sp=9.0,  B=34, lblf=333),
    (6, 5, 20): dict(T1=11.5, T2=10.0, T3=13.0, a_s="#4", a_sp=5.0, b_s="#4", b_sp=5.0, e_s="#4", e_sp=7.5,  B=32, lblf=244),
    (6, 6, 10): dict(T1=8.0,  T2=8.5,  T3=8.5,  a_s="#5", a_sp=5.0, b_s="#5", b_sp=4.5, e_s="#4", e_sp=7.0,  B=35, lblf=362),
    (6, 6, 20): dict(T1=11.5, T2=11.0, T3=12.5, a_s="#4", a_sp=5.0, b_s="#5", b_sp=5.0, e_s="#4", e_sp=6.5,  B=34, lblf=297),

    # --- SPAN 7' ---
    (7, 3, 10): dict(T1=9.0,  T2=6.5,  T3=9.5,  a_s="#5", a_sp=5.5, b_s="#5", b_sp=5.0,  e_s="#4", e_sp=13.5, B=40, lblf=327),
    (7, 3, 20): dict(T1=13.5, T2=7.5,  T3=14.0, a_s="#4", a_sp=6.0, b_s="#4", b_sp=5.0,  e_s="#4", e_sp=11.0, B=41, lblf=264),
    (7, 4, 10): dict(T1=8.5,  T2=7.5,  T3=9.5,  a_s="#5", a_sp=5.0, b_s="#5", b_sp=6.0,  e_s="#4", e_sp=11.0, B=41, lblf=333),
    (7, 4, 20): dict(T1=13.5, T2=8.0,  T3=14.0, a_s="#4", a_sp=6.0, b_s="#4", b_sp=5.0,  e_s="#4", e_sp=10.0, B=41, lblf=276),
    (7, 5, 10): dict(T1=8.5,  T2=7.5,  T3=9.5,  a_s="#5", a_sp=5.0, b_s="#5", b_sp=5.0,  e_s="#4", e_sp=10.5, B=41, lblf=355),
    (7, 5, 20): dict(T1=13.0, T2=9.5,  T3=14.0, a_s="#5", a_sp=6.0, b_s="#5", b_sp=5.0,  e_s="#4", e_sp=8.0,  B=43, lblf=311),
    (7, 6, 10): dict(T1=8.5,  T2=8.5,  T3=9.5,  a_s="#5", a_sp=5.5, b_s="#5", b_sp=5.0,  e_s="#4", e_sp=8.0,  B=44, lblf=377),
    (7, 6, 20): dict(T1=13.0, T2=11.0, T3=14.0, a_s="#5", a_sp=6.0, b_s="#5", b_sp=5.0,  e_s="#4", e_sp=6.5,  B=44, lblf=338),
    (7, 7, 10): dict(T1=8.5,  T2=9.5,  T3=9.5,  a_s="#5", a_sp=5.5, b_s="#6", b_sp=5.5,  e_s="#4", e_sp=6.0,  B=46, lblf=406),
    (7, 7, 20): dict(T1=13.0, T2=13.0, T3=14.5, a_s="#5", a_sp=6.0, b_s="#5", b_sp=6.0,  e_s="#4", e_sp=5.5,  B=49, lblf=348),

    # --- SPAN 8' ---
    (8, 4, 10): dict(T1=10.0, T2=6.5,  T3=10.5, a_s="#5", a_sp=5.5, b_s="#5", b_sp=5.0,  e_s="#4", e_sp=13.0, B=44, lblf=373),
    (8, 4, 20): dict(T1=15.0, T2=8.0,  T3=15.5, a_s="#5", a_sp=5.5, b_s="#5", b_sp=7.0,  e_s="#4", e_sp=10.0, B=44, lblf=339),
    (8, 5, 10): dict(T1=9.5,  T2=7.5,  T3=10.5, a_s="#5", a_sp=5.5, b_s="#5", b_sp=5.0,  e_s="#4", e_sp=11.0, B=44, lblf=388),
    (8, 5, 20): dict(T1=15.0, T2=9.5,  T3=15.5, a_s="#5", a_sp=5.5, b_s="#5", b_sp=6.0,  e_s="#4", e_sp=8.0,  B=47, lblf=367),
    (8, 6, 10): dict(T1=9.5,  T2=8.5,  T3=10.5, a_s="#5", a_sp=5.5, b_s="#5", b_sp=5.5,  e_s="#4", e_sp=9.0,  B=45, lblf=399),
    (8, 6, 20): dict(T1=14.5, T2=11.5, T3=16.0, a_s="#5", a_sp=5.5, b_s="#5", b_sp=5.5,  e_s="#4", e_sp=6.0,  B=47, lblf=395),
    (8, 7, 10): dict(T1=9.5,  T2=9.5,  T3=10.5, a_s="#5", a_sp=5.5, b_s="#5", b_sp=5.0,  e_s="#4", e_sp=7.0,  B=48, lblf=429),
    (8, 7, 20): dict(T1=14.5, T2=13.0, T3=16.0, a_s="#5", a_sp=5.5, b_s="#5", b_sp=5.5,  e_s="#4", e_sp=5.5,  B=49, lblf=414),
    (8, 8, 10): dict(T1=9.5,  T2=11.0, T3=10.5, a_s="#5", a_sp=5.5, b_s="#6", b_sp=5.0,  e_s="#4", e_sp=5.5,  B=53, lblf=509),
    (8, 8, 20): dict(T1=14.5, T2=15.0, T3=16.0, a_s="#5", a_sp=6.5, b_s="#5", b_sp=5.5,  e_s="#5", e_sp=7.0,  B=53, lblf=441),

    # --- SPAN 10' ---
    (10, 5,  10): dict(T1=10,   T2=8.5,  T3=10,   a_s="#6", a_sp=4.5, b_s="#5", b_sp=4.5, e_s="#4", e_sp=9.5, B=46, lblf=251),
    (10, 5,  20): dict(T1=15,   T2=10,   T3=15,   a_s="#7", a_sp=5,   b_s="#5", b_sp=4.5, e_s="#4", e_sp=7.5, B=46, lblf=284),
    (10, 6,  10): dict(T1=9.5,  T2=8.5,  T3=10,   a_s="#6", a_sp=4.5, b_s="#6", b_sp=5,   e_s="#4", e_sp=8.5, B=45, lblf=285),
    (10, 6,  20): dict(T1=14,   T2=11.5, T3=15,   a_s="#7", a_sp=5,   b_s="#6", b_sp=5,   e_s="#4", e_sp=6,   B=39, lblf=318),
    (10, 7,  10): dict(T1=9.5,  T2=10,   T3=10,   a_s="#6", a_sp=5,   b_s="#6", b_sp=4.5, e_s="#4", e_sp=7.5, B=48, lblf=307),
    (10, 7,  20): dict(T1=13.5, T2=12.5, T3=15,   a_s="#7", a_sp=5,   b_s="#6", b_sp=5,   e_s="#4", e_sp=5.5, B=42, lblf=338),
    (10, 8,  10): dict(T1=9.5,  T2=11.5, T3=10,   a_s="#6", a_sp=5,   b_s="#7", b_sp=5,   e_s="#4", e_sp=6,   B=57, lblf=375),
    (10, 8,  20): dict(T1=14,   T2=14,   T3=15.5, a_s="#6", a_sp=4.5, b_s="#5", b_sp=4.5, e_s="#4", e_sp=5,   B=53, lblf=313),
    (10, 9,  10): dict(T1=10,   T2=12,   T3=10,   a_s="#6", a_sp=5,   b_s="#7", b_sp=4.5, e_s="#4", e_sp=5,   B=57, lblf=418),
    (10, 9,  20): dict(T1=15,   T2=15.5, T3=16,   a_s="#6", a_sp=4.5, b_s="#6", b_sp=5,   e_s="#5", e_sp=6.5, B=59, lblf=375),
    (10, 10, 10): dict(T1=10,   T2=13.5, T3=10.5, a_s="#5", a_sp=4.5, b_s="#7", b_sp=4.5, e_s="#5", e_sp=6,   B=58, lblf=425),
    (10, 10, 20): dict(T1=15,   T2=16.5, T3=15,   a_s="#6", a_sp=5,   b_s="#6", b_sp=4.5, e_s="#5", e_sp=5,   B=55, lblf=404),

    # --- SPAN 12' ---
    (12, 6,  10): dict(T1=11.5, T2=9,    T3=11,   a_s="#7", a_sp=4.5, b_s="#6", b_sp=4.5, e_s="#4", e_sp=8.5, B=51, lblf=381),
    (12, 6,  20): dict(T1=17,   T2=12,   T3=17.5, a_s="#7", a_sp=4.5, b_s="#6", b_sp=4.5, e_s="#4", e_sp=6,   B=49, lblf=381),
    (12, 7,  10): dict(T1=11.5, T2=10.5, T3=11,   a_s="#7", a_sp=5,   b_s="#6", b_sp=4.5, e_s="#4", e_sp=7,   B=51, lblf=382),
    (12, 7,  20): dict(T1=16.5, T2=13,   T3=17.5, a_s="#7", a_sp=4.5, b_s="#6", b_sp=5,   e_s="#4", e_sp=5.5, B=49, lblf=397),
    (12, 8,  10): dict(T1=11.5, T2=11.5, T3=11,   a_s="#7", a_sp=5,   b_s="#7", b_sp=4.5, e_s="#4", e_sp=6,   B=60, lblf=469),
    (12, 8,  20): dict(T1=16,   T2=14.5, T3=17,   a_s="#7", a_sp=4.5, b_s="#6", b_sp=5,   e_s="#5", e_sp=7.5, B=51, lblf=418),
    (12, 9,  10): dict(T1=11,   T2=12.5, T3=11,   a_s="#7", a_sp=5,   b_s="#7", b_sp=4.5, e_s="#4", e_sp=5.5, B=63, lblf=497),
    (12, 9,  20): dict(T1=16,   T2=16,   T3=17,   a_s="#7", a_sp=4.5, b_s="#6", b_sp=5,   e_s="#5", e_sp=6.5, B=61, lblf=455),
    (12, 10, 10): dict(T1=11.5, T2=14,   T3=11,   a_s="#6", a_sp=4.5, b_s="#7", b_sp=4.5, e_s="#5", e_sp=5,   B=63, lblf=488),
    (12, 10, 20): dict(T1=17,   T2=16.5, T3=16,   a_s="#7", a_sp=5,   b_s="#7", b_sp=4.5, e_s="#5", e_sp=6.5, B=74, lblf=534),
    (12, 11, 10): dict(T1=11.5, T2=15,   T3=12,   a_s="#6", a_sp=4.5, b_s="#7", b_sp=4.5, e_s="#5", e_sp=5.5, B=64, lblf=526),
    (12, 11, 20): dict(T1=17.5, T2=18,   T3=19,   a_s="#6", a_sp=4.5, b_s="#6", b_sp=4.5, e_s="#5", e_sp=5,   B=66, lblf=479),
    (12, 12, 10): dict(T1=12,   T2=16.5, T3=12.5, a_s="#6", a_sp=4.5, b_s="#7", b_sp=4.5, e_s="#5", e_sp=4.5, B=64, lblf=548),
    (12, 12, 20): dict(T1=18,   T2=20,   T3=20,   a_s="#6", a_sp=4.5, b_s="#6", b_sp=4.5, e_s="#6", e_sp=6,   B=67, lblf=515),

    # --- SPAN 14' ---
    (14, 7,  10): dict(T1=13,   T2=9.5,  T3=12.5, a_s="#8", a_sp=5,   b_s="#7", b_sp=4.5, e_s="#4", e_sp=7.5, B=56, lblf=526),
    (14, 7,  20): dict(T1=19.5, T2=13.5, T3=19.5, a_s="#8", a_sp=5,   b_s="#7", b_sp=4.5, e_s="#4", e_sp=5,   B=54, lblf=492),
    (14, 8,  10): dict(T1=13,   T2=11.5, T3=12.5, a_s="#7", a_sp=4.5, b_s="#7", b_sp=5,   e_s="#4", e_sp=6,   B=60, lblf=498),
    (14, 8,  20): dict(T1=19,   T2=15,   T3=19.5, a_s="#8", a_sp=5,   b_s="#6", b_sp=4.5, e_s="#4", e_sp=5,   B=53, lblf=512),
    (14, 9,  10): dict(T1=13,   T2=12.5, T3=12.5, a_s="#7", a_sp=4.5, b_s="#7", b_sp=4.5, e_s="#4", e_sp=5.5, B=64, lblf=550),
    (14, 9,  20): dict(T1=17.5, T2=16.5, T3=19,   a_s="#8", a_sp=5,   b_s="#6", b_sp=4.5, e_s="#4", e_sp=6.5, B=60, lblf=540),
    (14, 10, 10): dict(T1=13,   T2=14,   T3=12.5, a_s="#7", a_sp=5,   b_s="#7", b_sp=4.5, e_s="#4", e_sp=5,   B=68, lblf=560),
    (14, 10, 20): dict(T1=18,   T2=16.5, T3=19,   a_s="#8", a_sp=5,   b_s="#6", b_sp=4.5, e_s="#4", e_sp=6.5, B=64, lblf=563),
    (14, 11, 10): dict(T1=13,   T2=15.5, T3=12.5, a_s="#7", a_sp=5,   b_s="#8", b_sp=4.5, e_s="#5", e_sp=7,   B=77, lblf=652),
    (14, 11, 20): dict(T1=18,   T2=16.5, T3=20,   a_s="#7", a_sp=4.5, b_s="#6", b_sp=4.5, e_s="#5", e_sp=5,   B=69, lblf=562),
    (14, 12, 10): dict(T1=13.5, T2=16.5, T3=13,   a_s="#6", a_sp=4.5, b_s="#8", b_sp=5,   e_s="#5", e_sp=5.5, B=77, lblf=651),
    (14, 12, 20): dict(T1=20,   T2=19.5, T3=22,   a_s="#7", a_sp=4.5, b_s="#6", b_sp=4.5, e_s="#5", e_sp=4.5, B=71, lblf=596),
    (14, 13, 10): dict(T1=13.5, T2=18,   T3=13,   a_s="#6", a_sp=4.5, b_s="#8", b_sp=5,   e_s="#5", e_sp=5,   B=78, lblf=691),
    (14, 13, 20): dict(T1=19.5, T2=22,   T3=22,   a_s="#7", a_sp=5,   b_s="#7", b_sp=5,   e_s="#6", e_sp=6,   B=82, lblf=674),
    (14, 14, 10): dict(T1=13.5, T2=19.5, T3=14,   a_s="#6", a_sp=4.5, b_s="#8", b_sp=4.5, e_s="#5", e_sp=5,   B=78, lblf=730),
    (14, 14, 20): dict(T1=20.5, T2=24.5, T3=21.5, a_s="#7", a_sp=5,   b_s="#7", b_sp=4.5, e_s="#6", e_sp=5,   B=83, lblf=753),
}

# ---------------------------------------------------------------------------
# "i" bar count table (earth cover <= 10')
# Key: span_ft -> count of i-bars
# For cover > 10': use #4 @ 12" max instead (computed from span)
# ---------------------------------------------------------------------------

_I_BAR_COUNT: dict[int, int] = {
    4: 5, 5: 6, 6: 8, 7: 10, 8: 13, 10: 14, 12: 16, 14: 19,
}

# Known spans present in the D80 table
_KNOWN_SPANS = sorted({k[0] for k in _D80})


# ---------------------------------------------------------------------------
# Helper: D80 lookup (with nearest-span interpolation for missing spans 6/7/8)
# ---------------------------------------------------------------------------

def _bc_lookup(span_ft: int, height_ft: int, cover_ft: int,
               logger: ReasoningLogger) -> dict:
    """
    Return the D80 row for (span_ft, height_ft, cover_ft).

    For spans 6, 7, and 8 (data pending), the row is linearly interpolated
    between the nearest bracketing spans.  A warning is logged in all
    interpolated cases.

    For exact keys not in the table (height outside the populated range for a
    given span), the nearest available height for that span/cover is used and
    a warning is logged.
    """
    cover_key = 20 if cover_ft > 10 else 10

    # --- exact span is in the table ---
    if span_ft in _KNOWN_SPANS:
        key = (span_ft, height_ft, cover_key)
        if key in _D80:
            return _D80[key]

        # Height not listed for this span — find nearest height
        available = sorted(
            {k[1] for k in _D80 if k[0] == span_ft and k[2] == cover_key}
        )
        if not available:
            raise ValueError(
                f"D80 table has no entries for span={span_ft}' cover={cover_key}'"
            )
        nearest_h = min(available, key=lambda h: abs(h - height_ft))
        logger.warn(
            f"D80: no exact row for span={span_ft}' height={height_ft}' "
            f"cover={cover_key}' — using nearest height={nearest_h}'",
            source="BoxCulvertRules",
        )
        return _D80[(span_ft, nearest_h, cover_key)]

    # --- span not in the table (6, 7, or 8) — interpolate between neighbours ---
    lower_spans = [s for s in _KNOWN_SPANS if s < span_ft]
    upper_spans = [s for s in _KNOWN_SPANS if s > span_ft]

    if not lower_spans or not upper_spans:
        # Off the edge of the table — clamp to nearest span
        clamp = _KNOWN_SPANS[0] if not lower_spans else _KNOWN_SPANS[-1]
        logger.warn(
            f"D80: span={span_ft}' outside table range — clamping to span={clamp}'",
            source="BoxCulvertRules",
        )
        return _bc_lookup(clamp, height_ft, cover_ft, logger)

    s_lo = lower_spans[-1]
    s_hi = upper_spans[0]
    t = (span_ft - s_lo) / (s_hi - s_lo)   # interpolation factor [0, 1]

    row_lo = _bc_lookup(s_lo, height_ft, cover_ft, logger)
    row_hi = _bc_lookup(s_hi, height_ft, cover_ft, logger)

    # Interpolate numeric fields; use lower span for bar size strings
    interp: dict = {}
    for field_name in ("T1", "T2", "T3", "a_sp", "b_sp", "e_sp", "B", "lblf"):
        interp[field_name] = row_lo[field_name] + t * (row_hi[field_name] - row_lo[field_name])
    for field_name in ("a_s", "b_s", "e_s"):
        interp[field_name] = row_lo[field_name]   # conservative: use lower span bar size

    logger.warn(
        f"D80: span={span_ft}' has no table entry. "
        f"Values interpolated between span={s_lo}' and span={s_hi}' "
        f"(t={t:.2f}). Verify with D80 standard plan.",
        source="BoxCulvertRules",
    )
    log.warning(
        "D80 interpolation used for span=%d' — replace with actual table data.",
        span_ft,
    )
    return interp


# ---------------------------------------------------------------------------
# Rule functions
# ---------------------------------------------------------------------------

def rule_bc_a_bars(p: Params, logger: ReasoningLogger) -> list[BarRow]:
    """
    A1 — Main transverse a-bars (C/U-shape wrapping inside of box).

    These are the primary flexural bars on the inside face.  The bar wraps
    around the inside perimeter: span + 2 rises + two 90-deg hooks.

    Cover: 1" interior (per D82 Note 9).

    qty = floor((barrel_length_in - 2) / a_sp) + 1   [1" end cover each end]
    bar_length = S_in + 2*H_in + 2*hook_add("std_90", a_size)
    """
    S_in   = int(p.span_ft) * 12
    H_in   = p.height_ft * 12
    L_in   = p.barrel_length_ft * 12

    row    = _bc_lookup(int(p.span_ft), int(p.height_ft), int(p.max_earth_cover_ft), logger)
    a_size = row["a_s"]
    a_sp   = row["a_sp"]

    ha      = hook_add("std_90", a_size)
    bar_len = S_in + 2 * H_in + 2 * ha
    qty     = math.floor((L_in - 2) / a_sp) + 1

    logger.step(
        f"A1 ({a_size}@{a_sp}\"): S={S_in}\" + 2×H={2*H_in}\" + 2×hook({ha}\") = {bar_len:.1f}\"  "
        f"qty=⌊({L_in}-2)/{a_sp}⌋+1={qty}",
        source="BoxCulvertRules",
    )
    logger.result("A1", f"{a_size} × {qty} @ {fmt_inches(bar_len)}", source="BoxCulvertRules")

    return [BarRow(
        mark="A1", size=a_size, qty=qty, length_in=bar_len,
        shape="C",
        leg_a_in=ha, leg_b_in=H_in, leg_c_in=S_in, leg_d_in=H_in,
        notes=f"A-bars @{a_sp}\" oc  S+2H+2hooks",
        source_rule="rule_bc_a_bars",
    )]


def rule_bc_b_bars(p: Params, logger: ReasoningLogger) -> list[BarRow]:
    """
    B1 — Secondary transverse b-bars (outside face, U-shape).

    These bars span the outside of the box: span + 2 wall thicknesses + hooks.

    qty = floor((barrel_length_in - 2) / b_sp) + 1   [1" end cover each end]
    bar_length = S_in + 2*T2 + 2*hook_add("std_90", b_size)
    """
    S_in = int(p.span_ft) * 12
    L_in = p.barrel_length_ft * 12

    row    = _bc_lookup(int(p.span_ft), int(p.height_ft), int(p.max_earth_cover_ft), logger)
    b_size = row["b_s"]
    b_sp   = row["b_sp"]
    T2     = row["T2"]

    hb      = hook_add("std_90", b_size)
    bar_len = S_in + 2 * T2 + 2 * hb
    qty     = math.floor((L_in - 2) / b_sp) + 1

    logger.step(
        f"B1 ({b_size}@{b_sp}\"): S={S_in}\" + 2×T2={2*T2}\" + 2×hook({hb}\") = {bar_len:.1f}\"  "
        f"qty=⌊({L_in}-2)/{b_sp}⌋+1={qty}",
        source="BoxCulvertRules",
    )
    logger.result("B1", f"{b_size} × {qty} @ {fmt_inches(bar_len)}", source="BoxCulvertRules")

    return [BarRow(
        mark="B1", size=b_size, qty=qty, length_in=bar_len,
        shape="U",
        leg_a_in=hb, leg_b_in=S_in + 2 * T2, leg_c_in=hb,
        notes=f"B-bars @{b_sp}\" oc  S+2×T2+2hooks",
        source_rule="rule_bc_b_bars",
    )]


def rule_bc_e_bars(p: Params, logger: ReasoningLogger) -> list[BarRow]:
    """
    E1 — Longitudinal distribution e-bars (both faces, along barrel length).

    These bars run the full barrel length and are distributed around the
    cross-section perimeter (both faces of all four walls/slabs).

    qty_per_row = floor(2*(S_in + H_in) / e_sp) + 1
    bar_length  = barrel_length_in - 4   [2" cover each end]
    """
    S_in = int(p.span_ft) * 12
    H_in = p.height_ft * 12
    L_in = p.barrel_length_ft * 12

    row    = _bc_lookup(int(p.span_ft), int(p.height_ft), int(p.max_earth_cover_ft), logger)
    e_size = row["e_s"]
    e_sp   = row["e_sp"]

    bar_len = L_in - 4
    qty     = math.floor(2 * (S_in + H_in) / e_sp) + 1

    logger.step(
        f"E1 ({e_size}@{e_sp}\"): length={L_in}-4={bar_len}\"  "
        f"qty=⌊2×({S_in}+{H_in})/{e_sp}⌋+1={qty}",
        source="BoxCulvertRules",
    )
    logger.result("E1", f"{e_size} × {qty} @ {fmt_inches(bar_len)}", source="BoxCulvertRules")

    return [BarRow(
        mark="E1", size=e_size, qty=qty, length_in=bar_len,
        shape="Str",
        notes=f"E-bars @{e_sp}\" oc  perimeter distribution",
        source_rule="rule_bc_e_bars",
    )]


def rule_bc_i_bars(p: Params, logger: ReasoningLogger) -> list[BarRow]:
    """
    I1 — Longitudinal i-bars along the barrel (from D80 i-bar count table).

    For earth cover <= 10': count from {4:5, 5:6, 6:8, 7:10, 8:13, 10:14, 12:16, 14:19}.
    For earth cover >  10': qty = floor((S_in - 4) / 12) + 1  (#4 @ 12" max).

    Size is always #4.
    bar_length = barrel_length_in - 4   [2" cover each end]
    """
    S_in   = int(p.span_ft) * 12
    L_in   = p.barrel_length_ft * 12
    cover  = int(p.max_earth_cover_ft)
    span   = int(p.span_ft)

    bar_len = L_in - 4

    if cover <= 10:
        qty = _I_BAR_COUNT.get(span)
        if qty is None:
            # Interpolate for spans not in the i-bar count table (6, 7, 8)
            lo_spans = [s for s in sorted(_I_BAR_COUNT) if s <= span]
            hi_spans = [s for s in sorted(_I_BAR_COUNT) if s >= span]
            if lo_spans and hi_spans:
                s_lo, s_hi = lo_spans[-1], hi_spans[0]
                if s_lo == s_hi:
                    qty = _I_BAR_COUNT[s_lo]
                else:
                    t = (span - s_lo) / (s_hi - s_lo)
                    qty = round(_I_BAR_COUNT[s_lo] + t * (_I_BAR_COUNT[s_hi] - _I_BAR_COUNT[s_lo]))
            else:
                qty = math.floor((S_in - 4) / 12) + 1
            logger.warn(
                f"I-bar count for span={span}' not in table — interpolated qty={qty}. "
                "Verify when D80 span data is obtained.",
                source="BoxCulvertRules",
            )
        logger.step(
            f"I1 (cover={cover}'<=10'): table count={qty} bars  length={fmt_inches(bar_len)}",
            source="BoxCulvertRules",
        )
    else:
        qty = math.floor((S_in - 4) / 12) + 1
        logger.step(
            f"I1 (cover={cover}'>10'): #4@12\" max  qty=⌊({S_in}-4)/12⌋+1={qty}  "
            f"length={fmt_inches(bar_len)}",
            source="BoxCulvertRules",
        )

    logger.result("I1", f"#4 × {qty} @ {fmt_inches(bar_len)}", source="BoxCulvertRules")

    return [BarRow(
        mark="I1", size="#4", qty=qty, length_in=bar_len,
        shape="Str",
        notes="I-bars  cover={}'  {}".format(cover, "table" if cover <= 10 else "#4@12\" max"),
        source_rule="rule_bc_i_bars",
    )]


def rule_bc_hoops(p: Params, logger: ReasoningLogger) -> list[BarRow]:
    """
    HP1 — #4 closed rectangular hoops @ 12" max (per D82 miscellaneous details).

    Hoops encircle the full box cross-section perimeter.

    qty        = floor((barrel_length_in - 2) / 12) + 1   [1" end cover]
    hoop_perimeter = 2*(S_in + 2*T2 + H_in + T1 + T3)
    hoop_length = hoop_perimeter - bend_reduce("shape_4", "#4")
    """
    S_in = int(p.span_ft) * 12
    H_in = p.height_ft * 12
    L_in = p.barrel_length_ft * 12

    row = _bc_lookup(int(p.span_ft), int(p.height_ft), int(p.max_earth_cover_ft), logger)
    T1  = row["T1"]
    T2  = row["T2"]
    T3  = row["T3"]

    perimeter  = 2 * (S_in + 2 * T2 + H_in + T1 + T3)
    deduct     = bend_reduce("shape_4", "#4")
    hoop_len   = perimeter - deduct
    qty        = math.floor((L_in - 2) / 12) + 1

    logger.step(
        f"HP1 (#4@12\"): perimeter=2×(S+2T2+H+T1+T3)=2×({S_in}+{2*T2}+{H_in}+{T1}+{T3})={perimeter}\"  "
        f"deduct={deduct}\"  hoop_len={hoop_len:.1f}\"  "
        f"qty=⌊({L_in}-2)/12⌋+1={qty}",
        source="BoxCulvertRules",
    )
    logger.result("HP1", f"#4 × {qty} @ {fmt_inches(hoop_len)}", source="BoxCulvertRules")

    return [BarRow(
        mark="HP1", size="#4", qty=qty, length_in=hoop_len,
        shape="Rect",
        leg_a_in=S_in + 2 * T2,
        leg_b_in=H_in + T1 + T3,
        notes=f"Hoops @12\" oc  perimeter={fmt_inches(perimeter)}-{deduct}\" deduct",
        source_rule="rule_bc_hoops",
    )]


def rule_bc_validate(p: Params, logger: ReasoningLogger) -> list[BarRow]:
    """
    Validate span/height combo exists (or can be interpolated) in the D80 table,
    and log lb/lf estimate against the D80 published value for sanity checking.
    """
    span   = int(p.span_ft)
    height = int(p.height_ft)
    cover  = int(p.max_earth_cover_ft)

    cover_key = 20 if cover > 10 else 10
    exact_key = (span, height, cover_key)

    if exact_key in _D80:
        logger.ok(
            f"D80 exact row found: span={span}' height={height}' cover={cover_key}'",
            source="BoxCulvertRules",
        )
        published_lblf = _D80[exact_key]["lblf"]
        logger.step(
            f"D80 published lb/lf = {published_lblf} (reference only — "
            "actual weight depends on barrel length and bar cut lengths)",
            source="BoxCulvertRules",
        )
    else:
        if span not in _KNOWN_SPANS:
            logger.warn(
                f"span={span}' is not a standard D80 span — interpolated values used. "
                "Verify with D80 standard plan.",
                source="BoxCulvertRules",
            )
        else:
            available_heights = sorted(
                {k[1] for k in _D80 if k[0] == span and k[2] == cover_key}
            )
            logger.warn(
                f"D80: no row for span={span}' height={height}' cover={cover_key}'. "
                f"Available heights for this span/cover: {available_heights}.",
                source="BoxCulvertRules",
            )

    if height < 2:
        logger.warn("Height < 2' — below D80 table minimum.", source="BoxCulvertRules")
    if height > 14:
        logger.warn(
            f"Height={height}' exceeds D80 table maximum of 14' — "
            "structural analysis required.",
            source="BoxCulvertRules",
        )
    if span > 14:
        logger.warn(
            f"Span={span}' exceeds D80 table maximum of 14' — "
            "structural analysis required.",
            source="BoxCulvertRules",
        )

    return []
