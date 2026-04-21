"""
CNSTRUCT 1.0 — Rebar Detail Generator
Streamlit web app  ·  streamlit run app.py
"""

from __future__ import annotations

import csv
import hashlib
import html
import io
import json
import os
import re
from datetime import date

import pandas as pd
import streamlit as st

import assistant as asst
import defaults as dflt
from caltrans_tables import caltrans_lookup

def _api_key_available() -> bool:
    """Check for API key in Streamlit secrets (cloud) or env var (local)."""
    try:
        if st.secrets.get("ANTHROPIC_API_KEY"):
            return True
    except Exception:
        pass
    return bool(os.environ.get("ANTHROPIC_API_KEY"))
import diagram_gen
import history as hist
from vistadetail.engine.calculator import barlist_to_rows, barlist_total_weight_lb, generate_barlist
from vistadetail.engine.reasoning_logger import ReasoningLogger
from vistadetail.engine.templates import TEMPLATE_NAMES, TEMPLATE_REGISTRY

# ── Init ──────────────────────────────────────────────────────────────────────

@st.cache_resource
def _init():
    hist.init_db()

_init()

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="CNSTRUCT 1.0",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
/* ── Hide Streamlit chrome ────────────────────────────────────── *
 * Removes all default Streamlit UI elements so the app looks like
 * a standalone tool, not a Streamlit demo:
 *   - collapsedControl: the sidebar toggle arrow
 *   - stHeader: the top bar with Share, Star, GitHub, and deploy menu
 *   - MainMenu: the hamburger (three-dot) menu in the top-right
 *   - stDecoration: the thin colored line across the top of the page
 * Also set toolbarMode = "minimal" in .streamlit/config.toml.       */
[data-testid="collapsedControl"] { display: none; }
header[data-testid="stHeader"] { display: none !important; }
#MainMenu { visibility: hidden; }
[data-testid="stDecoration"] { display: none !important; }

.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 2rem !important;
    max-width: 1380px !important;
}

/* Page background */
.stApp { background-color: #f5f6fa !important; }

/* ── Typography ─────────────────────────────────────────────── */
h1, h2, h3, .stMarkdown h2 {
    font-weight: 700 !important;
    letter-spacing: -0.3px !important;
    color: #1a1d23 !important;
}

/* ── Header card ─────────────────────────────────────────────── */
div[data-testid="stVerticalBlock"] > div:first-child {
    /* handled by columns below */
}

/* ── Metric cards ────────────────────────────────────────────── */
[data-testid="stMetric"] {
    background: #ffffff;
    border: 1px solid #e8eaed;
    border-radius: 10px;
    padding: 1rem 1.25rem !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
[data-testid="stMetricLabel"] {
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
    color: #6c737a !important;
}
[data-testid="stMetricValue"] {
    font-size: 1.6rem !important;
    font-weight: 700 !important;
    color: #1c3461 !important;
}

/* ── Buttons ─────────────────────────────────────────────────── */
div[data-testid="column"] > div > div > div > button,
div[data-testid="column"] > div > div > div > div > button {
    border-radius: 7px !important;
    font-weight: 600 !important;
    font-size: 0.82rem !important;
    height: 2.3rem !important;
    border: 1.5px solid #e0e3e8 !important;
    background: #ffffff !important;
    color: #2d3748 !important;
    transition: all 0.15s ease !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
}
div[data-testid="column"] > div > div > div > button:hover {
    border-color: #1c3461 !important;
    color: #1c3461 !important;
    box-shadow: 0 2px 6px rgba(28,52,97,0.12) !important;
}
/* Primary generate button */
div[data-testid="column"] > div > div > div > button[kind="primary"],
button[data-testid="baseButton-primary"] {
    background: #1c3461 !important;
    color: #ffffff !important;
    border-color: #1c3461 !important;
    box-shadow: 0 2px 6px rgba(28,52,97,0.25) !important;
}
button[data-testid="baseButton-primary"]:hover {
    background: #16295a !important;
    box-shadow: 0 3px 10px rgba(28,52,97,0.35) !important;
}

/* ── Download buttons ────────────────────────────────────────── */
a[data-testid="stDownloadButton"] button,
div[data-testid="stDownloadButton"] button {
    border-radius: 7px !important;
    font-weight: 600 !important;
    font-size: 0.82rem !important;
    height: 2.3rem !important;
    border: 1.5px solid #e0e3e8 !important;
    background: #ffffff !important;
    color: #2d3748 !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
}

/* ── DataFrames ──────────────────────────────────────────────── */
[data-testid="stDataFrame"] {
    border-radius: 10px !important;
    border: 1px solid #e8eaed !important;
    overflow: hidden !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06) !important;
}

/* ── Tabs ────────────────────────────────────────────────────── */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 2px solid #e8eaed !important;
    gap: 0.25rem !important;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    border-radius: 7px 7px 0 0 !important;
    font-weight: 600 !important;
    font-size: 0.83rem !important;
    color: #6c737a !important;
    padding: 0.5rem 1rem !important;
    border-bottom: 2px solid transparent !important;
    background: transparent !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
    color: #1c3461 !important;
    border-bottom: 2px solid #1c3461 !important;
    background: transparent !important;
}

/* ── Expanders ───────────────────────────────────────────────── */
[data-testid="stExpander"] {
    border: 1px solid #e8eaed !important;
    border-radius: 10px !important;
    background: #ffffff !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
}
[data-testid="stExpander"] summary {
    font-weight: 600 !important;
    color: #2d3748 !important;
    font-size: 0.86rem !important;
}

/* ── Input fields ────────────────────────────────────────────── */
[data-testid="stNumberInput"] > div,
[data-testid="stTextInput"] > div > div,
[data-testid="stSelectbox"] > div > div {
    border-radius: 7px !important;
    background: #ffffff !important;
    border: 1px solid #dce0e8 !important;
}
.stNumberInput input, .stTextInput input {
    background: #ffffff !important;
    color: #1a1d23 !important;
}

/* ── Image panel ─────────────────────────────────────────────── */
[data-testid="stImage"] {
    border-radius: 10px !important;
    overflow: hidden !important;
    border: 1px solid #e8eaed !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.07) !important;
}

/* ── Info / warning / success boxes ─────────────────────────── */
[data-testid="stAlert"] {
    border-radius: 8px !important;
    border-left-width: 4px !important;
}

/* ── Divider ─────────────────────────────────────────────────── */
hr {
    border-color: #e8eaed !important;
    margin: 0.75rem 0 !important;
}

/* ── Chat — user bubble (right-aligned) ──────────────────────── */
.cnstruct-user-msg {
    display: flex;
    justify-content: flex-end;
    margin: 8px 0 8px 56px;
}
.cnstruct-user-bubble {
    background: #1c3461;
    color: #ffffff;
    border-radius: 20px 20px 4px 20px;
    padding: 10px 16px;
    font-size: 0.88rem;
    line-height: 1.6;
    white-space: pre-wrap;
    word-break: break-word;
}

/* ── Chat — AI message (st.chat_message) ─────────────────────── */
[data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 4px 0 !important;
    margin: 4px 0 !important;
}
/* Navy avatar circle */
[data-testid="stChatMessageAvatarContainer"] {
    background: #1c3461 !important;
    border-radius: 50% !important;
}
[data-testid="stChatMessageAvatarContainer"] svg {
    color: #ffffff !important;
    fill: #ffffff !important;
}

/* ── Chat — input bar ────────────────────────────────────────── */
[data-testid="stChatInput"] > div {
    border-radius: 28px !important;
    border: 2px solid #e4e8f0 !important;
    background: #ffffff !important;
    box-shadow: 0 2px 10px rgba(0,0,0,0.06) !important;
    transition: border-color 0.15s ease, box-shadow 0.15s ease !important;
}
[data-testid="stChatInput"] > div:focus-within {
    border-color: #1c3461 !important;
    box-shadow: 0 2px 14px rgba(28,52,97,0.14) !important;
}
[data-testid="stChatInput"] textarea {
    background: transparent !important;
    font-size: 0.91rem !important;
    padding: 13px 20px !important;
    color: #1a1d23 !important;
    border: none !important;
}
[data-testid="stChatInput"] textarea::placeholder {
    color: #aab0bb !important;
}
[data-testid="stChatInputSubmitButton"] button {
    background: #1c3461 !important;
    border-radius: 50% !important;
    width: 34px !important;
    height: 34px !important;
    margin: 7px 8px 7px 0 !important;
    border: none !important;
    box-shadow: none !important;
}
[data-testid="stChatInputSubmitButton"] button:hover {
    background: #16295a !important;
}
[data-testid="stChatInputSubmitButton"] svg {
    fill: #ffffff !important;
    color: #ffffff !important;
}

/* ── Section labels ──────────────────────────────────────────── */
label[data-testid="stWidgetLabel"] {
    font-weight: 600 !important;
    font-size: 0.83rem !important;
    color: #374151 !important;
}
</style>
""", unsafe_allow_html=True)


# ── Input widget helpers ──────────────────────────────────────────────────────

def _is_bool_float(f) -> bool:
    return f.dtype == float and f.min == 0.0 and f.max == 1.0

def _float_step_fmt(f):
    vals = [v for v in [f.min, f.max, f.default] if v is not None]
    all_whole = all(v == int(v) for v in vals)
    rng = (f.max - f.min) if f.min is not None and f.max is not None else 100.0
    if all_whole and rng > 3:
        return 1.0, "%.0f"
    return (0.25, "%.2f") if rng <= 10 else (0.5, "%.1f")

# ── Ft-inches parsing / formatting ───────────────────────────────────────────

def _parse_ft_in(s: str) -> float | None:
    """Parse a feet-inches string to decimal feet.

    Accepted formats:  5'-6"  5'6  5-6  5' 6"  5.5  5'-11 3/8"  0
    Returns None if the string cannot be parsed.
    """
    if s is None:
        return None
    s = str(s).strip().rstrip('"\'').strip()
    if not s:
        return None
    # Plain number (decimal feet)
    try:
        return float(s)
    except ValueError:
        pass
    # Separator between feet and inches: ' and/or - with optional spaces
    _SEP = r"(?:['\u2032]\s*-?\s*|-\s*)"
    # Feet-inches with fractional inches:  5'-11 3/8  or  2'-11 3/8
    m = re.match(r"(\d+)\s*" + _SEP + r"(\d+)\s+(\d+)/(\d+)", s)
    if m:
        return int(m.group(1)) + (int(m.group(2)) + int(m.group(3)) / int(m.group(4))) / 12.0
    # Feet-inches:  5'-6  or  5'6  or  5-6
    m = re.match(r"(\d+)\s*" + _SEP + r"(\d+(?:\.\d+)?)\s*$", s)
    if m:
        return int(m.group(1)) + float(m.group(2)) / 12.0
    # Just feet with optional tick:  5'  or  5
    m = re.match(r"(\d+(?:\.\d+)?)\s*['\u2032]?\s*$", s)
    if m:
        return float(m.group(1))
    return None


def _format_ft_in(ft_val: float) -> str:
    """Format decimal feet to  ft'-in\"  with 1/8-inch precision."""
    if ft_val < 0:
        return f"-{_format_ft_in(-ft_val)}"
    total_in = ft_val * 12.0
    feet = int(total_in // 12)
    eighths = round((total_in - feet * 12) * 8)
    if eighths >= 96:          # rolled over 12"
        feet += 1
        eighths = 0
    whole_in = eighths // 8
    frac = eighths % 8
    if frac == 0:
        return f"{feet}'-{whole_in}\""
    num, den = frac, 8
    while num % 2 == 0:
        num //= 2
        den //= 2
    if whole_in:
        return f"{feet}'-{whole_in} {num}/{den}\""
    return f"{feet}'-{num}/{den}\""


def _parse_ft_params(template, params_raw: dict) -> list[str]:
    """Parse ft-in text values in *params_raw* **in-place** to decimal floats.

    Returns a list of validation error strings (empty on success).
    """
    errors: list[str] = []
    for f in template.inputs:
        raw = params_raw.get(f.name)
        if f.dtype == float and f.name.endswith("_ft") and isinstance(raw, str):
            parsed = _parse_ft_in(raw)
            if parsed is not None:
                params_raw[f.name] = parsed
            else:
                label = getattr(f, "label", f.name.replace("_", " ").title())
                errors.append(f"Cannot parse dimension '{raw}' for {label}")
    return errors


def _widget(f, key_prefix="", container=None):
    """Render one input widget. Returns (name, value)."""
    target = container or st
    label = f.label or f.name
    key   = f"{key_prefix}__{f.name}"
    hint  = f.hint or None

    if _is_bool_float(f):
        v = target.checkbox(label, value=bool(f.default), key=key, help=hint)
        return f.name, 1.0 if v else 0.0

    if f.choices:
        choices = list(f.choices)
        idx = choices.index(f.default) if f.default in choices else 0
        return f.name, target.selectbox(label, choices, index=idx, key=key, help=hint)

    if f.dtype == int:
        lo = int(f.min) if f.min is not None else 0
        hi = int(f.max) if f.max is not None else 9999
        dv = int(f.default) if f.default is not None else lo
        return f.name, target.number_input(label, min_value=lo, max_value=hi,
                                           value=dv, step=1, key=key, help=hint)

    if f.dtype == float:
        # Feet-dimension fields → text input with ft-in format
        if f.name.endswith("_ft"):
            dv = float(f.default) if f.default is not None else 0.0
            dv_str = _format_ft_in(dv)
            return f.name, target.text_input(label, value=dv_str, key=key,
                                             help=hint,
                                             placeholder="e.g. 5'-6\"")
        lo  = float(f.min) if f.min is not None else 0.0
        hi  = float(f.max) if f.max is not None else 9999.0
        dv  = float(f.default) if f.default is not None else lo
        step, fmt = _float_step_fmt(f)
        return f.name, target.number_input(label, min_value=lo, max_value=hi,
                                           value=dv, step=step, format=fmt,
                                           key=key, help=hint)

    dv = str(f.default) if f.default is not None else ""
    return f.name, target.text_input(label, value=dv, key=key, help=hint)


# ── Export helpers ────────────────────────────────────────────────────────────

def _make_csv(bars) -> str:
    buf = io.StringIO()
    csv.writer(buf).writerows(barlist_to_rows(bars))
    return buf.getvalue()

def _make_xml(bars, template_name, job_info=None) -> str:
    """Generate a simple XML barlist export."""
    from xml.etree.ElementTree import Element, SubElement, tostring
    from xml.dom.minidom import parseString

    root = Element("barlist")
    root.set("template", template_name)
    root.set("date", str(date.today()))
    if job_info:
        meta = SubElement(root, "job")
        for k, v in job_info.items():
            if v:
                meta.set(k.lower().replace(" ", "_").replace("#", "num"), str(v))
    for b in bars:
        bar_el = SubElement(root, "bar")
        bar_el.set("mark", b.mark)
        bar_el.set("size", b.size)
        bar_el.set("qty", str(b.qty))
        bar_el.set("length_in", f"{b.length_in:.2f}")
        bar_el.set("length", b.length_ft_in)
        bar_el.set("shape", b.shape)
        if b.leg_a_in:
            bar_el.set("leg_a_in", f"{b.leg_a_in:.2f}")
        if b.leg_b_in:
            bar_el.set("leg_b_in", f"{b.leg_b_in:.2f}")
        if b.leg_c_in:
            bar_el.set("leg_c_in", f"{b.leg_c_in:.2f}")
        if b.notes:
            bar_el.set("notes", b.notes)
    return parseString(tostring(root, encoding="unicode")).toprettyxml(indent="  ")


def _make_pdf(bars, template_name, job_info=None,          # noqa: C901
              params_raw=None, template=None) -> bytes:
    """
    Render a Vista Steel–style barlist PDF (black and white).

    Parameters
    ----------
    bars          : list[BarRow]
    template_name : str
    job_info      : dict  — Project, Job #, Detailer, Date
    params_raw    : dict  — template input values (displayed as Dimensions Used)
    template      : BaseTemplate — needed to get human-readable field labels
    """
    from reportlab.lib import colors as rc
    from reportlab.lib.pagesizes import landscape, letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        Image as RLImage, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
    )
    from reportlab.graphics.shapes import (
        Drawing, Line, Rect, Circle, String as GStr,
    )
    from collections import defaultdict as _dd
    from vistadetail.engine.hooks import BAR_WEIGHT_LB_FT as _WLBFT

    # ── Black-and-white palette ───────────────────────────────────────────
    _BLACK  = rc.black
    _WHITE  = rc.white
    _STRIPE = rc.HexColor("#f2f2f2")   # very light gray alternating rows
    _MID    = rc.HexColor("#dddddd")   # grid lines / borders
    _WARN   = rc.HexColor("#fff3cd")   # yellow flag — keep for review rows

    PAGE_W = 10.0 * inch   # usable width (11" − 2 × 0.5" margin)

    # ── Compact dimension label ("ft-in" compact, e.g. 81 → '6-9') ──────
    def _cdim(in_val):
        if not in_val:
            return ""
        ft  = int(in_val // 12)
        ins = round(in_val % 12)
        if ins >= 12:
            ft += 1; ins = 0
        return f"{ft}-{ins}"

    # ── Bar shape sketch (reportlab Drawing) ─────────────────────────────
    def _sketch(bar):
        SW, SH = 2.0 * inch, 0.55 * inch
        d  = Drawing(SW, SH)
        lw = 1.8
        m  = 8.0
        fs = 6.0

        a = _cdim(bar.leg_a_in) if bar.leg_a_in else None
        b = _cdim(bar.leg_b_in) if bar.leg_b_in else None
        c = _cdim(bar.leg_c_in) if bar.leg_c_in else None
        dd = _cdim(bar.leg_d_in) if bar.leg_d_in else None
        g = _cdim(bar.leg_g_in) if bar.leg_g_in else None
        shape = (bar.shape or "Str").strip()

        if shape == "Str":
            y = SH * 0.65
            d.add(Line(m, y, SW - m, y, strokeWidth=lw, strokeColor=_BLACK))
            if a:
                d.add(GStr(SW / 2, 2, a, fontSize=fs,
                           textAnchor="middle", fillColor=_BLACK))

        elif shape in ("L", "Hook"):
            hy = SH - m - fs - 2
            x1 = m; x2 = SW - m
            yd = 2
            d.add(Line(x1, hy, x2, hy, strokeWidth=lw, strokeColor=_BLACK))
            d.add(Line(x1, hy, x1, yd, strokeWidth=lw, strokeColor=_BLACK))
            if b:
                d.add(GStr((x1 + x2) / 2, hy + 2, b,
                           fontSize=fs, textAnchor="middle", fillColor=_BLACK))
            if a:
                d.add(GStr(x1 + 4, (hy + yd) / 2, a,
                           fontSize=fs, textAnchor="start", fillColor=_BLACK))

        elif shape == "U":
            xl = m + 12; xr = SW - m - 12
            yt = SH - 4; yb = fs + 4
            d.add(Line(xl, yt, xr, yt, strokeWidth=lw, strokeColor=_BLACK))
            d.add(Line(xl, yt, xl, yb, strokeWidth=lw, strokeColor=_BLACK))
            d.add(Line(xr, yt, xr, yb, strokeWidth=lw, strokeColor=_BLACK))
            if a:
                d.add(GStr(xl - 3, (yt + yb) / 2, a,
                           fontSize=fs, textAnchor="end", fillColor=_BLACK))
            if b:
                d.add(GStr((xl + xr) / 2, 2, b,
                           fontSize=fs, textAnchor="middle", fillColor=_BLACK))

        elif shape == "Hoop":
            # S6 hoop — sketch style: rectangle body, top bar overshoots
            # the right side and curves down, suggesting a closed loop.
            # Bottom stays straight (matches field hand-draw convention).
            xl    = m + 8          # left edge of rectangle
            xr    = SW * 0.60      # right edge of rectangle body
            yt    = SH - 5         # top y
            yb    = fs + 3         # bottom y
            x_ext = SW - m - 10    # top bar extends this far right (past xr)

            # Rectangle: bottom, left side, right side
            d.add(Line(xl, yb, xr, yb, strokeWidth=lw, strokeColor=_BLACK))
            d.add(Line(xl, yb, xl, yt, strokeWidth=lw, strokeColor=_BLACK))
            d.add(Line(xr, yb, xr, yt, strokeWidth=lw, strokeColor=_BLACK))
            # Top bar overshooting past right side
            d.add(Line(xl, yt, x_ext, yt, strokeWidth=lw, strokeColor=_BLACK))
            # Straight vertical drop from overshoot end (matches SVG thumbnail style)
            d.add(Line(x_ext, yt, x_ext, yt - 14, strokeWidth=lw, strokeColor=_BLACK))

            # Key dimension labels only (B = side height, C = bottom span)
            rect_cx = (xl + xr) / 2
            if b:
                d.add(GStr(xl - 2, (yt + yb) / 2, b,
                           fontSize=fs - 0.5, textAnchor="end", fillColor=_BLACK))
            if c:
                d.add(GStr(rect_cx, 1, c,
                           fontSize=fs - 0.5, textAnchor="middle", fillColor=_BLACK))

        elif shape == "Rect":
            lx = m + 4; rx = SW - m - 4
            by = fs + 4; ty = SH - 4
            d.add(Rect(lx, by, rx - lx, ty - by,
                       strokeWidth=lw, strokeColor=_BLACK,
                       fillColor=_WHITE))
            if a:
                d.add(GStr((lx + rx) / 2, 2, a,
                           fontSize=fs, textAnchor="middle", fillColor=_BLACK))
            if b:
                d.add(GStr(rx + 3, (by + ty) / 2, b,
                           fontSize=fs, textAnchor="start", fillColor=_BLACK))

        elif shape == "Rng":
            cx = SW / 2; cy = SH / 2 + fs / 2
            r  = min(SW, SH) / 2 - m
            d.add(Circle(cx, cy, r,
                         strokeWidth=lw, strokeColor=_BLACK,
                         fillColor=_WHITE))
            if a:
                d.add(GStr(cx, cy - fs / 2, a,
                           fontSize=fs, textAnchor="middle", fillColor=_BLACK))

        elif shape == "C":
            # C-bar hairpin: top span, two vertical legs, chamfered bottom corners,
            # short inward feet at the bottom (open end).
            # Chamfer approximates the R=9" radius bend without needing Arc.
            xl = m + 14; xr = SW - m - 14
            yt = SH - 4
            R_pts  = 5.0   # corner chamfer size (approximates radius in sketch)
            foot   = 9.0   # horizontal foot length in pts
            yb_leg = fs + 4 + R_pts   # legs stop here, then chamfer
            yb_ft  = fs + 4            # foot level
            # top span (body "0")
            d.add(Line(xl, yt, xr, yt, strokeWidth=lw, strokeColor=_BLACK))
            # left leg going down to chamfer start
            d.add(Line(xl, yt, xl, yb_leg, strokeWidth=lw, strokeColor=_BLACK))
            # right leg going down to chamfer start
            d.add(Line(xr, yt, xr, yb_leg, strokeWidth=lw, strokeColor=_BLACK))
            # bottom-left chamfer (diagonal, simulates radius)
            d.add(Line(xl, yb_leg, xl + R_pts, yb_ft, strokeWidth=lw, strokeColor=_BLACK))
            # bottom-right chamfer
            d.add(Line(xr, yb_leg, xr - R_pts, yb_ft, strokeWidth=lw, strokeColor=_BLACK))
            # left foot going inward (rightward)
            d.add(Line(xl + R_pts, yb_ft, xl + R_pts + foot, yb_ft,
                       strokeWidth=lw, strokeColor=_BLACK))
            # right foot going inward (leftward)
            d.add(Line(xr - R_pts, yb_ft, xr - R_pts - foot, yb_ft,
                       strokeWidth=lw, strokeColor=_BLACK))
            # label "0" on body (top span)
            if a:
                d.add(GStr((xl + xr) / 2, yt + 2, f"0={a}",
                           fontSize=fs - 0.5, textAnchor="middle", fillColor=_BLACK))
            # label "d" on inner span
            if dd:
                d.add(GStr((xl + xr) / 2, (yt + yb_ft) / 2 + 2, f"d={dd}",
                           fontSize=fs - 0.5, textAnchor="middle", fillColor=_BLACK))
            # label "c" and "B" on the two feet
            if b:
                d.add(GStr(xl - 2, yb_ft + 1, f"c={b}",
                           fontSize=fs - 0.5, textAnchor="end", fillColor=_BLACK))
                d.add(GStr(xr + 2, yb_ft + 1, f"B={b}",
                           fontSize=fs - 0.5, textAnchor="start", fillColor=_BLACK))
            # R label at bottom center
            if g:
                d.add(GStr((xl + xr) / 2, yb_ft - fs + 1, f"R={g}",
                           fontSize=fs - 1.0, textAnchor="middle", fillColor=_BLACK))

        elif shape == "S":
            # Symmetric standee (mat chair):
            #   top: A-hook — B-center — C-hook  (all at same height)
            #   drops down from B ends
            #   base: D feet extending outward left and right
            cx    = SW / 2
            top_hw = 7     # half-width of B center bar
            hook   = 9     # A and C hook extension (each side)
            drop   = 15    # vertical drop height
            base_e = 12    # base foot extension each side beyond drop
            ytop  = SH - 5
            ybot  = ytop - drop
            # top center bar (B)
            d.add(Line(cx - top_hw, ytop, cx + top_hw, ytop,
                       strokeWidth=lw, strokeColor=_BLACK))
            # left hook (A) extending left from B
            d.add(Line(cx - top_hw, ytop, cx - top_hw - hook, ytop,
                       strokeWidth=lw, strokeColor=_BLACK))
            # right hook (C) extending right from B
            d.add(Line(cx + top_hw, ytop, cx + top_hw + hook, ytop,
                       strokeWidth=lw, strokeColor=_BLACK))
            # left vertical drop
            d.add(Line(cx - top_hw, ytop, cx - top_hw, ybot,
                       strokeWidth=lw, strokeColor=_BLACK))
            # right vertical drop
            d.add(Line(cx + top_hw, ytop, cx + top_hw, ybot,
                       strokeWidth=lw, strokeColor=_BLACK))
            # base left foot (D/2) extending left
            d.add(Line(cx - top_hw, ybot, cx - top_hw - base_e, ybot,
                       strokeWidth=lw, strokeColor=_BLACK))
            # base right foot (D/2) extending right
            d.add(Line(cx + top_hw, ybot, cx + top_hw + base_e, ybot,
                       strokeWidth=lw, strokeColor=_BLACK))
            # Labels
            if b:   # B = center span / riser
                d.add(GStr(cx, ytop + 2, b,
                           fontSize=fs - 0.5, textAnchor="middle", fillColor=_BLACK))
            if a:   # A = left hook
                d.add(GStr(cx - top_hw - hook / 2, ytop + 2, a,
                           fontSize=fs - 0.5, textAnchor="middle", fillColor=_BLACK))
            if dd:  # D = base
                d.add(GStr(cx, ybot - fs + 1, dd,
                           fontSize=fs - 1.0, textAnchor="middle", fillColor=_BLACK))

        else:
            y = SH * 0.65
            d.add(Line(m, y, SW - m, y, strokeWidth=lw, strokeColor=_BLACK))
            if a:
                d.add(GStr(SW / 2, 2, a, fontSize=fs,
                           textAnchor="middle", fillColor=_BLACK))

        return d

    # ── Paragraph styles ─────────────────────────────────────────────────
    _S  = getSampleStyleSheet()
    # Black-text styles
    b8  = ParagraphStyle("b8",  parent=_S["Normal"],
                          fontName="Helvetica-Bold", fontSize=8,
                          textColor=_BLACK)
    n8  = ParagraphStyle("n8",  parent=_S["Normal"],
                          fontName="Helvetica",      fontSize=8,
                          textColor=_BLACK, leading=11)
    # White-text styles for black header rows
    b8w = ParagraphStyle("b8w", parent=_S["Normal"],
                          fontName="Helvetica-Bold", fontSize=8,
                          textColor=_WHITE)
    # Header title style: two-line, enough leading for 16pt first line
    hdr_title = ParagraphStyle("hdr_title", parent=_S["Normal"],
                                fontName="Helvetica", fontSize=8,
                                leading=22, textColor=_BLACK)

    # ── Document ─────────────────────────────────────────────────────────
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(letter),
                            leftMargin=0.5 * inch, rightMargin=0.5 * inch,
                            topMargin=0.5 * inch, bottomMargin=0.5 * inch)
    elems = []

    # ── Header ───────────────────────────────────────────────────────────
    ji      = job_info or {}
    project = ji.get("Project") or ""
    job_num = ji.get("Job #")   or ""
    dtlr    = ji.get("Detailer") or ""
    today   = str(ji.get("Date") or date.today())

    right_lines = []
    if project: right_lines.append(f"<b>Project:</b> {project}")
    if job_num: right_lines.append(f"<b>Job #:</b>   {job_num}")
    if dtlr:    right_lines.append(f"<b>Detailer:</b> {dtlr}")
    right_lines.append(f"<b>Date:</b> {today}")

    left_para = Paragraph(
        f"<font size='16'><b>VISTA STEEL</b></font><br/>"
        f"<b>{template_name}</b>  —  Rebar Barlist",
        hdr_title,
    )

    hdr = Table(
        [[left_para, Paragraph("<br/>".join(right_lines), n8)]],
        colWidths=[6.5 * inch, 3.5 * inch],
        rowHeights=[0.75 * inch],
    )
    hdr.setStyle(TableStyle([
        ("BOX",           (0, 0), (-1, -1), 1.0, _BLACK),
        ("LINEAFTER",     (0, 0), (0, -1),  0.5, _MID),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
    ]))
    elems.append(hdr)
    elems.append(Spacer(1, 0.1 * inch))

    # ── Dimensions Used ──────────────────────────────────────────────────
    if params_raw and template:
        entries = []
        for f in template.inputs:
            val = params_raw.get(f.name)
            if val is None:
                continue
            lbl = f.label or f.name.replace("_", " ").title()
            fv  = f"{val:g}" if isinstance(val, float) else str(val)
            entries.append((lbl, fv))

        if entries:
            half  = (len(entries) + 1) // 2
            col_a = entries[:half]
            col_b = entries[half:]
            while len(col_b) < len(col_a):
                col_b.append(("", ""))

            # Single flat table: section header row + data rows
            dim_rows = [[
                Paragraph("DIMENSIONS USED", b8w), "", "", "",
            ]]
            for (la, va), (lb, vb) in zip(col_a, col_b):
                dim_rows.append([
                    Paragraph(la, b8), Paragraph(va, n8),
                    Paragraph(lb, b8), Paragraph(vb, n8),
                ])

            n_data = len(dim_rows) - 1  # rows after header

            # Try to get a live diagram annotated with the current values
            _diag_png = diagram_gen.get_diagram_live(template_name, params_raw or {})

            if _diag_png:
                # Side-by-side layout: dim table (5") | diagram (5")
                dim_tbl = Table(
                    dim_rows,
                    colWidths=[1.6*inch, 0.9*inch, 1.6*inch, 0.9*inch],
                )
            else:
                # Full-width dim table
                dim_tbl = Table(
                    dim_rows,
                    colWidths=[3.0*inch, 2.0*inch, 3.0*inch, 2.0*inch],
                )

            style_cmds = [
                # Header row: black bg, white text, spans all 4 cols
                ("SPAN",          (0, 0), (-1, 0)),
                ("BACKGROUND",    (0, 0), (-1, 0), _BLACK),
                ("TEXTCOLOR",     (0, 0), (-1, 0), _WHITE),
                ("TOPPADDING",    (0, 0), (-1, 0), 4),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
                ("LEFTPADDING",   (0, 0), (-1, 0), 8),
                # Data rows
                ("GRID",          (0, 1), (-1, -1), 0.4, _MID),
                ("TOPPADDING",    (0, 1), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 1), (-1, -1), 2),
                ("LEFTPADDING",   (0, 1), (-1, -1), 6),
                ("FONTSIZE",      (0, 0), (-1, -1), 8),
                ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ]
            # Alternating stripes on data rows
            for i in range(1, n_data + 1):
                if i % 2 == 0:
                    style_cmds.append(("BACKGROUND", (0, i), (-1, i), _STRIPE))
            dim_tbl.setStyle(TableStyle(style_cmds))

            if _diag_png:
                rl_img = RLImage(io.BytesIO(_diag_png), width=4.8*inch, height=3.2*inch)
                side_tbl = Table(
                    [[dim_tbl, rl_img]],
                    colWidths=[5.0*inch, 5.0*inch],
                )
                side_tbl.setStyle(TableStyle([
                    ("VALIGN",        (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING",   (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
                    ("TOPPADDING",    (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]))
                elems.append(side_tbl)
            else:
                elems.append(dim_tbl)

            elems.append(Spacer(1, 0.1 * inch))

    # ── Barlist table with shape sketches ────────────────────────────────
    ROW_H   = 0.60 * inch
    bar_hdr = [
        Paragraph("<b>Mark</b>",      b8w),
        Paragraph("<b>Qty / Size</b>", b8w),
        Paragraph("<b>Shape</b>",     b8w),
        Paragraph("<b>Length</b>",    b8w),
        Paragraph("<b>Notes</b>",     b8w),
    ]
    bar_rows    = [bar_hdr]
    row_heights = [None]

    for bar in bars:
        bar_rows.append([
            Paragraph(bar.mark, n8),
            Paragraph(f"<b>{bar.qty} {bar.size}</b>", n8),
            _sketch(bar),
            Paragraph(bar.length_ft_in, n8),
            Paragraph(bar.notes or "", n8),
        ])
        row_heights.append(ROW_H)

    # mark | qty+size | sketch | length | notes  (total = 10.0")
    col_w = [0.55*inch, 0.75*inch, 2.0*inch, 0.9*inch, 5.8*inch]

    bar_tbl = Table(bar_rows, colWidths=col_w,
                    rowHeights=row_heights, repeatRows=1)
    bar_style = [
        ("BACKGROUND",    (0, 0), (-1,  0), _BLACK),
        ("TEXTCOLOR",     (0, 0), (-1,  0), _WHITE),
        ("FONTSIZE",      (0, 0), (-1, -1), 8),
        ("GRID",          (0, 0), (-1, -1), 0.4, _MID),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING",   (0, 0), (-1, -1), 4),
    ]
    for i in range(1, len(bars) + 1):
        if bars[i - 1].review_flag:
            bar_style.append(("BACKGROUND", (0, i), (-1, i), _WARN))
        elif i % 2 == 0:
            bar_style.append(("BACKGROUND", (0, i), (-1, i), _STRIPE))
    bar_tbl.setStyle(TableStyle(bar_style))
    elems.append(bar_tbl)
    elems.append(Spacer(1, 0.15 * inch))

    # ── Weight summary (bottom) ───────────────────────────────────────────
    weight_lb = barlist_total_weight_lb(bars)
    _sz_wt: dict = _dd(float)
    for _b in bars:
        _sz_wt[_b.size] += _WLBFT.get(_b.size, 0.0) * (_b.length_in / 12.0) * _b.qty
    _sorted_sz = sorted(_sz_wt.keys(), key=lambda s: int(s.lstrip("#")))

    wt_rows = [[Paragraph("<b>Size</b>", b8w), Paragraph("<b>Weight (lb)</b>", b8w)]]
    for _s in _sorted_sz:
        wt_rows.append([_s, f"{_sz_wt[_s]:,.1f}"])
    wt_rows.append([Paragraph("<b>TOTAL</b>", b8),
                    Paragraph(f"<b>{weight_lb:,.1f}</b>", b8)])

    wt_tbl = Table(wt_rows, colWidths=[0.9 * inch, 1.2 * inch])
    wt_style = [
        ("BACKGROUND",    (0,  0), (-1,  0), _BLACK),
        ("TEXTCOLOR",     (0,  0), (-1,  0), _WHITE),
        ("FONTSIZE",      (0,  0), (-1, -1), 8),
        ("GRID",          (0,  0), (-1, -1), 0.4, _MID),
        ("VALIGN",        (0,  0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0,  0), (-1, -1), 2),
        ("BOTTOMPADDING", (0,  0), (-1, -1), 2),
        ("LEFTPADDING",   (0,  0), (-1, -1), 4),
        ("BOX",           (0, -1), (-1, -1), 1.0, _BLACK),
    ]
    for i in range(1, len(wt_rows) - 1):
        if i % 2 == 0:
            wt_style.append(("BACKGROUND", (0, i), (-1, i), _STRIPE))
    wt_tbl.setStyle(TableStyle(wt_style))
    elems.append(wt_tbl)

    doc.build(elems)
    return buf.getvalue()


# ── Cut optimizer ─────────────────────────────────────────────────────────────

from collections import defaultdict
from vistadetail.engine.schema import fmt_inches as _fmt_in

# ── Bar shape symbols (drawn from Vista Steel barlist convention) ──────────────
# Unicode characters that visually represent each bend type.
SHAPE_SYMBOLS: dict[str, str] = {
    "Str":  "━━━",     # straight bar
    "Rng":  "○",       # circular ring / hoop
    "L":    "└━━",     # L-bar — 90 deg hook one end
    "U":    "⊓",       # U-bar — hooks both ends (stirrup profile)
    "C":    "⊏",       # C-bar — open on one side
    "S":    "⟳",       # spiral
    "Rect": "▭",       # rectangular tie / hoop
    "Hoop": "⊐",       # inlet hoop — C-shape, closed left, open right
    "Hook": "└",       # single 90-deg hook
}


def _bar_shape_svg(shape: str) -> str:
    """
    Return a base64 SVG data URI thumbnail for the given rebar bend shape.
    Displayed in the barlist table Type column as a small engineering sketch.
    """
    import base64
    import math

    W, H = 92, 54
    lw   = 2.2
    m    = 9   # margin

    def ln(x1, y1, x2, y2):
        return (
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" '
            f'x2="{x2:.1f}" y2="{y2:.1f}"/>'
        )

    def arc(cx, cy, r, a0_deg, a1_deg):
        """SVG arc from angle a0 to a1 (degrees, 0=right, clockwise in SVG)."""
        a0 = math.radians(a0_deg)
        a1 = math.radians(a1_deg)
        sx = cx + r * math.cos(a0)
        sy = cy + r * math.sin(a0)
        ex = cx + r * math.cos(a1)
        ey = cy + r * math.sin(a1)
        # large-arc-flag: 0 for arcs <= 180
        laf = 1 if abs(a1_deg - a0_deg) > 180 else 0
        # sweep: 1 = clockwise
        return f'<path d="M {sx:.1f},{sy:.1f} A {r},{r} 0 {laf},1 {ex:.1f},{ey:.1f}"/>'

    lines: list[str] = []

    if shape == "Str":
        y = H * 0.44
        lines.append(ln(m, y, W - m, y))

    elif shape in ("L", "Hook"):
        yt = H * 0.35
        lines.append(ln(m, yt, W - m, yt))   # horizontal
        lines.append(ln(m, yt, m, H - m))    # vertical drop left

    elif shape == "U":
        xl, xr = m + 6, W - m - 6
        yt = m + 4
        yb = H - m
        lines.append(ln(xl, yt, xr, yt))     # top bar
        lines.append(ln(xl, yt, xl, yb))     # left leg down
        lines.append(ln(xr, yt, xr, yb))     # right leg down

    elif shape == "C":
        # C-bar hairpin: straight top bar, straight legs, CURVED BOTTOM corners,
        # then short inward feet. Arcs are at the bottom (R = radius).
        R       = 5.0
        foot    = 9
        xl      = m + 10
        xr      = W - m - 10
        yt      = m + 5
        yb_leg  = H - m - 8 - R   # legs end here, arc begins
        yb_ft   = H - m - 8       # foot level (= yb_leg + R)
        # straight top bar
        lines.append(ln(xl, yt, xr, yt))
        # left leg going down (straight to arc start)
        lines.append(ln(xl, yt, xl, yb_leg))
        # bottom-left arc: from (xl, yb_leg) curving to (xl+R, yb_ft)
        # arc(cx, cy, r, a0, a1): center=(xl+R, yb_leg), 180°→90° clockwise
        lines.append(arc(xl + R, yb_leg, R, 180, 90))
        # left foot going inward (rightward)
        lines.append(ln(xl + R, yb_ft, xl + R + foot, yb_ft))
        # right leg going down
        lines.append(ln(xr, yt, xr, yb_leg))
        # bottom-right arc: from (xr, yb_leg) curving to (xr-R, yb_ft)
        # center=(xr-R, yb_leg), 0°→90° clockwise
        lines.append(arc(xr - R, yb_leg, R, 0, 90))
        # right foot going inward (leftward)
        lines.append(ln(xr - R, yb_ft, xr - R - foot, yb_ft))

    elif shape == "S":
        # Standee — symmetric chair shape:
        #   A and C hooks extend outward from B center bar at top,
        #   two vertical drops, D feet extend outward at bottom.
        cx  = W / 2
        tw  = 10    # half-width of center B bar
        hw  = 15    # A and C hook width (each side)
        sh  = 20    # drop height
        fw  = 16    # D base foot extension each side
        yt  = m + 4
        yb  = yt + sh
        # top center bar (B)
        lines.append(ln(cx - tw, yt, cx + tw, yt))
        # left hook (A) extending left
        lines.append(ln(cx - tw, yt, cx - tw - hw, yt))
        # right hook (C) extending right
        lines.append(ln(cx + tw, yt, cx + tw + hw, yt))
        # left vertical drop
        lines.append(ln(cx - tw, yt, cx - tw, yb))
        # right vertical drop
        lines.append(ln(cx + tw, yt, cx + tw, yb))
        # left foot extending LEFT (D)
        lines.append(ln(cx - tw, yb, cx - tw - fw, yb))
        # right foot extending RIGHT (D)
        lines.append(ln(cx + tw, yb, cx + tw + fw, yb))

    elif shape == "Hoop":
        # Rectangle body with top bar overhanging right side and curling down
        xl    = m + 6
        xr    = W * 0.60
        yt    = m + 5
        yb    = H - m - 5
        x_ext = xr + 16
        gap   = 7   # open gap: right side stops short of top bar (T-junction illusion)
        lines.append(ln(xl, yt, x_ext, yt))            # top bar (full overshoot)
        lines.append(ln(xl, yt, xl, yb))               # left side
        lines.append(ln(xl, yb, xr, yb))               # bottom (full)
        lines.append(ln(xr, yb, xr, yt + gap))         # right side (stops short of top)
        # small hook curl from overshoot end downward
        lines.append(ln(x_ext, yt, x_ext, yt + 12))

    elif shape == "Rect":
        xl, xr = m + 4, W - m - 4
        yt, yb = m + 6, H - m - 6
        lines.append(ln(xl, yt, xr, yt))
        lines.append(ln(xr, yt, xr, yb))
        lines.append(ln(xr, yb, xl, yb))
        lines.append(ln(xl, yb, xl, yt))

    elif shape == "Rng":
        cx = W / 2
        cy = H / 2
        r  = min(W, H) / 2 - m
        lines.append(
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}"/>'
        )

    else:
        # Unknown — draw as straight
        y = H * 0.44
        lines.append(ln(m, y, W - m, y))

    inner = "".join(lines)
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
        f'<rect width="{W}" height="{H}" fill="white" rx="3"/>'
        f'<g stroke="#1a1d23" stroke-width="{lw}" fill="none" '
        f'stroke-linecap="round" stroke-linejoin="round">'
        f'{inner}'
        f'</g></svg>'
    )
    b64 = base64.b64encode(svg.encode()).decode()
    return f"data:image/svg+xml;base64,{b64}"

# ── Smart field predictions ───────────────────────────────────────────────────
# Maps template → [(trigger_field, target_field, fn(trigger_val) → suggested_val)]
# When the trigger field changes, the target is auto-suggested.
# Rules are grounded in Caltrans standard sizing conventions.
def _ft_predict(v, fn=lambda x: x):
    """Parse ft-in string, apply *fn*, re-format to ft-in."""
    parsed = _parse_ft_in(str(v)) if isinstance(v, str) else v
    if parsed is None:
        return v
    return _format_ft_in(fn(float(parsed)))


_FIELD_PREDICTIONS: dict[str, list] = {
    # G2 Inlet: no predictions — Y is fixed, Interior X derived in custom block
    # G2 Expanded Inlet: no auto X→Y (user complained about crosstalk)
    "Box Culvert": [
        ("clear_span_ft", "clear_rise_ft", lambda v: _ft_predict(v)),
    ],
    "Junction Structure": [
        ("inside_length_ft", "inside_width_ft",  lambda v: _ft_predict(v)),
        ("inside_length_ft", "inside_depth_ft",  lambda v: _ft_predict(v, lambda x: x + 1.0)),
    ],
}

def _cut_optimize(bars, stock_len_in):
    by_size = defaultdict(list)
    for b in bars:
        by_size[b.size].extend([b.length_in] * b.qty)
    results = []
    for size in sorted(by_size.keys(), key=lambda s: int(s.lstrip("#"))):
        all_l = by_size[size]
        oversized = [l for l in all_l if l > stock_len_in]
        lengths = sorted([l for l in all_l if l <= stock_len_in], reverse=True)
        sticks_c: list[list[float]] = []
        sticks_r: list[float] = []
        for length in lengths:
            placed = False
            for i, rem in enumerate(sticks_r):
                if rem >= length:
                    sticks_c[i].append(length)
                    sticks_r[i] -= length
                    placed = True
                    break
            if not placed:
                sticks_c.append([length])
                sticks_r.append(stock_len_in - length)
        manifest = [{"Size": size, "Stick #": i+1,
                     "Cuts": " | ".join(_fmt_in(l) for l in sorted(c, reverse=True)),
                     "_cuts_raw": sorted(c, reverse=True),
                     "# Pcs": len(c), "Waste": _fmt_in(r), "Waste (in)": round(r, 2)}
                    for i, (c, r) in enumerate(zip(sticks_c, sticks_r))]
        n = len(sticks_c)
        tot_ord = n * stock_len_in
        used = sum(lengths)
        waste = sum(sticks_r)
        results.append({
            "Size": size, "Sticks": n, "Stock (ft)": stock_len_in/12,
            "Ordered (ft)": round(tot_ord/12,1), "Used (ft)": round(used/12,1),
            "Waste (ft)": round(waste/12,1), "Waste %": round(waste/tot_ord*100,1) if tot_ord else 0,
            "_oversized": len(oversized), "_manifest": manifest,
        })
    return results

def _manifest_csv(results) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Size","Stick #","Cuts","# Pcs","Waste","Waste (in)"])
    for r in results:
        for row in r["_manifest"]:
            w.writerow([row["Size"],row["Stick #"],row["Cuts"],row["# Pcs"],row["Waste"],row["Waste (in)"]])
        w.writerow([])
    return buf.getvalue()


def _draw_cuts_chart(results, stock_len_in):
    """Horizontal bar chart showing each stick's cut layout. Returns a matplotlib Figure."""
    import matplotlib.pyplot as plt

    _PALETTE = ["#1c3461","#2e6fce","#4ca3dd","#7ec8e3","#a8d8ea","#f4a261","#e76f51","#9b59b6"]
    _WASTE_CLR = "#e8eaed"
    _WASTE_EDGE = "#c8cdd4"

    total_rows = sum(len(r["_manifest"]) for r in results)
    fig_h = max(2.5, min(total_rows * 0.38 + len(results) * 0.5, 14))
    fig, ax = plt.subplots(figsize=(9, fig_h), facecolor="#f5f6fa")
    ax.set_facecolor("#f5f6fa")

    y = 0
    yticks, ytick_labels = [], []

    for r in results:
        for stick in r["_manifest"]:
            cuts = stick["_cuts_raw"]
            waste_in = stick["Waste (in)"]
            x = 0.0
            for j, cut in enumerate(cuts):
                frac = cut / stock_len_in
                ax.barh(y, frac, left=x / stock_len_in,
                        color=_PALETTE[j % len(_PALETTE)], height=0.65,
                        edgecolor="white", linewidth=0.4)
                if frac > 0.06:
                    ax.text(x / stock_len_in + frac / 2, y,
                            f"{cut/12:.1f}'", va="center", ha="center",
                            fontsize=6.5, color="white", fontweight="bold")
                x += cut
            if waste_in > 0:
                wfrac = waste_in / stock_len_in
                ax.barh(y, wfrac, left=x / stock_len_in,
                        color=_WASTE_CLR, height=0.65,
                        edgecolor=_WASTE_EDGE, linewidth=0.4)
                if wfrac > 0.06:
                    ax.text(x / stock_len_in + wfrac / 2, y,
                            f"W {waste_in/12:.1f}'", va="center", ha="center",
                            fontsize=5.5, color="#888")
            yticks.append(y)
            ytick_labels.append(f"{r['Size']} #{stick['Stick #']}")
            y += 1

    ax.set_xlim(0, 1)
    ax.set_yticks(yticks)
    ax.set_yticklabels(ytick_labels, fontsize=7, color="#374151")
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
    ax.set_xlabel("Fraction of stock length", fontsize=8, color="#6c737a")
    ax.tick_params(axis="x", colors="#6c737a", labelsize=7)
    ax.tick_params(axis="y", length=0)
    for spine in ax.spines.values():
        spine.set_color("#e8eaed")
    ax.set_title("Stick Cut Layout", fontsize=9, fontweight="bold", color="#1a1d23", pad=8)
    plt.tight_layout(pad=1.2)
    return fig


# ── Template usage stats (from history) ──────────────────────────────────────

@st.cache_data(ttl=30)
def _template_stats(template_name: str) -> str:
    runs = hist.list_runs(200)
    tmpl_runs = [r for r in runs if r["template_name"] == template_name]
    n = len(tmpl_runs)
    if n == 0:
        return "No runs yet"
    return f"{n} run{'s' if n != 1 else ''}  ·  history tracked"




# ═════════════════════════════════════════════════════════════════════════════
# HEADER
# ═════════════════════════════════════════════════════════════════════════════

h1, h2 = st.columns([3, 2])

with h1:
    st.markdown(
        "<div style='display:flex;align-items:center;gap:10px;margin-bottom:2px'>"
        "<span style='background:#1c3461;color:#fff;border-radius:7px;padding:5px 11px;"
        "font-weight:800;font-size:1rem;letter-spacing:0.5px'>CNSTRUCT</span>"
        "<span style='font-size:1.35rem;font-weight:700;color:#1a1d23'>Rebar Detail Generator</span>"
        "</div>"
        "<div style='font-size:0.75rem;color:#8a909a;margin-top:2px'>Vista Steel &nbsp;·&nbsp; v1.0</div>",
        unsafe_allow_html=True,
    )

with h2:
    template_name = st.selectbox(
        "Structure Type", TEMPLATE_NAMES, key="template_select",
        label_visibility="collapsed",
    )

# Job info row (compact)
j1, j2, j3, j4 = st.columns(4)
detailer   = j1.text_input("Detailer", key="detailer", placeholder="Initials")
job_name   = j2.text_input("Project",  key="job_name", placeholder="Project name")
job_number = j3.text_input("Job #",    key="job_number", placeholder="2024-001")
run_date   = j4.date_input("Date",     value=date.today(), key="run_date")

# Template change → clear results
if template_name != st.session_state.get("_last_template"):
    st.session_state._last_template = template_name
    for _k in ("bars", "log_lines", "warnings", "error", "_pdf_bytes"):
        st.session_state.pop(_k, None)

template = TEMPLATE_REGISTRY[template_name]

st.markdown("---")

# ═════════════════════════════════════════════════════════════════════════════
# STATE
# ═════════════════════════════════════════════════════════════════════════════

bars      = st.session_state.get("bars")
log_lines = st.session_state.get("log_lines", [])
warnings  = st.session_state.get("warnings", [])

generate_btn = st.session_state.pop("_gen_bottom", False)

if generate_btn:
    st.session_state.pop("error", None)

if generate_btn:
    # Build params_raw from current widget values.
    # Key format must match exactly what _widget() produces:
    #   primary_{template.name}__{field}  and  adv_{template.name}__{field}
    params_raw: dict = {}
    for f in template.inputs:
        key     = f"primary_{template.name}__{f.name}"
        adv_key = f"adv_{template.name}__{f.name}"
        if key in st.session_state:
            params_raw[f.name] = st.session_state[key]
        elif adv_key in st.session_state:
            params_raw[f.name] = st.session_state[adv_key]
        else:
            params_raw[f.name] = f.default

    # ── Parse ft-in text values to floats ────────────────────────────────
    _ft_errors = _parse_ft_params(template, params_raw)

    # ── Pre-flight input validation ───────────────────────────────────────
    # Fields where 0 is a valid sentinel (auto-calculate), not an error
    _ZERO_OK = {"footing_width_ft", "cover_ft"}

    _validation_errors: list[str] = list(_ft_errors)
    for f in template.inputs:
        val = params_raw.get(f.name)
        if val is None:
            continue
        if f.dtype in (int, float):
            try:
                num = float(val) if val != "" else 0.0
            except (TypeError, ValueError):
                continue   # already captured by _ft_errors
            if f.name.endswith("_ft") and num <= 0 and f.name not in _ZERO_OK:
                _label = f.label if hasattr(f, "label") else f.name.replace("_", " ").title()
                _validation_errors.append(f"{_label} must be greater than zero (got {val})")
            if f.name == "num_structures" and num < 1:
                _validation_errors.append(f"Number of structures must be at least 1 (got {val})")

    if _validation_errors:
        st.session_state.error = "**Input problems:**\n" + "\n".join(
            f"- {e}" for e in _validation_errors)
        st.session_state.bars       = None
        st.session_state._pdf_bytes = None
    else:
        # ── Run engine ────────────────────────────────────────────────────
        log = ReasoningLogger(None)
        with st.spinner("Running engine..."):
            try:
                b = generate_barlist(template, params_raw, log, call_ai=False)
                st.session_state.bars        = b
                st.session_state.log_lines   = log.get_lines()
                st.session_state.warnings    = [ln for ln in log.get_lines() if ln[1].strip()=="WARN"]
                st.session_state.error       = None
                st.session_state.explanation = None   # clear old explanation
                st.session_state._gen_params_hash = hashlib.md5(
                    json.dumps(params_raw, sort_keys=True, default=str).encode()
                ).hexdigest()[:12]
                hist.save_run(template_name, job_name, job_number, detailer,
                              params_raw, b, barlist_total_weight_lb(b), 0.0)
                _template_stats.clear()
                # Pre-compute PDF so download_button always serves a stable blob
                # (avoids the first-click-wrong-file issue caused by render-time recompute)
                try:
                    _pdf_ji = {"Project": job_name, "Job #": job_number,
                               "Detailer": detailer, "Date": str(run_date)}
                    st.session_state._pdf_bytes = _make_pdf(
                        b, template_name, _pdf_ji,
                        params_raw=params_raw, template=template)
                except BaseException:
                    # BaseException (not just Exception) ensures StopIteration
                    # and other non-Exception subclasses don't crash the app
                    # on Python 3.12+ where exception handling semantics differ.
                    st.session_state._pdf_bytes = None
            except Exception as exc:
                st.session_state.error     = str(exc)
                st.session_state.bars      = None
                st.session_state._pdf_bytes = None

    # AI explanation disabled (paused to save API usage — re-enable when needed)
    # if st.session_state.get("bars") and _api_key_available():
    #     with st.spinner("AI is explaining the barlist…"):
    #         try:
    #             chunks = []
    #             for chunk in asst.explain_barlist_stream(
    #                 template_name=template_name,
    #                 params_raw=params_raw,
    #                 bars=st.session_state.bars,
    #                 warnings=st.session_state.warnings,
    #                 log_lines=st.session_state.get("log_lines"),
    #             ):
    #                 chunks.append(chunk)
    #             st.session_state.explanation = "".join(chunks)
    #         except Exception:
    #             st.session_state.explanation = None

    st.rerun()   # always rerun — prevents stale bars from rendering on error

st.markdown("---")

# ═════════════════════════════════════════════════════════════════════════════
# MAIN CONTENT — diagram | inputs (side by side), results full-width below
# ═════════════════════════════════════════════════════════════════════════════

diag_col, inp_col = st.columns([1.3, 1], gap="large")

# ── INPUTS (rendered first so params_raw is populated before diagram) ─────────
with inp_col:
    _tname = template.name   # use template.name consistently for all session-state keys
    params_raw: dict = {}

    # ======================================================================
    # G2 Inlet — custom inputs with bidirectional X and Y display
    # ======================================================================
    if template_name == "G2 Inlet":
        _Y_INT_IN = 35.375   # fixed interior Y (2'-11 3/8")

        # --- Read current T from session state (set by prior render) -------
        _t_wk = f"primary_{_tname}__wall_thick_in"
        _cur_t = int(st.session_state.get(_t_wk, 9))

        # --- Bidirectional X prediction ------------------------------------
        _ext_wk   = f"primary_{_tname}__x_dim_ft"
        _int_wk   = f"_g2_x_interior_{_tname}"
        _prev_e_k = f"_prev_g2_ext_{_tname}"
        _prev_i_k = f"_prev_g2_int_{_tname}"
        _prev_t_k = f"_prev_g2_t_{_tname}"
        _src_k    = f"_g2_x_source_{_tname}"

        _cur_ext = st.session_state.get(_ext_wk)
        _cur_int = st.session_state.get(_int_wk)
        _prev_e  = st.session_state.get(_prev_e_k)
        _prev_i  = st.session_state.get(_prev_i_k)
        _prev_t  = st.session_state.get(_prev_t_k)

        _ext_chg = (_cur_ext is not None and _cur_ext != _prev_e)
        _int_chg = (_cur_int is not None and _cur_int != _prev_i)
        _t_chg   = (_prev_t is not None and _cur_t != _prev_t)

        if _int_chg and not _ext_chg:
            st.session_state[_src_k] = "int"
        elif _ext_chg and not _int_chg:
            st.session_state[_src_k] = "ext"

        _src = st.session_state.get(_src_k, "ext")

        # Derive the non-primary field
        if _src == "ext" and _cur_ext is not None and (_ext_chg or _t_chg):
            _xef = _parse_ft_in(str(_cur_ext))
            if _xef is not None:
                st.session_state[_int_wk] = _format_ft_in(max(0, _xef - 2 * _cur_t / 12.0))
        elif _src == "int" and _cur_int is not None and (_int_chg or _t_chg):
            _xif = _parse_ft_in(str(_cur_int))
            if _xif is not None:
                st.session_state[_ext_wk] = _format_ft_in(_xif + 2 * _cur_t / 12.0)

        st.session_state[_prev_t_k] = _cur_t

        # --- Render widgets ------------------------------------------------
        _x_field = next(f for f in template.inputs if f.name == "x_dim_ft")
        _t_field = next(f for f in template.inputs if f.name == "wall_thick_in")
        _x_def   = float(_x_field.default) if _x_field.default is not None else 5.5
        _int_def = max(0, _x_def - 2 * 9 / 12.0)

        c1, c2 = st.columns(2)
        with c1:
            _ev = st.text_input("X Exterior", key=_ext_wk,
                                value=_format_ft_in(_x_def),
                                help="Exterior face-to-face width",
                                placeholder="e.g. 5'-6\"")
            params_raw["x_dim_ft"] = _ev
        with c2:
            st.text_input("X Interior", key=_int_wk,
                          value=_format_ft_in(_int_def),
                          help="Interior clear width = Exterior - 2T",
                          placeholder="e.g. 4'-0\"")

        # Store for next-run change detection
        st.session_state[_prev_e_k] = st.session_state.get(_ext_wk)
        st.session_state[_prev_i_k] = st.session_state.get(_int_wk)

        # Wall thickness
        _, _tv = _widget(_t_field, key_prefix=f"primary_{_tname}", container=st)
        params_raw["wall_thick_in"] = _tv

        # Y display (interior fixed per Caltrans D73A, exterior derived)
        _y_ext_in = _Y_INT_IN + 2 * int(_tv)
        params_raw["_y_ext_ft"] = _y_ext_in / 12.0   # injected for live diagram Y label
        _yi_key = f"_g2_yi_{_tname}"
        _ye_key = f"_g2_ye_{_tname}"
        # Force the computed values into session state so they always display
        # correctly even if the user typed something in the field
        st.session_state[_yi_key] = "3'-0\""   # 2'-11 3/8" rounded up to next foot
        st.session_state[_ye_key] = _format_ft_in(_y_ext_in / 12.0)
        c3, c4 = st.columns(2)
        with c3:
            st.text_input("Y Interior", key=_yi_key,
                          help="Caltrans D73A minimum 2'-11 3/8\" — rounded up to 3'-0\" for barlist")
        with c4:
            st.text_input("Y Exterior", key=_ye_key,
                          help=f"Y Interior + 2 \u00d7 {int(_tv)}\" — updates with wall thickness")

        # Remaining template fields (wall_height, grate_type, num_structures)
        for f in template.inputs:
            if f.name in ("x_dim_ft", "wall_thick_in"):
                continue
            name, val = _widget(f, key_prefix=f"primary_{_tname}", container=st)
            params_raw[name] = val

    # ======================================================================
    # G2 Expanded Inlet — custom inputs with computed interior dimensions
    # ======================================================================
    # Straight Headwall — show H1 computed field + pipe inputs
    # ======================================================================
    elif template_name == "Straight Headwall":
        _hw_w_field = next(f for f in template.inputs if f.name == "wall_width_ft")
        _hw_h_field = next(f for f in template.inputs if f.name == "wall_height_ft")
        _hw_pq_field = next(f for f in template.inputs if f.name == "pipe_qty")
        _hw_pd_field = next(f for f in template.inputs if f.name == "pipe_dia_in")

        # Wall Width
        name, val = _widget(_hw_w_field, key_prefix=f"primary_{_tname}", container=st)
        params_raw[name] = val

        # Wall Height H + computed H1 side by side
        _hw_h_key = f"primary_{_tname}__wall_height_ft"
        c1, c2 = st.columns(2)
        with c1:
            name, val = _widget(_hw_h_field, key_prefix=f"primary_{_tname}", container=st)
            params_raw[name] = val
        with c2:
            # H1 — editable, minimum = H + 1'-0" per Caltrans D89A
            _h1_key     = f"primary_{_tname}__h1_ft"
            _h_prev_key = f"_hw_h1_prev__{_tname}"
            try:
                _h_raw = st.session_state.get(_hw_h_key, str(_hw_h_field.default or "5'-0\""))
                _h_ft  = _parse_ft_in(str(_h_raw)) if isinstance(_h_raw, str) else float(_h_raw or 0)
            except Exception:
                _h_ft = float(_hw_h_field.default or 5.0)
            _h1_floor     = _h_ft + 1.0
            _h1_floor_str = _format_ft_in(_h1_floor)

            # When H changes, bump H1 up to the new floor if it would go below
            if st.session_state.get(_h_prev_key) != _h_ft:
                _cur = st.session_state.get(_h1_key)
                _cur_ft = None
                if _cur is not None:
                    try:
                        _cur_ft = _parse_ft_in(str(_cur))
                    except Exception:
                        pass
                if _cur_ft is None or _cur_ft < _h1_floor:
                    st.session_state[_h1_key] = _h1_floor_str
                st.session_state[_h_prev_key] = _h_ft

            _h1_raw = st.text_input(
                "H1 (min = H + 1'-0\")",
                key=_h1_key,
                help=(
                    "Physical wall height used for bar lengths. "
                    "Caltrans D89A minimum is H + 1'-0\". "
                    "Contractor may specify more."
                ),
                placeholder=_h1_floor_str,
            )
            try:
                _h1_ft_val = _parse_ft_in(str(_h1_raw)) if _h1_raw else _h1_floor
            except Exception:
                _h1_ft_val = _h1_floor
            if _h1_ft_val < _h1_floor:
                st.caption(f"Minimum H1 = {_h1_floor_str} — clamped.")
                _h1_ft_val = _h1_floor
            params_raw["h1_ft"] = _h1_ft_val

        # Pipe info
        st.markdown("**Pipe**")
        c3, c4 = st.columns(2)
        with c3:
            name, val = _widget(_hw_pq_field, key_prefix=f"primary_{_tname}", container=c3)
            params_raw[name] = val
        with c4:
            name, val = _widget(_hw_pd_field, key_prefix=f"primary_{_tname}", container=c4)
            params_raw[name] = val

    # ======================================================================
    # All other templates — standard primary / advanced layout
    # ======================================================================
    else:
        # Smart suggestions: pre-seed derived fields when trigger changes
        for _trig, _tgt, _fn in _FIELD_PREDICTIONS.get(template_name, []):
            _trig_key = f"primary_{_tname}__{_trig}"
            _prev_key = f"_prev_{_trig}__{_tname}"
            _trig_val = st.session_state.get(_trig_key)
            if _trig_val is not None:
                if st.session_state.get(_prev_key) != _trig_val:
                    st.session_state[_prev_key] = _trig_val
                    st.session_state[f"primary_{_tname}__{_tgt}"] = _fn(_trig_val)

        primary_fields = dflt.get_primary_inputs(template)
        for f in primary_fields:
            name, val = _widget(f, key_prefix=f"primary_{_tname}", container=st)
            params_raw[name] = val

        # Caltrans auto-fill (silently pre-fills advanced fields)
        _ct_result = caltrans_lookup(template_name, params_raw)
        _ct_src    = _ct_result.pop("_source", "")
        if _ct_result:
            _phash_key = f"_phash__{_tname}"
            _phash = hashlib.md5(
                json.dumps(params_raw, sort_keys=True, default=str).encode()
            ).hexdigest()[:8]
            if st.session_state.get(_phash_key) != _phash:
                st.session_state[_phash_key] = _phash
                for _cf, _cv in _ct_result.items():
                    st.session_state[f"primary_{_tname}__{_cf}"] = _cv

        secondary = dflt.get_secondary_inputs(template)
        if secondary:
            with st.expander("Advanced", expanded=False):
                for f in secondary:
                    name, val = _widget(f, key_prefix=f"adv_{template.name}", container=st)
                    params_raw[name] = val

    # ── Parse ft-in text values to decimal floats ────────────────────────
    _parse_ft_params(template, params_raw)

    # ── Inject computed inside-dimensions for live diagram annotation ─────
    # Any template that has x_dim_ft + wall_thick_in gets _inside_x_ft.
    # Any template that has y_dim_ft + wall_thick_in gets _inside_y_ft.
    # G2 Inlet: Y is derived (35.375" fixed interior + 2T) → _y_ext_ft.
    # These synthetic _ft keys are picked up by _FIELD_LABELS in diagram_gen.
    try:
        _di_t = float(params_raw.get("wall_thick_in", 0) or 0)
        _di_x = params_raw.get("x_dim_ft")
        _di_y = params_raw.get("y_dim_ft")
        if _di_t and _di_x is not None:
            params_raw["_inside_x_ft"] = max(0.0, float(_di_x) - 2 * _di_t / 12.0)
        if _di_t and _di_y is not None:
            params_raw["_inside_y_ft"] = max(0.0, float(_di_y) - 2 * _di_t / 12.0)
        if template_name == "G2 Inlet" and _di_t:
            params_raw["_y_ext_ft"] = (35.375 + 2 * _di_t) / 12.0
    except (TypeError, ValueError):
        pass

    # Store params
    st.session_state._last_params = params_raw
    _cur_phash = hashlib.md5(json.dumps(params_raw, sort_keys=True, default=str).encode()).hexdigest()[:12]
    st.session_state._cur_params_hash = _cur_phash

    # Generate button (below inputs)
    st.markdown("")
    if st.button("Generate", type="primary", use_container_width=True, key="btn_gen_bottom"):
        st.session_state["_gen_bottom"] = True
        st.rerun()

# ── DIAGRAM (rendered after inputs so params_raw values are available) ────────
with diag_col:
    diag = diagram_gen.get_diagram_live(template_name, params_raw)
    if diag:
        st.image(diag, use_container_width=True)
    if template.description:
        st.caption(template.description)

# ── RESULTS -- full width below diagram + inputs ───────────────────────────────
if st.session_state.get("error"):
    _err = st.session_state.error
    if _err.startswith("**Input problems:**"):
        st.warning(_err)
    else:
        st.error(
            f"**Generation failed:** {_err}\n\n"
            "_Check that all dimensions are positive and the template inputs make sense, "
            "then click Generate again._"
        )

if bars is not None:
    st.markdown("---")
    weight_lb = barlist_total_weight_lb(bars)

    # Metrics row
    m1, m2, m3 = st.columns(3)
    m1.metric("Marks",      len({b.mark for b in bars}))
    m2.metric("Total Bars", f"{sum(b.qty for b in bars):,}")
    m3.metric("Weight",     f"{weight_lb:,.1f} lb")

    # Warnings inline (if any)
    if warnings:
        for _ts, _tag, msg, detail, _src in warnings:
            st.warning(f"{msg}\n\n_{detail}_" if detail else msg)

    # Barlist table
    df = pd.DataFrame([{
        "Mark":   b.mark,  "Size":   b.size,   "Qty":    b.qty,
        "Length": b.length_ft_in,
        "Type":   _bar_shape_svg(b.shape),
        "A":  b.leg_a_ft_in, "B":  b.leg_b_ft_in, "C":  b.leg_c_ft_in,
        "D":  b.leg_d_ft_in, "G":  b.leg_g_ft_in,
        "Notes":  b.notes, "Ref":    b.ref,    "Review": b.review_flag,
    } for b in bars])

    def _hl(row):
        return ["background-color:#fff3cd"]*len(row) if row["Review"] else [""]*len(row)

    st.dataframe(
        df.style.apply(_hl, axis=1),
        use_container_width=True,
        hide_index=True,
        height=360,
        column_config={
            "Type": st.column_config.ImageColumn(
                "Type", width="small",
                help="Rebar bend shape sketch",
            ),
        },
    )

    # ── Export buttons (below barlist) ───────────────────────────────────────
    ex1, ex2, ex3, _pad = st.columns([1, 1, 1, 3])
    ji = {"Project": job_name, "Job #": job_number,
          "Detailer": detailer, "Date": str(run_date)}
    ex1.download_button(
        "Export CSV",
        data=_make_csv(bars),
        file_name=f"{template_name.replace(' ','_')}_barlist.csv",
        mime="text/csv", use_container_width=True, key="btn_csv",
    )
    ex2.download_button(
        "Export XML",
        data=_make_xml(bars, template_name, ji),
        file_name=f"{template_name.replace(' ','_')}_barlist.xml",
        mime="application/xml", use_container_width=True, key="btn_xml",
    )
    _pdf_bytes = st.session_state.get("_pdf_bytes")
    if _pdf_bytes:
        ex3.download_button(
            "Export PDF",
            data=_pdf_bytes,
            file_name=f"{template_name.replace(' ','_')}_barlist.pdf",
            mime="application/pdf", use_container_width=True, key="btn_pdf",
        )
    else:
        ex3.button("Export PDF", disabled=True, use_container_width=True, key="btn_pdf_na")

# ═════════════════════════════════════════════════════════════════════════════
# AI EXPLANATION — shown inline after generate
# ═════════════════════════════════════════════════════════════════════════════

if st.session_state.get("explanation"):
    st.markdown("---")
    st.markdown(
        "<div style='display:flex;align-items:center;gap:10px;margin-bottom:0.75rem'>"
        "<div style='background:#1c3461;color:#fff;border-radius:8px;padding:4px 10px;"
        "font-size:0.72rem;font-weight:800;letter-spacing:1.2px'>AI</div>"
        "<span style='font-size:1.0rem;font-weight:700;color:#1a1d23'>Barlist Explanation</span>"
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown(st.session_state.explanation)

# ═════════════════════════════════════════════════════════════════════════════
# COMPUTATION LOG (collapsed)
# ═════════════════════════════════════════════════════════════════════════════

if bars is not None or log_lines:
    non_blank = [(ts, tag, msg, det, src) for ts, tag, msg, det, src in log_lines if msg.strip()]
    if non_blank:
        with st.expander("Computation Log", expanded=False):
            log_df = pd.DataFrame(non_blank, columns=["Time","Tag","Message","Detail","Source"])
            st.dataframe(log_df, use_container_width=True, hide_index=True, height=300)

# ═════════════════════════════════════════════════════════════════════════════
# AI ASSISTANT — full-width chat section
# ═════════════════════════════════════════════════════════════════════════════

st.markdown("---")

# Section header
st.markdown(
    "<div style='display:flex;align-items:center;gap:10px;margin-bottom:1rem'>"
    "<div style='background:#1c3461;color:#fff;border-radius:8px;padding:5px 12px;"
    "font-size:0.75rem;font-weight:800;letter-spacing:1.2px'>AI</div>"
    "<span style='font-size:1.05rem;font-weight:700;color:#1a1d23'>"
    "Rebar Detailing Assistant</span>"
    "<span style='font-size:0.8rem;color:#9aa5b4;margin-left:6px'>"
    "Ask about this barlist, ACI 318-19, or Caltrans standards</span>"
    "</div>",
    unsafe_allow_html=True,
)

_api_key_set = _api_key_available()

if not _api_key_set:
    st.info(
        "Set `ANTHROPIC_API_KEY` in your environment to enable the AI assistant.\n\n"
        "```bash\nexport ANTHROPIC_API_KEY=sk-ant-...\n```"
    )
else:
    # Reset chat when template changes
    if st.session_state.get("_chat_template") != template_name:
        st.session_state.chat_messages = []
        st.session_state._chat_template = template_name

    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    # Build context-aware system prompt
    _explanation_ctx = st.session_state.get("explanation", "")
    _chat_system = asst.build_system_prompt(
        template_name=template_name,
        params_raw=st.session_state.get("_last_params"),
        bars=st.session_state.get("bars"),
        cost=None,
        warnings=st.session_state.get("warnings", []),
    )
    if _explanation_ctx:
        _chat_system += (
            f"\n\n## Prior AI Explanation\n"
            f"You already generated this explanation for this barlist:\n{_explanation_ctx}"
        )

    # ── Empty state — welcome card with suggestion chips ──────────────────────
    _suggestions = [
        f"What does each bar mark mean for a {template_name}?",
        "Walk me through the quantity formula for one of these bars",
        "What ACI 318-19 sections apply here?",
        "What should I double-check before submitting this barlist?",
        "How does cover affect the bar count in this design?",
        "Explain the difference between primary and T&S steel here",
    ]

    if not st.session_state.chat_messages:
        st.markdown(
            "<div style='text-align:center;padding:2rem 1rem 1rem'>"
            "<div style='display:inline-flex;align-items:center;justify-content:center;"
            "width:48px;height:48px;background:#1c3461;border-radius:50%;margin-bottom:0.75rem'>"
            "<svg width='22' height='22' viewBox='0 0 24 24' fill='none' stroke='white' "
            "stroke-width='2' stroke-linecap='round' stroke-linejoin='round'>"
            "<path d='M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z'/>"
            "</svg></div>"
            "<div style='font-weight:700;font-size:1rem;color:#1a1d23;margin-bottom:0.25rem'>"
            "Ask me anything about this design</div>"
            "<div style='font-size:0.83rem;color:#9aa5b4;margin-bottom:1.5rem'>"
            "Generate a barlist first for the most relevant answers</div>"
            "</div>",
            unsafe_allow_html=True,
        )
        sug_cols = st.columns(3)
        for i, sug in enumerate(_suggestions):
            if sug_cols[i % 3].button(sug, key=f"sug_{i}", use_container_width=True):
                st.session_state.chat_messages.append({"role": "user", "content": sug})
                st.rerun()
        st.markdown(
            "<div style='margin-top:1rem;border-top:1px solid #f0f2f5'></div>",
            unsafe_allow_html=True,
        )

    # ── Conversation history ──────────────────────────────────────────────────
    for msg in st.session_state.chat_messages:
        if msg["role"] == "user":
            _safe = html.escape(msg["content"])
            st.markdown(
                f'<div class="cnstruct-user-msg">'
                f'<div class="cnstruct-user-bubble">{_safe}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            with st.chat_message("assistant"):
                st.markdown(msg["content"])

    # ── Live input + streaming ────────────────────────────────────────────────
    if user_input := st.chat_input(
        f"Message the assistant…",
        key="chat_input",
    ):
        st.session_state.chat_messages.append({"role": "user", "content": user_input})
        _safe = html.escape(user_input)
        st.markdown(
            f'<div class="cnstruct-user-msg">'
            f'<div class="cnstruct-user-bubble">{_safe}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        with st.chat_message("assistant"):
            placeholder = st.empty()
            full_response = ""
            try:
                for chunk in asst.chat_stream(
                    st.session_state.chat_messages, system=_chat_system
                ):
                    full_response += chunk
                    placeholder.markdown(full_response + "▌")
                placeholder.markdown(full_response)
                st.session_state.chat_messages.append(
                    {"role": "assistant", "content": full_response}
                )
            except Exception as exc:
                err = f"Assistant error: {exc}"
                placeholder.error(err)
                st.session_state.chat_messages.append(
                    {"role": "assistant", "content": err}
                )

    # Clear link — only when there's a conversation
    if st.session_state.chat_messages:
        st.markdown(
            "<div style='text-align:right;margin-top:0.5rem'>",
            unsafe_allow_html=True,
        )
        if st.button("Clear conversation", key="chat_clear"):
            st.session_state.chat_messages = []
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
