"""
Auto-generate labeled engineering schematic diagrams for each structure template.

Each diagram draws a clean cross-section or plan view with:
  - Gray filled concrete shapes
  - Red lines / dots for rebar
  - Dimension callouts labeled with the exact input parameter name

Usage:
    from vistadetail.workbook.diagram_generator import generate_diagram_png
    png_bytes = generate_diagram_png("G2 Inlet", params_dict)

Returns raw PNG bytes — write to a temp file and embed via xlwings pictures.add().
"""

from __future__ import annotations

import io
import math
from typing import Any

import matplotlib
matplotlib.use("Agg")   # non-interactive — no window needed
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# ── Colour palette ────────────────────────────────────────────────────────────
_C  = "#CCCCCC"      # concrete fill (light gray)
_CD = "#999999"      # concrete edge / dark fill
_R  = "#CC2222"      # rebar
_E  = "#C8B97A"      # earth / soil fill
_V  = "#DCF0FF"      # void / open interior
_W  = "#FFFFFF"      # white background
_D  = "#222222"      # dimension / text
_H  = "#1C3461"      # Vista navy (title)

_LW_CONC  = 1.5      # outline linewidth
_LW_REBAR = 1.8
_LW_DIM   = 0.8
_FS       = 7.5      # default font size for labels
_FS_TITLE = 9.5


# ── Helpers ───────────────────────────────────────────────────────────────────

def _rect(ax, x, y, w, h, fc=_C, ec=_CD, lw=_LW_CONC, zorder=2, alpha=1.0):
    ax.add_patch(mpatches.Rectangle(
        (x, y), w, h, facecolor=fc, edgecolor=ec,
        linewidth=lw, zorder=zorder, alpha=alpha
    ))


def _bar(ax, x1, y1, x2, y2, lw=_LW_REBAR):
    ax.plot([x1, x2], [y1, y2], color=_R, lw=lw, solid_capstyle="round", zorder=4)


def _dot(ax, x, y, s=18):
    ax.scatter([x], [y], s=s, color=_R, zorder=4)


def _callout(ax, xy, txt, xytext, fs=_FS):
    """Arrow pointing from xytext label to xy point on drawing."""
    ax.annotate(
        txt, xy=xy, xytext=xytext,
        fontsize=fs, color=_D, ha="center", va="center",
        fontfamily="monospace",
        arrowprops=dict(arrowstyle="->", color=_D, lw=0.7, shrinkA=2, shrinkB=3),
        bbox=dict(boxstyle="round,pad=0.2", fc=_W, ec="none", alpha=0.9),
        zorder=6,
    )


def _label(ax, x, y, txt, ha="center", va="center", fs=_FS, bold=False, color=_D):
    ax.text(x, y, txt, ha=ha, va=va, fontsize=fs, color=color,
            fontfamily="monospace", fontweight="bold" if bold else "normal",
            bbox=dict(boxstyle="round,pad=0.15", fc=_W, ec="none", alpha=0.85),
            zorder=6)


def _dim_h(ax, x1, x2, y, label, y_off=0.25, fs=_FS):
    """Horizontal dimension line."""
    ax.annotate("", xy=(x2, y + y_off), xytext=(x1, y + y_off),
                arrowprops=dict(arrowstyle="<->", color=_D, lw=_LW_DIM))
    ax.plot([x1, x1], [y, y + y_off], color=_D, lw=0.5, ls=":")
    ax.plot([x2, x2], [y, y + y_off], color=_D, lw=0.5, ls=":")
    _label(ax, (x1 + x2) / 2, y + y_off + 0.08, label, fs=fs)


def _dim_v(ax, y1, y2, x, label, x_off=-0.35, fs=_FS):
    """Vertical dimension line."""
    ax.annotate("", xy=(x + x_off, y2), xytext=(x + x_off, y1),
                arrowprops=dict(arrowstyle="<->", color=_D, lw=_LW_DIM))
    ax.plot([x, x + x_off], [y1, y1], color=_D, lw=0.5, ls=":")
    ax.plot([x, x + x_off], [y2, y2], color=_D, lw=0.5, ls=":")
    ax.text(x + x_off - 0.08, (y1 + y2) / 2, label,
            ha="right", va="center", fontsize=fs, color=_D,
            fontfamily="monospace", rotation=90,
            bbox=dict(boxstyle="round,pad=0.15", fc=_W, ec="none", alpha=0.85),
            zorder=6)


def _fig(w=8.5, h=5.2, title=""):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_aspect("equal", adjustable="datalim")
    ax.axis("off")
    fig.patch.set_facecolor(_W)
    ax.set_facecolor(_W)
    if title:
        fig.suptitle(title, fontsize=_FS_TITLE, fontweight="bold",
                     color=_H, y=0.97)
    return fig, ax


def _to_png(fig) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight",
                facecolor=_W, edgecolor="none")
    buf.seek(0)
    plt.close(fig)
    return buf.read()


def _p(d: dict, key: str, fallback=0.0):
    """Safe param lookup — returns float or fallback."""
    v = d.get(key, fallback)
    try:
        return float(v) if v not in (None, "") else fallback
    except (TypeError, ValueError):
        return fallback


def _fmt_in(total_in: float) -> str:
    """Format a raw-inches value as feet-inches string for diagram labels."""
    total_in = max(0.0, total_in)
    ft = int(total_in // 12)
    frac = round((total_in % 12) * 8) / 8
    if frac >= 12.0:
        ft += 1
        frac = 0.0
    if ft == 0:
        return f'{frac:g}"'
    if frac == 0.0:
        return f"{ft}'-0\""
    whole = int(frac)
    rem = round((frac - whole) * 8)
    if rem == 0:
        return f"{ft}'-{whole}\""
    return f"{ft}'-{whole} {rem}/8\""


# ── Diagram functions ─────────────────────────────────────────────────────────

def _draw_wall_elevation(ax, p: dict, title: str):
    """
    Front-elevation view of a rectangular concrete wall with EF reinforcement.
    Used for: G2 Inlet, G2 Expanded Inlet, Wing Wall.
    """
    W = min(_p(p, "wall_length_ft", 12), 20)   # cap for display
    H = _p(p, "wall_height_ft", 6)
    T = _p(p, "wall_thick_in", 9) / 12
    cov = _p(p, "cover_in", 2) / 12
    hs  = _p(p, "horiz_spacing_in", 12) / 12
    vs  = _p(p, "vert_spacing_in", 12) / 12
    sx, sy = 1.2, 0.6

    # Concrete body
    _rect(ax, sx, sy, W, H)

    # Cover inset lines
    inset = cov
    ax.add_patch(mpatches.Rectangle(
        (sx + inset, sy + inset), W - 2*inset, H - 2*inset,
        fill=False, edgecolor=_R, lw=0.5, ls="--", zorder=3, alpha=0.4
    ))

    # Horizontal rebar lines (EF — both faces shown as one set)
    n_h = max(1, int((H - 2*cov) / hs))
    for i in range(n_h + 1):
        yy = sy + cov + i * hs
        if yy > sy + H - cov: break
        _bar(ax, sx + cov, yy, sx + W - cov, yy, lw=1.2)

    # Vertical rebar lines
    n_v = max(1, int((W - 2*cov) / vs))
    for i in range(n_v + 1):
        xx = sx + cov + i * vs
        if xx > sx + W - cov: break
        _bar(ax, xx, sy + cov, xx, sy + H - cov, lw=1.2)

    # Dimensions
    _dim_h(ax, sx, sx + W, sy, "wall_length_ft", y_off=-0.35)
    _dim_v(ax, sy, sy + H, sx, "wall_height_ft", x_off=-0.5)
    _callout(ax, (sx + W/2, sy + H/2 - 0.2), f"wall_thick_in={int(_p(p,'wall_thick_in',9))}\"",
             (sx + W + 1.5, sy + H/2 + 1))
    _callout(ax, (sx + cov + hs, sy + cov + hs*0.5), f"@{_p(p,'horiz_spacing_in',12):.0f}oc",
             (sx + W + 1.5, sy + H * 0.7))
    _callout(ax, (sx + cov*2, sy + cov + H/2), f"EF", (sx - 0.8, sy + H/2))

    ax.set_xlim(-0.2, sx + W + 2.5)
    ax.set_ylim(sy - 0.8, sy + H + 0.8)
    ax.set_title(title, fontsize=_FS_TITLE, fontweight="bold", color=_H, pad=6)


def _draw_g2_inlet_top(ax, p: dict, title: str):
    """
    Cross-section view of a G2 Inlet Top slab sitting on box walls.

    Shows:
      - Top slab (hatched concrete rectangle) with rebar dots inside
      - Two wall stubs below the slab ends (showing what the slab bears on)
      - Void/opening in the centre (inlet interior)
      - Dimension callouts for slab_length_ft, slab_width_ft (shown as depth
        into page via dashed plan inset), slab_thick_in
      - Long-direction bar dots (bottom layer) and short-direction bar dots
        (top layer) in the slab cross-section
    """
    L   = min(_p(p, "slab_length_ft",  8.0), 20)   # horizontal span
    W   = min(_p(p, "slab_width_ft",   4.0), 12)   # depth into page (shown as inset)
    T   = _p(p, "slab_thick_in",  9) / 12          # slab thickness (ft)
    cov = _p(p, "cover_in",       2) / 12
    ls  = _p(p, "long_spacing_in",  12) / 12
    ss  = _p(p, "short_spacing_in", 12) / 12

    # Wall stub geometry
    wall_t = max(0.75, T)    # stub width ~= slab thickness for proportions
    wall_h = T * 1.4         # stub height below slab

    sx, sy = 0.5, 0.8        # slab top-left origin

    # ── Wall stubs (left and right) ─────────────────────────────────────────
    _rect(ax, sx,                   sy - wall_h, wall_t, wall_h + T)
    _rect(ax, sx + L - wall_t,      sy - wall_h, wall_t, wall_h + T)

    # ── Open void between wall stubs (interior of inlet) ────────────────────
    void_x = sx + wall_t
    void_w = L - 2 * wall_t
    _rect(ax, void_x, sy, void_w, T, fc=_V, ec=_CD, lw=0.8)
    ax.text(void_x + void_w / 2, sy + T / 2,
            "INLET\nOPENING", ha="center", va="center",
            fontsize=6.5, color="#4488AA", fontfamily="monospace", zorder=5)

    # ── Top slab over full length ────────────────────────────────────────────
    _rect(ax, sx, sy, L, T)

    # Hatch the slab concrete
    ax.add_patch(mpatches.Rectangle(
        (sx, sy), L, T,
        hatch="////", facecolor="none", edgecolor=_CD,
        linewidth=0.4, zorder=3
    ))

    # ── Rebar dots in slab cross-section ────────────────────────────────────
    # Long bars (run parallel to slab_length, spaced at long_spacing_in)
    # Shown as circles at bottom layer
    y_long = sy + cov + 0.03
    n_long = max(1, int((L - 2 * cov) / ls))
    for i in range(n_long + 1):
        xx = sx + cov + i * ls
        if xx > sx + L - cov:
            break
        _dot(ax, xx, y_long, s=14)

    # Short bars (run parallel to slab_width / into page, spaced at short_spacing_in)
    # Shown as circles at top layer
    y_short = sy + T - cov - 0.03
    n_short = max(1, int((L - 2 * cov) / ss))
    for i in range(n_short + 1):
        xx = sx + cov + ss * 0.25 + i * ss
        if xx > sx + L - cov:
            break
        _dot(ax, xx, y_short, s=14)

    # ── Plan inset (small dashed rectangle, top right) ──────────────────────
    # Shows the W (depth into page) dimension not visible in cross-section
    ix, iy = sx + L + 0.35, sy + T * 0.1
    iW, iH = min(W * 0.35, 2.0), min(L * 0.18, 1.4)
    ax.add_patch(mpatches.Rectangle(
        (ix, iy), iW, iH,
        facecolor=_C, edgecolor=_CD, linewidth=0.8, linestyle="--", zorder=2
    ))
    _label(ax, ix + iW / 2, iy + iH + 0.18, "PLAN", fs=6.0)
    # Width arrow on inset
    ax.annotate("", xy=(ix + iW, iy - 0.12), xytext=(ix, iy - 0.12),
                arrowprops=dict(arrowstyle="<->", color=_D, lw=0.7))
    ax.text(ix + iW / 2, iy - 0.26,
            "slab_width_ft", ha="center", va="top", fontsize=5.5,
            color=_D, fontfamily="monospace", zorder=6)

    # ── Dimension callouts ──────────────────────────────────────────────────
    _dim_h(ax, sx, sx + L, sy + T, "slab_length_ft", y_off=0.28)
    _dim_v(ax, sy, sy + T, sx,     "slab_thick_in", x_off=-0.45)

    # Bar callouts
    _callout(ax, (sx + cov, y_long),
             f"long@{_p(p,'long_spacing_in',12):.0f}\" oc",
             (sx - 0.1, sy - 0.35))
    _callout(ax, (sx + cov + ss * 0.25, y_short),
             f"short@{_p(p,'short_spacing_in',12):.0f}\" oc",
             (sx + L * 0.3, sy + T + 0.65))

    # Ground line
    gx1, gx2 = sx - 0.3, sx + wall_t * 0.5
    gy = sy - wall_h
    ax.plot([gx1, gx2], [gy, gy], color=_E, lw=1.2, ls="-")
    gx1b, gx2b = sx + L - wall_t * 0.5, sx + L + 0.3
    ax.plot([gx1b, gx2b], [gy, gy], color=_E, lw=1.2, ls="-")

    ax.set_xlim(sx - 0.8, sx + L + 2.6)
    ax.set_ylim(sy - wall_h - 0.5, sy + T + 1.0)
    ax.set_title(title, fontsize=_FS_TITLE, fontweight="bold", color=_H, pad=6)


def _draw_slab_plan(ax, p: dict, title: str):
    """
    Plan view of a flat slab with bars each way.
    Used for: Flat Slab, Slab on Grade, Dual Slab.
    """
    L  = min(_p(p, "slab_length_ft", p.get("length_ft", 10)), 20)
    W  = min(_p(p, "slab_width_ft",  p.get("width_ft",  4)), 12)
    T  = _p(p, "slab_thick_in", 8) / 12
    cov = _p(p, "cover_in", 2) / 12
    ls  = _p(p, "long_spacing_in",  p.get("spacing_in", 12)) / 12
    ss  = _p(p, "short_spacing_in", p.get("spacing_in", 12)) / 12
    sx, sy = 1.0, 0.8

    # Concrete body
    _rect(ax, sx, sy, L, W)

    # Long bars (run along L, spaced across W)
    n_l = max(1, int((W - 2*cov) / ls))
    for i in range(n_l + 1):
        yy = sy + cov + i * ls
        if yy > sy + W - cov: break
        _bar(ax, sx + cov, yy, sx + L - cov, yy, lw=1.5)

    # Short bars (run along W, spaced along L)
    n_s = max(1, int((L - 2*cov) / ss))
    for i in range(n_s + 1):
        xx = sx + cov + i * ss
        if xx > sx + L - cov: break
        _bar(ax, xx, sy + cov, xx, sy + W - cov, lw=1.0)

    # Dimensions
    _dim_h(ax, sx, sx + L, sy, "slab_length_ft", y_off=-0.35)
    _dim_v(ax, sy, sy + W, sx, "slab_width_ft", x_off=-0.5)
    _callout(ax, (sx + L - cov, sy + cov + ls * 0.5),
             f"long@{_p(p,'long_spacing_in', p.get('spacing_in',12)):.0f}oc",
             (sx + L + 1.5, sy + W * 0.8))
    _callout(ax, (sx + cov + ss * 0.5, sy + W - cov * 2),
             f"short@{_p(p,'short_spacing_in', p.get('spacing_in',12)):.0f}oc",
             (sx + L * 0.5, sy + W + 0.7))
    _callout(ax, (sx + L * 0.5, sy), f"slab_thick_in={int(_p(p,'slab_thick_in',8))}\"",
             (sx + L * 0.5, sy - 0.7))

    ax.set_xlim(-0.2, sx + L + 2.2)
    ax.set_ylim(sy - 1.2, sy + W + 1.1)
    ax.set_title(title, fontsize=_FS_TITLE, fontweight="bold", color=_H, pad=6)


def _draw_headwall(ax, p: dict, title: str):
    """
    Cross-section of a straight headwall (Caltrans D89a style).
    Shows wall body, C-bars wrapping around, front/back face bars, footing.
    """
    WW  = _p(p, "wall_width_ft", 8)
    WH  = _p(p, "wall_height_ft", 5.9)
    WT  = _p(p, "wall_thick_in", 12) / 12
    cov = _p(p, "cover_in", 2) / 12
    hs  = _p(p, "horiz_spacing_in", 12) / 12
    leg = _p(p, "c_bar_leg_in", 14) / 12
    fw  = _p(p, "footing_width_ft", 5.33)
    sx, sy = 1.5, 1.2

    # Footing
    fsx = sx + WW/2 - fw/2
    _rect(ax, fsx, sy - 1.0, fw, 1.0, fc="#BBBBBB")

    # Wall body (front elevation cross-section — we show side view)
    # Draw as section: wall is WT wide (thick), WH tall
    sect_x = sx + WW/2 - WT/2
    _rect(ax, sect_x, sy, WT, WH)

    # Front face bars
    n_h = max(1, int((WH - 2*cov) / hs))
    for i in range(n_h + 1):
        yy = sy + cov + i * hs
        if yy > sy + WH - cov: break
        _dot(ax, sect_x + cov, yy)          # front face dot
        _dot(ax, sect_x + WT - cov, yy)     # back face dot

    # C-bars shown as U-shape brackets on the front face
    c_yy = sy + WH + 0.15
    _bar(ax, sect_x - leg, c_yy, sect_x - leg, sy + cov)           # left leg
    _bar(ax, sect_x - leg, sy + cov, sect_x + WT + leg, sy + cov)  # bottom
    _bar(ax, sect_x + WT + leg, sy + cov, sect_x + WT + leg, c_yy) # right leg
    _label(ax, sect_x - leg - 0.25, sy + WH/2, "C-bar\nleg", fs=6.5)

    # Dimensions
    _dim_v(ax, sy, sy + WH, sect_x, "wall_height_ft", x_off=-0.6)
    _callout(ax, (sect_x + WT/2, sy + WH * 0.6), f"wall_thick_in={int(_p(p,'wall_thick_in',12))}\"",
             (sect_x + WT + 1.8, sy + WH * 0.7))
    _callout(ax, (sect_x + WT/2, sy - 0.5), f"footing_width_ft={_p(p,'footing_width_ft',5.33):.1f}'",
             (sect_x + WT + 1.8, sy - 0.3))
    _callout(ax, (sect_x - leg - 0.05, sy + WH/2), f"c_bar_leg_in={int(_p(p,'c_bar_leg_in',14))}\"",
             (sect_x - leg - 1.6, sy + WH * 0.85))
    _label(ax, sx + WW/2, sy + WH + 0.5,
           f"wall_width_ft = {WW:.0f}'  (plan, see front elevation)",
           fs=6.5, color="#555555")

    ax.set_xlim(sect_x - 2.5, sect_x + WT + 3.0)
    ax.set_ylim(sy - 1.5, sy + WH + 1.0)
    ax.set_title(title, fontsize=_FS_TITLE, fontweight="bold", color=_H, pad=6)


def _draw_junction_box(ax, p: dict, title: str):
    """
    Plan view of a junction structure (rectangular drainage box).
    Shows outer walls (thick), inner void, floor area.
    """
    IL = min(_p(p, "inside_length_ft", 6), 16)
    IW = min(_p(p, "inside_width_ft",  4), 12)
    WT = _p(p, "wall_thick_in",  12) / 12
    FT = _p(p, "floor_thick_in", 12) / 12
    ID = _p(p, "inside_depth_ft", 5)
    sx, sy = 1.0, 0.8
    OL = IL + 2 * WT
    OW = IW + 2 * WT

    # Outer walls (concrete)
    _rect(ax, sx, sy, OL, OW)
    # Inner void
    _rect(ax, sx + WT, sy + WT, IL, IW, fc=_V, ec="#AAAACC", lw=0.8)
    _label(ax, sx + WT + IL/2, sy + WT + IW/2, "OPEN\n(inside)", fs=7, color="#446688")

    # Rebar dots in walls (simplified — top wall shown)
    cov = _p(p, "cover_in", 2) / 12
    hs  = _p(p, "horiz_spacing_in", 12) / 12
    n_h = max(1, int(OL / hs))
    for i in range(n_h + 1):
        xx = sx + cov + i * hs
        if xx > sx + OL - cov: break
        _dot(ax, xx, sy + WT/2, s=12)
        _dot(ax, xx, sy + OW - WT/2, s=12)

    # Dimensions
    _dim_h(ax, sx + WT, sx + WT + IL, sy, "inside_length_ft", y_off=-0.35)
    _dim_h(ax, sx, sx + OL, sy + OW, "total outside", y_off=0.35)
    _dim_v(ax, sy + WT, sy + WT + IW, sx, "inside_width_ft", x_off=-0.5)
    _callout(ax, (sx + WT/2, sy + WT/2), f"wall_thick_in={int(_p(p,'wall_thick_in',12))}\"",
             (sx - 0.3, sy - 0.6))
    _callout(ax, (sx + OL/2, sy + OW/2),
             f"inside_depth_ft={ID:.0f}'",
             (sx + OL + 1.8, sy + OW * 0.6))

    ax.set_xlim(-0.3, sx + OL + 2.5)
    ax.set_ylim(sy - 1.0, sy + OW + 0.9)
    ax.set_title(title, fontsize=_FS_TITLE, fontweight="bold", color=_H, pad=6)


def _draw_box_culvert(ax, p: dict, title: str):
    """Cross-section of a rectangular box culvert."""
    span = _p(p, "span_ft", 8)
    rise = _p(p, "rise_ft", 6)
    WT   = _p(p, "wall_thick_in", 12) / 12
    cov  = _p(p, "cover_in", 2) / 12
    sx, sy = 1.0, 0.5
    OW = span + 2 * WT
    OH = rise + 2 * WT

    # Top slab, bottom slab, two side walls as one outline
    _rect(ax, sx, sy, OW, OH)   # outer
    _rect(ax, sx + WT, sy + WT, span, rise, fc=_V, ec="#AAAACC")  # inner void
    _label(ax, sx + WT + span/2, sy + WT + rise/2, "INTERIOR", fs=7, color="#446688")

    # Rebar lines in top and bottom slabs
    _bar(ax, sx + cov, sy + WT - cov, sx + OW - cov, sy + WT - cov)  # bottom slab top mat
    _bar(ax, sx + cov, sy + cov, sx + OW - cov, sy + cov)             # bottom slab bot mat
    _bar(ax, sx + cov, sy + OH - cov, sx + OW - cov, sy + OH - cov)  # top slab top mat
    _bar(ax, sx + cov, sy + OH - WT + cov, sx + OW - cov, sy + OH - WT + cov)

    # Dimensions
    _dim_h(ax, sx + WT, sx + WT + span, sy, "span_ft", y_off=-0.4)
    _dim_v(ax, sy + WT, sy + WT + rise, sx, "rise_ft", x_off=-0.5)
    _callout(ax, (sx + WT/2, sy + OH/2), f"wall_thick_in\n={int(_p(p,'wall_thick_in',12))}\"",
             (sx - 0.8, sy + OH * 0.6))

    ax.set_xlim(-0.2, sx + OW + 1.5)
    ax.set_ylim(sy - 0.9, sy + OH + 0.6)
    ax.set_title(title, fontsize=_FS_TITLE, fontweight="bold", color=_H, pad=6)


def _draw_retaining_wall(ax, p: dict, title: str):
    """Cantilever retaining wall cross-section."""
    SH  = min(_p(p, "stem_height_ft", 10), 14)
    ST  = _p(p, "stem_thick_in", 12) / 12
    toe = _p(p, "toe_width_ft", 3)
    heel= _p(p, "heel_width_ft", 4)
    FT  = _p(p, "footing_thick_in", 18) / 12
    cov = _p(p, "cover_in", 2) / 12
    hs  = _p(p, "horiz_spacing_in", 12) / 12
    sx, sy = 2.0, 0.5
    fw = toe + ST + heel

    # Footing
    _rect(ax, sx - toe, sy, fw, FT, fc="#BBBBBB")
    # Stem
    _rect(ax, sx, sy + FT, ST, SH)

    # Earth hatching (right side of stem)
    for i in range(10):
        yy = sy + FT + i * (SH / 10)
        ax.plot([sx + ST, sx + ST + 0.6 + 0.1*i], [yy, yy - 0.3],
                color=_E, lw=0.7, alpha=0.6)

    # Stem rebar (back face = right side)
    n_h = max(1, int((SH - 2*cov) / hs))
    for i in range(n_h + 1):
        yy = sy + FT + cov + i * hs
        if yy > sy + FT + SH - cov: break
        _dot(ax, sx + ST - cov, yy, s=14)    # back face
        _dot(ax, sx + cov, yy, s=10)         # front face (smaller)

    # Dimensions
    _dim_v(ax, sy + FT, sy + FT + SH, sx, "stem_height_ft", x_off=-0.6)
    _callout(ax, (sx + ST/2, sy + FT + SH * 0.5), f"stem_thick_in\n={int(_p(p,'stem_thick_in',12))}\"",
             (sx + ST + 1.6, sy + FT + SH * 0.6))
    _callout(ax, (sx - toe/2, sy + FT/2), f"toe_width\n={toe:.1f}'",
             (sx - toe - 0.8, sy + FT + 1.0))
    _callout(ax, (sx + ST + heel/2, sy + FT/2), f"heel_width\n={heel:.1f}'",
             (sx + ST + heel + 0.5, sy + FT + 1.0))

    ax.set_xlim(sx - toe - 1.5, sx + ST + 2.5)
    ax.set_ylim(sy - 0.5, sy + FT + SH + 0.8)
    ax.set_title(title, fontsize=_FS_TITLE, fontweight="bold", color=_H, pad=6)


def _draw_pad(ax, p: dict, title: str):
    """Plan + section of an equipment / switchboard / fuel pad."""
    L  = min(_p(p, "pad_length_ft", 10), 18)
    W  = min(_p(p, "pad_width_ft",  6), 14)
    T  = _p(p, "pad_thick_in", 12) / 12
    cov = _p(p, "cover_in", 2) / 12
    ss  = _p(p, "long_spacing_in", p.get("bar_spacing_in", 12)) / 12

    # ── Plan view (left) ──────────────────────────────────────────────────
    px, py = 0.5, 0.8
    _rect(ax, px, py, L, W)
    n_l = max(1, int((W - 2*cov) / ss))
    for i in range(n_l + 1):
        yy = py + cov + i * ss
        if yy > py + W - cov: break
        _bar(ax, px + cov, yy, px + L - cov, yy, lw=1.2)
    n_s = max(1, int((L - 2*cov) / ss))
    for i in range(n_s + 1):
        xx = px + cov + i * ss
        if xx > px + L - cov: break
        _bar(ax, xx, py + cov, xx, py + W - cov, lw=0.9)

    _dim_h(ax, px, px + L, py, "pad_length_ft", y_off=-0.35)
    _dim_v(ax, py, py + W, px, "pad_width_ft", x_off=-0.5)
    _label(ax, px + L/2, py + W + 0.3, "PLAN VIEW", fs=7, bold=True, color=_H)

    # ── Section view (right) ──────────────────────────────────────────────
    gx = px + L + 1.5
    gy = py + W/2 - T/2
    _rect(ax, gx, gy, L * 0.6, T)
    _bar(ax, gx + cov, gy + cov, gx + L*0.6 - cov, gy + cov, lw=1.4)         # bottom mat
    _bar(ax, gx + cov, gy + T - cov, gx + L*0.6 - cov, gy + T - cov, lw=1.4) # top mat
    # Earth
    _rect(ax, gx, gy - 0.3, L * 0.6, 0.3, fc=_E, ec=_E)
    _dim_v(ax, gy, gy + T, gx, "pad_thick_in", x_off=-0.4)
    _label(ax, gx + L*0.3, gy + T + 0.3, "SECTION", fs=7, bold=True, color=_H)
    _callout(ax, (gx + L*0.3, gy + cov + 0.02),
             f"cover_in={int(_p(p,'cover_in',2))}\"", (gx + L*0.6 + 0.8, gy - 0.1))

    ax.set_xlim(px - 0.8, gx + L*0.6 + 1.5)
    ax.set_ylim(py - 0.8, py + W + 0.7)
    ax.set_title(title, fontsize=_FS_TITLE, fontweight="bold", color=_H, pad=6)


def _draw_cage(ax, p: dict, title: str):
    """Elevation of a drilled shaft cage or pipe collar cage."""
    CL  = min(_p(p, "cage_length_ft", p.get("collar_length_ft", 4)), 16)
    CD  = _p(p, "cage_diam_in", p.get("collar_diam_in", 24)) / 12
    cov = _p(p, "cover_in", 1.5) / 12
    ns  = max(3, int(_p(p, "long_bar_qty", p.get("num_long_bars", 6))))
    hs  = _p(p, "spiral_pitch_in", p.get("hoop_spacing_in", 12)) / 12
    sx, sy = 1.0, 0.5

    # Outer cylinder outline
    for xi in [sx, sx + CD]:
        ax.plot([xi, xi], [sy, sy + CL], color=_CD, lw=_LW_CONC, zorder=2)
    ax.plot([sx, sx + CD], [sy, sy],       color=_CD, lw=_LW_CONC, ls="--", zorder=2)
    ax.plot([sx, sx + CD], [sy + CL, sy + CL], color=_CD, lw=_LW_CONC, zorder=2)

    # Spiral / hoops
    n_hoops = max(1, int(CL / hs))
    for i in range(n_hoops + 1):
        yy = sy + i * hs
        if yy > sy + CL: break
        ax.plot([sx, sx + CD], [yy, yy], color=_R, lw=1.0, alpha=0.7, zorder=3)

    # Longitudinal bars (shown as vertical lines near inner face)
    for i in range(min(ns, 8)):
        xx = sx + cov + (i + 0.5) * (CD - 2*cov) / max(ns - 1, 1)
        _bar(ax, xx, sy + cov, xx, sy + CL - cov, lw=1.4)

    _dim_h(ax, sx, sx + CD, sy, f"diam={int(_p(p,'cage_diam_in',24))}\"", y_off=-0.4)
    _dim_v(ax, sy, sy + CL, sx, "cage_length_ft", x_off=-0.5)
    _callout(ax, (sx + CD/2, sy + hs * 0.5),
             f"spiral@{int(_p(p,'spiral_pitch_in',12))}oc",
             (sx + CD + 1.5, sy + CL * 0.5))

    ax.set_xlim(sx - 0.8, sx + CD + 2.2)
    ax.set_ylim(sy - 0.8, sy + CL + 0.5)
    ax.set_title(title, fontsize=_FS_TITLE, fontweight="bold", color=_H, pad=6)


def _draw_footing(ax, p: dict, title: str):
    """Spread footing cross-section."""
    FL  = min(_p(p, "footing_length_ft", p.get("length_ft", 8)), 18)
    FW  = _p(p, "footing_width_ft", p.get("width_ft", 5))
    FT  = _p(p, "footing_thick_in", 18) / 12
    cov = _p(p, "cover_in", 3) / 12
    ts  = _p(p, "transv_spacing_in", 12) / 12
    sx, sy = 1.0, 0.8

    # Earth below
    _rect(ax, sx - 0.1, sy - 0.4, FL + 0.2, 0.4, fc=_E, ec=_E)
    # Footing
    _rect(ax, sx, sy, FL, FT)
    # Rebar (transverse = along FW, shown as dots; longitudinal = along FL)
    _bar(ax, sx + cov, sy + cov, sx + FL - cov, sy + cov)         # bottom long
    _bar(ax, sx + cov, sy + FT - cov, sx + FL - cov, sy + FT - cov) # top long
    n_t = max(1, int(FL / ts))
    for i in range(n_t + 1):
        xx = sx + cov + i * ts
        if xx > sx + FL - cov: break
        _dot(ax, xx, sy + cov)
        _dot(ax, xx, sy + FT - cov)

    _dim_h(ax, sx, sx + FL, sy, "footing_length_ft", y_off=-0.5)
    _dim_v(ax, sy, sy + FT, sx, "footing_thick_in", x_off=-0.5)
    _callout(ax, (sx + FL/2, sy + cov + 0.02),
             f"cover_in={int(_p(p,'cover_in',3))}\"", (sx + FL + 1.5, sy + 0.2))
    _callout(ax, (sx + cov + ts, sy + cov), f"@{int(ts*12)}oc",
             (sx + ts*2 + 0.2, sy + FT + 0.5))

    ax.set_xlim(sx - 0.8, sx + FL + 2.0)
    ax.set_ylim(sy - 0.8, sy + FT + 0.8)
    ax.set_title(title, fontsize=_FS_TITLE, fontweight="bold", color=_H, pad=6)


def _draw_pipe_encasement(ax, p: dict, title: str):
    """Pipe encasement cross-section — pipe inside a concrete rectangle."""
    PD  = _p(p, "pipe_diam_in", 24) / 12
    EW  = _p(p, "encasement_width_ft", p.get("width_ft", PD + 1.0))
    ET  = _p(p, "encasement_thick_ft", p.get("thick_ft", PD + 0.75))
    cov = _p(p, "cover_in", 3) / 12
    sx, sy = 1.0, 0.5
    # Center pipe in encasement
    cx = sx + EW / 2
    cy = sy + ET / 2
    r  = PD / 2

    # Concrete encasement
    _rect(ax, sx, sy, EW, ET)
    # Pipe void
    circle = mpatches.Circle((cx, cy), r, facecolor=_V, edgecolor="#7799BB", lw=1.5, zorder=3)
    ax.add_patch(circle)
    _label(ax, cx, cy, f"PIPE\nID={int(_p(p,'pipe_diam_in',24))}\"", fs=6.5, color="#446688")

    # Hoop rebar dots around pipe
    n_h = 8
    for i in range(n_h):
        angle = 2 * math.pi * i / n_h
        bx = cx + (r + cov/2) * math.cos(angle)
        by = cy + (r + cov/2) * math.sin(angle)
        _dot(ax, bx, by, s=14)

    # Longitudinal bar dots at corners
    for cx2, cy2 in [(sx+cov, sy+cov), (sx+EW-cov, sy+cov),
                     (sx+cov, sy+ET-cov), (sx+EW-cov, sy+ET-cov)]:
        _dot(ax, cx2, cy2, s=20)

    _dim_h(ax, sx, sx + EW, sy, "encasement_width_ft", y_off=-0.4)
    _dim_v(ax, sy, sy + ET, sx, "encasement_thick", x_off=-0.5)
    _callout(ax, (cx + r, cy),
             f"pipe_diam_in={int(_p(p,'pipe_diam_in',24))}\"",
             (sx + EW + 1.5, cy + 0.3))

    ax.set_xlim(sx - 0.8, sx + EW + 2.2)
    ax.set_ylim(sy - 0.8, sy + ET + 0.6)
    ax.set_title(title, fontsize=_FS_TITLE, fontweight="bold", color=_H, pad=6)


def _draw_seatwall(ax, p: dict, title: str):
    """Seatwall cross-section — low concrete wall acting as a seat/ledge."""
    SL  = min(_p(p, "seat_length_ft", 12), 16)
    SW  = _p(p, "seat_width_ft", 2)
    ST  = _p(p, "seat_thick_in", 18) / 12
    cov = _p(p, "cover_in", 2) / 12
    ls  = _p(p, "long_spacing_in", 12) / 12
    sx, sy = 1.0, 0.6

    _rect(ax, sx, sy, SL, ST)
    n_l = max(1, int((SL - 2*cov) / ls))
    for i in range(n_l + 1):
        xx = sx + cov + i * ls
        if xx > sx + SL - cov: break
        _dot(ax, xx, sy + cov)
        _dot(ax, xx, sy + ST - cov)
    # Transverse bar lines
    ns = max(2, int(SW / 0.75))
    for i in range(ns + 1):
        _bar(ax, sx + SL * 0.2 + i * 0.4, sy + cov,
             sx + SL * 0.2 + i * 0.4, sy + ST - cov, lw=1.0)

    _dim_h(ax, sx, sx + SL, sy, "seat_length_ft", y_off=-0.35)
    _dim_v(ax, sy, sy + ST, sx, "seat_thick_in", x_off=-0.5)
    _callout(ax, (sx + SL/2, sy + ST/2), f"seat_width_ft={SW:.1f}'",
             (sx + SL + 1.5, sy + ST * 0.6))

    ax.set_xlim(sx - 0.8, sx + SL + 2.2)
    ax.set_ylim(sy - 0.7, sy + ST + 0.7)
    ax.set_title(title, fontsize=_FS_TITLE, fontweight="bold", color=_H, pad=6)


def _draw_header(ax, p: dict, title: str):
    """Concrete header cross-section."""
    HL  = min(_p(p, "header_length_ft", 8), 16)
    HW  = _p(p, "header_width_ft", 1.5)
    HD  = _p(p, "header_depth_in", 18) / 12
    cov = _p(p, "cover_in", 2) / 12
    sx, sy = 1.0, 0.8

    _rect(ax, sx, sy, HL, HD)
    _bar(ax, sx + cov, sy + cov, sx + HL - cov, sy + cov)
    _bar(ax, sx + cov, sy + HD - cov, sx + HL - cov, sy + HD - cov)
    n_s = max(2, int(HL / 1.0))
    for i in range(n_s + 1):
        xx = sx + cov + i * (HL - 2*cov) / max(n_s, 1)
        _dot(ax, xx, sy + cov)
        _dot(ax, xx, sy + HD - cov)

    _dim_h(ax, sx, sx + HL, sy, "header_length_ft", y_off=-0.35)
    _dim_v(ax, sy, sy + HD, sx, "header_depth_in", x_off=-0.5)
    _callout(ax, (sx + HL/2, sy + HD/2), f"header_width_ft={HW:.1f}'",
             (sx + HL + 1.5, sy + HD * 0.5))

    ax.set_xlim(sx - 0.8, sx + HL + 2.2)
    ax.set_ylim(sy - 0.7, sy + HD + 0.7)
    ax.set_title(title, fontsize=_FS_TITLE, fontweight="bold", color=_H, pad=6)


def _draw_dual_slab(ax, p: dict, title: str):
    """Plan view of two adjacent slabs (Dual Slab)."""
    LA = min(_p(p, "slab_a_length_ft", 8), 14)
    LB = min(_p(p, "slab_b_length_ft", 6), 14)
    W  = min(_p(p, "slab_width_ft", 4),  10)
    T  = _p(p, "slab_thick_in", 8) / 12
    cov = _p(p, "cover_in", 2) / 12
    ss  = _p(p, "spacing_in", 12) / 12
    sx, sy = 0.8, 0.8

    # Slab A
    _rect(ax, sx, sy, LA, W, fc="#CCCCCC", ec="#888888")
    # Slab B
    _rect(ax, sx + LA + 0.1, sy, LB, W, fc="#BBBBBB", ec="#888888")

    # Bars in A
    n = max(1, int((W - 2*cov) / ss))
    for i in range(n + 1):
        yy = sy + cov + i * ss
        if yy > sy + W - cov: break
        _bar(ax, sx + cov, yy, sx + LA - cov, yy, lw=1.2)

    # Bars in B
    for i in range(n + 1):
        yy = sy + cov + i * ss
        if yy > sy + W - cov: break
        _bar(ax, sx + LA + 0.1 + cov, yy, sx + LA + 0.1 + LB - cov, yy, lw=1.2)

    _dim_h(ax, sx, sx + LA, sy, "slab_a_length_ft", y_off=-0.35)
    _dim_h(ax, sx + LA + 0.1, sx + LA + 0.1 + LB, sy, "slab_b_length_ft", y_off=-0.35)
    _dim_v(ax, sy, sy + W, sx, "slab_width_ft", x_off=-0.5)
    _label(ax, sx + LA/2, sy + W/2, "SLAB A", fs=8, bold=True, color="#555555")
    _label(ax, sx + LA + 0.1 + LB/2, sy + W/2, "SLAB B", fs=8, bold=True, color="#555555")

    ax.set_xlim(sx - 0.8, sx + LA + 0.1 + LB + 1.5)
    ax.set_ylim(sy - 0.8, sy + W + 0.6)
    ax.set_title(title, fontsize=_FS_TITLE, fontweight="bold", color=_H, pad=6)


def _draw_slab_on_grade(ax, p: dict, title: str):
    """Section view of slab on grade showing earth below and mid-slab rebar."""
    SL  = min(_p(p, "slab_length_ft", 20), 20)
    ST  = _p(p, "slab_thick_in", 6) / 12
    cov = _p(p, "cover_in", 1.5) / 12
    ss  = _p(p, "spacing_in", 12) / 12
    sx, sy = 0.8, 1.0

    # Earth
    _rect(ax, sx - 0.2, sy - 0.5, SL + 0.4, 0.5, fc=_E, ec=_E)
    # Slab
    _rect(ax, sx, sy, SL, ST)
    # Mid-slab or bottom rebar
    n = max(1, int((SL - 2*cov) / ss))
    for i in range(n + 1):
        xx = sx + cov + i * ss
        if xx > sx + SL - cov: break
        _dot(ax, xx, sy + ST / 2, s=18)

    _dim_h(ax, sx, sx + SL, sy, "slab_length_ft", y_off=-0.6)
    _dim_v(ax, sy, sy + ST, sx, "slab_thick_in", x_off=-0.5)
    _callout(ax, (sx + ss, sy + ST/2), f"@{int(ss*12)}oc", (sx + ss*3, sy + ST + 0.5))

    ax.set_xlim(sx - 0.8, sx + SL + 1.5)
    ax.set_ylim(sy - 0.9, sy + ST + 0.8)
    ax.set_title(title, fontsize=_FS_TITLE, fontweight="bold", color=_H, pad=6)


# ── G2 Inlet plan-view diagram ────────────────────────────────────────────────

def _draw_g2_inlet_plan(ax, p: dict, title: str):
    """
    Plan view of a Caltrans G2 Inlet (or G2 Expanded Inlet).

    Shows the exterior box (X × Y), wall thickness T on all four sides,
    interior void, and the grate opening L1 on the front face.

    Dimensions labeled: X across top, Y on right, T via callout, L1 at bottom.
    """
    p = p or {}

    x_ft = _p(p, "x_dim_ft", 5.5)
    y_ft = _p(p, "y_dim_ft", 4.5)
    x_in = x_ft * 12.0
    y_in = y_ft * 12.0

    # ── Wall thickness (mirror the geometry rule logic) ───────────────
    t_raw = _p(p, "wall_thick_in", 0)
    t_in  = (9.0 if x_in <= 54.0 else 11.0) if t_raw <= 0 else t_raw
    t_ft  = t_in / 12.0

    # ── Interior ──────────────────────────────────────────────────────
    int_x_ft = x_ft - 2.0 * t_ft
    int_y_ft = y_ft - 2.0 * t_ft

    # ── Grate deduction / L1 ─────────────────────────────────────────
    grate_str   = str(p.get("grate_type", "Type 24")) if isinstance(p, dict) else "Type 24"
    grate_ded   = 24.0 if "24" in grate_str else 18.0
    l1_in       = max(0.0, int_x_ft * 12.0 - grate_ded)
    l1_ft       = l1_in / 12.0
    grate_side  = (int_x_ft - l1_ft) / 2.0   # bearing seat each side, ft

    # ── Scale so diagram fits in ~7.5 ft display width ───────────────
    scale = min(1.0, 7.5 / max(x_ft, 0.5))
    X     = x_ft      * scale
    Y     = y_ft      * scale
    T     = t_ft      * scale
    INT_X = int_x_ft  * scale
    INT_Y = int_y_ft  * scale
    L1    = l1_ft     * scale
    GS    = grate_side * scale     # bearing seat each side (scaled)

    sx, sy = 1.6, 1.0   # drawing origin

    # ── Concrete walls (gray fill) ─────────────────────────────────────
    _rect(ax, sx, sy, X, Y)

    # ── Interior void (light blue) ─────────────────────────────────────
    if INT_X > 0 and INT_Y > 0:
        _rect(ax, sx + T, sy + T, INT_X, INT_Y, fc=_V, ec="#99AACC", lw=0.8)

    # ── Grate opening on front (bottom) wall — hatched ─────────────────
    if L1 > 0.02:
        ax.add_patch(mpatches.Rectangle(
            (sx + T + GS, sy), L1, T,
            facecolor="#B0C8EE", edgecolor="#4466AA",
            linewidth=1.2, zorder=3, hatch="//", alpha=0.75,
        ))

    # ── Rebar dots in left and right walls ────────────────────────────
    # Represent EF bars as paired dot rows inside each wall
    n_v = max(3, int(Y / 0.15))   # number of vert positions across height
    for face_x in [sx + T * 0.28, sx + T * 0.72,
                   sx + X - T * 0.72, sx + X - T * 0.28]:
        for i in range(n_v):
            yy = sy + T * 0.3 + i * (Y - T * 0.6) / max(n_v - 1, 1)
            _dot(ax, face_x, yy, s=9)

    # Horiz bars running the full depth (top/bottom walls) — show as lines
    n_h = max(2, int(Y * 4))
    for face_y in [sy + T * 0.5, sy + Y - T * 0.5]:
        _bar(ax, sx + T, face_y, sx + T + INT_X, face_y, lw=1.0)

    # ── Dimension: X across top ────────────────────────────────────────
    _dim_h(ax, sx, sx + X, sy + Y,
           f"X = {x_ft:.2f}'  ({_fmt_in(x_in)})", y_off=0.38)

    # ── Dimension: Y on right ──────────────────────────────────────────
    _dim_v(ax, sy, sy + Y, sx + X,
           f"Y = {y_ft:.2f}'", x_off=0.42)

    # ── Dimension: L1 grate opening at bottom ─────────────────────────
    if L1 > 0.05:
        _dim_h(ax, sx + T + GS, sx + T + GS + L1, sy,
               f"L1 = {_fmt_in(l1_in)}", y_off=-0.40)

    # ── Callout: T on left wall ────────────────────────────────────────
    _callout(ax, (sx + T / 2, sy + Y / 2),
             f"T = {t_in:.0f}\"",
             (sx - 0.55, sy + Y * 0.75))

    # ── Interior label ─────────────────────────────────────────────────
    if INT_X > 0.3 and INT_Y > 0.2:
        _label(ax, sx + T + INT_X / 2, sy + T + INT_Y / 2,
               f"INTERIOR\n{_fmt_in(int_x_ft * 12)} × {_fmt_in(int_y_ft * 12)}",
               fs=6.2, color="#334466")

    # ── Grate type label on opening ────────────────────────────────────
    if L1 > 0.12:
        _label(ax, sx + T + GS + L1 / 2, sy + T / 2,
               grate_str, fs=5.8, color="#4466AA")

    # ── Bearing-seat callout (T side strips of front wall) ────────────
    if GS > 0.05:
        _callout(ax, (sx + T + GS / 2, sy + T / 2),
                 f"{_fmt_in(grate_side * 12)} seat",
                 (sx + T / 2, sy - 0.65))

    ax.set_xlim(sx - 1.3, sx + X + 1.5)
    ax.set_ylim(sy - 1.1, sy + Y + 1.0)
    ax.set_title(title, fontsize=_FS_TITLE, fontweight="bold", color=_H, pad=6)


# ── Dispatch map: template name → draw function ───────────────────────────────

def _draw_generic(ax, p: dict, title: str):
    """Fallback — simple labeled box when no specific diagram exists."""
    _rect(ax, 1, 1, 6, 3)
    _label(ax, 4, 2.5, title, fs=11, bold=True, color=_H)
    _label(ax, 4, 1.8, "Select template and click Refresh Inputs\nto populate fields →", fs=8)
    ax.set_xlim(0, 8)
    ax.set_ylim(0, 5)


_DRAW_MAP: dict[str, Any] = {
    "G2 Inlet":               _draw_g2_inlet_plan,
    "G2 Expanded Inlet":      _draw_g2_inlet_plan,
    "G2 Inlet Top":           _draw_g2_inlet_top,
    "G2 Expanded Inlet Top":  _draw_g2_inlet_top,
    "Straight Headwall":      _draw_headwall,
    "Junction Structure":     _draw_junction_box,
    "Wing Wall":              _draw_wall_elevation,
    "Box Culvert":            _draw_box_culvert,
    "Retaining Wall":         _draw_retaining_wall,
    "Flat Slab":              _draw_slab_plan,
    "Drilled Shaft Cage":     _draw_cage,
    "Concrete Pipe Collar":   _draw_cage,
    "Slab on Grade":          _draw_slab_on_grade,
    "Equipment Pad":          _draw_pad,
    "Switchboard Pad":        _draw_pad,
    "Seatwall":               _draw_seatwall,
    "Concrete Header":        _draw_header,
    "Pipe Encasement":        _draw_pipe_encasement,
    "Fuel Foundation":        _draw_pad,
    "Dual Slab":              _draw_dual_slab,
    "Spread Footing":         _draw_footing,
}


# ── Public API ────────────────────────────────────────────────────────────────

def generate_diagram_png(template_name: str, params: dict | None = None) -> bytes:
    """
    Generate a labeled engineering schematic for the given template name.

    Parameters
    ----------
    template_name : str
        Must match a key in TEMPLATE_REGISTRY (e.g. "G2 Inlet").
    params : dict, optional
        Current input parameter values. If None, defaults are used for sizing.

    Returns
    -------
    bytes
        Raw PNG image bytes. Write to a .png temp file and embed via xlwings.
    """
    if params is None:
        params = {}
    draw_fn = _DRAW_MAP.get(template_name, _draw_generic)
    fig, ax = _fig(title="")
    draw_fn(ax, params, template_name)
    return _to_png(fig)
