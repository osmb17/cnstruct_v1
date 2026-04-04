"""
CNSTRUCT 1.0 — Rebar Detail Generator
Streamlit web app  ·  streamlit run app.py
"""

from __future__ import annotations

import csv
import io
import os
from datetime import date

import pandas as pd
import streamlit as st

import assistant as asst
import defaults as dflt

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

/* ── Chat messages ───────────────────────────────────────────── */
[data-testid="stChatMessage"] {
    background: #ffffff !important;
    border: 1px solid #e8eaed !important;
    border-radius: 10px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
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
        f"Date: {date.today()}  |  Weight: {weight_lb:,.1f} lb",
        styles["Normal"]))
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

h1, h2, h3, h4, h5 = st.columns([2, 2.5, 1.8, 1.8, 1.2])

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
    detailer = st.text_input("Detailer", key="detailer", placeholder="Name / initials")

with h4:
    job_name   = st.text_input("Project", key="job_name",   placeholder="Project name")
    job_number = st.text_input("Job #",   key="job_number", placeholder="2024-0042")

with h5:
    run_date = st.date_input("Date", value=date.today(), key="run_date",
                             label_visibility="visible")

# Template change → clear results
if template_name != st.session_state.get("_last_template"):
    st.session_state._last_template = template_name
    for _k in ("bars","log_lines","warnings","error"):
        st.session_state.pop(_k, None)

template = TEMPLATE_REGISTRY[template_name]

# ── Options ───────────────────────────────────────────────────────────────────
with st.expander("Options", expanded=False):
    call_ai = st.toggle("AI Reviewer Notes", value=False, key="opt_ai",
                        help="Requires ANTHROPIC_API_KEY env var")

st.markdown("---")

# ═════════════════════════════════════════════════════════════════════════════
# BUTTON BAR
# ═════════════════════════════════════════════════════════════════════════════

bars     = st.session_state.get("bars")
log_lines = st.session_state.get("log_lines", [])
warnings  = st.session_state.get("warnings", [])

b1, b2, b3, b4, b5, b6, b7 = st.columns(7)

generate_btn = b1.button("⚡ Generate",  type="primary", use_container_width=True, key="btn_gen")
refresh_btn  = b2.button("↺ Refresh",   use_container_width=True, key="btn_refresh",
                          disabled=bars is None)
clear_btn    = b3.button("✕ Clear All", use_container_width=True, key="btn_clear")

# CSV + PDF download buttons (or disabled placeholders)
if bars is not None:
    b4.download_button("↓ Export CSV",
                       data=_make_csv(bars),
                       file_name=f"{template_name.replace(' ','_')}_barlist.csv",
                       mime="text/csv", use_container_width=True, key="btn_csv")
    try:
        ji = {"Project": job_name, "Job #": job_number, "Detailer": detailer}
        b5.download_button("↓ Compose Hoja",
                           data=_make_pdf(bars, template_name, ji),
                           file_name=f"{template_name.replace(' ','_')}_barlist.pdf",
                           mime="application/pdf", use_container_width=True, key="btn_pdf")
    except ImportError:
        b5.button("↓ Compose Hoja", disabled=True, use_container_width=True, key="btn_pdf_na")
else:
    b4.button("↓ Export CSV",   disabled=True, use_container_width=True, key="btn_csv_na")
    b5.button("↓ Compose Hoja", disabled=True, use_container_width=True, key="btn_pdf_na")

show_cut_tab  = b6.button("✂ Cut Optimizer", use_container_width=True, key="btn_cut")
show_hist_tab = b7.button("📋 History",       use_container_width=True, key="btn_hist")

# ── Button actions ────────────────────────────────────────────────────────────

if clear_btn:
    for _k in ("bars","log_lines","warnings","error"):
        st.session_state.pop(_k, None)
    st.rerun()

if generate_btn or refresh_btn:
    # Collect params from session state widgets
    st.session_state.pop("error", None)

if generate_btn or refresh_btn:
    # Build params_raw from current widget values
    params_raw: dict = {}
    for f in template.inputs:
        key = f"primary__{template.name}__{f.name}"
        adv_key = f"adv__{template.name}__{f.name}"
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

    log = ReasoningLogger(None)
    with st.spinner("Running engine…"):
        try:
            b = generate_barlist(template, params_raw, log, call_ai=call_ai)
            st.session_state.bars        = b
            st.session_state.log_lines   = log.get_lines()
            st.session_state.warnings    = [ln for ln in log.get_lines() if ln[1].strip()=="WARN"]
            st.session_state.error       = None
            st.session_state.explanation = None   # clear old explanation
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
                ):
                    chunks.append(chunk)
                st.session_state.explanation = "".join(chunks)
            except Exception:
                st.session_state.explanation = None

    if not st.session_state.get("error"):
        st.rerun()

st.markdown("---")

# ═════════════════════════════════════════════════════════════════════════════
# MAIN CONTENT — left: diagram + inputs   right: barlist
# ═════════════════════════════════════════════════════════════════════════════

left, right = st.columns([2, 3], gap="large")

# ── LEFT PANEL ────────────────────────────────────────────────────────────────
with left:
    # Template diagram
    diag = _get_diagram(template_name)
    if diag:
        st.image(diag, use_container_width=True)
    if template.description:
        st.caption(template.description)

    st.markdown(
        "<div style='font-size:0.78rem;font-weight:700;text-transform:uppercase;"
        "letter-spacing:0.8px;color:#6c737a;margin:0.75rem 0 0.4rem'>Dimensions</div>",
        unsafe_allow_html=True,
    )

    # Primary inputs
    params_raw: dict = {}
    primary_fields = dflt.get_primary_inputs(template)
    for f in primary_fields:
        name, val = _widget(f, key_prefix=f"primary_{template.name}", container=st)
        params_raw[name] = val

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
            col_lbl.markdown(
                f"**{ov_field.label or ov_field.name}:** "
                f"<span style='color:#1c3461'>auto (Caltrans std)</span>",
                unsafe_allow_html=True)
            params_raw[ov_field.name] = 0

    # Advanced inputs (collapsed)
    secondary = dflt.get_secondary_inputs(template)
    if secondary:
        with st.expander(f"Advanced  ({len(secondary)} inputs)", expanded=False):
            for f in secondary:
                name, val = _widget(f, key_prefix=f"adv_{template.name}", container=st)
                params_raw[name] = val

    # Store params for refresh
    st.session_state._last_params = params_raw

# ── RIGHT PANEL ───────────────────────────────────────────────────────────────
with right:
    if st.session_state.get("error"):
        st.error(f"**Error:** {st.session_state.error}")

    if bars is not None:
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
            "Length": b.length_ft_in, "Shape":  b.shape,
            "Leg A":  b.leg_a_ft_in, "Leg B":  b.leg_b_ft_in, "Leg C":  b.leg_c_ft_in,
            "Notes":  b.notes, "Ref":    b.ref,    "Review": b.review_flag,
        } for b in bars])

        def _hl(row):
            return ["background-color:#fff3cd"]*len(row) if row["Review"] else [""]*len(row)

        st.dataframe(df.style.apply(_hl, axis=1),
                     use_container_width=True, hide_index=True, height=320)

        # ── AI Explanation card ───────────────────────────────────────────────
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
            st.markdown(
                f"<div style='background:#ffffff;border:1px solid #e8eaed;border-left:4px solid #1c3461;"
                f"border-radius:0 10px 10px 0;padding:1.1rem 1.3rem;line-height:1.7;"
                f"font-size:0.87rem;color:#1a1d23'>{explanation}</div>",
                unsafe_allow_html=True,
            )
            if st.button("↺ Re-explain", key="btn_reexplain", help="Generate a fresh explanation"):
                st.session_state.explanation = None
                with st.spinner("Re-generating explanation…"):
                    try:
                        chunks = []
                        for chunk in asst.explain_barlist_stream(
                            template_name=template_name,
                            params_raw=st.session_state.get("_last_params"),
                            bars=bars,
                            warnings=st.session_state.get("warnings", []),
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

    else:
        # Empty state
        st.markdown(
            "<div style='text-align:center;padding:3rem 1rem;color:#8a909a'>"
            "<div style='font-size:2.5rem;margin-bottom:0.5rem'>📐</div>"
            "<div style='font-size:1rem;font-weight:600;color:#374151;margin-bottom:0.25rem'>"
            "Ready to generate</div>"
            "<div style='font-size:0.85rem'>Set dimensions and click "
            "<strong>⚡ Generate</strong></div>"
            "</div>",
            unsafe_allow_html=True,
        )
        rows = [{"Template": nm,
                 "Primary Inputs": len(dflt.PRIMARY_INPUTS.get(nm, [])),
                 "Total Inputs": len(TEMPLATE_REGISTRY[nm].inputs),
                 "Rules": len(TEMPLATE_REGISTRY[nm].rules)}
                for nm in TEMPLATE_NAMES]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

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
    f"⚠ Warnings{f' ({len(warnings)})' if warnings else ''}",
    "📄 Reasoning Log",
    "✂ Cut Optimizer",
    "📋 History",
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
        ca, cb = st.columns([1, 3])
        with ca:
            stock_ft = st.selectbox("Stock Length", [20, 40, 60], index=0,
                                    format_func=lambda x: f"{x} ft", key="cut_stock")
            st.caption("FFD bin-packing")
        results = _cut_optimize(bars, stock_ft * 12)
        disp_cols = ["Size","Sticks","Stock (ft)","Ordered (ft)","Used (ft)","Waste (ft)","Waste %"]
        df_cut = pd.DataFrame([{c: r[c] for c in disp_cols} for r in results])

        def _hl_waste(row):
            return ["background-color:#fff3cd"]*len(row) if row["Waste %"] > 20 else [""]*len(row)

        with cb:
            st.dataframe(df_cut.style.apply(_hl_waste, axis=1),
                         use_container_width=True, hide_index=True)

        for r in results:
            if r["_oversized"]:
                st.warning(f"**{r['Size']}**: {r['_oversized']} bar(s) exceed {stock_ft} ft — special order required.")

        total_sticks = sum(r["Sticks"] for r in results)
        total_waste  = round(sum(r["Waste (ft)"] for r in results), 1)
        avg_waste    = round(sum(r["Waste %"] for r in results) / len(results), 1) if results else 0

        inf_c, dl_c = st.columns([4, 1])
        inf_c.info(f"**{total_sticks}** sticks  |  **{total_waste} ft** waste  |  **{avg_waste}%** avg waste")
        dl_c.download_button("↓ Cut List CSV", data=_manifest_csv(results),
                             file_name="cut_list.csv", mime="text/csv", key="btn_cutcsv")

        st.markdown("**Stick Manifest**")
        for r in results:
            mdf = pd.DataFrame(r["_manifest"])[["Stick #","Cuts","# Pcs","Waste"]]
            with st.expander(f"{r['Size']} — {r['Sticks']} sticks  ({r['Waste %']}% waste)"):
                st.dataframe(mdf, use_container_width=True, hide_index=True)
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
                hx1.download_button("↓ CSV", data=_make_csv(hbars),
                                    file_name=f"run_{run['id']}.csv", mime="text/csv",
                                    key=f"hcsv_{run['id']}")
                try:
                    ji2 = {"Project": run["job_name"], "Job #": run["job_number"],
                           "Detailer": run["detailer"]}
                    hx2.download_button("↓ PDF", data=_make_pdf(hbars, run["template_name"], ji2),
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

                if st.button(f"Delete run #{run['id']}", key=f"hdel_{run['id']}"):
                    hist.delete_run(run["id"])
                    _template_stats.clear()
                    st.rerun()

# ═════════════════════════════════════════════════════════════════════════════
# AI ASSISTANT — full-width chat section
# ═════════════════════════════════════════════════════════════════════════════

st.markdown("---")
st.markdown(
    "<div style='display:flex;align-items:center;gap:10px;margin-bottom:0.75rem'>"
    "<span style='background:#1c3461;color:#fff;border-radius:6px;padding:4px 10px;"
    "font-size:0.82rem;font-weight:700;letter-spacing:0.5px'>AI</span>"
    "<span style='font-size:1.1rem;font-weight:700;color:#1a1d23'>Rebar Detailing Assistant</span>"
    "<span style='font-size:0.8rem;color:#8a909a;margin-left:4px'>— ask anything about this barlist, "
    "ACI 318-19, Caltrans, or rebar detailing in general</span>"
    "</div>",
    unsafe_allow_html=True,
)

_api_key_set = _api_key_available()

if not _api_key_set:
    st.info(
        "💡 Set `ANTHROPIC_API_KEY` in your environment to enable the AI assistant and auto-explanations.\n\n"
        "```bash\nexport ANTHROPIC_API_KEY=sk-ant-...\n```"
    )
else:
    # Reset chat when template changes
    if st.session_state.get("_chat_template") != template_name:
        st.session_state.chat_messages = []
        st.session_state._chat_template = template_name

    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    # Build context-aware system prompt (includes barlist + explanation if available)
    _explanation_ctx = st.session_state.get("explanation", "")
    _chat_system = asst.build_system_prompt(
        template_name=template_name,
        params_raw=st.session_state.get("_last_params"),
        bars=st.session_state.get("bars"),
        cost=None,
        warnings=st.session_state.get("warnings", []),
    )
    if _explanation_ctx:
        _chat_system += f"\n\n## Prior AI Explanation\nYou already generated this explanation for this barlist:\n{_explanation_ctx}"

    # Suggested follow-up prompts (dynamic per template)
    _has_bars = st.session_state.get("bars") is not None
    _suggestions = [
        f"What does each bar mark mean for a {template_name}?",
        "Walk me through the quantity formula for one of these bars",
        "What ACI 318-19 sections apply here?",
        "What should I double-check before submitting this barlist?",
        "How does cover affect the bar count in this design?",
        "Explain the difference between primary and temperature/shrinkage steel here",
    ]

    if not st.session_state.chat_messages:
        st.markdown(
            "<div style='background:#f0f4ff;border:1px solid #d0d9f0;border-radius:10px;"
            "padding:1rem 1.2rem;margin-bottom:1rem'>"
            "<div style='font-weight:600;color:#1c3461;margin-bottom:0.5rem;font-size:0.9rem'>"
            "💬 Try asking…</div>"
            "<div style='display:flex;flex-wrap:wrap;gap:0.4rem'>",
            unsafe_allow_html=True,
        )
        # Show suggestion buttons in columns
        sug_cols = st.columns(3)
        for i, sug in enumerate(_suggestions):
            if sug_cols[i % 3].button(sug, key=f"sug_{i}", use_container_width=True):
                st.session_state.chat_messages.append({"role": "user", "content": sug})
                st.rerun()
        st.markdown("</div></div>", unsafe_allow_html=True)

    # Render conversation history
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.chat_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # Chat input
    if user_input := st.chat_input(
        f"Ask about this {template_name} barlist, ACI code, or rebar detailing…",
        key="chat_input",
    ):
        st.session_state.chat_messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            placeholder = st.empty()
            full_response = ""
            try:
                for chunk in asst.chat_stream(st.session_state.chat_messages, system=_chat_system):
                    full_response += chunk
                    placeholder.markdown(full_response + "▌")
                placeholder.markdown(full_response)
                st.session_state.chat_messages.append(
                    {"role": "assistant", "content": full_response}
                )
            except Exception as exc:
                err = f"Assistant error: {exc}"
                placeholder.error(err)
                st.session_state.chat_messages.append({"role": "assistant", "content": err})

    # Clear button — only when there's a conversation
    if st.session_state.chat_messages:
        if st.button("Clear conversation", key="chat_clear"):
            st.session_state.chat_messages = []
            st.rerun()
