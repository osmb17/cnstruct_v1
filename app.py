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
/* ── Base & page ─────────────────────────────────────────────── */
[data-testid="collapsedControl"] { display: none; }

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

def _make_pdf(bars, template_name, job_info=None) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import landscape, letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    _NAVY   = colors.HexColor("#1c3461")
    _STRIPE = colors.HexColor("#f0f4ff")
    _WARN   = colors.HexColor("#fff3cd")

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(letter),
                            leftMargin=0.5*inch, rightMargin=0.5*inch,
                            topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    elems  = []

    elems.append(Paragraph(f"<b>CNSTRUCT 1.0 — {template_name} Rebar Barlist</b>", styles["Title"]))
    if job_info:
        parts = [f"{k}: {v}" for k, v in job_info.items() if v]
        if parts:
            elems.append(Paragraph("  |  ".join(parts), styles["Normal"]))
    weight_lb = barlist_total_weight_lb(bars)
    elems.append(Paragraph(
        f"Date: {date.today()}  |  Total Weight: {weight_lb:,.1f} lb",
        styles["Normal"]))
    elems.append(Spacer(1, 0.15*inch))

    # Weight breakdown by bar size
    from collections import defaultdict as _dd
    from vistadetail.engine.hooks import BAR_WEIGHT_LB_FT as _WLBFT
    _sz_wt: dict = _dd(float)
    for _b in bars:
        _sz_wt[_b.size] += _WLBFT.get(_b.size, 0.0) * (_b.length_in / 12.0) * _b.qty
    _sorted_sz = sorted(_sz_wt.keys(), key=lambda s: int(s.lstrip("#")))
    wt_rows = [["Bar Size", "Weight (lb)"]]
    for _s in _sorted_sz:
        wt_rows.append([_s, f"{_sz_wt[_s]:,.1f}"])
    wt_rows.append(["Total", f"{weight_lb:,.1f}"])
    wt_tbl = Table(wt_rows, colWidths=[1.1*inch, 1.1*inch])
    wt_tbl.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1,  0), _NAVY),
        ("TEXTCOLOR",   (0, 0), (-1,  0), colors.white),
        ("FONTNAME",    (0, 0), (-1,  0), "Helvetica-Bold"),
        ("FONTNAME",    (0,-1), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, -1), 8),
        ("BACKGROUND",  (0,-1), (-1, -1), _STRIPE),
        ("ROWBACKGROUNDS", (0,1), (-1,-2), [colors.white, _STRIPE]),
        ("GRID",        (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",  (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING",(0, 0),(-1, -1), 2),
    ]))
    elems.append(wt_tbl)
    elems.append(Spacer(1, 0.2*inch))

    header = ["Mark","Size","Qty","Length","Shape","Leg A","Leg B","Leg C","Notes"]
    data   = [header] + [b.to_row()[:9] for b in bars]
    col_w  = [w*inch for w in [0.55, 0.5, 0.5, 0.85, 0.55, 0.7, 0.7, 0.7, 3.4]]
    tbl = Table(data, colWidths=col_w, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),_NAVY), ("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"), ("FONTSIZE",(0,0),(-1,-1),8),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,_STRIPE]),
        ("GRID",(0,0),(-1,-1),0.25,colors.lightgrey),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"), ("TOPPADDING",(0,0),(-1,-1),2),
        ("BOTTOMPADDING",(0,0),(-1,-1),2),
    ]))
    for i, bar in enumerate(bars, 1):
        if bar.review_flag:
            tbl.setStyle(TableStyle([("BACKGROUND",(0,i),(-1,i),_WARN)]))
    elems.append(tbl)
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
    "Hook": "└",       # single 90-deg hook
}

# ── Smart field predictions ───────────────────────────────────────────────────
# Maps template → [(trigger_field, target_field, fn(trigger_val) → suggested_val)]
# When the trigger field changes, the target is auto-suggested.
# Rules are grounded in Caltrans standard sizing conventions.
_FIELD_PREDICTIONS: dict[str, list] = {
    "G2 Inlet": [
        # Square plan is the most common starting point for G2 inlets
        ("x_dim_ft", "y_dim_ft", lambda v: round(v, 2)),
    ],
    "G2 Expanded Inlet": [
        ("x_dim_ft", "y_dim_ft", lambda v: round(v, 2)),
    ],
    "Box Culvert": [
        # Square box (span = rise) is standard unless hydraulics dictate otherwise
        ("clear_span_ft", "clear_rise_ft", lambda v: round(v, 2)),
    ],
    "Junction Structure": [
        # Square plan → same width; depth ≈ width + 1 ft (per D91B proportions)
        ("inside_length_ft", "inside_width_ft",  lambda v: round(v, 2)),
        ("inside_length_ft", "inside_depth_ft",  lambda v: round(v + 1.0, 2)),
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


# ── Cached diagram ────────────────────────────────────────────────────────────

@st.cache_data
def _get_diagram(template_name: str):
    return diagram_gen.get_diagram(template_name)


# ═════════════════════════════════════════════════════════════════════════════
# HEADER ROW
# ═════════════════════════════════════════════════════════════════════════════

h1, h2, h3, h4, h5, h6 = st.columns([2, 2.2, 1.2, 1.4, 1.0, 0.9])

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
        help="Select template"
    )
    st.markdown(
        f"<span style='font-size:0.72rem;color:#8a909a;font-weight:500'>"
        f"{_template_stats(template_name)}</span>",
        unsafe_allow_html=True,
    )

with h3:
    detailer = st.text_input("Detailer", key="detailer", placeholder="Initials")

with h4:
    job_name = st.text_input("Project", key="job_name", placeholder="Project name")

with h5:
    job_number = st.text_input("Job #", key="job_number", placeholder="2024-001")

with h6:
    run_date = st.date_input("Date", value=date.today(), key="run_date")

# Template change → clear results
if template_name != st.session_state.get("_last_template"):
    st.session_state._last_template = template_name
    for _k in ("bars","log_lines","warnings","error"):
        st.session_state.pop(_k, None)

template = TEMPLATE_REGISTRY[template_name]

st.markdown("---")

# ═════════════════════════════════════════════════════════════════════════════
# BUTTON BAR
# ═════════════════════════════════════════════════════════════════════════════

bars      = st.session_state.get("bars")
log_lines = st.session_state.get("log_lines", [])
warnings  = st.session_state.get("warnings", [])

b1, b2, b3, b4, b5, b6, b7, b8 = st.columns([1.2, 1, 1, 1, 1, 1, 1, 0.9])

generate_btn = b1.button("Generate",   type="primary", use_container_width=True, key="btn_gen")
refresh_btn  = b2.button("Refresh",    use_container_width=True, key="btn_refresh",
                          disabled=bars is None)
clear_btn    = b3.button("Clear All",  use_container_width=True, key="btn_clear")

# CSV + PDF download buttons (or disabled placeholders)
if bars is not None:
    b4.download_button("Export CSV",
                       data=_make_csv(bars),
                       file_name=f"{template_name.replace(' ','_')}_barlist.csv",
                       mime="text/csv", use_container_width=True, key="btn_csv")
    try:
        ji = {"Project": job_name, "Job #": job_number, "Detailer": detailer}
        b5.download_button("Barlist Sheet",
                           data=_make_pdf(bars, template_name, ji),
                           file_name=f"{template_name.replace(' ','_')}_barlist.pdf",
                           mime="application/pdf", use_container_width=True, key="btn_pdf")
    except ImportError:
        b5.button("Barlist Sheet", disabled=True, use_container_width=True, key="btn_pdf_na")
else:
    b4.button("Export CSV",   disabled=True, use_container_width=True, key="btn_csv_na")
    b5.button("Barlist Sheet", disabled=True, use_container_width=True, key="btn_pdf_na")

show_cut_tab  = b6.button("Cut Optimizer", use_container_width=True, key="btn_cut")
show_hist_tab = b7.button("History",       use_container_width=True, key="btn_hist")
call_ai       = b8.toggle("AI Review", value=False, key="opt_ai",
                           help="Add per-bar AI review notes flagging potential issues")

# ── Button actions ────────────────────────────────────────────────────────────

if clear_btn:
    for _k in ("bars","log_lines","warnings","error"):
        st.session_state.pop(_k, None)
    st.rerun()

if generate_btn or refresh_btn:
    # Collect params from session state widgets
    st.session_state.pop("error", None)

if generate_btn or refresh_btn:
    # Build params_raw from current widget values.
    # Key format must match exactly what _widget() produces:
    #   primary_{template.name}__{field}  and  adv_{template.name}__{field}
    params_raw: dict = {}
    for f in template.inputs:
        key     = f"primary_{template.name}__{f.name}"
        adv_key = f"adv_{template.name}__{f.name}"
        ov_key  = f"ov__{template.name}__{f.name}"
        ov_en   = f"oven__{template.name}__{f.name}"
        if key in st.session_state:
            params_raw[f.name] = st.session_state[key]
        elif adv_key in st.session_state:
            params_raw[f.name] = st.session_state[adv_key]
        elif ov_en in st.session_state and st.session_state[ov_en] and ov_key in st.session_state:
            params_raw[f.name] = st.session_state[ov_key]
        else:
            params_raw[f.name] = f.default

    # ── Pre-flight input validation ───────────────────────────────────────
    _validation_errors: list[str] = []
    for f in template.inputs:
        val = params_raw.get(f.name)
        if val is None:
            continue
        if f.dtype in (int, float):
            num = float(val) if val != "" else 0.0
            if f.name.endswith("_ft") and num <= 0:
                _label = f.label if hasattr(f, "label") else f.name.replace("_", " ").title()
                _validation_errors.append(f"{_label} must be greater than zero (got {val})")
            if f.name == "wall_height_ft" and num <= 0:
                _validation_errors.append(f"Wall height must be greater than zero (got {val})")
            if f.name == "num_structures" and num < 1:
                _validation_errors.append(f"Number of structures must be at least 1 (got {val})")

    # Expanded inlet: expanded Y must be larger than standard Y
    if template_name == "G2 Expanded Inlet":
        _y_std = float(params_raw.get("y_dim_ft", 0))
        _y_exp = float(params_raw.get("y_expanded_ft", 0))
        if _y_exp > 0 and _y_std > 0 and _y_exp <= _y_std:
            _validation_errors.append(
                f"Expanded Y ({_y_exp} ft) must be larger than standard Y ({_y_std} ft)")

    if _validation_errors:
        st.session_state.error = "**Input problems:**\n" + "\n".join(
            f"- {e}" for e in _validation_errors)
        st.session_state.bars = None
    else:
        # ── Run engine ────────────────────────────────────────────────────
        log = ReasoningLogger(None)
        with st.spinner("Running engine..."):
            try:
                b = generate_barlist(template, params_raw, log, call_ai=call_ai)
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
            except Exception as exc:
                st.session_state.error = str(exc)
                st.session_state.bars  = None

    # Stream AI explanation immediately after engine run (if API key is set)
    if st.session_state.get("bars") and _api_key_available():
        with st.spinner("AI is explaining the barlist…"):
            try:
                chunks = []
                for chunk in asst.explain_barlist_stream(
                    template_name=template_name,
                    params_raw=params_raw,
                    bars=st.session_state.bars,
                    warnings=st.session_state.warnings,
                    log_lines=st.session_state.get("log_lines"),
                ):
                    chunks.append(chunk)
                st.session_state.explanation = "".join(chunks)
            except Exception:
                st.session_state.explanation = None

    if not st.session_state.get("error"):
        st.rerun()

st.markdown("---")

# ═════════════════════════════════════════════════════════════════════════════
# MAIN CONTENT — diagram | inputs (side by side), results full-width below
# ═════════════════════════════════════════════════════════════════════════════

diag_col, inp_col = st.columns([1.3, 1], gap="large")

# ── DIAGRAM ───────────────────────────────────────────────────────────────────
with diag_col:
    diag = _get_diagram(template_name)
    if diag:
        st.image(diag, use_container_width=True)
    if template.description:
        st.caption(template.description)

# ── INPUTS ────────────────────────────────────────────────────────────────────
with inp_col:
    st.markdown(
        "<div style='font-size:0.78rem;font-weight:700;text-transform:uppercase;"
        "letter-spacing:0.8px;color:#6c737a;margin:0 0 0.4rem'>Dimensions</div>",
        unsafe_allow_html=True,
    )

    # ── Smart suggestions: pre-seed target fields before they render ─────────
    # Read each trigger's current session-state value; if it changed from last
    # render, push the predicted value into the target's session-state key so
    # the widget renders with the suggestion already in place.
    _active_suggestions: dict[str, any] = {}   # target_field → suggested_val
    for _trig, _tgt, _fn in _FIELD_PREDICTIONS.get(template_name, []):
        _trig_key = f"primary_{template_name}__{_trig}"
        _prev_key = f"_prev_{_trig}__{template_name}"
        _trig_val = st.session_state.get(_trig_key)
        if _trig_val is not None:
            _sugg = _fn(_trig_val)
            _active_suggestions[_tgt] = _sugg
            if st.session_state.get(_prev_key) != _trig_val:
                st.session_state[_prev_key] = _trig_val
                st.session_state[f"primary_{template_name}__{_tgt}"] = _sugg

    # Primary inputs
    params_raw: dict = {}
    primary_fields = dflt.get_primary_inputs(template)
    for f in primary_fields:
        name, val = _widget(f, key_prefix=f"primary_{template_name}", container=st)
        params_raw[name] = val
        # Show suggestion note when this field is carrying a predicted value
        if name in _active_suggestions and val == _active_suggestions[name]:
            st.caption(
                f"Standard sizing suggestion — edit to override"
            )

    # ── Caltrans auto-fill ────────────────────────────────────────────────────
    # After collecting primary dims, look up Caltrans standard values for
    # secondary fields (bar sizes, spacing). When primary dims change, reset
    # the secondary widget values to Caltrans standard defaults automatically.
    _ct_result = caltrans_lookup(template_name, params_raw)
    _ct_src    = _ct_result.pop("_source", "")
    _ov_name   = dflt.OVERRIDEABLE.get(template_name, "")

    # Caltrans source badge — visible pill so the user always knows which table ran
    if _ct_src:
        st.markdown(
            f"<div style='display:inline-flex;align-items:center;gap:6px;"
            f"background:#eef2fc;color:#1c3461;border:1px solid #c5d5f8;"
            f"border-radius:20px;padding:3px 12px 3px 8px;font-size:0.72rem;"
            f"font-weight:600;margin:6px 0 2px;letter-spacing:0.2px'>"
            f"<span style='width:7px;height:7px;background:#1c3461;border-radius:50%;"
            f"display:inline-block;flex-shrink:0'></span>"
            f"Caltrans {_ct_src}</div>",
            unsafe_allow_html=True,
        )
    # Exclude the overrideable field — it's handled separately below
    _ct_secondary = {k: v for k, v in _ct_result.items() if k != _ov_name}

    if _ct_secondary:
        _phash_key = f"_phash__{template_name}"
        _phash = hashlib.md5(
            json.dumps(params_raw, sort_keys=True, default=str).encode()
        ).hexdigest()[:8]
        if st.session_state.get(_phash_key) != _phash:
            st.session_state[_phash_key] = _phash
            for _cf, _cv in _ct_secondary.items():
                st.session_state[f"adv_{template_name}__{_cf}"] = _cv

    # Wall thickness shown from Caltrans table or kept auto via engine
    _ct_wall_thick = _ct_result.get(_ov_name) if _ov_name else None

    # Auto-computed / overrideable field (e.g. wall_thick_in)
    ov_field = dflt.get_overrideable_field(template)
    if ov_field:
        ov_en_key  = f"oven__{template.name}__{ov_field.name}"
        ov_val_key = f"ov__{template.name}__{ov_field.name}"
        col_lbl, col_chk = st.columns([3, 1])
        override_on = col_chk.checkbox("override", key=ov_en_key,
                                       help="Uncheck to use Caltrans auto-computed value")
        if override_on:
            lo = int(ov_field.min) if ov_field.min is not None else 0
            hi = int(ov_field.max) if ov_field.max is not None else 36
            dv = int(ov_field.default) if ov_field.default and ov_field.default > 0 else lo + 9
            ov_val = col_lbl.number_input(
                f"{ov_field.label or ov_field.name} (custom)",
                min_value=lo, max_value=hi, value=dv, step=1, key=ov_val_key)
            params_raw[ov_field.name] = ov_val
        else:
            _thick_label = ov_field.label or ov_field.name
            if _ct_wall_thick:
                col_lbl.markdown(
                    f"**{_thick_label}:** "
                    f"<span style='color:#1c3461'>{_ct_wall_thick}\" (Caltrans std)</span>",
                    unsafe_allow_html=True)
                params_raw[ov_field.name] = _ct_wall_thick
            else:
                col_lbl.markdown(
                    f"**{_thick_label}:** "
                    f"<span style='color:#1c3461'>auto (Caltrans std)</span>",
                    unsafe_allow_html=True)
                params_raw[ov_field.name] = 0

    # Advanced inputs (collapsed)
    secondary = dflt.get_secondary_inputs(template)
    if secondary:
        _adv_label = f"Advanced  ({len(secondary)} inputs)"
        if _ct_src:
            _adv_label += f"  ·  Caltrans {_ct_src}"
        with st.expander(_adv_label, expanded=False):
            if _ct_src and _ct_secondary:
                st.caption(
                    f"Values pre-filled from Caltrans standard plan ({_ct_src}). "
                    "Edit any field to override."
                )
            for f in secondary:
                name, val = _widget(f, key_prefix=f"adv_{template.name}", container=st)
                params_raw[name] = val

    # Store current params (used by refresh and re-explain)
    st.session_state._last_params = params_raw
    # Hash for staleness detection (has the user changed inputs since last generate?)
    _cur_phash = hashlib.md5(json.dumps(params_raw, sort_keys=True, default=str).encode()).hexdigest()[:12]
    st.session_state._cur_params_hash = _cur_phash

# ── RESULTS — full width below diagram + inputs ───────────────────────────────
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

    # Metrics
    m1, m2, m3 = st.columns(3)
    m1.metric("Marks",      len({b.mark for b in bars}))
    m2.metric("Total Bars", f"{sum(b.qty for b in bars):,}")
    m3.metric("Weight",     f"{weight_lb:,.1f} lb")

    st.markdown("")

    # Barlist table
    df = pd.DataFrame([{
        "Mark":   b.mark,  "Size":   b.size,   "Qty":    b.qty,
        "Length": b.length_ft_in,
        "Type":   SHAPE_SYMBOLS.get(b.shape, b.shape),
        "Leg A":  b.leg_a_ft_in, "Leg B":  b.leg_b_ft_in, "Leg C":  b.leg_c_ft_in,
        "Notes":  b.notes, "Ref":    b.ref,    "Review": b.review_flag,
    } for b in bars])

    def _hl(row):
        return ["background-color:#fff3cd"]*len(row) if row["Review"] else [""]*len(row)

    st.dataframe(df.style.apply(_hl, axis=1),
                 use_container_width=True, hide_index=True, height=320)

    # ── Computation Trace (deterministic) ─────────────────────────────────────
    _trace_lines = st.session_state.get("log_lines", [])
    if _trace_lines:
        with st.expander("Computation Trace", expanded=False):
            _trace_html_parts = []
            for _ts, _tag, _msg, _detail, _src in _trace_lines:
                _tag = _tag.strip()
                _msg = html.escape(_msg.strip())
                _detail = html.escape((_detail or "").strip())

                if not _tag and not _msg:
                    _trace_html_parts.append("<div style='height:6px'></div>")
                    continue
                if _tag == "────":
                    _trace_html_parts.append(
                        "<hr style='border:none;border-top:1px solid #d0d5dd;margin:8px 0'>"
                    )
                    continue

                # Color-code by tag type
                if _tag == "WARN":
                    _color = "#c62828"
                    _bg = "#fff3e0"
                    _prefix = "[!] "
                elif _tag == "OUT":
                    _color = "#1565c0"
                    _bg = "#e3f2fd"
                    _prefix = ""
                elif _tag == "RULE":
                    _color = "#37474f"
                    _bg = "#eceff1"
                    _prefix = ""
                elif _tag == "DONE":
                    _color = "#2e7d32"
                    _bg = "#e8f5e9"
                    _prefix = ""
                else:
                    _color = "#1a1d23"
                    _bg = "transparent"
                    _prefix = ""

                _detail_span = (
                    f"<span style='color:#78909c;font-size:0.78rem;margin-left:8px'>{_detail}</span>"
                    if _detail else ""
                )
                _trace_html_parts.append(
                    f"<div style='background:{_bg};padding:2px 8px;margin:1px 0;"
                    f"font-family:monospace;font-size:0.82rem;color:{_color};"
                    f"border-radius:3px;line-height:1.5'>"
                    f"<b style='min-width:50px;display:inline-block'>{html.escape(_tag)}</b> "
                    f"{_prefix}{_msg}{_detail_span}</div>"
                )

            st.markdown(
                "<div style='max-height:400px;overflow-y:auto;border:1px solid #e8eaed;"
                "border-radius:8px;padding:6px'>"
                + "".join(_trace_html_parts)
                + "</div>",
                unsafe_allow_html=True,
            )

    # ── AI Explanation card ───────────────────────────────────────────────────
    explanation = st.session_state.get("explanation")
    _api_ready  = _api_key_available()

    st.markdown(
        "<div style='display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem'>"
        "<span style='background:#1c3461;color:#fff;border-radius:5px;padding:2px 8px;"
        "font-size:0.7rem;font-weight:700;letter-spacing:0.5px'>AI</span>"
        "<span style='font-size:0.78rem;font-weight:700;text-transform:uppercase;"
        "letter-spacing:0.8px;color:#6c737a'>Barlist Explanation</span>"
        "</div>",
        unsafe_allow_html=True,
    )

    if explanation:
        # Detect if inputs changed since the barlist was generated
        _gen_hash = st.session_state.get("_gen_params_hash", "")
        _cur_hash = st.session_state.get("_cur_params_hash", "")
        if _gen_hash and _cur_hash and _gen_hash != _cur_hash:
            st.caption(
                "Inputs have changed since this barlist was generated. "
                "Click **Generate** to update the results and explanation."
            )
        st.markdown(
            f"<div style='background:#ffffff;border:1px solid #e8eaed;border-left:4px solid #1c3461;"
            f"border-radius:0 10px 10px 0;padding:1.1rem 1.3rem;line-height:1.7;"
            f"font-size:0.87rem;color:#1a1d23'>{explanation}</div>",
            unsafe_allow_html=True,
        )
        if st.button("Re-explain", key="btn_reexplain", help="Generate a fresh explanation"):
            st.session_state.explanation = None
            with st.spinner("Re-generating explanation…"):
                try:
                    chunks = []
                    for chunk in asst.explain_barlist_stream(
                        template_name=template_name,
                        params_raw=st.session_state.get("_last_params"),
                        bars=bars,
                        warnings=st.session_state.get("warnings", []),
                        log_lines=st.session_state.get("log_lines"),
                    ):
                        chunks.append(chunk)
                    st.session_state.explanation = "".join(chunks)
                    st.rerun()
                except Exception as exc:
                    st.error(f"Explanation error: {exc}")
    elif not _api_ready:
        st.markdown(
            "<div style='background:#f8f9fa;border:1px solid #e8eaed;border-radius:8px;"
            "padding:0.9rem 1.1rem;color:#6c737a;font-size:0.84rem'>"
            "Set <code>ANTHROPIC_API_KEY</code> to enable AI explanations.</div>",
            unsafe_allow_html=True,
        )
    else:
        st.info("Explanation will appear after the next generate.")

# ═════════════════════════════════════════════════════════════════════════════
# BOTTOM TABS — always visible
# ═════════════════════════════════════════════════════════════════════════════

st.markdown("---")

# Determine active tab from button clicks
_active = st.session_state.get("_active_tab", 0)
if show_cut_tab:
    _active = 2
if show_hist_tab:
    _active = 3
st.session_state._active_tab = _active

tab_warn, tab_log, tab_cut, tab_hist = st.tabs([
    f"Warnings{f' ({len(warnings)})' if warnings else ''}",
    "Reasoning Log",
    "Cut Optimizer",
    "History",
])

# ── Warnings ──────────────────────────────────────────────────────────────────
with tab_warn:
    if warnings:
        for _ts, _tag, msg, detail, _src in warnings:
            st.warning(f"{msg}\n\n_{detail}_" if detail else msg)
    elif bars is not None:
        st.success("All checks passed — no validation warnings.")
    else:
        st.info("Warnings will appear here after generation.")

# ── Reasoning Log ─────────────────────────────────────────────────────────────
with tab_log:
    non_blank = [(ts, tag, msg, det, src) for ts, tag, msg, det, src in log_lines if msg.strip()]
    if non_blank:
        log_df = pd.DataFrame(non_blank, columns=["Time","Tag","Message","Detail","Source"])
        st.dataframe(log_df, use_container_width=True, hide_index=True, height=420)
    else:
        st.info("Reasoning log appears here after generation.")

# ── Cut Optimizer ─────────────────────────────────────────────────────────────
with tab_cut:
    if bars is not None:
        ca, cb, cc = st.columns([1, 1, 3])
        with ca:
            stock_ft = st.selectbox("Stock Length", [20, 40, 60], index=0,
                                    format_func=lambda x: f"{x} ft", key="cut_stock")
            st.caption("FFD bin-packing")
        with cb:
            price_lb = st.number_input("Price per lb ($)", min_value=0.0, max_value=10.0,
                                       value=0.80, step=0.05, format="%.2f", key="cut_price_lb")
            st.caption("Material cost estimate")

        results = _cut_optimize(bars, stock_ft * 12)
        disp_cols = ["Size","Sticks","Stock (ft)","Ordered (ft)","Used (ft)","Waste (ft)","Waste %"]
        df_cut = pd.DataFrame([{c: r[c] for c in disp_cols} for r in results])

        def _hl_waste(row):
            return ["background-color:#fff3cd"]*len(row) if row["Waste %"] > 20 else [""]*len(row)

        with cc:
            st.dataframe(df_cut.style.apply(_hl_waste, axis=1),
                         use_container_width=True, hide_index=True)

        for r in results:
            if r["_oversized"]:
                st.warning(f"**{r['Size']}**: {r['_oversized']} bar(s) exceed {stock_ft} ft — special order required.")

        # Summary + cost estimate
        from vistadetail.engine.hooks import BAR_WEIGHT_LB_FT as _WLBFT
        total_sticks = sum(r["Sticks"] for r in results)
        total_waste  = round(sum(r["Waste (ft)"] for r in results), 1)
        avg_waste    = round(sum(r["Waste %"] for r in results) / len(results), 1) if results else 0
        total_ordered_lb = sum(
            r["Sticks"] * stock_ft * _WLBFT.get(r["Size"], 0.0)
            for r in results
        )
        est_cost = total_ordered_lb * price_lb

        sm1, sm2, sm3, sm4, dl_c = st.columns([1, 1, 1, 1, 1])
        sm1.metric("Sticks",      total_sticks)
        sm2.metric("Waste",       f"{total_waste} ft  ({avg_waste}%)")
        sm3.metric("Ordered Wt",  f"{total_ordered_lb:,.0f} lb")
        sm4.metric("Est. Cost",   f"${est_cost:,.2f}")
        dl_c.download_button("Cut List CSV", data=_manifest_csv(results),
                             file_name="cut_list.csv", mime="text/csv", key="btn_cutcsv")

        st.markdown("**Stick Manifest**")
        for r in results:
            mdf = pd.DataFrame(r["_manifest"])[["Stick #","Cuts","# Pcs","Waste"]]
            with st.expander(f"{r['Size']} — {r['Sticks']} sticks  ({r['Waste %']}% waste)"):
                st.dataframe(mdf, use_container_width=True, hide_index=True)

        # Visual stick layout
        with st.expander("Stick Cut Layout Chart", expanded=False):
            import matplotlib.pyplot as plt
            _fig = _draw_cuts_chart(results, stock_ft * 12)
            st.pyplot(_fig, use_container_width=True)
            plt.close(_fig)
    else:
        st.info("Generate a barlist to use the cut optimizer.")

# ── History ───────────────────────────────────────────────────────────────────
with tab_hist:
    runs = hist.list_runs()
    if not runs:
        st.info("No history yet.")
    else:
        disp = [{"#": r["id"], "Date": r["timestamp"], "Template": r["template_name"],
                 "Project": r["job_name"] or "—", "Job #": r["job_number"] or "—",
                 "Detailer": r["detailer"] or "—",
                 "Weight (lb)": r["total_weight_lb"]}
                for r in runs]
        st.dataframe(pd.DataFrame(disp), use_container_width=True, hide_index=True)

        st.markdown("---")
        opts = {f"#{r['id']}  {r['timestamp']}  —  {r['template_name']}  —  {r['job_name'] or 'no job'}": r["id"]
                for r in runs}
        sel = st.selectbox("View run", list(opts.keys()), key="hist_sel")
        if sel:
            run = hist.load_run(opts[sel])
            if run:
                hbars = run["bars"]
                hweight = barlist_total_weight_lb(hbars)
                hj = [f"**{k}:** {v}" for k, v in
                      [("Project", run["job_name"]), ("Job #", run["job_number"]),
                       ("Detailer", run["detailer"])] if v]
                if hj:
                    st.markdown("  |  ".join(hj))
                hm1, hm2, hm3 = st.columns(3)
                hm1.metric("Marks",  len({b.mark for b in hbars}))
                hm2.metric("Bars",   sum(b.qty for b in hbars))
                hm3.metric("Weight", f"{hweight:,.1f} lb")

                hx1, hx2, _s = st.columns([1,1,5])
                hx1.download_button("CSV", data=_make_csv(hbars),
                                    file_name=f"run_{run['id']}.csv", mime="text/csv",
                                    key=f"hcsv_{run['id']}")
                try:
                    ji2 = {"Project": run["job_name"], "Job #": run["job_number"],
                           "Detailer": run["detailer"]}
                    hx2.download_button("PDF", data=_make_pdf(hbars, run["template_name"], ji2),
                                        file_name=f"run_{run['id']}.pdf", mime="application/pdf",
                                        key=f"hpdf_{run['id']}")
                except ImportError:
                    pass

                hdf = pd.DataFrame([{
                    "Mark": b.mark, "Size": b.size, "Qty": b.qty,
                    "Length": b.length_ft_in, "Shape": b.shape,
                    "Notes": b.notes, "Ref": b.ref,
                } for b in hbars])
                st.dataframe(hdf, use_container_width=True, hide_index=True)

                _del_col1, _del_col2 = st.columns([1, 4])
                with _del_col1:
                    _del_clicked = st.button(
                        f"Delete run #{run['id']}", key=f"hdel_{run['id']}",
                        type="secondary")
                if _del_clicked:
                    _confirm_key = f"_confirm_del_{run['id']}"
                    st.session_state[_confirm_key] = True
                if st.session_state.get(f"_confirm_del_{run['id']}"):
                    with _del_col2:
                        st.warning("Are you sure? This cannot be undone.")
                    _c1, _c2, _c3 = st.columns([1, 1, 4])
                    if _c1.button("Yes, delete", key=f"hdelyes_{run['id']}",
                                  type="primary"):
                        hist.delete_run(run["id"])
                        st.session_state.pop(f"_confirm_del_{run['id']}", None)
                        _template_stats.clear()
                        st.rerun()
                    if _c2.button("Cancel", key=f"hdelno_{run['id']}"):
                        st.session_state.pop(f"_confirm_del_{run['id']}", None)
                        st.rerun()

        # ── Compare two runs ──────────────────────────────────────────────────
        if len(runs) >= 2:
            st.markdown("---")
            st.markdown(
                "<div style='font-size:0.78rem;font-weight:700;text-transform:uppercase;"
                "letter-spacing:0.8px;color:#6c737a;margin-bottom:0.5rem'>Compare Two Runs</div>",
                unsafe_allow_html=True,
            )
            comp_opts = {
                f"#{r['id']}  {r['timestamp']}  —  {r['template_name']}  —  {r['job_name'] or 'no job'}": r["id"]
                for r in runs
            }
            _keys = list(comp_opts.keys())
            cc1, cc2 = st.columns(2)
            run_a_key = cc1.selectbox("Run A", _keys, index=0, key="comp_run_a")
            run_b_key = cc2.selectbox("Run B", _keys, index=min(1, len(_keys)-1), key="comp_run_b")

            if run_a_key != run_b_key:
                _ra = hist.load_run(comp_opts[run_a_key])
                _rb = hist.load_run(comp_opts[run_b_key])
                if _ra and _rb:
                    _wa = barlist_total_weight_lb(_ra["bars"])
                    _wb = barlist_total_weight_lb(_rb["bars"])
                    _marks_a = len({b.mark for b in _ra["bars"]})
                    _marks_b = len({b.mark for b in _rb["bars"]})
                    _qty_a   = sum(b.qty for b in _ra["bars"])
                    _qty_b   = sum(b.qty for b in _rb["bars"])

                    cm1, cm2, cm3, cm4, cm5, cm6 = st.columns(6)
                    cm1.metric("A: Marks",  _marks_a)
                    cm2.metric("A: Bars",   _qty_a)
                    cm3.metric("A: Weight", f"{_wa:,.1f} lb")
                    cm4.metric("B: Marks",  _marks_b,  delta=_marks_b - _marks_a)
                    cm5.metric("B: Bars",   _qty_b,    delta=_qty_b - _qty_a)
                    cm6.metric("B: Weight", f"{_wb:,.1f} lb",
                               delta=f"{_wb - _wa:+,.1f} lb")

                    # Aligned diff by mark
                    _ma = {b.mark: b for b in _ra["bars"]}
                    _mb = {b.mark: b for b in _rb["bars"]}
                    _all_marks = sorted(set(_ma) | set(_mb))
                    _comp_rows = []
                    for m in _all_marks:
                        a, b_ = _ma.get(m), _mb.get(m)
                        changed = (
                            "Added"   if not a else
                            "Removed" if not b_ else
                            "" if (a.size == b_.size and a.qty == b_.qty and a.length_in == b_.length_in)
                            else "Changed"
                        )
                        _comp_rows.append({
                            "Mark":     m,
                            "A Size":   a.size       if a  else "—",
                            "A Qty":    a.qty        if a  else "—",
                            "A Length": a.length_ft_in if a else "—",
                            "B Size":   b_.size      if b_ else "—",
                            "B Qty":    b_.qty       if b_ else "—",
                            "B Length": b_.length_ft_in if b_ else "—",
                            "Status":   changed,
                        })

                    def _hl_comp(row):
                        if row["Status"] == "Added":
                            return ["background-color:#d4edda"] * len(row)
                        if row["Status"] == "Removed":
                            return ["background-color:#f8d7da"] * len(row)
                        if row["Status"] == "Changed":
                            return ["background-color:#fff3cd"] * len(row)
                        return [""] * len(row)

                    _comp_df = pd.DataFrame(_comp_rows)
                    st.dataframe(_comp_df.style.apply(_hl_comp, axis=1),
                                 use_container_width=True, hide_index=True)
                    st.caption("Green = added in B  |  Red = removed in B  |  Yellow = changed")
            else:
                st.info("Select two different runs to compare.")

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
