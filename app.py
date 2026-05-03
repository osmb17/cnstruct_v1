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

from web import assistant as asst
from web import defaults as dflt
from web.caltrans_tables import caltrans_lookup

def _api_key_available() -> bool:
    """Check for API key in Streamlit secrets (cloud) or env var (local)."""
    try:
        if st.secrets.get("ANTHROPIC_API_KEY"):
            return True
    except Exception:
        pass
    return bool(os.environ.get("ANTHROPIC_API_KEY"))
from web import diagram_gen
from web import history as hist
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
            # C-bar: horizontal bar with large chamfered corner (approximating
            # the radius bend), then vertical leg going down. L-shape.
            xl    = m + 4
            xr    = SW - m - 10
            yt    = SH - 4      # top of bar
            yb    = fs + 2      # bottom of vertical leg
            R_pts = 7.0         # chamfer size (approximates the large radius)
            # horizontal bar
            d.add(Line(xl, yt, xr - R_pts, yt, strokeWidth=lw, strokeColor=_BLACK))
            # chamfer (diagonal approximating the large-radius curve)
            d.add(Line(xr - R_pts, yt, xr, yt - R_pts, strokeWidth=lw, strokeColor=_BLACK))
            # vertical leg
            d.add(Line(xr, yt - R_pts, xr, yb, strokeWidth=lw, strokeColor=_BLACK))
            # label horizontal bar
            if b:
                d.add(GStr((xl + xr) / 2, yt + 2, b,
                           fontSize=fs - 0.5, textAnchor="middle", fillColor=_BLACK))
            # label vertical leg
            if a:
                d.add(GStr(xr + 2, (yt + yb) / 2, a,
                           fontSize=fs, textAnchor="start", fillColor=_BLACK))
            # label radius
            if g:
                d.add(GStr(xr - R_pts - 1, yt - R_pts - 1, f"R={g}",
                           fontSize=fs - 1.5, textAnchor="end", fillColor=_BLACK))

        elif shape == "S":
            # Standee: top horizontal bar spanning full width, two straight vertical
            # legs going down, then a sharp kink with diagonal extensions spreading
            # outward-downward. Matches user-drawn SVG reference.
            xl_s  = m + 14; xr_s = SW - m - 14
            ytop  = SH - 5
            yk    = ytop - 14    # kink point (ReportLab y-up: subtract = going down)
            yb    = yk - 10      # bottom of diagonals
            lx    = xl_s + 10    # left diagonal end x (inward, toward center)
            rx    = xr_s + 10    # right diagonal end x (outward)
            # top span
            d.add(Line(xl_s, ytop, xr_s, ytop, strokeWidth=lw, strokeColor=_BLACK))
            # right leg (straight down to kink)
            d.add(Line(xr_s, ytop, xr_s, yk, strokeWidth=lw, strokeColor=_BLACK))
            # right diagonal (outward-downward)
            d.add(Line(xr_s, yk, rx, yb, strokeWidth=lw, strokeColor=_BLACK))
            # left leg (straight down to kink)
            d.add(Line(xl_s, ytop, xl_s, yk, strokeWidth=lw, strokeColor=_BLACK))
            # left diagonal (outward-downward)
            d.add(Line(xl_s, yk, lx, yb, strokeWidth=lw, strokeColor=_BLACK))
            # Labels
            if b:
                d.add(GStr((xl_s + xr_s) / 2, ytop + 2, b,
                           fontSize=fs - 0.5, textAnchor="middle", fillColor=_BLACK))
            if a:
                d.add(GStr(xl_s - 2, (ytop + yk) / 2, a,
                           fontSize=fs - 0.5, textAnchor="end", fillColor=_BLACK))
            if dd:
                d.add(GStr(xr_s + 2, (yk + yb) / 2, dd,
                           fontSize=fs - 1.0, textAnchor="start", fillColor=_BLACK))

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
        # C-bar: horizontal bar going right with a large smooth-radius curve
        # at the right end, then straight vertical leg going down. L-shape.
        R   = 16.0
        xl  = m + 3
        xr  = W - m - 4
        yt  = m + 2
        yb  = H - m - 3
        # horizontal bar (left end to curve start)
        lines.append(ln(xl, yt, xr - R, yt))
        # large-radius curve: center=(xr-R, yt+R), 270°→360° CW
        lines.append(arc(xr - R, yt + R, R, 270, 360))
        # vertical leg (curve end down to open bottom)
        lines.append(ln(xr, yt + R, xr, yb))

    elif shape == "S":
        # Standee: top horizontal bar, two straight vertical legs going down,
        # then a sharp kink at the bottom of each leg with diagonal extensions
        # spreading outward-downward. No curves, no horizontal feet.
        xl  = m + 19
        xr  = W - m - 19
        yt  = m + 5
        yk  = yt + 19     # kink y (where vertical leg transitions to diagonal)
        lx  = xl + 12     # left diagonal end x (inward, toward center)
        rx  = xr + 12     # right diagonal end x (outward)
        yb  = yk + 12     # bottom of diagonals
        # top span
        lines.append(ln(xl, yt, xr, yt))
        # right leg (straight down to kink)
        lines.append(ln(xr, yt, xr, yk))
        # right diagonal (outward-downward)
        lines.append(ln(xr, yk, rx, yb))
        # left leg (straight down to kink)
        lines.append(ln(xl, yt, xl, yk))
        # left diagonal (outward-downward)
        lines.append(ln(xl, yk, lx, yb))

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

    elif shape == "S6":
        # S6: hand-drawn sketch (user-provided, already bolded)
        s6_png_uri = "data:image/png;base64,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gAABAgQIECBAYBMCgq5NjNGTIECAAAECBAgQIECAAAECBAgQEHR5DRAgQIAAAQIECBAgQIAAAQIECGxCQNC1iTF6EgQIECBAgAABAgQIECBAgAABAoIurwECBAgQIECAAAECBAgQIECAAIFNCAi6NjFGT4IAAQIECBAgQIAAAQIECBAgQEDQ5TVAgAABAgQIECBAgAABAgQIECCwCQFB1ybG6EkQIECAAAECBAgQIECAAAECBAgIurwGCBAgQIAAAQIECBAgQIAAAQIENiEg6NrEGD0JAgQIECBAgAABAgQIECBAgAABQZfXAAECBAgQIECAAAECBAgQIECAwCYEBF2bGKMnQYAAAQIECBAgQIAAAQIECBAgIOjyGiBAgAABAgQIECBAgAABAgQIENiEgKBrE2P0JAgQIECAAAECBAgQIECAAAECBARdXgMECBAgQIAAAQIECBAgQIAAAQKbEBB0bWKMngQBAgQIECBAgAABAgQIECBAgICgy2uAAAECBAgQIECAAAECBAgQIEBgEwKCrk2M0ZMgQIAAAQIECBAgQIAAAQIECBAQdHkNECBAgAABAgQIECBAgAABAgQIbEJA0LWJMXoSBAgQIECAAAECBAgQIECAAAECgi6vAQIECBAgQIAAAQIECBAgQIAAgU0ICLo2MUZPggABAgQIECBAgAABAgQIECBAQNDlNUCAAAECBAgQIECAAAECBAgQILAJAUHXJsboSRAgQIAAAQIECBAgQIAAAQIECAi6vAYIECBAgAABAgQIECBAgAABAgQ2ISDo2sQYPQkCBAgQIECAAAECBAgQIECAAAFBl9cAAQIECBAgQIAAAQIECBAgQIDAJgQEXZsYoydBgAABAgQIECBAgAABAgQIECAg6PIaIECAAAECBAgQIECAAAECBAgQ2ISAoGsTY/QkCBAgQIAAAQIECBAgQIAAAQIEBF1eAwQIECBAgAABAgQIECBAgAABApsQEHRtYoyeBAECBAgQIECAAAECBAgQIECAgKDLa4AAAQIECBAgQIAAAQIECBAgQGATAoKuTYzRkyBAgAABAgQIECBAgAABAgQIEBB0eQ0QIECAAAECBAgQIECAAAECBAhsQkDQtYkxehIECBAgQIAAAQIECBAgQIAAAQKCLq8BAgQIECBAgAABAgQIECBAgACBTQgIujYxRk+CAAECBAgQ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YWC7J0CAAAECBAgQIECAAAECBAgQWEdA0LWOs0chQIAAAQIECBAgQIAAAQIECBBYWEDQtTCw3RMgQIAAAQIECBAgQIAAAQIECKwjIOhax9mjECBAgAABAgQIECBAgAABAgQILCwg6FoY2O4JECBAgAABAgQIECBAgAABAgTWERB0rePsUQgQIECAAAECBAgQIECAAAECBBYWEHQtDGz3BAgQIECAAAECBAgQIECAAAEC6wgIutZx9igECBAgQIAAAQIECBAgQIAAAQILCwi6Fga2ewIECBAgQIAAAQIECBAgQIAAgXUEBF3rOHsUAgQIECBAgAABAgQIECBAgACBhQUEXQsD2z0BAgQIECBAgAABAgQIECBAgMA6AoKudZw9CgECBAgQIECAAAECBAgQIECAwMICgq6Fge2eAAECBAgQIECAAAECBAgQIEBgHQFB1zrOHoUAAQIECBAgQIAAAQIECBAgQGBhAUHXwsB2T4AAAQIECBAgQIAAAQIECBAgsI6AoGsdZ49CgAABAgQIECBAgAABAgQIECCwsICga2FguydAgAABAgQIECBAgAABAgQIEFhHQNC1jrNHIUCAAAECBAgQIECAAAECBAgQWFhA0LUwsN0TIECAAAECBAgQIECAAAECBAisIyDoWsfZoxAgQIAAAQIECBAgQIAAAQIECCwsIOhaGNjuCRAgQIAAAQIECBAgQIAAAQIE1hEQdK3j7FEIECBAgAABAgQIECBAgAABAgQWFhB0LQxs9wQIECBAgAABAgQIECBAgAABAusICLrWcfYoBAgQIECAAAECBAgQIECAAAECCwsIuhYGtnsCBAgQIECAAAECBAgQIECAAIF1BARd6zh7FAIECBAgQIAAAQIECBAgQIAAgYUFBF0LA9s9AQIECBAgQIAAAQIECBAgQIDAOgKCrnWcPQoBAgQIECBAgAABAgQIECBAgMDCAoKuhYHtngABAgQIECBAgAABAgQIECBAYB0BQdc6zh6FAAECBAgQIECAAAECBAgQIEBgYQFB18LAdk+AAAECBAgQIECAAAECBAgQILCOgKBrHWePQoAAAQIECBAgQIAAAQIECBAgsLCAoGthYLsnQIAAAQIECBAgQIAAAQIECBBYR0DQtY6zRyFAgAABAgQIECBAgAABAgQIEFhYQNC1MLDdEyBAgAABAgQIECBAgAABAgQIrCMg6FrH2aMQIECAAAECBAgQIECAAAECBAgsLCDoWhjY7gkQIECAAAECBAgQIECAAAECBNYREHSt4+xRCBAgQIAAAQIECBAgQIAAAQIEFhYQdC0MbPcECBAgQIAAAQIECBAgQIAAAQLrCAi61nH2KAQIECBAgAABAgQIECBAgAABAgsLCLoWBrZ7AgQIECBAgAABAgQIECBAgACBdQQEXes4exQCBAgQIECAAAECBAgQIECAAIGFBQRdCwPbPQECBAgQIECAAAECBAgQIECAwDoCgq51nD0KAQIECBAgQIAAAQIECBAgQIDAwgKCroWB7Z4AAQIECBAgQIAAAQIECBAgQGAdAUHXOs4ehQABAgQIECBAgAABAgQIECBAYGEBQdfCwHZPgAABAgQIECBAgAABAgQIECCwjoCgax1nj0KAAAECBAgQIECAAAECBAgQILCwgKBrYWC7J0CAAAECBAgQIECAAAECBAgQWEdA0LWOs0chQIAAAQIECBAgQIAAAQIECBBYWEDQtTCw3RMgQIAAAQIECBAgQIAAAQIECKwjIOhax9mjECBAgAABAgQIECBAgAABAgQILCwg6FoY2O4JECBAgAABAgQIECBAgAABAgTWERB0rePsUQgQIECAAAECBAgQIECAAAECBBYWEHQtDGz3BAgQIECAAAECBAgQIECAAAEC6wgIutZx9igECBAgQIAAAQIECBAgQIAAAQILCwi6Fga2ewIECBAgQIAAAQIECBAgQIAAgXUEBF3rOHsUAgQIECBAgAABAgQIECBAgACBhQUEXQsD2z0BAgQIECBAgAABAgQIECBAgMA6AoKudZw9CgECBAgQIECAAAECBAgQIECAwMICgq6Fge2eAAECBAgQIECAAAECBAgQIEBgHQFB1zrOHoUAAQIECBAgQIAAAQIECBAgQGBhAUHXwsB2T4AAAQIECBAgQIAAAQIECBAgsI6AoGsdZ49CgAABAgQIECBAgAABAgQIECCwsICga2FguydAgAABAgQIECBAgAABAgQIEFhHQNC1jrNHIUCAAAECBAgQIECAAAECBAgQWFhA0LUwsN0TIECAAAECBAgQIECAAAECBAisIyDoWsfZoxAgQIAAAQIECBAgQIAAAQIECCwsIOhaGNjuCRAgQIAAAQIECBAgQIAAAQIE1hEQdK3j7FEIECBAgAABAgQIECBAgAABAgQWFhB0LQxs9wQIECBAgAABAgQIECBAgAABAusICLrWcfYoBAgQIECAAAECBAgQIECAAAECCwsIuhYGtnsCBAgQIECAAAECBAgQIECAAIF1BARd6zh7FAIECBAgQIAAAQIECBAgQIAAgYUFBF0LA9s9AQIECBAgQIAAAQIECBAgQIDAOgKCrnWcPQoBAgQIECBAgAABAgQIECBAgMDCAoKuhYHtngABAgQIECBAgAABAgQIECBAYB0BQdc6zh6FAAECBAgQIECAAAECBAgQIEBgYQFB18LAdk+AAAECBAgQIECAAAECBAgQILCOgKBrHWePQoAAAQIECBAgQIAAAQIECBAgsLDA+YX3b/cECBAgQIAAAQIECBAgsHGBT58+Tdk+fvz4+Tpfj238/CiGM2fOTNnOnj37P9v4Wa5dCBAgcBwBQddxlNyHAAECBAgQIECAAAECBI4UGAHXb7/9NmV7//799O7du89bvs/tud9Rl4RY58+fn7777rvp4sWL85avs+X2c+fOzQGYsOsoPbcRIHBYQNB1WMT3BAgQIECAAAECBAgQIHBsgQRYCbLevn07/fLLL9ObN2+m169fT69evZpevnw5f5/gK/c56pIwKwHXlStXpps3b07Xrl2bt8uXL0+XLl2aLly4MK/4EnQdpec2AgQOCwi6Dov4ngABAgQIECBAgAABAgSOLZDTExNiJeR6/vz59OzZs+nx48fTo0ePpocPH87fJ/TKyq6jLgmyEm7duXNnevDgwXT//v3561u3bs13zymNWdXlQoAAgeMICLqOo+Q+BAgQIECAAAECBAgQIHCkwO6Krqzkevr06Rxw/etf/5r+8Y9/zF+/ePFi+vXXX4+sz6qthFoJuRKYZeVWgq0EYONUxi+d9njkDt1IgMCpFhB0nerxe/IECBAgQIAAAQIECBDYTyAhVFZ1ZcVWVnVl9VZWdR0cHEw//fTTvCX8+lLQlVMUU5P9ZGXX9evXpxs3bsynQib4yr4FXfvNSDWB0yQg6DpN0/ZcCRAgQIAAAQIECBAgsIBAwqgPHz7812d1ZXVXTmVMyJUtIdhRlwRdOT0xAVdqEoiNz/QSch0l5jYCBL4mIOj6mo6fESBAgAABAgQIECBAgMCxBRJMjS3B19iy2utLn9GVv66YlVvjvqM+q7is5Do2vTsSIPD/AoIuLwUCBAgQIECAAAECBAgQ+N0CI5AaoVSuR1iV6xFg5fqoy+7PR93uPsfXR9W6jQABAocFBF2HRXxPgAABAgQIECBAgAABAr9LYIRSh8OuEXgdtdMEXV8KuI66v9sIECDwNQFB19d0/IwAAQIECBAgQIAAAQIEygK7gdfu10ftaPz8qJ+5jQABAlWBs9UC9ydAgAABAgQIECBAgAABAgQIECDQUUDQ1XEqeiJAgAABAgQIECBAgAABAgQIECgLCLrKZAoIECBAgAABAgQIECBAgAABAgQ6Cgi6Ok5FTwQIECBAgAABAgQIECBAgAABAmUBQVeZTAEBAgQIECBAgAABAgQIECBAgEBHAUFXx6noiQABAgQIECBAgAABAgQIECBAoCwg6CqTKSBAgAABAgQIECBAgAABAgQIEOgoIOjqOBU9ESBAgAABAgQIECBAgAABAgQIlAUEXWUyBQQIECBAgAABAgQIECBAgAABAh0FBF0dp6InAgQIECBAgAABAgQIECBAgACBsoCgq0ymgAABAgQIECBAgAABAgQIECBAoKOAoKvjVPREgAABAgQIECBAgAABAgQIECBQFhB0lckUECBAgAABAgQIECBAgAABAgQIdBQQdHWcip4IECBAgAABAgQIECBAgAABAgTKAoKuMpkCAgQIECBAgAABAgQIECBAgACBjgKCro5T0RMBAgQIECBAgAABAgQIECBAgEBZQNBVJlNAgAABAgQIECBAgAABAgQIECDQUUDQ1XEqeiJAgAABAgQIECBAgAABAgQIECgLCLrKZAoIECBAgAABAgQIECBAgAABAgQ6Cgi6Ok5FTwQIECBAgAABAgQIECBAgAABAmUBQVeZTAEBAgQIECBAgAABAgQIECBAgEBHAUFXx6noiQABAgQIECBAgAABAgQIECBAoCwg6CqTKSBAgAABAgQIECBAgAABAgQIEOgoIOjqOBU9ESBAgAABAgQIECBAgAABAgQIlAUEXWUyBQQIECBAgAABAgQIECBAgAABAh0FBF0dp6InAgQIECBAgAABAgQIECBAgACBsoCgq0ymgAABAgQIECBAgAABAgQIECBAoKOAoKvjVPREgAABAgQIECBAgAABAgQIECBQFhB0lckUECBAgAABAgQIECBAgAABAgQIdBQQdHWcip4IECBAgAABAgQIECBAgAABAgTKAoKuMpkCAgQIECBAgAABAgQIECBAgACBjgKCro5T0RMBAgQIECBAgAABAgQIECBAgEBZQNBVJlNAgAABAgQIECBAgAABAgQIECDQUUDQ1XEqeiJAgAABAgQIECBAgAABAgQIECgLCLrKZAoIECBAgAABAgQIECBAgAABAgQ6Cgi6Ok5FTwQIECBAgAABAgQIECBAgAABAmUBQVeZTAEBAgQIECBAgAABAgQIECBAgEBHAUFXx6noiQABAgQIECBAgAABAgQIECBAoCwg6CqTKSBAgAABAgQIECBAgAABAgQIEOgoIOjqOBU9ESBAgAABAgQIECBAgAABAgQIlAUEXWUyBQQIECBAgAABAgQIECBAgAABAh0FBF0dp6InAgQIECBAgAABAgQIECBAgACBsoCgq0ymgAABAgQIECBAgAABAgQIECBAoKOAoKvjVPREgAABAgQIECBAgAABAgQIECBQFhB0lckUECBAgAABAgQIECBAgAABAgQIdBQQdHWcip4IECBAgAABAgQIECBAgAABAgTKAoKuMpkCAgQIECBAgAABAgQIECBAgACBjgKCro5T0RMBAgQIECBAgAABAgQIECBAgEBZQNBVJlNAgAABAgQIECBAgAABAgQIECDQUUDQ1XEqeiJAgAABAgQIECBAgAABAgQIECgLCLrKZAoIECBAgAABAgQIECBAgAABAgQ6Cgi6Ok5FTwQIECBAgAABAgQIECBAgAABAmUBQVeZTAEBAgQIECBAgAABAgQIECBAgEBHAUFXx6noiQABAgQIECBAgAABAgQIECBAoCwg6CqTKSBAgAABAgQIECBAgAABAgQIEOgoIOjqOBU9ESBAgAABAgQIECBAgAABAgQIlAUEXWUyBQQIECBAgAABAgQIECBAgAABAh0FBF0dp6InAgQIECBAgAABAgQIECBAgACBsoCgq0ymgAABAgQIECBAgAABAgQIECBAoKOAoKvjVPREgAABAgQIECBAgAABAgQIECBQFhB0lckUECBAgAABAgQIECBAgAABAgQIdBQQdHWcip4IECBAgAABAgQIECBAgAABAgTKAoKuMpkCAgQIECBAgAABAgQIECBAgACBjgKCro5T0RMBAgQIECBAgAABAgQIECBAgEBZQNBVJlNAgAABAgQIECBAgAABAgQIECDQUUDQ1XEqeiJAgAABAgQIECBAgAABAgQIECgLCLrKZAoIECBAgAABAgQIECBAgAABAgQ6Cgi6Ok5FTwQIECBAgAABAgQIECBAgAABAmUBQVeZTAEBAgQIECBAgAABAgQIECBAgEBHAUFXx6noiQABAgQIECBAgAABAgQIECBAoCwg6CqTKSBAgAABAgQIECBAgAABAgQIEOgoIOjqOBU9ESBAgAABAgQIECBAgAABAgQIlAUEXWUyBQQIECBAgAABAgQIECBAgAABAh0FBF0dp6InAgQIECBAgAABAgQIECBAgACBsoCgq0ymgAABAgQIECBAgAABAgQIECBAoKOAoKvjVPREgAABAgQIECBAgAABAgQIECBQFhB0lckUECBAgAABAgQIECBAgAABAgQIdBQQdHWcip4IECBAgAABAgQIECBAgAABAgTKAoKuMpkCAgQIECBAgAABAgQIECBAgACBjgKCro5T0RMBAgQIECBAgAABAgQIECBAgEBZQNBVJlNAgAABAgQIECBAgAABAgQIECDQUUDQ1XEqeiJAgAABAgQIECBAgAABAgQIECgLCLrKZAoIECBAgAABAgQIECBAgAABAgQ6Cgi6Ok5FTwQIECBAgAABAgQIECBAgAABAmUBQVeZTAEBAgQIECBAgAABAgQIECBAgEBHAUFXx6noiQABAgQIECBAgAABAgQIECBAoCwg6CqTKSBAgAABAgQIECBAgAABAgQIEOgoIOjqOBU9ESBAgAABAgQIECBAgAABAgQIlAUEXWUyBQQIECBAgAABAgQIECBAgAABAh0FBF0dp6InAgQIECBAgAABAgQIECBAgACBsoCgq0ymgAABAgQIECBAgAABAgQIECBAoKOAoKvjVPREgAABAgQIECBAgAABAgQIECBQFhB0lckUECBAgAABAgQIECBAgAABAgQIdBQQdHWcip4IECBAgAABAgQIECBAgAABAgTKAoKuMpkCAgQIECBAgAABAgQIECBAgACBjgKCro5T0RMBAgQIECBAgAABAgQIECBAgEBZQNBVJlNAgAABAgQIECBAgAABAgQIECDQUUDQ1XEqeiJAgAABAgQIECBAgAABAgQIECgLCLrKZAoIECBAgAABAgQIECBAgAABAgQ6Cgi6Ok5FTwQIECBAgAABAgQIECBAgAABAmUBQVeZTAEBAgQIECBAgAABAgQIECBAgEBHAUFXx6noiQABAgQIECBAgAABAgQIECBAoCwg6CqTKSBAgAABAgQIECBAgAABAgQIEOgoIOjqOBU9ESBAgAABAgQIECBAgAABAgQIlAUEXWUyBQQIECBAgAABAgQIECBAgAABAh0FBF0dp6InAgQIECBAgAABAgQIECBAgACBsoCgq0ymgAABAgQIECBAgAABAgQIECBAoKOAoKvjVPREgAABAgQIECBAgAABAgQIECBQFhB0lckUECBAgAABAgQIECBAgAABAgQIdBQQdHWcip4IECBAgAABAgQIECBAgAABAgTKAoKuMpkCAgQIECBAgAABAgQIECBAgACBjgKCro5T0RMBAgQIECBAgAABAgQIECBAgEBZQNBVJlNAgAABAgQIECBAgAABAgQIECDQUUDQ1XEqeiJAgAABAgQIECBAgAABAgQIECgLCLrKZAoIECBAgAABAgQIECBAgAABAgQ6Cgi6Ok5FTwQIECBAgAABAgQIECBAgAABAmUBQVeZTAEBAgQIECBAgAABAgQIECBAgEBHAUFXx6noiQABAgQIECBAgAABAgQIECBAoCwg6CqTKSBAgAABAgQIECBAgAABAgQIEOgoIOjqOBU9ESBAgAABAgQIECBAgAABAgQIlAUEXWUyBQQIECBAgAABAgQIECBAgAABAh0FBF0dp6InAgQIECBAgAABAgQIECBAgACBsoCgq0ymgAABAgQIECBAgAABAgQIECBAoKOAoKvjVPREgAABAgQIECBAgAABAgQIECBQFhB0lckUECBAgAABAgQIECBAgAABAgQIdBQQdHWcip4IECBAgAABAgQIECBAgAABAgTKAoKuMpkCAgQIECBAgAABAgQIECBAgACBjgKCro5T0RMBAgQIECBAgAABAgQIECBAgEBZQNBVJlNAgAABAgQIECBAgAABAgQIECDQUUDQ1XEqeiJAgAABAgQIECBAgAABAgQIECgLCLrKZAoIECBAgAABAgQIECBAgAABAgQ6Cgi6Ok5FTwQIECBAgAABAgQIECBAgAABAmUBQVeZTAEBAgQIECBAgAABAgQIECBAgEBHAUFXx6noiQABAgQIECBAgAABAgQIECBAoCwg6CqTKSBAgAABAgQIECBAgAABAgQIEOgoIOjqOBU9ESBAgAABAgQIECBAgAABAgQIlAUEXWUyBQQIECBAgAABAgQIECBAgAABAh0FBF0dp6InAgQIECBAgAABAgQIECBAgACBsoCgq0ymgAABAgQIECBAgAABAgQIECBAoKOAoKvjVPREgAABAgQIECBAgAABAgQIECBQFhB0lckUECBAgAABAgQIECBAgAABAgQIdBQQdHWcip4IECBAgAABAgQIECBAgAABAgTKAoKuMpkCAgQIECBAgAABAgQIECBAgACBjgKCro5T0RMBAgQIECBAgAABAgQIECBAgEBZQNBVJlNAgAABAgQIECBAgAABAgQIECDQUUDQ1XEqeiJAgAABAgQIECBAgAABAgQIECgLCLrKZAoIECBAgAABAgQIECBAgAABAgQ6Cgi6Ok5FTwQIECBAgAABAgQIECBAgAABAmUBQVeZTAEBAgQIECBAgAABAgQIECBAgEBHAUFXx6noiQABAgQIECBAgAABAgQIECBAoCwg6CqTKSBAgAABAgQIECBAgAABAgQIEOgoIOjqOBU9ESBAgAABAgQIECBAgAABAgQIlAUEXWUyBQQIECBAgAABAgQIECBAgAABAh0FBF0dp6InAgQIECBAgAABAgQIECBAgACBsoCgq0ymgAABAgQIECBAgAABAgQIECBAoKOAoKvjVPREgAABAgQIECBAgAABAgQIECBQFhB0lckUECBAgAABAgQIECBAgAABAgQIdBQQdHWcip4IECBAgAABAgQIECBAgAABAgTKAoKuMpkCAgQIECBAgAABAgQIECBAgACBjgKCro5T0RMBAgQIECBAgAABAgQIECBAgEBZQNBVJlNAgAABAgQIECBAgAABAgQIECDQUUDQ1XEqeiJAgAABAgQIECBAgAABAgQIECgLCLrKZAoIECBAgAABAgQIECBAgAABAgQ6Cgi6Ok5FTwQIECBAgAABAgQIECBAgAABAmUBQVeZTAEBAgQIECBAgAABAgQIECBAgEBHAUFXx6noiQABAgQIECBAgAABAgQIECBAoCwg6CqTKSBAgAABAgQIECBAgAABAgQIEOgoIOjqOBU9ESBAgAABAgQIECBAgAABAgQIlAUEXWUyBQQIECBAgAABAgQIECBAgAABAh0FBF0dp6InAgQIECBAgAABAgQIECBAgACBsoCgq0ymgAABAgQIECBAgAABAgQIECBAoKOAoKvjVPREgAABAgQIECBAgAABAgQIECBQFhB0lckUECBAgAABAgQIECBAgAABAgQIdBQQdHWcip4IECBAgAABAgQIECBAgAABAgTKAoKuMpkCAgQIECBAgAABAgQIECBAgACBjgKCro5T0RMBAgQIECBAgAABAgQIECBAgEBZQNBVJlNAgAABAgQIECBAgAABAgQIECDQUUDQ1XEqeiJAgAABAgQIECBAgAABAgQIECgLCLrKZAoIECBAgAABAgQIECBAgAABAgQ6Cgi6Ok5FTwQIECBAgAABAgQIECBAgAABAmUBQVeZTAEBAgQIECBAgAABAgQIECBAgEBHAUFXx6noiQABAgQIECBAgAABAgQIECBAoCwg6CqTKSBAgAABAgQIECBAgAABAgQIEOgoIOjqOBU9ESBAgAABAgQIECBAgAABAgQIlAUEXWUyBQQIECBAgAABAgQIECBAgAABAh0FBF0dp6InAgQIECBAgAABAgQIECBAgACBsoCgq0ymgAABAgQIECBAgAABAgQIECBAoKOAoKvjVPREgAABAgQIECBAgAABAgQIECBQFhB0lckUECBAgAABAgQIECBAgAABAgQIdBQQdHWcip4IECBAgAABAgQIECBAgAABAgTKAoKuMpkCAgQIECBAgAABAgQIECBAgACBjgKCro5T0RMBAgQIECBAgAABAgQIECBAgEBZQNBVJlNAgAABAgQIECBAgAABAgQIECDQUUDQ1XEqeiJAgAABAgQIECBAgAABAgQIECgLCLrKZAoIECBAgAABAgQIECBAgAABAgQ6Cgi6Ok5FTwQIECBAgAABAgQIECBAgAABAmUBQVeZTAEBAgQIECBAgAABAgQIECBAgEBHAUFXx6noiQABAgQIECBAgAABAgQIECBAoCwg6CqTKSBAgAABAgQIECBAgAABAgQIEOgoIOjqOBU9ESBAgAABAgQIECBAgAABAgQIlAUEXWUyBQQIECBAgAABAgQIECBAgAABAh0FBF0dp6InAgQIECBAgAABAgQIECBAgACBsoCgq0ymgAABAgQIECBAgAABAgQIECBAoKOAoKvjVPREgAABAgQIECBAgAABAgQIECBQFhB0lckUECBAgAABAgQIECBAgAABAgQIdBQQdHWcip4IECBAgAABAgQIECBAgAABAgTKAoKuMpkCAgQIECBAgAABAgQIECBAgACBjgKCro5T0RMBAgQIECBAgAABAgQIECBAgEBZQNBVJlNAgAABAgQIECBAgAABAgQIECDQUUDQ1XEqeiJAgAABAgQIECBAgAABAgQIECgLCLrKZAoIECBAgAABAgQIECBAgAABAgQ6Cgi6Ok5FTwQIECBAgAABAgQIECBAgAABAmUBQVeZTAEBAgQIECBAgAABAgQIECBAgEBHAUFXx6noiQABAgQIECBAgAABAgQIECBAoCwg6CqTKSBAgAABAgQIECBAgAABAgQIEOgoIOjqOBU9ESBAgAABAgQIECBAgAABAgQIlAUEXWUyBQQIECBAgAABAgQIECBAgAABAh0FBF0dp6InAgQIECBAgAABAgQIECBAgACBsoCgq0ymgAABAgQIECBAgAABAgQIECBAoKOAoKvjVPREgAABAgQIECBAgAABAgQIECBQFhB0lckUECBAgAABAgQIECBAgAABAgQIdBQQdHWcip4IECBAgAABAgQIECBAgAABAgTKAoKuMpkCAgQIECBAgAABAgQIECBAgACBjgKCro5T0RMBAgQIECBAgAABAgQIECBAgEBZQNBVJlNAgAABAgQIECBAgAABAgQIECDQUUDQ1XEqeiJAgAABAgQIECBAgAABAgQIECgLCLrKZAoIECBAgAABAgQIECBAgAABAgQ6Cgi6Ok5FTwQIECBAgAABAgQIECBAgAABAmUBQVeZTAEBAgQIECBAgAABAgQIECBAgEBHAUFXx6noiQABAgQIECBAgAABAgQIECBAoCwg6CqTKSBAgAABAgQIECBAgAABAgQIEOgoIOjqOBU9ESBAgAABAgQIECBAgAABAgQIlAUEXWUyBQQIECBAgAABAgQIECBAgAABAh0FBF0dp6InAgQIECBAgAABAgQIECBAgACBsoCgq0ymgAABAgQIECBAgAABAgQIECBAoKOAoKvjVPREgAABAgQIECBAgAABAgQIECBQFhB0lckUECBAgAABAgQIECBAgAABAgQIdBQQdHWcip4IECBAgAABAgQIECBAgAABAgTKAoKuMpkCAgQIECBAgAABAgQIECBAgACBjgKCro5T0RMBAgQIECBAgAABAgQIECBAgEBZQNBVJlNAgAABAgQIECBAgAABAgQIECDQUUDQ1XEqeiJAgAABAgQIECBAgAABAgQIECgLCLrKZAoIECBAgAABAgQIECBAgAABAgQ6Cgi6Ok5FTwQIECBAgAABAgQIECBAgAABAmUBQVeZTAEBAgQIECBAgAABAgQIECBAgEBHAUFXx6noiQABAgQIECBAgAABAgQIECBAoCwg6CqTKSBAgAABAgQIECBAgAABAgQIEOgoIOjqOBU9ESBAgAABAgQIECBAgAABAgQIlAUEXWUyBQQIECBAgAABAgQIECBAgAABAh0FBF0dp6InAgQIECBAgAABAgQIECBAgACBsoCgq0ymgAABAgQIECBAgAABAgQIECBAoKOAoKvjVPREgAABAgQIECBAgAABAgQIECBQFhB0lckUECBAgAABAgQIECBAgAABAgQIdBQQdHWcip4IECBAgAABAgQIECBAgAABAgTKAoKuMpkCAgQIECBAgAABAgQIECBAgACBjgKCro5T0RMBAgQIECBAgAABAgQIECBAgEBZQNBVJlNAgAABAgQIECBAgAABAgQIECDQUUDQ1XEqeiJAgAABAgQIECBAgAABAgQIECgLCLrKZAoIECBAgAABAgQIECBAgAABAgQ6Cgi6Ok5FTwQIECBAgAABAgQIECBAgAABAmUBQVeZTAEBAgQIECBAgAABAgQIECBAgEBHAUFXx6noiQABAgQIECBAgAABAgQIECBAoCwg6CqTKSBAgAABAgQIECBAgAABAgQIEOgoIOjqOBU9ESBAgAABAgQIECBAgAABAgQIlAUEXWUyBQQIECBAgAABAgQIECBAgAABAh0FBF0dp6InAgQIECBAgAABAgQIECBAgACBsoCgq0ymgAABAgQIECBAgAABAgQIECBAoKOAoKvjVPREgAABAgQIECBAgAABAgQIECBQFhB0lckUECBAgAABAgQIECBAgAABAgQIdBQQdHWcip4IECBAgAABAgQIECBAgAABAgTKAoKuMpkCAgQIECBAgAABAgQIECBAgACBjgKCro5T0RMBAgQIECBAgAABAgQIECBAgEBZQNBVJlNAgAABAgQIECBAgAABAgQIECDQUUDQ1XEqeiJAgAABAgQIECBAgAABAgQIECgLCLrKZAoIECBAgAABAgQIECBAgAABAgQ6Cgi6Ok5FTwQIECBAgAABAgQIECBAgAABAmUBQVeZTAEBAgQIECBAgAABAgQIECBAgEBHAUFXx6noiQABAgQIECBAgAABAgQIECBAoCwg6CqTKSBAgAABAgQIECBAgAABAgQIEOgoIOjqOBU9ESBAgAABAgQIECBAgAABAgQIlAUEXWUyBQQIECBAgAABAgQIECBAgAABAh0FBF0dp6InAgQIECBAgAABAgQIECBAgACBsoCgq0ymgAABAgQIECBAgAABAgQIECBAoKOAoKvjVPREgAABAgQIECBAgAABAgQIECBQFhB0lckUECBAgAABAgQIECBAgAABAgQIdBQQdHWcip4IECBAgAABAgQIECBAgAABAgTKAoKuMpkCAgQIECBAgAABAgQIECBAgACBjgKCro5T0RMBAgQIECBAgAABAgQIECBAgEBZQNBVJlNAgAABAgQIECBAgAABAgQIECDQUUDQ1XEqeiJAgAABAgQIECBAgAABAgQIECgLCLrKZAoIECBAgAABAgQIECBAgAABAgQ6Cgi6Ok5FTwQIECBAgAABAgQIECBAgAABAmUBQVeZTAEBAgQIECBAgAABAgQIECBAgEBHAUFXx6noiQABAgQIECBAgAABAgQIECBAoCwg6CqTKSBAgAABAgQIECBAgAABAgQIEOgoIOjqOBU9ESBAgAABAgQIECBAgAABAgQIlAUEXWUyBQQIECBAgAABAgQIECBAgAABAh0FBF0dp6InAgQIECBAgAABAgQIECBAgACBsoCgq0ymgAABAgQIECBAgAABAgQIECBAoKOAoKvjVPREgAABAgQIECBAgAABAgQIECBQFhB0lckUECBAgAABAgQIECBAgAABAgQIdBQQdHWcip4IECBAgAABAgQIECBAgAABAgTKAoKuMpkCAgQIECBAgAABAgQIECBAgACBjgKCro5T0RMBAgQIECBAgAABAgQIECBAgEBZQNBVJlNAgAABAgQIECBAgAABAgQIECDQUUDQ1XEqeiJAgAABAgQIECBAgAABAgQIECgLCLrKZAoIECBAgAABAgQIECBAgAABAgQ6Cgi6Ok5FTwQIECBAgAABAgQIECBAgAABAmUBQVeZTAEBAgQIECBAgAABAgQIECBAgEBHAUFXx6noiQABAgQIECBAgAABAgQIECBAoCwg6CqTKSBAgAABAgQIECBAgAABAgQIEOgoIOjqOBU9ESBAgAABAgQIECBAgAABAgQIlAUEXWUyBQQIECBAgAABAgQIECBAgAABAh0FBF0dp6InAgQIECBAgAABAgQIECBAgACBsoCgq0ymgAABAgQIECBAgAABAgQIECBAoKOAoKvjVPREgAABAgQIECBAgAABAgQIECBQFhB0lckUECBAgAABAgQIECBAgAABAgQIdBQQdHWcip4IECBAgAABAgQIECBAgAABAgTKAoKuMpkCAgQIECBAgAABAgQIECBAgACBjgKCro5T0RMBAgQIECBAgAABAgQIECBAgEBZQNBVJlNAgAABAgQIECBAgAABAgQIECDQUUDQ1XEqeiJAgAABAgQIECBAgAABAgQIECgLCLrKZAoIECBAgAABAgQIECBAgAABAgQ6Cgi6Ok5FTwQIECBAgAABAgQIECBAgAABAmUBQVeZTAEBAgQIECBAgAABAgQIECBAgEBHAUFXx6noiQABAgQIECBAgAABAgQIECBAoCwg6CqTKSBAgAABAgQIECBAgAABAgQIEOgoIOjqOBU9ESBAgAABAgQIECBAgAABAgQIlAUEXWUyBQQIECBAgAABAgQIECBAgAABAh0FBF0dp6InAgQIECBAgAABAgQIECBAgACBsoCgq0ymgAABAgQIECBAgAABAgQIECBAoKOAoKvjVPREgAABAgQIECBAgAABAgQIECBQFhB0lckUECBAgAABAgQIECBAgAABAgQIdBQQdHWcip4IECBAgAABAgQIECBAgAABAgTKAoKuMpkCAgQIECBAgAABAgQIECBAgACBjgKCro5T0RMBAgQIECBAgAABAgQIECBAgEBZQNBVJlNAgAABAgQIECBAgAABAgQIECDQUUDQ1XEqeiJAgAABAgQIECBAgAABAgQIECgLCLrKZAoIECBAgAABAgQIECBAgAABAgQ6Cgi6Ok5FTwQIECBAgAABAgQIECBAgAABAmUBQVeZTAEBAgQIECBAgAABAgQIECBAgEBHAUFXx6noiQABAgQIECBAgAABAgQIECBAoCwg6CqTKSBAgAABAgQIECBAgAABAgQIEOgoIOjqOBU9ESBAgAABAgQIECBAgAABAgQIlAUEXWUyBQQIECBAgAABAgQIECBAgAABAh0FBF0dp6InAgQIECBAgAABAgQIECBAgACBsoCgq0ymgAABAgQIECBAgAABAgQIECBAoKOAoKvjVPREgAABAgQIECBAgAABAgQIECBQFhB0lckUECBAgAABAgQIECBAgAABAgQIdBQQdHWcip4IECBAgAABAgQIECBAgAABAgTKAoKuMpkCAgQIECBAgAABAgQIECBAgACBjgKCro5T0RMBAgQIECBAgAABAgQIECBAgEBZQNBVJlNAgAABAgQIECBAgAABAgQIECDQUUDQ1XEqeiJAgAABAgQIECBAgAABAgQIECgLCLrKZAoIECBAgAABAgQIECBAgAABAgQ6Cgi6Ok5FTwQIECBAgAABAgQIECBAgAABAmUBQVeZTAEBAgQIECBAgAABAgQIECBAgEBHAUFXx6noiQABAgQIECBAgAABAgQIECBAoCwg6CqTKSBAgAABAgQIECBAgAABAgQIEOgoIOjqOBU9ESBAgAABAgQIECBAgAABAgQIlAUEXWUyBQQIECBAgAABAgQIECBAgAABAh0FBF0dp6InAgQIECBAgAABAgQIECBAgACBsoCgq0ymgAABAgQIECBAgAABAgQIECBAoKOAoKvjVPREgAABAgQIECBAgAABAgQIECBQFhB0lckUECBAgAABAgQIECBAgAABAgQIdBQQdHWcip4IECBAgAABAgQIECBAgAABAgTKAoKuMpkCAgQIECBAgAABAgQIECBAgACBjgKCro5T0RMBAgQIECBAgAABAgQIECBAgEBZQNBVJlNAgAABAgQIECBAgAABAgQIECDQUUDQ1XEqeiJAgAABAgQIECBAgAABAgQIECgLCLrKZAoIECBAgAABAgQIECBAgAABAgQ6Cgi6Ok5FTwQIECBAgAABAgQIECBAgAABAmUBQVeZTAEBAgQIECBAgAABAt9mNlEAACFiSURBVAQIECBAgEBHAUFXx6noiQABAgQIECBAgAABAgQIECBAoCwg6CqTKSBAgAABAgQIECBAgAABAgQIEOgoIOjqOBU9ESBAgAABAgQIECBAgAABAgQIlAUEXWUyBQQIECBAgAABAgQIECBAgAABAh0FBF0dp6InAgQIECBAgAABAgQIECBAgACBsoCgq0ymgAABAgQIECBAgAABAgQIECBAoKOAoKvjVPREgAABAgQIECBAgAABAgQIECBQFhB0lckUECBAgAABAgQIECBAgAABAgQIdBQQdHWcip4IECBAgAABAgQIECBAgAABAgTKAoKuMpkCAgQIECBAgAABAgQIECBAgACBjgKCro5T0RMBAgQIECBAgAABAgQIECBAgEBZQNBVJlNAgAABAgQIECBAgAABAgQIECDQUUDQ1XEqeiJAgAABAgQIECBAgAABAgQIECgLCLrKZAoIECBAgAABAgQIECBAgAABAgQ6Cgi6Ok5FTwQIECBAgAABAgQIECBAgAABAmUBQVeZTAEBAgQIECBAgAABAgQIECBAgEBHAUFXx6noiQABAgQIECBAgAABAgQIECBAoCwg6CqTKSBAgAABAgQIECBAgAABAgQIEOgoIOjqOBU9ESBAgAABAgQIECBAgAABAgQIlAUEXWUyBQQIECBAgAABAgQIECBAgAABAh0FBF0dp6InAgQIECBAgAABAgQIECBAgACBsoCgq0ymgAABAgQIECBAgAABAgQIECBAoKOAoKvjVPREgAABAgQIECBAgAABAgQIECBQFhB0lckUECBAgAABAgQIECBAgAABAgQIdBQQdHWcip4IECBAgAABAgQIECBAgAABAgTKAoKuMpkCAgQIECBAgAABAgQIECBAgACBjgKCro5T0RMBAgQIECBAgAABAgQIECBAgEBZQNBVJlNAgAABAgQIECBAgAABAgQIECDQUUDQ1XEqeiJAgAABAgQIECBAgAABAgQIECgLCLrKZAoIECBAgAABAgQIECBAgAABAgQ6Cgi6Ok5FTwQIECBAgAABAgQIECBAgAABAmUBQVeZTAEBAgQIECBAgAABAgQIECBAgEBHAUFXx6noiQABAgQIECBAgAABAgQIECBAoCwg6CqTKSBAgAABAgQIECBAgAABAgQIEOgoIOjqOBU9ESBAgAABAgQIECBAgAABAgQIlAUEXWUyBQQIECBAgAABAgQIECBAgAABAh0FBF0dp6InAgQIECBAgAABAgQIECBAgACBsoCgq0ymgAABAgQIECBAgAABAgQIECBAoKOAoKvjVPREgAABAgQIECBAgAABAgQIECBQFhB0lckUECBAgAABAgQIECBAgAABAgQIdBQQdHWcip4IECBAgAABAgQIECBAgAABAgTKAoKuMpkCAgQIECBAgAABAgQIECBAgACBjgKCro5T0RMBAgQIECBAgAABAgQIECBAgEBZQNBVJlNAgAABAgQIECBAgAABAgQIECDQUUDQ1XEqeiJAgAABAgQIECBAgAABAgQIECgLCLrKZAoIECBAgAABAgQIECBAgAABAgQ6Cgi6Ok5FTwQIECBAgAABAgQIECBAgAABAmUBQVeZTAEBAgQIECBAgAABAgQIECBAgEBHAUFXx6noiQABAgQIECBAgAABAgQIECBAoCwg6CqTKSBAgAABAgQIECBAgAABAgQIEOgoIOjqOBU9ESBAgAABAgQIECBAgAABAgQIlAUEXWUyBQQIECBAgAABAgQIECBAgAABAh0FBF0dp6InAgQIECBAgAABAgQIECBAgACBsoCgq0ymgAABAgQIECBAgAABAgQIECBAoKOAoKvjVPREgAABAgQIECBAgAABAgQIECBQFhB0lckUECBAgAABAgQIECBAgAABAgQIdBQQdHWcip4IECBAgAABAgQIECBAgAABAgTKAoKuMpkCAgQIECBAgAABAgQIECBAgACBjgKCro5T0RMBAgQIECBAgAABAgQIECBAgEBZQNBVJlNAgAABAgQIECBAgAABAgQIECDQUUDQ1XEqeiJAgAABAgQIECBAgAABAgQIECgLCLrKZAoIECBAgAABAgQIECBAgAABAgQ6Cgi6Ok5FTwQIECBAgAABAgQIECBAgAABAmUBQVeZTAEBAgQIECBAgAABAgQIECBAgEBHAUFXx6noiQABAgQIECBAgAABAgQIECBAoCwg6CqTKSBAgAABAgQIECBAgAABAgQIEOgoIOjqOBU9ESBAgAABAgQIECBAgAABAgQIlAUEXWUyBQQIECBAgAABAgQIECBAgAABAh0FBF0dp6InAgQIECBAgAABAgQIECBAgACBsoCgq0ymgAABAgQIECBAgAABAgQIECBAoKOAoKvjVPREgAABAgQIECBAgAABAgQIECBQFhB0lckUECBAgAABAgQIECBAgAABAgQIdBQQdHWcip4IECBAgAABAgQIECBAgAABAgTKAoKuMpkCAgQIECBAgAABAgQIECBAgACBjgKCro5T0RMBAgQIECBAgAABAgQIECBAgEBZQNBVJlNAgAABAgQIECBAgAABAgQIECDQUUDQ1XEqeiJAgAABAgQIECBAgAABAgQIECgLCLrKZAoIECBAgAABAgQIECBAgAABAgQ6Cgi6Ok5FTwQIECBAgAABAgQIECBAgAABAmUBQVeZTAEBAgQIECBAgAABAgQIECBAgEBHAUFXx6noiQABAgQIECBAgAABAgQIECBAoCwg6CqTKSBAgAABAgQIECBAgAABAgQIEOgoIOjqOBU9ESBAgAABAgQIECBAgAABAgQIlAUEXWUyBQQIECBAgAABAgQIECBAgAABAh0FBF0dp6InAgQIECBAgAABAgQIECBAgACBsoCgq0ymgAABAgQIECBAgAABAgQIECBAoKOAoKvjVPREgAABAgQIECBAgAABAgQIECBQFhB0lckUECBAgAABAgQIECBAgAABAgQIdBQQdHWcip4IECBAgAABAgQIECBAgAABAgTKAoKuMpkCAgQIECBAgAABAgQIECBAgACBjgKCro5T0RMBAgQIECBAgAABAgQIECBAgEBZQNBVJlNAgAABAgQIECBAgAABAgQIECDQUUDQ1XEqeiJAgAABAgQIECBAgAABAgQIECgLCLrKZAoIECBAgAABAgQIECBAgAABAgQ6Cgi6Ok5FTwQIECBAgAABAgQIECBAgAABAmUBQVeZTAEBAgQIECBAgAABAgQIECBAgEBHgfMdm9LTugKfPn2aPn78OH348GF6//799Pbt2+mXX36ZXr9+Pb169Wq6cOHC3FBudyFAgAABAgQIECBAgMCuwLt376aXL1/Oxw45hsixRI4dcmyRY4wca+SYw4UAAQJrCAi61lBu/hj5pfPbb7/Nv4zevHkzvXjxYnry5MkccJ05c2b69ddfp6tXr34OvJo/He0RIECAAAECBAgQILCiQIKuBFzPnj2bDg4O5mOJHFPk2CKBV441BF0rDsRDETjlAoKuU/4CyNPP/7Dkl0/+5yW/nC5evDir5JdSfkFdv359unz58vTdd9/RIkCAAAECBAgQIECAwH8JZOVWjiWyquvp06fT48ePp4cPH87HFrk9xxo55nAhQIDAGgKCrjWUmz9GfumM5cbnz5+flxgn4Pr555+na9eufQ65zp071/yZaI8AAQIECBAgQIAAgbUFxkegJNTKR58k8MrxRP4TPV/nWEPQtfZUPB6B0ysg6Dq9s//8zLOMePwvTE5VHKHXpUuX5tVdWcmVACw/cyFAgAABAgQIECBAgMCuwPgolPF5v/nok4ReOXUx17ndqYu7Yr4mQGBJAUHXkronZN/j1MX8Qhqru3KOfcKtbFnJdfbsWUHXCZmnNgkQIECAAAECBAisKZAQK8cRWdmV0xSzJdzKf6Bnc+rimtPwWAQICLq8BmaBEXaN/41JsDW2rOTK1y4ECBAgQIAAAQIECBA4SiDHEyPwytcj+Bp/dfGoGrcRIEBgCQFB1xKqJ2yfYxlxfhnl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EHTtCaicAAECBAgQIECAAAECBAgQIECgh4Cgq8ccdEGAAAECBAgQIECAAAECBAgQILCngKBrT0DlBAgQIECAAAECBAgQIECAAAECPQQEXT3moAsCBAgQIECAAAECBAgQIECAAIE9BQRdewIqJ0CAAAECBAgQIECAAAECBAgQ6CEg6OoxB10QIECAAAECBAgQIECAAAECBAjsKSDo2hNQOQECBAgQIECAAAECBAgQIECAQA8BQVePOeiCAAECBAgQIECAAAECBAgQIEBgTwFB156AygkQIECAAAECBAgQIECAAAECBHoICLp6zEEXBAgQIECAAAECBAgQIECAAAECewoIuvYEVE6AAAECBAgQIECAAAECBAgQINBDQNDVYw66IECAAAECBAgQIECAAAECBAgQ2FNA0LUnoHICBAgQIECAAAECBAgQIECAAIEeAoKuHnPQBQECBAgQIECAAAECBAgQIECAwJ4Cgq49AZUTIECAAAECBAgQIECAAAECBAj0EBB09ZiDLggQIECAAAECBAgQIECAAAECBPYUEHTtCaicAAECBAgQIECAAAECBAgQIECgh4Cgq8ccdEGAAAECBAgQIECAAAECBAgQILCngKBrT0DlBAgQIECAAAECBAgQIECAAAECPQQEXT3moAsCBAgQIECAAAECBAgQIECAAIE9BQRdewIqJ0CAAAECBAgQIECAAAECBAgQ6CEg6OoxB10QIECAAAECBAgQIECAAAECBAjsKSDo2hNQOQECBAgQIECAAAECBAgQIECAQA8BQVePOeiCAAECBAgQIECAAAECBAgQIEBgTwFB156AygkQIECAAAECBAgQIECAAAECBHoICLp6zEEXBAgQIECAAAECBAgQIECAAAECewoIuvYEVE6AAAECBAgQIECAAAECBAgQINBDQNDVYw66IECAAAECBAgQIECAAAECBAgQ2FNA0LUnoHICBAgQIECAAAECBAgQIECAAIEeAoKuHnPQBQECBAgQIECAAAECBAgQIECAwJ4Cgq49AZUTIECAAAECBAgQIECAAAECBAj0EBB09ZiDLggQIECAAAECBAgQIECAAAECBPYUEHTtCaicAAECBAgQIECAAAECBAgQIECgh4Cgq8ccdEGAAAECBAgQIECAAAECBAgQILCngKBrT0DlBAgQIECAAAECBAgQIECAAAECPQQEXT3moAsCBAgQIECAAAECBAgQIECAAIE9BQRdewIqJ0CAAAECBAgQIECAAAECBAgQ6CEg6OoxB10QIECAAAECBAgQIECAAAECBAjsKSDo2hNQOQECBAgQIECAAAECBAgQIECAQA8BQVePOeiCAAECBAgQIECAAAECBAgQIEBgTwFB156AygkQIECAAAECBAgQIECAAAECBHoICLp6zEEXBAgQIECAAAECBAgQIECAAAECewoIuvYEVE6AAAECBAj8Xzt2TAMAAIAwzL9rRPDsqAASUj4IECBAgAABAgQIEGgIOLoaO2hBgAABAgQIECBAgAABAgQIECBwCji6TkBxAgQIECBAgAABAgQIECBAgACBhoCjq7GDFgQIECBAgAABAgQIECBAgAABAqeAo+sEFCdAgAABAgQIECBAgAABAgQIEGgIOLoaO2hBgAABAgQIECBAgAABAgQIECBwCji6TkBxAgQIECBAgAABAgQIECBAgACBhoCjq7GDFgQIECBAgAABAgQIECBAgAABAqeAo+sEFCdAgAABAgQIECBAgAABAgQIEGgIOLoaO2hBgAABAgQIECBAgAABAgQIECBwCji6TkBxAgQIECBAgAABAgQIECBAgACBhoCjq7GDFgQIECBAgAABAgQIECBAgAABAqeAo+sEFCdAgAABAgQIECBAgAABAgQIEGgIOLoaO2hBgAABAgQIECBAgAABAgQIECBwCji6TkBxAgQIECBAgAABAgQIECBAgACBhoCjq7GDFgQIECBAgAABAgQIECBAgAABAqeAo+sEFCdAgAABAgQIECBAgAABAgQIEGgIOLoaO2hBgAABAgQIECBAgAABAgQIECBwCji6TkBxAgQIECBAgAABAgQIECBAgACBhoCjq7GDFgQIECBAgAABAgQIECBAgAABAqeAo+sEFCdAgAABAgQIECBAgAABAgQIEGgIOLoaO2hBgAABAgQIECBAgAABAgQIECBwCji6TkBxAgQIECBAgAABAgQIECBAgACBhoCjq7GDFgQIECBAgAABAgQIECBAgAABAqeAo+sEFCdAgAABAgQIECBAgAABAgQIEGgIOLoaO2hBgAABAgQIECBAgAABAgQIECBwCji6TkBxAgQIECBAgAABAgQIECBAgACBhoCjq7GDFgQIECBAgAABAgQIECBAgAABAqeAo+sEFCdAgAABAgQIECBAgAABAgQIEGgIOLoaO2hBgAABAgQIECBAgAABAgQIECBwCji6TkBxAgQIECBAgAABAgQIECBAgACBhoCjq7GDFgQIECBAgAABAgQIECBAgAABAqeAo+sEFCdAgAABAgQIECBAgAABAgQIEGgIOLoaO2hBgAABAgQIECBAgAABAgQIECBwCji6TkBxAgQIECBAgAABAgQIECBAgACBhoCjq7GDFgQIECBAgAABAgQIECBAgAABAqeAo+sEFCdAgAABAgQIECBAgAABAgQIEGgIOLoaO2hBgAABAgQIECBAgAABAgQIECBwCji6TkBxAgQIECBAgAABAgQIECBAgACBhoCjq7GDFgQIECBAgAABAgQIECBAgAABAqeAo+sEFCdAgAABAgQIECBAgAABAgQIEGgIOLoaO2hBgAABAgQIECBAgAABAgQIECBwCji6TkBxAgQIECBAgAABAgQIECBAgACBhoCjq7GDFgQIECBAgAABAgQIECBAgAABAqeAo+sEFCdAgAABAgQIECBAgAABAgQIEGgIOLoaO2hBgAABAgQIECBAgAABAgQIECBwCji6TkBxAgQIECBAgAABAgQIECBAgACBhoCjq7GDFgQIECBAgAABAgQIECBAgAABAqeAo+sEFCdAgAABAgQIECBAgAABAgQIEGgIOLoaO2hBgAABAgQIECBAgAABAgQIECBwCji6TkBxAgQIECBAgAABAgQIECBAgACBhoCjq7GDFgQIECBAgAABAgQIECBAgAABAqeAo+sEFCdAgAABAgQIECBAgAABAgQIEGgIOLoaO2hBgAABAgQIECBAgAABAgQIECBwCji6TkBxAgQIECBAgAABAgQIECBAgACBhoCjq7GDFgQIECBAgAABAgQIECBAgAABAqeAo+sEFCdAgAABAgQIECBAgAABAgQIEGgIOLoaO2hBgAABAgQIECBAgAABAgQIECBwCji6TkBxAgQIECBAgAABAgQIECBAgACBhoCjq7GDFgQIECBAgAABAgQIECBAgAABAqeAo+sEFCdAgAABAgQIECBAgAABAgQIEGgIOLoaO2hBgAABAgQIECBAgAABAgQIECBwCji6TkBxAgQIECBAgAABAgQIECBAgACBhoCjq7GDFgQIECBAgAABAgQIECBAgAABAqeAo+sEFCdAgAABAgQIECBAgAABAgQIEGgIOLoaO2hBgAABAgQIECBAgAABAgQIECBwCji6TkBxAgQIECBAgAABAgQIECBAgACBhoCjq7GDFgQIECBAgAABAgQIECBAgAABAqeAo+sEFCdAgAABAgQIECBAgAABAgQIEGgIOLoaO2hBgAABAgQIECBAgAABAgQIECBwCji6TkBxAgQIECBAgAABAgQIECBAgACBhoCjq7GDFgQIECBAgAABAgQIECBAgAABAqeAo+sEFCdAgAABAgQIECBAgAABAgQIEGgIOLoaO2hBgAABAgQIECBAgAABAgQIECBwCji6TkBxAgQIECBAgAABAgQIECBAgACBhoCjq7GDFgQIECBAgAABAgQIECBAgAABAqeAo+sEFCdAgAABAgQIECBAgAABAgQIEGgIOLoaO2hBgAABAgQIECBAgAABAgQIECBwCji6TkBxAgQIECBAgAABAgQIECBAgACBhoCjq7GDFgQIECBAgAABAgQIECBAgAABAqeAo+sEFCdAgAABAgQIECBAgAABAgQIEGgIOLoaO2hBgAABAgQIECBAgAABAgQIECBwCji6TkBxAgQIECBAgAABAgQIECBAgACBhoCjq7GDFgQIECBAgAABAgQIECBAgAABAqeAo+sEFCdAgAABAgQIECBAgAABAgQIEGgIOLoaO2hBgAABAgQIECBAgAABAgQIECBwCji6TkBxAgQIECBAgAABAgQIECBAgACBhoCjq7GDFgQIECBAgAABAgQIECBAgAABAqeAo+sEFCdAgAABAgQIECBAgAABAgQIEGgIOLoaO2hBgAABAgQIECBAgAABAgQIECBwCji6TkBxAgQIECBAgAABAgQIECBAgACBhoCjq7GDFgQIECBAgAABAgQIECBAgAABAqeAo+sEFCdAgAABAgQIECBAgAABAgQIEGgIOLoaO2hBgAABAgQIECBAgAABAgQIECBwCji6TkBxAgQIECBAgAABAgQIECBAgACBhoCjq7GDFgQIECBAgAABAgQIECBAgAABAqeAo+sEFCdAgAABAgQIECBAgAABAgQIEGgIOLoaO2hBgAABAgQIECBAgAABAgQIECBwCji6TkBxAgQIECBAgAABAgQIECBAgACBhoCjq7GDFgQIECBAgAABAgQIECBAgAABAqeAo+sEFCdAgAABAgQIECBAgAABAgQIEGgIOLoaO2hBgAABAgQIECBAgAABAgQIECBwCji6TkBxAgQIECBAgAABAgQIECBAgACBhoCjq7GDFgQIECBAgAABAgQIECBAgAABAqeAo+sEFCdAgAABAgQIECBAgAABAgQIEGgIOLoaO2hBgAABAgQIECBAgAABAgQIECBwCgy2PyVtI6iUqAAAAABJRU5ErkJggg=="
        return s6_png_uri

    elif shape == "T14":
        # T14: hand-drawn sketch (user-provided, already bolded)
        t14_png_uri = "data:image/png;base64,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d+68+g98RIAAgcEE9uzZMwtt8615+fuYBwECBEYQEHyMMAV7IECAAAEC3wrkHxRywHHz5s10/fr12e0tf/3rX9Pm5ubs8zkE8SBAgMDIAvfu3UtfffVV+uyzz1K+7SXfspff79+/P+3duzfl1wDxIECAwFYLLH37m6V/XVO71StbjwABAgQIEHhFIIcdOej485//nH7/+9/Pgo9bt27NfnDIP0w8fvz4la/3AQECBEYTyC9mmkOOHHa89dZb6fjx4+nXv/51+uUvf5nef//9dODAgdG2bD8ECExAwBUfExiyFgkQIEBgMQTyFR/5BUz//ve/pz/96U+z35iWO19aWkrbtm1Ly8vLKR/nNw8CBAj0FChvz3v+/PksoM0hbr5y7dKlSymHtzkE+clPfpJ+9rOf9dyqtQkQmLCA4GPCw9c6AQIECCyWQA49du7cObtUfGVlZRaALFYHdkuAQDSB/Doez549m92ql69Ky8f5czkQye+fPn36yuei9a8fAgQWQ0DwsRhzsksCBAgQIJB2796djh49mt5+++3ZpeT5knIPAgQI9BTIrz2UX3j5m2++mf0Vqvw6RfOrQPK+5iGIu+t7TsnaBAgIPpwDBAgQIEBgQQTy5eK/+c1v0kcffZTee++92eXjC7J12yRAIKhAvqXliy++SGfPnp39NZccfHgQIEBgNAHBx2gTsR8CBAgQIPADArt27UpHjhxJH374YTp58mQ6ePDgD3ylTxMgQGBrBL7++uvZ7Xf5io/8PcqDAAECIwosj7gpeyJAgAABAgQIECBAgAABAgQI1BAQfNRQVIMAAQIECBAgQIAAAQIECBAYUkDwMeRYbIoAAQIECBAgQIAAAQIECBCoISD4qKGoBgECBAgQIECAAAECBAgQIDCkgOBjyLHYFAECBAgQIECAAAECBAgQIFBDQPBRQ1ENAgQIECBAgAABAgQIECBAYEgBwceQY7EpAgQIECBAgAABAgQIECBAoIaA4KOGohoECBAgQIAAAQIECBAgQIDAkAKCjyHHYlMECBAgQIAAAQIECBAgQIBADQHBRw1FNQgQIECAAAECBAgQIECAAIEhBQQfQ47FpggQIECAAAECBAgQIECAAIEaAoKPGopqECBAgAABAgQIECBAgAABAkMKCD6GHItNESBAgAABAgQIECBAgAABAjUEBB81FNUgQIAAAQIECBAgQIAAAQIEhhQQfAw5FpsiQIAAAQIECBAgQIAAAQIEaggIPmooqkGAAAECBAgQIECAAAECBAgMKSD4GHIsNkWAAAECBAgQIECAAAECBAjUEBB81FBUgwABAgQIECBAgAABAgQIEBhSQPAx5FhsigABAgQIECBAgAABAgQIEKghIPiooagGAQIECBAgQIAAAQIECBAgMKSA4GPIsdgUAQIECBAgQIAAAQIECBAgUENA8FFDUQ0CBAgQIECAAAECBAgQIEBgSAHBx5BjsSkCBAgQIECAAAECBAgQIECghoDgo4aiGgQIECBAgAABAgQIECBAgMCQAoKPIcdiUwQIECBAgAABAgQIECBAgEANAcFHDUU1CBAgQIAAAQIECBAgQIAAgSEFBB9DjsWmCBAgQIAAAQIECBAgQIAAgRoCgo8aimoQIECAAAECBAgQIECAAAECQwoIPoYci00RIECAAAECBAgQIECAAAECNQQEHzUU1SBAgAABAgQIECBAgAABAgSGFBB8DDkWmyJAgAABAgQIECBAgAABAgRqCAg+aiiqQYAAAQIECBAgQIAAAQIECAwpIPgYciw2RYAAAQIECBAgQIAAAQIECNQQEHzUUFSDAAECBAgQIECAAAECBAgQGFJA8DHkWGyKAAECBAgQIECAAAECBAgQqCEg+KihqAYBAgQIECBAgAABAgQIECAwpIDgY8ix2BQBAgQIECBAgAABAgQIECBQQ0DwUUNRDQIECBAgQIAAAQIECBAgQGBIAcHHkGOxKQIECBAgQIAAAQIECBAgQKCGgOCjhqIaBAgQIECAAAECBAgQIECAwJACgo8hx2JTBAgQIECAAAECBAgQIECAQA0BwUcNRTUIECBAgAABAgQIECBAgACBIQUEH0OOxaYIECBAgAABAgQIECBAgACBGgKCjxqKahAgQIAAAQIECBAgQIAAAQJDCgg+hhyLTREgQIAAAQIECBAgQIAAAQI1BAQfNRTVIECAAAECBAgQIECAAAECBIYUEHwMORabIkCAAAECBAgQIECAAAECBGoICD5qKKpBgAABAgQIECBAgAABAgQIDCkg+BhyLDZFgAABAgQIECBAgAABAgQI1BAQfNRQVIMAAQIECBAgQIAAAQIECBAYUkDwMeRYbIoAAQIECBAgQIAAAQIECBCoISD4qKGoBgECBAgQIECAAAECBAgQIDCkgOBjyLHYFAECBAgQIECAAAECBAgQIFBDQPBRQ1ENAgQIECBAgAABAgQIECBAYEgBwceQY7EpAgQIECBAgAABAgQIECBAoIaA4KOGohoECBAgQIAAAQIECBAgQIDAkAKCjyHHYlMECBAgQIAAAQIECBAgQIBADQHBRw1FNQgQIECAAAECBAgQIECAAIEhBQQfQ47FpggQIECAAAECBAgQIECAAIEaAoKPGopqECBAgAABAgQIECBAgAABAkMKCD6GHItNESBAgAABAgQIECBAgAABAjUEBB81FNUgQIAAAQIECBAgQIAAAQIEhhQQfAw5FpsiQIAAAQIECBAgQIAAAQIEaggIPmooqkGAAAECBAgQIECAAAECBAgMKSD4GHIsNkWAAAECBAgQIECAAAECBAjUEBB81FBUgwABAgQIECBAgAABAgQIEBhSQPAx5FhsigABAgQIECBAgAABAgQIEKghIPiooagGAQIECBAgQIAAAQIECBAgMKSA4GPIsdgUAQIECBAgQIAAAQIECBAgUENA8FFDUQ0CBAgQIECAAAECBAgQIEBgSAHBx5BjsSkCBAgQIECAAAECBAgQIECghoDgo4aiGgQIECBAgAABAgQIECBAgMCQAoKPIcdiUwQIECBAgAABAgQIECBAgEANAcFHDUU1CBAgQIAAAQIECBAgQIAAgSEFBB9DjsWmCBAgQIAAAQIECBAgQIAAgRoCgo8aimoQIECAAAECBAgQIECAAAECQwoIPoYci00RIECAAAECBAgQIECAAAECNQQEHzUU1SBAgAABAgQIECBAgAABAgSGFBB8DDkWmyJAgAABAgQIECBAgAABAgRqCAg+aiiqQYAAAQIECBAgQIAAAQIECAwpIPgYciw2RYAAAQIECBAgQIAAAQIECNQQEHzUUFSDAAECBAgQIECAAAECBAgQGFJA8DHkWGyKAAECBAgQIECAAAECBAgQqCEg+KihqAYBAgQIECBAgAABAgQIECAwpIDgY8ix2BQBAgQIECBAgAABAgQIECBQQ0DwUUNRDQIECBAgQIAAAQIECBAgQGBIAcHHkGOxKQIECBAgQIAAAQIECBAgQKCGgOCjhqIaBAgQIECAAAECBAgQIECAwJACgo8hx2JTBAgQIECAAAECBAgQIECAQA0BwUcNRTUIECBAgAABAgQIECBAgACBIQUEH0OOxaYIECBAgAABAgQIECBAgACBGgKCjxqKahAgQIAAAQIECBAgQIAAAQJDCgg+hhyLTREgQIAAAQIECBAgQIAAAQI1BAQfNRTVIECAAAECBAgQIECAAAECBIYUEHwMORabIkCAAAECBAgQIECAAAECBGoICD5qKKpBgAABAgQIECBAgAABAgQIDCkg+BhyLDZFgAABAgQIECBAgAABAgQI1BAQfNRQVIMAAQIECBAgQIAAAQIECBAYUkDwMeRYbIoAAQIECBAgQIAAAQIECBCoISD4qKGoBgECBAgQIECAAAECBAgQIDCkgOBjyLHYFAECBAgQIECAAAECBAgQIFBDQPBRQ1ENAgQIECBAgAABAgQIECBAYEgBwceQY7EpAgQIECBAgAABAgQIECBAoIaA4KOGohoECBAgQIAAAQIECBAgQIDAkAKCjyHHYlMECBAgQIAAAQIECBAgQIBADQHBRw1FNQgQIECAAAECBAgQIECAAIEhBQQfQ47FpggQIECAAAECBAgQIECAAIEaAoKPGopqECBAgAABAgQIECBAgAABAkMKCD6GHItNESBAgAABAgQIECBAgAABAjUEBB81FNUgQIAAAQIECBAgQIAAAQIEhhQQfAw5FpsiQIAAAQIECBAgQIAAAQIEaggIPmooqkGAAAECBAgQIECAAAECBAgMKSD4GHIsNkWAAAECBAgQIECAAAECBAjUEBB81FBUgwABAgQIECBAgAABAgQIEBhSQPAx5FhsigABAgQIECBAgAABAgQIEKghIPiooagGAQIECBAgQIAAAQIECBAgMKSA4GPIsdgUAQIECBAgQIAAAQIECBAgUENA8FFDUQ0CBAgQIECAAAECBAgQIEBgSAHBx5BjsSkCBAgQIECAAAECBAgQIECghoDgo4aiGgQIECBAgAABAgQIECBAgMCQAoKPIcdiUwQIECBAgAABAgQIECBAgEANAcFHDUU1CBAgQIAAAQIECBAgQIAAgSEFBB9DjsWmCBAgQIAAAQIECBAgQIAAgRoCgo8aimoQIECAAAECBAgQIECAAAECQwoIPoYci00RIECAAAECBAgQIECAAAECNQQEHzUU1SBAgAABAgQIECBAgAABAgSGFBB8DDkWmyJAgAABAgQIECBAgAABAgRqCAg+aiiqQYAAAQIECBAgQIAAAQIECAwpIPgY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QIBATwHBR099axMgQIAAAQIECBAgQIAAAQJNBQQfTXkVJ0CAAAECBAgQIECAAAECBHoKCD566lubAAECBAgQIECAAAECBAgQaCog+GjKqzgBAgQIECBAgAABAgQIECDQU0Dw0VPf2gQIECBAgAABAgQIECBAgEBTAcFHU17FCRAgQIAAAQIECBAgQIAAgZ4Cgo+e+tYmQIAAAQIECBAgQIAAAQIEmgoIPpryKk6AAAECBAgQIECAAAECBAj0FBB89NS3NgECBAgQIECAAAECBAgQINBUQPDRlFdxAgQIECBAgAABAgQIECBAoKeA4KOnvrUJECBAgAABAgQIECBAgACBpgKCj6a8ihMgQIAAAQIECBAgQIAAAQI9BQQfPfWtTYAAAQIECBAgQIAAAQIECDQVEHw05VWcAAECBAgQIECAAAECBAgQ6Ckg+Oipb20CBAgQIECAAAECBAgQIECgqYDgoymv4gQIECBAgAABAgQIECBAgEBPAcFHT31rEyBAgAABAgQIECBAgAABAk0FBB9NeRUnQIAAAQIECBAgQIAAAQIEegoIPnrqW5sAAQIECBAgQIAAAQIECBBoKiD4aMqrOAECBAgQIECAAAECBAgQINBTQPDRU9/aBAgQIECAAAECBAgQIECAQFMBwUdTXsUJECBAgAABAgQIECBAgACBngKCj5761iZAgAABAgQIECBAgAABAgSaCgg+mvIqToAAAQIECBAgQIAAAQIECPQUEHz01Lc2AQIECBAgQIAAAQIECBAg0FRA8NGUV3ECBAgQIECAAAECBAgQIECgp4Dgo6e+tQkQIECAAAECBAgQIECAAIGmAoKPpryKEyBAgAABAgQIECBAgAABAj0FBB899a1NgAABAgQIECBAgAABAgQINBUQfDTlVZwAAQIECBAgQIAAAQIECBDoKSD46KlvbQIECBAgQIAAAQIECBAgQKCpgOCjKa/iBAgQIECAAAECBAgQIECAQE8BwUdPfWsTIECAAAECBAgQIECAAAECTQUEH015FSdAgAABAgQIECBAgAABAgR6Cgg+eupbmwABAgQIECBAgAABAgQIEGgqIPhoyqs4AQIECBAgQIAAAQIECBAg0FNA8NFT39oECBAgQIAAAQIECBAgQIBAUwHBR1NexQkQIECAAAECBAgQIECAAIGeAoKPnvrWJkCAAAECBAgQIECAAAECBJoKCD6a8ipOgAABAgQIECBAgAABAgQI9BQQfPTUtzYBAgQIECBAgAABAgQIECDQVEDw0ZRXcQIECBAgQIAAAQIECBAgQKCngOCjp761CRAgQIAAAQIECBAgQIAAgaYCgo+mvIoTIECAAAECBAgQIECAAAECPQUEHz31rU2AAAECBAgQIECAAAECBAg0FRB8NOVVnAABAgQIECBAgAABAgQIEOgpIPjoqW9tAgQIECBAgAABAgQIECBAoKmA4KMpr+IECBAgQIAAAQIECBAgQIBATwHBR099axMgQIAAAQIECBAgQIAAAQJNBQQfTXkVJ0CAAAECBAgQIECAAAECBHoKCD566lubAAECBAgQIECAAAECBAgQaCog+GjKqzgBAgQIECBAgAABAgQIECDQU0Dw0VPf2gQIECBAgAABAgQIECBAgEBTAcFHU17FCRAgQIAAAQIECBAgQIAAgZ4Cgo+e+tYmQIAAAQIECBAgQIAAAQIEmgoIPpryKk6AAAECBAgQIECAAAECBAj0FBB89NS3NgECBAgQIECAAAECBAgQINBUQPDRlFdxAgQIECBAgAABAgQIECBAoKeA4KOnvrUJECBAgAABAgQIECBAgACBpgKCj6a8ihMgQIAAAQIECBAgQIAAAQI9BQQfPfWtTYAAAQIECBAgQIAAAQIECDQVEHw05VWcAAECBAgQIECAAAECBAgQ6Ckg+Oipb20CBAgQIECAAAECBAgQIECgqYDgoymv4gQIECBAgAABAgQIECBAgEBPAcFHT31rEyBAgAABAgQIECBAgAABAk0FBB9NeRUnQIAAAQIECBAgQIAAAQIEegoIPnrqW5sAAQIECBAgQIAAAQIECBBoKiD4aMqrOAECBAgQIECAAAECBAgQINBTQPDRU9/aBAgQIECAAAECBAgQIECAQFMBwUdTXsUJECBAgAABAgQIECBAgACBngKCj5761iZAgAABAgQIECBAgAABAgSaCgg+mvIqToAAAQIECBAgQIAAAQIECPQUEHz01Lc2AQIECBAgQIAAAQIECBAg0FRA8NGUV3ECBAgQIECAAAECBAgQIECgp4Dgo6e+tQkQIECAAAECBAgQIECAAIGmAoKPpryKEyBAgAABAgQIECBAgAABAj0FBB899a1NgAABAgQIECBAgAABAgQINBUQfDTlVZwAAQIECBAgQIAAAQIECBDoKSD46KlvbQIECBAgQIAAAQIECBAgQKCpgOCjKa/iBAgQIECAAAECBAgQIECAQE8BwUdPfWsTIECAAAECBAgQIECAAAECTQUEH015FSdAgAABAgQIECBAgAABAgR6Cgg+eupbmwABAgQIECBAgAABAgQIEGgqIPhoyqs4AQIECBAgQIAAAQIECBAg0FNA8NFT39oECBAgQIAAAQIECBAgQIBAUwHBR1NexQkQIECAAAECBAgQIECAAIGeAoKPnvrWJkCAAAECBAgQIECAAAECBJoKCD6a8ipOgAABAgQIECBAgAABAgQI9BQQfPTUtzYBAgQIECBAgAABAgQIECDQVEDw0ZRXcQIECBAgQIAAAQIECBAgQKCngOCjp761CRAgQIAAAQIECBAgQIAAgaYCgo+mvIoTIECAAAECBAgQIECAAAECPQUEHz31rU2AAAECBAgQIECAAAECBAg0FRB8NOVVnAABAgQIECBAgAABAgQIEOgpIPjoqW9tAgQIECBAgAABAgQIECBAoKmA4KMpr+IECBAgQIAAAQIECBAgQIBATwHBR099axMgQIAAAQIECBAgQIAAAQJNBQQfTXkVJ0CAAAECBAgQIECAAAECBHoKCD566lubAAECBAgQIECAAAECBAgQaCog+GjKqzgBAgQIECBAgAABAgQIECDQU0Dw0VPf2gQIECBAgAABAgQIECBAgEBTAcFHU17FCRAgQIAAAQIECBAgQIAAgZ4Cgo+e+tYmQIAAAQIECBAgQIAAAQIEmgoIPpryKk6AAAECBAgQIECAAAECBAj0FBB89NS3NgECBAgQIECAAAECBAgQINBUQPDRlFdxAgQIECBAgAABAgQIECBAoKeA4KOnvrUJECBAgAABAgQIECBAgACBpgKCj6a8ihMgQIAAAQIECBAgQIAAAQI9BQQfPfWtTYAAAQIECBAgQIAAAQIECDQVEHw05VWcAAECBAgQIECAAAECBAgQ6Ckg+Oipb20CBAgQIECAAAECBAgQIECgqYDgoymv4gQIECBAgAABAgQIECBAgEBPAcFHT31rEyBAgAABAgQIECBAgAABAk0FBB9NeRUnQIAAAQIECBAgQIAAAQIEegoIPnrqW5sAAQIECBAgQIAAAQIECBBoKiD4aMqrOAECBAgQIECAAAECBAgQINBTQPDRU9/aBAgQIECAAAECBAgQIECAQFMBwUdTXsUJECBAgAABAgQIECBAgACBngKCj5761iZAgAABAgQIECBAgAABAgSaCgg+mvIqToAAAQIECBAgQIAAAQIECPQUEHz01Lc2AQIECBAgQIAAAQIECBAg0FRA8NGUV3ECBAgQIECAAAECBAgQIECgp4Dgo6e+tQkQIECAAAECBAgQIECAAIGmAoKPpryKEyBAgAABAgQIECBAgAABAj0FBB899a1NgAABAgQIECBAgAABAgQINBUQfDTlVZwAAQIECBAgQIAAAQIECBDoKSD46KlvbQIECBAgQIAAAQIECBAgQKCpgOCjKa/iBAgQIECAAAECBAgQIECAQE8BwUdPfWsTIECAAAECBAgQIECAAAECTQUEH015FSdAgAABAgQIECBAgAABAgR6Cgg+eupbmwABAgQIECBAgAABAgQIEGgqIPhoyqs4AQIECBAgQIAAAQIECBAg0FNA8NFT39oECBAgQIAAAQIECBAgQIBAUwHBR1NexQkQIECAAAECBAgQIECAAIGeAoKPnvrWJkCAAAECBAgQIECAAAECBJoKCD6a8ipOgAABAgQIECBAgAABAgQI9BQQfPTUtzYBAgQIECBAgAABAgQIECDQVEDw0ZRXcQIECBAgQIAAAQIECBAgQKCngOCjp761CRAgQIAAAQIECBAgQIAAgaYCgo+mvIoTIECAAAECBAgQIECAAAECPQUEHz31rU2AAAECBAgQIECAAAECBAg0FRB8NOVVnAABAgQIECBAgAABAgQIEOgpIPjoqW9tAgQIECBAgAABAgQIECBAoKmA4KMpr+IECBAgQIAAAQIECBAgQIBATwHBR099axMgQIAAAQIECBAgQIAAAQJNBQQfTXkVJ0CAAAECBAgQIECAAAECBHoKCD566lubAAECBAgQIECAAAECBAgQaCog+GjKqzgBAgQIECBAgAABAgQIECDQU0Dw0VPf2gQIECBAgAABAgQIECBAgEBTAcFHU17FCRAgQIAAAQIECBAgQIAAgZ4Cgo+e+tYmQIAAAQIECBAgQIAAAQIEmgoIPpryKk6AAAECBAgQIECAAAECBAj0FBB89NS3NgECBAgQIECAAAECBAgQINBUQPDRlFdxAgQIECBAgAABAgQIECBAoKeA4KOnvrUJECBAgAABAgQIECBAgACBpgKCj6a8ihMgQIAAAQIECBAgQIAAAQI9BQQfPfWtTYAAAQIECBAgQIAAAQIECDQVEHw05VWcAAECBAgQIECAAAECBAgQ6Ckg+Oipb20CBAgQIECAAAECBAgQIECgqYDgoymv4gQIECBAgAABAgQIECBAgEBPAcFHT31rEyBAgAABAgQIECBAgAABAk0FBB9NeRUnQIAAAQIECBAgQIAAAQIEegoIPnrqW5sAAQIECBAgQIAAAQIECBBoKiD4aMqrOAECBAgQIECAAAECBAgQINBTQPDRU9/aBAgQIECAAAECBAgQIECAQFMBwUdTXsUJECBAgAABAgQIECBAgACBngKCj5761iZAgAABAgQIECBAgAABAgSaCgg+mvIqToAAAQIECBAgQIAAAQIECPQUWOm5uLUJTFHg4cOH6cqVK+nChQvpyZMnaWNjY4oMeiZAgACBIAIvX75ML168SOX7IK0tRBtLS0spvy0vL8/e8vFWPm7evJm++OKL2XOb/BzHgwABAiMKCD5GnIo9hRbITxBOnz6dLl26lNbX19POnTtD96s5AgQIEIgtkEOPZ8+epadPn84C/fyxx9YJ5MBjZWUlbd++ffa2bdu2rVv825UeP36cbt++na5du5bycxwPAgQIjCgg+BhxKvYUWuDBgwfp8uXLaXNzc/ZEZaufoITG1RwBAgQIbLnA8+fP/x185PAjf+yxdQJl8LFjx4601c8ryvnnEMSDAAECIwoIPkacij2FFshPEPITg3ybS36ystWXpIbG1RwBAgQIbLlAeYvL/JaXLd/EhBec++erbvLzi61+XjFfP78Xek34RNQ6gcEFBB+DD8j2Fk8g/7blwIED6d13302/+tWv0v79+9OtW7dml4Heu3dv9qQkPznxIECAAAECBAi8qUAOHPJjlNAhPw/au3fv7PlPfh2z999/P73zzjuz50b5v3kQIECgh8DSt98s//Xdssfq1iQQUCD/tuXu3buz+1yvX7+eLl68mM6cOZPOnTs3e0HT/DkPAgQIECBAgEBEgfzLnw8++CCdPHly9gugHHy8/fbbsxdzz78MWl1djdi2nggQGFzAFR+DD8j2Fk9gfsVH/i1HvuojPwH45z//OXvRry+//DLdv39/8ZqyYwIECBAg8AMC+Xdo81tc5u9/4Et9uoFAvrUlv/X6qy6vt7Rv3750+PDh9POf/zz99re/TceOHZu97sh8f69/vY8JECCwFQKCj61QtsakBOb31s6fiOQgJP92Y21tLeUnAzkE8SBAgAABAlEEyhe39OKmWz/V3i9u+nrH+blOfs6ze/fu2fOf/Ndm5s+J5s+RXv83PiZAgEBrAcFHa2H1Jykw/x97fp//x3/06NF04sSJlEOQGzduTNJE0wQIECAQUyBf5eHP2fabbRl85JBhq/+qy+ud5yte81UeP/3pT2cBSO/9vL4/HxMgME0Br/ExzbnregsFHj16NHth0/y6H/k2l/zXXDwIECBAgEAUAbe69J3k/GqK+a0k81++9NpV/iXP/CrX9fV1r+nRaxDWJUDgFQHBxyscPiBAgAABAgQIECBAgAABAgQiCSxHakYvBAgQIECAAAECBAgQIECAAIFSQPBRajgmQIAAAQIECBAgQIAAAQIEQgkIPkKNUzMECBAgQIAAAQIECBAgQIBAKSD4KDUcEyBAgAABAgQIECBAgAABAqEEBB+hxqkZAgQIECBAgAABAgQIECBAoBQQfJQajgkQIECAAAECBAgQIECAAIFQAoKPUOPUDAECBAgQIECAAAECBAgQIFAKCD5KDccECBAgQIAAAQIECBAgQIBAKAHBR6hxaoYAAQIECBAgQIAAAQIECBAoBQQfpYZjAgQIECBAgAABAgQIECBAIJSA4CPUODVDgAABAgQIECBAgAABAgQIlAKCj1LDMQECBAgQIECAAAECBAgQIBBKQPARapyaIUCAAAECBAgQIECAAAECBEoBwUep4ZgAAQIECBAgQIAAAQIECBAIJSD4CDVOzRAgQIAAAQIECBAgQIAAAQKlgOCj1HBMgAABAgQIECBAgAABAgQIhBIQfIQap2YIECBAgAABAgQIECBAgACBUkDwUWo4JkCAAAECBAgQIECAAAECBEIJCD5CjVMzBAgQIECAAAECBAgQIECAQCkg+Cg1HBMgQIAAAQIECBAgQIAAAQKhBAQfocapGQIECBAgQIAAAQIECBAgQKAUEHyUGo4JECBAgAABAgQIECBAgACBUAKCj1Dj1AwBAgQIECBAgAABAgQIECBQCgg+Sg3HBAgQIECAAAECBAgQIECAQCgBwUeocWqGAAECBAgQIECAAAECBAgQKAUEH6WGYwIECBAgQIAAAQIECBAgQCCUgOAj1Dg1Q4AAAQIECBAgQIAAAQIECJQCgo9SwzEBAgQIECBAgAABAgQIECAQSkDwEWqcmiFAgAABAgQIECBAgAABAgRKAcFHqeGYAAECBAgQIECAAAECBAgQCCUg+Ag1Ts0QIECAAAECBAgQIECAAAECpYDgo9RwTIAAAQIECBAgQIAAAQIECIQSEHyEGqdmCBAgQIAAAQIECBAgQIAAgVJA8FFqOCZAgAABAgQIECBAgAABAgRCCQg+Qo1TMwQIECBAgAABAgQIECBAgEApIPgoNRwTIECAAAECBAgQIECAAAECoQQEH6HGqRkCBAgQIECAAAECBAgQIECgFBB8lBqOCRAgQIAAAQIECBAgQIAAgVACgo9Q49QMAQIECBAgQIAAAQIECBAgUAoIPkoNxwQIECBAgAABAgQIECBAgEAoAcFHqHFqhgABAgQIECBAgAABAgQIECgFBB+lhmMCBAgQIECAAAECBAgQIEAglIDgI9Q4NUOAAAECBAgQIECAAAECBAiUAoKPUsMxAQIECBAgQIAAAQIECBAgEEpA8BFqnJohQIAAAQIECBAgQIAAAQIESgHBR6nhmAABAgQIECBAgAABAgQIEAglIPgINU7NECBAgAABAgQIECBAgAABAqWA4KPUcEyAAAECBAgQIECAAAECBAiEEhB8hBqnZggQIECAAAECBAgQIECAAIFSQPBRajgmQIAAAQIECBAgQIAAAQIEQgkIPkKNUzMECBAgQIAAAQIECBAgQIBAKSD4KDUcEyBAgAABAgQIECBAgKiTKYsAAAiOSURBVAABAqEEBB+hxqkZAgQIECBAgAABAgQIECBAoBQQfJQajgkQIECAAAECBAgQIECAAIFQAoKPUOPUDAECBAgQIECAAAECBAgQIFAKCD5KDccECBAgQIAAAQIECBAgQIBAKAHBR6hxaoYAAQIECBAgQIAAAQIECBAoBQQfpYZjAgQIECBAgAABAgQIECBAIJSA4CPUODVDgAABAgQIECBAgAABAgQIlAKCj1LDMQECBAgQIECAAAECBAgQIBBKQPARapyaIUCAAAECBAgQIECAAAECBEoBwUep4ZgAAQIECBAgQIAAAQIECBAIJSD4CDVOzRAgQIAAAQIECBAgQIAAAQKlgOCj1HBMgAABAgQIECBAgAABAgQIhBIQfIQap2YIECBAgAABAgQIECBAgACBUkDwUWo4JkCAAAECBAgQIECAAAECBEIJCD5CjVMzBAgQIECAAAECBAgQIECAQCkg+Cg1HBMgQIAAAQIECBAgQIAAAQKhBAQfocapGQIECBAgQIAAAQIECBAgQKAUEHyUGo4JECBAgAABAgQIECBAgACBUAKCj1Dj1AwBAgQIECBAgAABAgQIECBQCgg+Sg3HBAgQIECAAAECBAgQIECAQCgBwUeocWqGAAECBAgQIECAAAECBAgQKAUEH6WGYwIECBAgQIAAAQIECBAgQCCUgOAj1Dg1Q4AAAQIECBAgQIAAAQIECJQCgo9SwzEBAgQIECBAgAABAgQIECAQSkDwEWqcmiFAgAABAgQIECBAgAABAgRKAcFHqeGYAAECBAgQIECAAAECBAgQCCUg+Ag1Ts0QIECAAAECBAgQIECAAAECpYDgo9RwTIAAAQIECBAgQIAAAQIECIQSEHyEGqdmCBAgQIAAAQIECBAgQIAAgVJA8FFqOCZAgAABAgQIECBAgAABAgRCCQg+Qo1TMwQIECBAgAABAgQIECBAgEApIPgoNRwTIECAAAECBAgQIECAAAECoQQEH6HGqRkCBAgQIECAAAECBAgQIECgFBB8lBqOCRAgQIAAAQIECBAgQIAAgVACgo9Q49QMAQIECBAgQIAAAQIECBAgUAoIPkoNxwQIECBAgAABAgQIECBAgEAoAcFHqHFqhgABAgQIECBAgAABAgQIECgFBB+lhmMCBAgQIECAAAECBAgQIEAglIDgI9Q4NUOAAAECBAgQIECAAAECBAiUAoKPUsMxAQIECBAgQIAAAQIECBAgEEpA8BFqnJohQIAAAQIECBAgQIAAAQIESgHBR6nhmAABAgQIECBAgAABAgQIEAglIPgINU7NECBAgAABAgQIECBAgAABAqWA4KPUcEyAAAECBAgQIECAAAECBAiEEhB8hBqnZggQIECAAAECBAgQIECAAIFSQPBRajgmQIAAAQIECBAgQIAAAQIEQgkIPkKNUzMECBAgQIAAAQIECBAgQIBAKSD4KDUcEyBAgAABAgQIECBAgAABAqEEBB+hxqkZAgQIECBAgAABAgQIECBAoBQQfJQajgkQIECAAAECBAgQIECAAIFQAoKPUOPUDAECBAgQIECAAAECBAgQIFAKCD5KDccECBAgQIAAAQIECBAgQIBAKAHBR6hxaoYAAQIECBAgQIAAAQIECBAoBQQfpYZjAgQIECBAgAABAgQIECBAIJSA4CPUODVDgAABAgQIECBAgAABAgQIlAKCj1LDMQECBAgQIECAAAECBAgQIBBKQPARapyaIUCAAAECBAgQIECAAAECBEoBwUep4ZgAAQIECBAgQIAAAQIECBAIJSD4CDVOzRAgQIAAAQIECBAgQIAAAQKlgOCj1HBMgAABAgQIECBAgAABAgQIhBIQfIQap2YIECBAgAABAgQIECBAgACBUkDwUWo4JkCAAAECBAgQIECAAAECBEIJCD5CjVMzBAgQIECAAAECBAgQIECAQCkg+Cg1HBMgQIAAAQIECBAgQIAAAQKhBAQfocapGQIECBAgQIAAAQIECBAgQKAUEHyUGo4JECBAgAABAgQIECBAgACBUAKCj1Dj1AwBAgQIECBAgAABAgQIECBQCgg+Sg3HBAgQIECAAAECBAgQIECAQCgBwUeocWqGAAECBAgQIECAAAECBAgQKAUEH6WGYwIECBAgQIAAAQIECBAgQCCUgOAj1Dg1Q4AAAQIECBAgQIAAAQIECJQCgo9SwzEBAgQIECBAgAABAgQIECAQSkDwEWqcmiFAgAABAgQIECBAgAABAgRKAcFHqeGYAAECBAgQIECAAAECBAgQCCUg+Ag1Ts0QIECAAAECBAgQIECAAAECpYDgo9RwTIAAAQIECBAgQIAAAQIECIQSEHyEGqdmCBAgQIAAAQIECBAgQIAAgVJA8FFqOCZAgAABAgQIECBAgAABAgRCCQg+Qo1TMwQIECBAgAABAgQIECBAgEApIPgoNRwTIECAAAECBAgQIECAAAECoQQEH6HGqRkCBAgQIECAAAECBAgQIECgFBB8lBqOCRAgQIAAAQIECBAgQIAAgVACgo9Q49QMAQIECBAgQIAAAQIECBAgUAoIPkoNxwQIECBAgAABAgQIECBAgEAoAcFHqHFqhgABAgQIECBAgAABAgQIECgFBB+lhmMCBAgQIECAAAECBAgQIEAglIDgI9Q4NUOAAAECBAgQIECAAAECBAiUAoKPUsMxAQIECBAgQIAAAQIECBAgEEpA8BFqnJohQIAAAQIECBAgQIAAAQIESgHBR6nhmAABAgQIECBAgAABAgQIEAglIPgINU7NECBAgAABAgQIECBAgAABAqWA4KPUcEyAAAECBAgQIECAAAECBAiEEhB8hBqnZggQIECAAAECBAgQIECAAIFSQPBRajgmQIAAAQIECBAgQIAAAQIEQgkIPkKNUzMECBAgQIAAAQIECBAgQIBAKfA/BD4/WgrlR7gAAAAASUVORK5CYII="
        return t14_png_uri

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
    # G2 Inlet Top — same 2-column layout as G2 Inlet, Height row added
    # ======================================================================
    elif template_name == "G2 Inlet Top":
        _x_field = next(f for f in template.inputs if f.name == "x_dim_ft")
        _t_field = next(f for f in template.inputs if f.name == "wall_thick_in")
        _y_field = next(f for f in template.inputs if f.name == "y_dim_ft")
        _h_field = next(f for f in template.inputs if f.name == "wall_height_ft")

        _t_wk  = f"primary_{_tname}__wall_thick_in"
        _cur_t = int(st.session_state.get(_t_wk, 9))

        # Row 1: X Exterior | X Interior (interior = exterior - 2T)
        _ext_wk = f"primary_{_tname}__x_dim_ft"
        _int_wk = f"_g2top_xi_{_tname}"
        _x_def  = float(_x_field.default) if _x_field.default is not None else 5.667

        _cur_xe = st.session_state.get(_ext_wk)
        _xef    = _parse_ft_in(str(_cur_xe)) if _cur_xe is not None else _x_def
        if _xef is None:
            _xef = _x_def
        st.session_state[_int_wk] = _format_ft_in(max(0, _xef - 2 * _cur_t / 12.0))

        c1, c2 = st.columns(2)
        with c1:
            _ev = st.text_input("X Exterior", key=_ext_wk,
                                value=_format_ft_in(_x_def),
                                help="Exterior face-to-face width",
                                placeholder='e.g. 5\'-8"')
            params_raw["x_dim_ft"] = _ev
        with c2:
            st.text_input("X Interior", key=_int_wk,
                          help="Interior clear width = Exterior \u2212 2\u00d7T")

        # Row 2: Wall Thickness
        _, _tv = _widget(_t_field, key_prefix=f"primary_{_tname}", container=st)
        params_raw["wall_thick_in"] = _tv

        # Row 3: Y Interior | Y Exterior (interior = exterior - 2T)
        _ye_wk  = f"primary_{_tname}__y_dim_ft"
        _yi_wk  = f"_g2top_yi_{_tname}"
        _y_def  = float(_y_field.default) if _y_field.default is not None else 5.0

        _cur_ye = st.session_state.get(_ye_wk)
        _yef    = _parse_ft_in(str(_cur_ye)) if _cur_ye is not None else _y_def
        if _yef is None:
            _yef = _y_def
        st.session_state[_yi_wk] = _format_ft_in(max(0, _yef - 2 * _cur_t / 12.0))

        c3, c4 = st.columns(2)
        with c3:
            st.text_input("Y Interior", key=_yi_wk,
                          help=f"Y Exterior \u2212 2\u00d7{_cur_t}\" \u2014 updates with wall thickness")
        with c4:
            _yv = st.text_input("Y Exterior", key=_ye_wk,
                                value=_format_ft_in(_y_def),
                                help="Exterior depth (same as inlet below)",
                                placeholder='e.g. 5\'-0"')
            params_raw["y_dim_ft"] = _yv

        # Row 4: Height
        _hname, _hval = _widget(_h_field, key_prefix=f"primary_{_tname}", container=st)
        params_raw[_hname] = _hval

        # Remaining (grate_type, num_structures)
        for f in template.inputs:
            if f.name in ("x_dim_ft", "wall_thick_in", "y_dim_ft", "wall_height_ft"):
                continue
            name, val = _widget(f, key_prefix=f"primary_{_tname}", container=st)
            params_raw[name] = val

    # ======================================================================
    # G2 Expanded Inlet Top — same layout as G2 Expanded Inlet + Height row
    # Y is fixed (5'-0" main / 8'-0" expanded) — no Y user input
    # ======================================================================
    elif template_name == "G2 Expanded Inlet Top":
        _x_field = next(f for f in template.inputs if f.name == "x_dim_ft")
        _t_field = next(f for f in template.inputs if f.name == "wall_thick_in")
        _h_field = next(f for f in template.inputs if f.name == "wall_height_ft")

        _t_wk  = f"primary_{_tname}__wall_thick_in"
        _cur_t = int(st.session_state.get(_t_wk, 9))

        # Row 1: X Exterior | X Interior (interior = exterior - 2T)
        _ext_wk = f"primary_{_tname}__x_dim_ft"
        _int_wk = f"_g2exptop_xi_{_tname}"
        _x_def  = float(_x_field.default) if _x_field.default is not None else 5.667

        _cur_xe = st.session_state.get(_ext_wk)
        _xef    = _parse_ft_in(str(_cur_xe)) if _cur_xe is not None else _x_def
        if _xef is None:
            _xef = _x_def
        st.session_state[_int_wk] = _format_ft_in(max(0, _xef - 2 * _cur_t / 12.0))

        c1, c2 = st.columns(2)
        with c1:
            _ev = st.text_input("X Exterior", key=_ext_wk,
                                value=_format_ft_in(_x_def),
                                help="Exterior face-to-face width",
                                placeholder='e.g. 5\'-8"')
            params_raw["x_dim_ft"] = _ev
        with c2:
            st.text_input("X Interior", key=_int_wk,
                          help="Interior clear width = Exterior − 2×T")

        # Row 2: Wall Thickness
        _, _tv = _widget(_t_field, key_prefix=f"primary_{_tname}", container=st)
        params_raw["wall_thick_in"] = _tv

        # Row 3: Height (wall_height_ft)
        _hname, _hval = _widget(_h_field, key_prefix=f"primary_{_tname}", container=st)
        params_raw[_hname] = _hval

        # Remaining (grate_type, num_structures)
        for f in template.inputs:
            if f.name in ("x_dim_ft", "wall_thick_in", "wall_height_ft"):
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
        "Bend #": b.bend_type,
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
