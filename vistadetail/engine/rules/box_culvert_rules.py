"""
Rule functions for Box Culvert template (D80).

Caltrans D80 CIP single box culvert.
Bar sizes, spacings, and concrete thicknesses looked up from the D80 standard
plan table keyed by (span_ft, height_ft, max_earth_cover_ft).

Marks produced:
  A1  — transverse a-bars, invert  (C-bar, inside face, 3\" cover)
  A2  — transverse a-bars, roof    (C-bar, inside face, 3\" cover)
  B1  — transverse b-bars          (L-bar, both side walls)
  E1  — vertical e-bars            (straight, both side walls)
  H1  — horizontal h-bars          (straight, all 4 faces, longitudinal)
  F1  — roof transverse f-bars     (straight, #4 @ 12\" max)
  I1  — longitudinal i-bars        (straight, invert, from D80 count table)
  G1  — barrel-end notch bars      (#4 U-bar, roof+invert per notched end, per D82)

Bar geometry based on Caltrans Standard Plan D80 (bar descriptions and
typical section).  Quantities verified against user barlist for
(H=6, S=8, L=20, cover=10).

Reference: Caltrans Standard Plan D80.
"""

from __future__ import annotations

import logging
import math

from vistadetail.engine.hooks import bend_reduce
from vistadetail.engine.reasoning_logger import ReasoningLogger
from vistadetail.engine.schema import BarRow, Params, fmt_inches

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# D80 lookup table
#
# Key:    (span_ft, height_ft, max_cover_ft)
# Values: T1   = roof thickness (in)
#         T2   = wall thickness (in)
#         T3   = invert thickness (in)
#         a_s  = a-bar size,  a_sp = a-bar spacing (in)
#         b_s  = b-bar size,  b_sp = b-bar spacing (in)
#         e_s  = e-bar size,  e_sp = e-bar spacing (in)
#         B    = b-bar short leg dimension (in) — direct from D80 table
#         lblf = reinforcement lb per linear foot (reference/validation only)
#
# Spans 4, 5: confirmed correct from D80 screenshots.
# Spans 6, 7: carried from prior entry — verify against D80 screenshots.
# Span  8:    corrected from clean D80 screenshots.
# Spans 10, 12, 14: unvalidated — update when screenshots are available.
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

    # --- SPAN 6' (verify against D80 screenshots) ---
    (6, 3, 10): dict(T1=7.5,  T2=6.5,  T3=8.5,  a_s="#5", a_sp=5.5, b_s="#5", b_sp=5.5, e_s="#4", e_sp=13.5, B=33, lblf=268),
    (6, 3, 20): dict(T1=12.0, T2=7.5,  T3=12.5, a_s="#4", a_sp=5.0, b_s="#4", b_sp=6.0, e_s="#4", e_sp=11.0, B=31, lblf=209),
    (6, 4, 10): dict(T1=7.5,  T2=7.0,  T3=8.5,  a_s="#5", a_sp=5.5, b_s="#4", b_sp=5.0, e_s="#4", e_sp=12.5, B=34, lblf=287),
    (6, 4, 20): dict(T1=11.5, T2=8.5,  T3=12.5, a_s="#4", a_sp=5.0, b_s="#4", b_sp=5.5, e_s="#4", e_sp=9.5,  B=32, lblf=232),
    (6, 5, 10): dict(T1=8.0,  T2=7.5,  T3=8.5,  a_s="#5", a_sp=5.0, b_s="#5", b_sp=5.0, e_s="#4", e_sp=9.0,  B=34, lblf=333),
    (6, 5, 20): dict(T1=11.5, T2=10.0, T3=13.0, a_s="#4", a_sp=5.0, b_s="#4", b_sp=5.0, e_s="#4", e_sp=7.5,  B=32, lblf=244),
    (6, 6, 10): dict(T1=8.0,  T2=8.5,  T3=8.5,  a_s="#5", a_sp=5.0, b_s="#5", b_sp=4.5, e_s="#4", e_sp=7.0,  B=35, lblf=362),
    (6, 6, 20): dict(T1=11.5, T2=11.0, T3=12.5, a_s="#4", a_sp=5.0, b_s="#5", b_sp=5.0, e_s="#4", e_sp=6.5,  B=34, lblf=297),

    # --- SPAN 7' (verify against D80 screenshots) ---
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

    # --- SPAN 8' (corrected from clean D80 screenshots) ---
    (8, 4, 10): dict(T1=9.5,  T2=6.5,  T3=8.5,  a_s="#6", a_sp=5.0, b_s="#5", b_sp=4.5, e_s="#4", e_sp=11.0, B=37, lblf=193),
    (8, 4, 20): dict(T1=12.5, T2=8.0,  T3=13.0, a_s="#6", a_sp=4.5, b_s="#5", b_sp=4.5, e_s="#4", e_sp=10.0, B=33, lblf=197),
    (8, 5, 10): dict(T1=9.5,  T2=7.0,  T3=8.5,  a_s="#6", a_sp=5.0, b_s="#6", b_sp=5.0, e_s="#4", e_sp=9.0,  B=40, lblf=229),
    (8, 5, 20): dict(T1=11.5, T2=9.5,  T3=13.0, a_s="#6", a_sp=4.5, b_s="#5", b_sp=4.5, e_s="#4", e_sp=8.0,  B=32, lblf=210),
    (8, 6, 10): dict(T1=9.5,  T2=8.5,  T3=8.5,  a_s="#6", a_sp=5.0, b_s="#6", b_sp=4.5, e_s="#4", e_sp=7.5,  B=43, lblf=262),
    (8, 6, 20): dict(T1=11.5, T2=11.0, T3=12.0, a_s="#6", a_sp=4.5, b_s="#5", b_sp=4.5, e_s="#4", e_sp=6.5,  B=39, lblf=234),
    (8, 7, 10): dict(T1=9.0,  T2=10.0, T3=8.5,  a_s="#5", a_sp=4.5, b_s="#9", b_sp=4.5, e_s="#4", e_sp=7.0,  B=68, lblf=491),
    (8, 7, 20): dict(T1=11.5, T2=12.0, T3=13.0, a_s="#6", a_sp=5.0, b_s="#5", b_sp=4.5, e_s="#4", e_sp=6.0,  B=42, lblf=242),
    (8, 8, 10): dict(T1=9.0,  T2=11.0, T3=8.5,  a_s="#5", a_sp=4.5, b_s="#9", b_sp=4.5, e_s="#4", e_sp=5.0,  B=69, lblf=527),
    (8, 8, 20): dict(T1=11.5, T2=13.5, T3=12.0, a_s="#6", a_sp=5.0, b_s="#6", b_sp=4.5, e_s="#5", e_sp=7.0,  B=46, lblf=309),

    # --- SPAN 10' (confirmed from D80 screenshots — all values correct) ---
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

    # --- SPAN 12' (corrected from D80 screenshots) ---
    (12, 6,  10): dict(T1=11.5, T2=9,    T3=11,   a_s="#7", a_sp=4.5, b_s="#6", b_sp=4.5, e_s="#4", e_sp=8.5, B=51, lblf=381),
    (12, 6,  20): dict(T1=17,   T2=12,   T3=17.5, a_s="#7", a_sp=4.5, b_s="#6", b_sp=5.0, e_s="#4", e_sp=6,   B=49, lblf=381),
    (12, 7,  10): dict(T1=11.5, T2=10.5, T3=11,   a_s="#7", a_sp=5,   b_s="#6", b_sp=4.5, e_s="#4", e_sp=7,   B=51, lblf=382),
    (12, 7,  20): dict(T1=16.5, T2=13,   T3=17.5, a_s="#7", a_sp=4.5, b_s="#6", b_sp=5,   e_s="#4", e_sp=5.5, B=49, lblf=397),
    (12, 8,  10): dict(T1=11.5, T2=11.5, T3=11,   a_s="#7", a_sp=5,   b_s="#7", b_sp=4.5, e_s="#4", e_sp=6,   B=60, lblf=469),
    (12, 8,  20): dict(T1=16,   T2=14.5, T3=17,   a_s="#7", a_sp=4.5, b_s="#6", b_sp=5,   e_s="#5", e_sp=7.5, B=51, lblf=418),
    (12, 9,  10): dict(T1=11,   T2=12.5, T3=11,   a_s="#7", a_sp=5,   b_s="#7", b_sp=4.5, e_s="#4", e_sp=5.5, B=63, lblf=497),
    (12, 9,  20): dict(T1=16,   T2=16,   T3=17,   a_s="#7", a_sp=4.5, b_s="#6", b_sp=5,   e_s="#5", e_sp=6.5, B=61, lblf=455),
    (12, 10, 10): dict(T1=11.5, T2=14,   T3=11.5, a_s="#6", a_sp=4.5, b_s="#7", b_sp=4.5, e_s="#4", e_sp=5,   B=63, lblf=488),
    (12, 10, 20): dict(T1=17,   T2=16.5, T3=16,   a_s="#7", a_sp=5,   b_s="#7", b_sp=5.0, e_s="#5", e_sp=6.5, B=74, lblf=534),
    (12, 11, 10): dict(T1=11.5, T2=15,   T3=12,   a_s="#6", a_sp=4.5, b_s="#7", b_sp=4.5, e_s="#5", e_sp=5.5, B=64, lblf=526),
    (12, 11, 20): dict(T1=17.5, T2=18,   T3=19,   a_s="#6", a_sp=4.5, b_s="#6", b_sp=4.5, e_s="#5", e_sp=5,   B=66, lblf=479),
    (12, 12, 10): dict(T1=12,   T2=16.5, T3=12.5, a_s="#6", a_sp=4.5, b_s="#7", b_sp=4.5, e_s="#5", e_sp=4.5, B=64, lblf=548),
    (12, 12, 20): dict(T1=18,   T2=20,   T3=20,   a_s="#6", a_sp=4.5, b_s="#6", b_sp=4.5, e_s="#6", e_sp=6,   B=67, lblf=515),

    # --- SPAN 14' (corrected from D80 screenshots) ---
    (14, 7,  10): dict(T1=13,   T2=9.5,  T3=12.5, a_s="#8", a_sp=5,   b_s="#7", b_sp=4.5, e_s="#4", e_sp=7.5, B=56, lblf=526),
    (14, 7,  20): dict(T1=19.5, T2=13.5, T3=19.5, a_s="#8", a_sp=5,   b_s="#6", b_sp=4.5, e_s="#4", e_sp=5,   B=54, lblf=492),
    (14, 8,  10): dict(T1=13,   T2=11.5, T3=12.5, a_s="#7", a_sp=4.5, b_s="#7", b_sp=5,   e_s="#4", e_sp=6,   B=60, lblf=498),
    (14, 8,  20): dict(T1=19,   T2=15,   T3=19.5, a_s="#8", a_sp=5,   b_s="#6", b_sp=4.5, e_s="#5", e_sp=7,   B=53, lblf=512),
    (14, 9,  10): dict(T1=13,   T2=12.5, T3=12.5, a_s="#7", a_sp=4.5, b_s="#7", b_sp=4.5, e_s="#4", e_sp=5.5, B=64, lblf=550),
    (14, 9,  20): dict(T1=17.5, T2=16.5, T3=19,   a_s="#8", a_sp=5,   b_s="#6", b_sp=4.5, e_s="#5", e_sp=6.5, B=60, lblf=540),
    (14, 10, 10): dict(T1=13,   T2=14,   T3=12.5, a_s="#7", a_sp=5,   b_s="#7", b_sp=4.5, e_s="#4", e_sp=5,   B=68, lblf=560),
    (14, 10, 20): dict(T1=18,   T2=16.5, T3=19,   a_s="#8", a_sp=5,   b_s="#6", b_sp=4.5, e_s="#5", e_sp=6.5, B=64, lblf=563),
    (14, 11, 10): dict(T1=13,   T2=15.5, T3=13,   a_s="#7", a_sp=5,   b_s="#8", b_sp=5,   e_s="#5", e_sp=7,   B=77, lblf=652),
    (14, 11, 20): dict(T1=19,   T2=16.5, T3=21,   a_s="#7", a_sp=4.5, b_s="#6", b_sp=4.5, e_s="#5", e_sp=5,   B=69, lblf=562),
    (14, 12, 10): dict(T1=13.5, T2=16.5, T3=13,   a_s="#6", a_sp=4.5, b_s="#8", b_sp=5,   e_s="#5", e_sp=5.5, B=77, lblf=651),
    (14, 12, 20): dict(T1=20,   T2=19.5, T3=21,   a_s="#7", a_sp=4.5, b_s="#6", b_sp=4.5, e_s="#5", e_sp=4.5, B=71, lblf=596),
    (14, 13, 10): dict(T1=13.5, T2=18,   T3=13.5, a_s="#6", a_sp=4.5, b_s="#8", b_sp=5,   e_s="#5", e_sp=4.5, B=78, lblf=691),
    (14, 13, 20): dict(T1=19.5, T2=22,   T3=22,   a_s="#7", a_sp=5,   b_s="#7", b_sp=5,   e_s="#6", e_sp=6,   B=82, lblf=674),
    (14, 14, 10): dict(T1=13.5, T2=19.5, T3=14,   a_s="#6", a_sp=4.5, b_s="#8", b_sp=5,   e_s="#6", e_sp=5.5, B=78, lblf=730),
    (14, 14, 20): dict(T1=20.5, T2=24.5, T3=21.5, a_s="#7", a_sp=5,   b_s="#7", b_sp=4.5, e_s="#6", e_sp=5,   B=83, lblf=753),
}

# ---------------------------------------------------------------------------
# "i" bar count table — confirmed from D80 plan inset
# Key: span_ft → count of i-bars (earth cover <= 10')
# For cover > 10': use #4 @ 12" max (computed from span width)
# ---------------------------------------------------------------------------

_I_BAR_COUNT: dict[int, int] = {
    4: 7, 5: 8, 6: 9, 7: 10, 8: 11, 10: 12, 12: 15, 14: 20,
}

# Known spans present in the D80 table
_KNOWN_SPANS = sorted({k[0] for k in _D80})


# ---------------------------------------------------------------------------
# Helper: notch end-treatment info
# ---------------------------------------------------------------------------

def _notch_info(p: Params) -> tuple[int, float]:
    """
    Return (n_notch_ends, notch_depth_in).

    n_notch_ends: 0 = no notch, 1 = one end, 2 = both ends.
    notch_depth_in: depth of the barrel-end recess (in).
    """
    notch = getattr(p, "notch_ends", "None")
    n = (2 if notch == "Both Ends" else
         1 if notch in ("Inlet End Only", "Outlet End Only") else
         0)
    d = float(getattr(p, "notch_depth_in", 0.0))
    return n, d


# ---------------------------------------------------------------------------
# Helper: D80 lookup (with nearest-height fallback for missing heights)
# ---------------------------------------------------------------------------

def _bc_lookup(span_ft: int, height_ft: int, cover_ft: int,
               logger: ReasoningLogger) -> dict:
    """
    Return the D80 row for (span_ft, height_ft, cover_ft).

    All D80 standard spans (4, 5, 6, 7, 8, 10, 12, 14) are in the dict.
    For non-standard spans, interpolates between nearest tabulated spans.
    For heights outside the tabulated range for a given span, uses the
    nearest available height and logs a warning.
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

    # --- span not in the table — interpolate between neighbours ---
    lower_spans = [s for s in _KNOWN_SPANS if s < span_ft]
    upper_spans = [s for s in _KNOWN_SPANS if s > span_ft]

    if not lower_spans or not upper_spans:
        clamp = _KNOWN_SPANS[0] if not lower_spans else _KNOWN_SPANS[-1]
        logger.warn(
            f"D80: span={span_ft}' outside table range — clamping to span={clamp}'",
            source="BoxCulvertRules",
        )
        return _bc_lookup(clamp, height_ft, cover_ft, logger)

    s_lo = lower_spans[-1]
    s_hi = upper_spans[0]
    t = (span_ft - s_lo) / (s_hi - s_lo)

    row_lo = _bc_lookup(s_lo, height_ft, cover_ft, logger)
    row_hi = _bc_lookup(s_hi, height_ft, cover_ft, logger)

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

# D80 a-bar hook dimensions (from D80 plan bar descriptions)
_J_INV  = 4.0   # invert a-bar hook tail (in)
_J_ROOF = 5.0   # roof a-bar hook tail (in)
_A_LEG  = 6.0   # a-bar short vertical leg (in)


def rule_bc_a_bars(p: Params, logger: ReasoningLogger) -> list[BarRow]:
    """
    A1/A2 — Transverse a-bars (C-shaped, inside face).

    A1 = invert C-bar, A2 = roof C-bar.  Both use the same size and spacing
    from the D80 table, but have different hook tails (J=4\" invert, J=5\" roof)
    per D80 bar schedule.

    B_flat = S + 2*T2 - 6   (3\" cover at each outside wall face)
    A_leg  = 6\" (standard)
    J_inv  = 4\", J_roof = 5\"
    Stock  = 2*(J + A_leg) + B_flat − bend_reduce(\"shape_2\", size)

    qty each = floor(L / a_sp) + 2
    """
    S_in = int(p.span_ft) * 12
    L_in = p.barrel_length_ft * 12

    row    = _bc_lookup(int(p.span_ft), int(p.height_ft), int(p.max_earth_cover_ft), logger)
    a_size = row["a_s"]
    a_sp   = row["a_sp"]
    T2     = row["T2"]

    B_flat  = S_in + 2 * T2 - 6
    deduct  = bend_reduce("shape_2", a_size)

    # A-bars do not extend into the notch zone at each notched end
    n_notch, notch_d = _notch_info(p)
    eff_L = L_in - n_notch * notch_d
    qty   = math.floor(eff_L / a_sp) + 2

    len_inv  = 2 * (_J_INV  + _A_LEG) + B_flat - deduct
    len_roof = 2 * (_J_ROOF + _A_LEG) + B_flat - deduct

    notch_note = (f"  eff_L={L_in}-{n_notch}×{notch_d}={eff_L:.1f}\"" if n_notch else "")
    logger.step(
        f"A-bars ({a_size}@{a_sp}\"): B_flat=S+2T2-6={S_in}+{2*T2:.1f}-6={B_flat:.1f}\"  "
        f"deduct(shape_2)={deduct}\"  qty=floor({eff_L:.1f}/{a_sp})+2={qty}{notch_note}",
        source="BoxCulvertRules",
    )
    logger.step(
        f"A1 invert: 2*(J={_J_INV}+A={_A_LEG})+{B_flat:.1f}-{deduct}={len_inv:.1f}\"  "
        f"A2 roof:   2*(J={_J_ROOF}+A={_A_LEG})+{B_flat:.1f}-{deduct}={len_roof:.1f}\"",
        source="BoxCulvertRules",
    )
    logger.result("A1", f"{a_size} x {qty} @ {fmt_inches(len_inv)}", source="BoxCulvertRules")
    logger.result("A2", f"{a_size} x {qty} @ {fmt_inches(len_roof)}", source="BoxCulvertRules")

    return [
        BarRow(
            mark="A1", size=a_size, qty=qty, length_in=len_inv,
            shape="C",
            leg_a_in=_J_INV, leg_b_in=_A_LEG, leg_c_in=B_flat,
            notes=f"Invert a-bars @{a_sp}\" oc  J={_J_INV}\" A={fmt_inches(_A_LEG)} B={fmt_inches(B_flat)}",
            source_rule="rule_bc_a_bars",
        ),
        BarRow(
            mark="A2", size=a_size, qty=qty, length_in=len_roof,
            shape="C",
            leg_a_in=_J_ROOF, leg_b_in=_A_LEG, leg_c_in=B_flat,
            notes=f"Roof a-bars @{a_sp}\" oc  J={_J_ROOF}\" A={fmt_inches(_A_LEG)} B={fmt_inches(B_flat)}",
            source_rule="rule_bc_a_bars",
        ),
    ]


def rule_bc_b_bars(p: Params, logger: ReasoningLogger) -> list[BarRow]:
    """
    B1 — Transverse b-bars (L-shaped, both side walls).

    Per D80 typical section the b-bar is an L-bar with:
      long_leg  = H + 12\"   (wall height plus 1'-0\" into slab)
      short_leg = table B    (horizontal arm; read directly from D80 table)

    Stock = long_leg + short_leg − bend_reduce(\"shape_1\", size)

    qty = 2 * (floor(L / b_sp) + 2)   (2 walls, 1\" cover each end)
    """
    H_in = p.height_ft * 12
    L_in = p.barrel_length_ft * 12

    row    = _bc_lookup(int(p.span_ft), int(p.height_ft), int(p.max_earth_cover_ft), logger)
    b_size = row["b_s"]
    b_sp   = row["b_sp"]
    B_dim  = row["B"]

    long_leg  = H_in + 12.0
    short_leg = float(B_dim)
    deduct    = bend_reduce("shape_1", b_size)
    bar_len   = long_leg + short_leg - deduct
    qty       = 2 * (math.floor(L_in / b_sp) + 2)

    logger.step(
        f"B1 ({b_size}@{b_sp}\"): long=H+12={H_in:.0f}+12={long_leg:.0f}\"  "
        f"short=B={short_leg:.0f}\"  deduct(shape_1)={deduct}\"  "
        f"stock={bar_len:.1f}\"  qty=2*(floor({L_in}/{b_sp})+2)={qty}",
        source="BoxCulvertRules",
    )
    logger.result("B1", f"{b_size} x {qty} @ {fmt_inches(bar_len)}", source="BoxCulvertRules")

    return [BarRow(
        mark="B1", size=b_size, qty=qty, length_in=bar_len,
        shape="L",
        leg_a_in=long_leg, leg_b_in=short_leg,
        notes=f"Wall b-bars @{b_sp}\" oc  A={fmt_inches(long_leg)} B={fmt_inches(short_leg)}",
        source_rule="rule_bc_b_bars",
    )]


def rule_bc_e_bars(p: Params, logger: ReasoningLogger) -> list[BarRow]:
    """
    E1 — Vertical e-bars (straight, both side walls).

    Per D80 typical section e-bars run vertically the full wall height
    including slab thicknesses, with 3\" cover top and bottom:

      bar_len = T1 + H + T3 - 6   (3\" cover at top and bottom)

    qty = 2 * (floor(L / e_sp) + 1)   (2 walls)
    """
    H_in = p.height_ft * 12
    L_in = p.barrel_length_ft * 12

    row    = _bc_lookup(int(p.span_ft), int(p.height_ft), int(p.max_earth_cover_ft), logger)
    e_size = row["e_s"]
    e_sp   = row["e_sp"]
    T1     = row["T1"]
    T3     = row["T3"]

    bar_len = T1 + H_in + T3 - 6.0
    qty     = 2 * (math.floor(L_in / e_sp) + 1)

    logger.step(
        f"E1 ({e_size}@{e_sp}\"): T1+H+T3-6={T1}+{H_in:.0f}+{T3}-6={bar_len:.1f}\"  "
        f"qty=2*(floor({L_in}/{e_sp})+1)={qty}",
        source="BoxCulvertRules",
    )
    logger.result("E1", f"{e_size} x {qty} @ {fmt_inches(bar_len)}", source="BoxCulvertRules")

    return [BarRow(
        mark="E1", size=e_size, qty=qty, length_in=bar_len,
        shape="Str",
        notes=f"Vertical e-bars @{e_sp}\" oc  T1+H+T3-6={fmt_inches(bar_len)}",
        source_rule="rule_bc_e_bars",
    )]


def rule_bc_h_bars(p: Params, logger: ReasoningLogger) -> list[BarRow]:
    """
    H1 — Horizontal h-bars (#4 @ 12\" max, longitudinal, all 4 wall faces).

    Per D80 typical section h-bars are horizontal longitudinal distribution
    bars at 12\" max vertical spacing on all four faces (inside and outside
    of both side walls).

      H_total       = T1 + H + T3
      bars_per_face = floor(H_total / 12) + 1
      qty           = 4 * bars_per_face   (2 walls x 2 faces)
      bar_len       = L - 6              (3\" cover each end, no notch)

    Per Caltrans D84 general note: \"EXTEND ALL LONGITUDINAL BARS IN BOX WALLS
    2'-0\" INTO WINGWALLS, EXCEPT WHERE EXPANSION JOINT OCCURS.\"  At each
    notched end (wingwall connection), the H1 bar extends 24\" past the barrel
    end face instead of stopping 3\" short of it:

      bar_len = L_in - 6 + n_notch * 27   (each notched end: replace -3\" with +24\")
    """
    H_in = p.height_ft * 12
    L_in = p.barrel_length_ft * 12

    row = _bc_lookup(int(p.span_ft), int(p.height_ft), int(p.max_earth_cover_ft), logger)
    T1  = row["T1"]
    T3  = row["T3"]

    H_total       = T1 + H_in + T3
    bars_per_face = math.floor(H_total / 12) + 1
    qty           = 4 * bars_per_face

    # D84: extend 2'-0" into wingwall at each notched end (replaces 3" end cover)
    n_notch, _notch_d = _notch_info(p)
    bar_len = L_in - 6.0 + n_notch * 27.0

    ext_note = (
        f"  D84 ext: +{n_notch}×27\"={n_notch * 27:.0f}\" ({n_notch} wingwall end(s))"
        if n_notch else ""
    )
    logger.step(
        f"H1 (#4@12\"): H_total=T1+H+T3={T1}+{H_in:.0f}+{T3}={H_total:.1f}\"  "
        f"bars_per_face=floor({H_total:.1f}/12)+1={bars_per_face}  "
        f"qty=4x{bars_per_face}={qty}  len={fmt_inches(bar_len)}{ext_note}",
        source="BoxCulvertRules",
    )
    logger.result("H1", f"#4 x {qty} @ {fmt_inches(bar_len)}", source="BoxCulvertRules")

    notes = f"h-bars #4 @12\" vert  4 faces x {bars_per_face}/face  len={fmt_inches(bar_len)}"
    if n_notch:
        notes += f"  (2'-0\" ext. per D84, {n_notch} wingwall end(s))"

    return [BarRow(
        mark="H1", size="#4", qty=qty, length_in=bar_len,
        shape="Str",
        notes=notes,
        source_rule="rule_bc_h_bars",
    )]


def rule_bc_f_bars(p: Params, logger: ReasoningLogger) -> list[BarRow]:
    """
    F1 — Transverse f-bars (#4 @ 12\" max, roof slab).

    Per D80 typical section f-bars are straight transverse bars in the
    roof slab, same flat length as the a-bars:

      bar_len = S + 2*T2 - 6   (3\" cover at each outside wall face)
      qty     = floor(L / 12) + 2
    """
    S_in = int(p.span_ft) * 12
    L_in = p.barrel_length_ft * 12

    row = _bc_lookup(int(p.span_ft), int(p.height_ft), int(p.max_earth_cover_ft), logger)
    T2  = row["T2"]

    bar_len = S_in + 2 * T2 - 6.0

    # F-bars do not extend into the notch zone at each notched end
    n_notch, notch_d = _notch_info(p)
    eff_L = L_in - n_notch * notch_d
    qty   = math.floor(eff_L / 12) + 2

    notch_note = (f"  eff_L={L_in}-{n_notch}×{notch_d}={eff_L:.1f}\"" if n_notch else "")
    logger.step(
        f"F1 (#4@12\"): S+2T2-6={S_in}+{2*T2:.1f}-6={bar_len:.1f}\"  "
        f"qty=floor({eff_L:.1f}/12)+2={qty}{notch_note}",
        source="BoxCulvertRules",
    )
    logger.result("F1", f"#4 x {qty} @ {fmt_inches(bar_len)}", source="BoxCulvertRules")

    return [BarRow(
        mark="F1", size="#4", qty=qty, length_in=bar_len,
        shape="Str",
        notes=f"Roof f-bars #4 @12\" oc  S+2T2-6={fmt_inches(bar_len)}",
        source_rule="rule_bc_f_bars",
    )]


def rule_bc_i_bars(p: Params, logger: ReasoningLogger) -> list[BarRow]:
    """
    I1 — Longitudinal i-bars (straight, invert slab).

    For earth cover <= 10': count from D80 i-bar table.
    For earth cover >  10': qty = floor((S - 4) / 12) + 1  (#4 @ 12\" max).

    Size is always #4.
    bar_len = L - 4   (2\" cover each end)
    """
    S_in  = int(p.span_ft) * 12
    L_in  = p.barrel_length_ft * 12
    cover = int(p.max_earth_cover_ft)
    span  = int(p.span_ft)

    # I1 bars run in the invert slab; stop at notch face (not barrel end face)
    n_notch, notch_d = _notch_info(p)
    bar_len = L_in - 4.0 - n_notch * notch_d

    if cover <= 10:
        qty = _I_BAR_COUNT.get(span)
        if qty is None:
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
                f"I-bar count for span={span}' not in table — interpolated qty={qty}.",
                source="BoxCulvertRules",
            )
        notch_note = f"  notch adj: -{n_notch}×{notch_d}\"" if n_notch else ""
        logger.step(
            f"I1 (cover={cover}'<=10'): D80 table count={qty}  "
            f"len=L-4{notch_note}={fmt_inches(bar_len)}",
            source="BoxCulvertRules",
        )
    else:
        qty = math.floor((S_in - 4) / 12) + 1
        notch_note = f"  notch adj: -{n_notch}×{notch_d}\"" if n_notch else ""
        logger.step(
            f"I1 (cover={cover}'>10'): #4@12\" max  qty=floor(({S_in}-4)/12)+1={qty}  "
            f"len=L-4{notch_note}={fmt_inches(bar_len)}",
            source="BoxCulvertRules",
        )

    logger.result("I1", f"#4 x {qty} @ {fmt_inches(bar_len)}", source="BoxCulvertRules")

    return [BarRow(
        mark="I1", size="#4", qty=qty, length_in=bar_len,
        shape="Str",
        notes="I-bars  cover={}'  {}".format(cover, "D80 table" if cover <= 10 else "#4@12\" max"),
        source_rule="rule_bc_i_bars",
    )]


def rule_bc_hoops(p: Params, logger: ReasoningLogger) -> list[BarRow]:
    """
    HP1 — #4 closed rectangular hoops (D82 miscellaneous details).

    Not called by the default template rules list.  Retained for reference.
    """
    S_in = int(p.span_ft) * 12
    H_in = p.height_ft * 12
    L_in = p.barrel_length_ft * 12

    row = _bc_lookup(int(p.span_ft), int(p.height_ft), int(p.max_earth_cover_ft), logger)
    T1  = row["T1"]
    T2  = row["T2"]
    T3  = row["T3"]

    perimeter = 2 * (S_in + 2 * T2 + H_in + T1 + T3)
    deduct    = bend_reduce("shape_4", "#4")
    hoop_len  = perimeter - deduct
    qty       = math.floor((L_in - 2) / 12) + 1

    logger.step(
        f"HP1 (#4@12\"): perimeter=2*(S+2T2+H+T1+T3)={perimeter}\"  "
        f"deduct={deduct}\"  hoop_len={hoop_len:.1f}\"  qty={qty}",
        source="BoxCulvertRules",
    )
    logger.result("HP1", f"#4 x {qty} @ {fmt_inches(hoop_len)}", source="BoxCulvertRules")

    return [BarRow(
        mark="HP1", size="#4", qty=qty, length_in=hoop_len,
        shape="Rect",
        leg_a_in=S_in + 2 * T2,
        leg_b_in=H_in + T1 + T3,
        notes=f"Hoops @12\" oc  (not in default template)",
        source_rule="rule_bc_hoops",
    )]


def rule_bc_haunch_bars(p: Params, logger: ReasoningLogger) -> list[BarRow]:
    """
    HC1 — #5 L-bars at the 4 inside re-entrant corners (D80 'SEE NOTE 6').

    D82 cross-section shows '#5 TOTAL 2' at each inside barrel corner
    (wall-to-slab junction), so 2 bars per corner x 4 corners = 8 bars total.
    Placed transversely; leg lengths estimated at 18\" each — verify per D82.

    qty    = 4 corners x 2 bars/corner = 8
    length = 18 + 18 − bend_reduce('shape_1', '#5')
    """
    leg    = 18.0
    deduct = bend_reduce("shape_1", "#5")
    bar_len = 2 * leg - deduct
    qty     = 8

    logger.step(
        f"HC1 (#5 L): 4 corners x 2/corner = {qty}  "
        f"len=2x{leg}-{deduct}={bar_len:.1f}\"",
        source="BoxCulvertRules",
    )
    logger.result("HC1", f"#5 x {qty} @ {fmt_inches(bar_len)}", source="BoxCulvertRules")

    return [BarRow(
        mark="HC1", size="#5", qty=qty, length_in=bar_len,
        shape="L",
        leg_a_in=leg, leg_b_in=leg,
        notes="Haunch bars #5  4 corners x 2/corner  each leg=18\" (est.)",
        review_flag="Verify leg dims per D82 haunch detail",
        source_rule="rule_bc_haunch_bars",
    )]


def rule_bc_notch_bars(p: Params, logger: ReasoningLogger) -> list[BarRow]:
    """
    G1 — Barrel-end notch bars.

    When notch_ends != \"None\" a rectangular keyway recess is formed at each
    specified barrel end in the roof slab and the invert slab per D82
    \"CULVERT EXTENSION\" and \"CAST-IN-PLACE END ELEVATION\" details.

    Per D82: one #4 U-bar at each notch face (roof + invert per notched end).

    Bar geometry (D82 Cast-in-Place End Elevation):
      size   = #4  (fixed, per D82)
      shape  = U
      body   = S + 2*T2 - 6   (3\" cover each outer wall face)
      legs   = 12\"            (development length, per D82)
      stock  = body + 2*legs − bend_reduce(\"shape_2\", \"#4\")
      qty    = 2 * n_ends      (1 roof + 1 invert per notched end)

    Keyway depth: 3\" for span <= 8', 4\" for span > 8' per D82.
    """
    notch = getattr(p, "notch_ends", "None")
    if notch == "None":
        return []

    S_in  = int(p.span_ft) * 12
    depth = float(getattr(p, "notch_depth_in", 3.0))

    row = _bc_lookup(int(p.span_ft), int(p.height_ft), int(p.max_earth_cover_ft), logger)
    T2  = row["T2"]

    n_ends = 2 if notch == "Both Ends" else 1
    body   = S_in + 2 * T2 - 6.0        # flat width — 3" cover each outer face
    legs   = 12.0                         # #4 development length per D82
    deduct = bend_reduce("shape_2", "#4")
    bar_len = body + 2 * legs - deduct
    qty    = 2 * n_ends  # 1 roof + 1 invert per notched end

    logger.step(
        f"G1 (#4 U): notch_ends={notch}  n_ends={n_ends}  depth={depth}\"  "
        f"body=S+2T2-6={S_in}+{2*T2:.1f}-6={body:.1f}\"  "
        f"legs=2×{legs}\"  deduct(shape_2,#4)={deduct}\"  "
        f"bar_len={bar_len:.1f}\"  qty=2×{n_ends}={qty}",
        source="BoxCulvertRules",
    )
    logger.result("G1", f"#4 x {qty} @ {fmt_inches(bar_len)}", source="BoxCulvertRules")

    return [BarRow(
        mark="G1", size="#4", qty=qty, length_in=bar_len,
        shape="U",
        leg_a_in=legs, leg_b_in=body,
        notes=(
            f"Barrel-end notch bars  {notch}  depth={depth}\"  "
            f"#4 U-bar per D82  1 roof + 1 invert per end  "
            f"body={fmt_inches(body)}  legs={legs}\""
        ),
        review_flag="Verify leg dimension and bar count per D82 CAST-IN-PLACE END ELEVATION",
        source_rule="rule_bc_notch_bars",
    )]


def rule_bc_validate(p: Params, logger: ReasoningLogger) -> list[BarRow]:
    """
    Validate span/height combo exists in the D80 table and log the
    published lb/lf for sanity checking.
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
        logger.step(
            f"D80 published lb/lf = {_D80[exact_key]['lblf']} (reference only)",
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
