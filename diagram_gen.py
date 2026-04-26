"""
diagram_gen.py -- Engineering schematic diagrams for each template.
Returns PNG bytes for display via st.image().

Every diagram includes:
  - Proportional concrete geometry with rebar hints
  - Standard engineering dimension lines with extension lines
  - X / Y coordinate axes (bottom-left compass)
  - Template-specific callouts
"""

from __future__ import annotations

import io
import math

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch

# -- Style constants -----------------------------------------------------------
_CONCRETE  = "#cdd4db"
_REBAR     = "#8b4513"
_OUTLINE   = "#1c3461"
_DIM       = "#444444"
_LABEL     = "#1c3461"
_BG        = "white"
_HATCH     = "////"
_SOIL      = "#d4c4a8"
_AXIS_CLR  = "#888888"
_TITLE_CLR = "#1a1d23"


# -- Live annotation context ---------------------------------------------------
# Set by get_diagram_live() before calling a diagram function.
# Maps dimension label string → formatted value string.
_DIM_VALUES: dict[str, str] = {}

# Raw param values from the current live call (field_name → raw float).
# Used by diagram functions that need to compute derived quantities (e.g. H1).
_LIVE_PARAMS: dict = {}


def _aug_label(label: str) -> str:
    """Return label augmented with its current value if one is set."""
    val = _DIM_VALUES.get(label)
    return f"{label}\n{val}" if val else label


def _fmt_dim_value(field_name: str, value: float) -> str:
    """Format a parameter value for display on the diagram."""
    if field_name.endswith("_ft"):
        total_in = round(value * 96) / 8  # nearest 1/8"
        ft = int(total_in // 12)
        rem = total_in % 12
        whole = int(rem)
        eighths = round((rem - whole) * 8)
        if eighths >= 8:
            whole += 1
            eighths = 0
        if whole >= 12:
            ft += 1
            whole = 0
        fmap = {0: "", 1: " 1/8\"", 2: " 1/4\"", 3: " 3/8\"",
                4: " 1/2\"", 5: " 5/8\"", 6: " 3/4\"", 7: " 7/8\""}
        fs = fmap.get(eighths, "")
        if ft == 0:
            return f"{whole}{fs}\""
        elif whole == 0 and not fs:
            return f"{ft}'-0\""
        elif whole == 0:
            return f"{ft}'-0{fs}\""
        else:
            return f"{ft}'-{whole}{fs}\""
    elif field_name.endswith("_in"):
        v = round(value * 8) / 8
        whole = int(v)
        eighths = round((v - whole) * 8)
        if eighths >= 8:
            whole += 1
            eighths = 0
        fmap = {0: "", 1: " 1/8", 2: " 1/4", 3: " 3/8",
                4: " 1/2", 5: " 5/8", 6: " 3/4", 7: " 7/8"}
        return f"{whole}{fmap.get(eighths, '')}\""
    else:
        return f"{int(value)}" if value == int(value) else f"{value:g}"


# -- Drawing helpers -----------------------------------------------------------

def _fig(w=6.0, h=5.0):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_aspect("equal")
    ax.axis("off")
    fig.patch.set_facecolor(_BG)
    ax.set_facecolor(_BG)
    return fig, ax


def _rect(ax, x, y, w, h, fc=_CONCRETE, ec=_OUTLINE, lw=1.5, zorder=2, hatch=None):
    kw = dict(linewidth=lw, edgecolor=ec, facecolor=fc, zorder=zorder)
    if hatch:
        kw["hatch"] = hatch
    ax.add_patch(mpatches.Rectangle((x, y), w, h, **kw))


def _dim_h(ax, x1, x2, y, label, gap=0.22, fontsize=9, ext_len=0.12):
    """Horizontal dimension with extension lines and double-headed arrow."""
    label = _aug_label(label)
    # Extension lines
    ax.plot([x1, x1], [y - ext_len, y + ext_len], color=_DIM, lw=0.5, zorder=6)
    ax.plot([x2, x2], [y - ext_len, y + ext_len], color=_DIM, lw=0.5, zorder=6)
    # Arrow
    ax.annotate("", xy=(x2, y), xytext=(x1, y),
                arrowprops=dict(arrowstyle="<->", color=_DIM, lw=1.0,
                                mutation_scale=10, shrinkA=0, shrinkB=0))
    mid = (x1 + x2) / 2
    ax.text(mid, y + gap, label, ha="center", va="bottom", fontsize=fontsize,
            color=_LABEL, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.92))


def _dim_v(ax, y1, y2, x, label, gap=0.22, fontsize=9, ext_len=0.12):
    """Vertical dimension with extension lines and double-headed arrow."""
    label = _aug_label(label)
    ax.plot([x - ext_len, x + ext_len], [y1, y1], color=_DIM, lw=0.5, zorder=6)
    ax.plot([x - ext_len, x + ext_len], [y2, y2], color=_DIM, lw=0.5, zorder=6)
    ax.annotate("", xy=(x, y2), xytext=(x, y1),
                arrowprops=dict(arrowstyle="<->", color=_DIM, lw=1.0,
                                mutation_scale=10, shrinkA=0, shrinkB=0))
    mid = (y1 + y2) / 2
    ax.text(x + gap, mid, label, ha="left", va="center", fontsize=fontsize,
            color=_LABEL, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.92))


def _ext_dim_h(ax, x1, x2, obj_y, dim_y, label, fontsize=9):
    """Horizontal dimension placed away from the object, with long extension lines."""
    for xp in [x1, x2]:
        ax.plot([xp, xp], [obj_y, dim_y], color=_DIM, lw=0.4, zorder=5)
    _dim_h(ax, x1, x2, dim_y, label, fontsize=fontsize)


def _ext_dim_v(ax, y1, y2, obj_x, dim_x, label, fontsize=9):
    """Vertical dimension placed away from the object, with long extension lines."""
    for yp in [y1, y2]:
        ax.plot([obj_x, dim_x], [yp, yp], color=_DIM, lw=0.4, zorder=5)
    _dim_v(ax, y1, y2, dim_x, label, fontsize=fontsize)


def _callout(ax, x, y, label, text, angle=45, dist=0.55, fontsize=8):
    """Leader line callout for thickness or other annotations."""
    display = _DIM_VALUES.get(label, text)
    dx = dist * math.cos(math.radians(angle))
    dy = dist * math.sin(math.radians(angle))
    ax.annotate(
        f"{label} = {display}",
        xy=(x, y), xytext=(x + dx, y + dy),
        fontsize=fontsize, color=_LABEL, fontweight="bold",
        arrowprops=dict(arrowstyle="-", color=_DIM, lw=0.8),
        bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=_DIM, lw=0.6, alpha=0.92),
    )


def _axes_compass(ax, ox, oy, length=0.7):
    """Draw X/Y coordinate axes (compass arrows) at origin (ox, oy)."""
    head_w, head_l = 0.08, 0.12
    ax.annotate("", xy=(ox + length, oy), xytext=(ox, oy),
                arrowprops=dict(arrowstyle="-|>", color=_AXIS_CLR, lw=1.2,
                                mutation_scale=12))
    ax.text(ox + length + 0.08, oy, "X", fontsize=8, color=_AXIS_CLR,
            fontweight="bold", va="center", ha="left")
    ax.annotate("", xy=(ox, oy + length), xytext=(ox, oy),
                arrowprops=dict(arrowstyle="-|>", color=_AXIS_CLR, lw=1.2,
                                mutation_scale=12))
    ax.text(ox, oy + length + 0.08, "Y", fontsize=8, color=_AXIS_CLR,
            fontweight="bold", va="bottom", ha="center")


def _title(ax, text, x=0.5, y=0.97):
    ax.text(x, y, text, transform=ax.transAxes, ha="center", va="top",
            fontsize=10, color=_TITLE_CLR, fontweight="bold")


def _subtitle(ax, text, x=0.5, y=0.92):
    ax.text(x, y, text, transform=ax.transAxes, ha="center", va="top",
            fontsize=7.5, color="#777", style="italic")


def _rebar_grid(ax, x0, y0, w, h, nx=5, ny=4, margin=0.15):
    """Draw a mat rebar grid inside a rectangular area."""
    x1, y1 = x0 + margin, y0 + margin
    x2, y2 = x0 + w - margin, y0 + h - margin
    dx = (x2 - x1) / max(nx - 1, 1) if nx > 1 else 0
    dy = (y2 - y1) / max(ny - 1, 1) if ny > 1 else 0
    for i in range(nx):
        xi = x1 + i * dx
        ax.plot([xi, xi], [y1, y2], color=_REBAR, lw=0.8, zorder=4)
    for j in range(ny):
        yj = y1 + j * dy
        ax.plot([x1, x2], [yj, yj], color=_REBAR, lw=0.8, zorder=4)


def _to_png(fig) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=140, bbox_inches="tight", facecolor=_BG)
    plt.close(fig)
    buf.seek(0)
    return buf.read()


# ==============================================================================
# Individual diagram functions
# ==============================================================================

def _diag_g2_inlet() -> bytes:
    """Plan view of G2 inlet -- outer X/Y, inside X/Y, wall thickness T, grate."""
    OX, OY = 6.0, 5.0
    T = 0.50
    IX, IY = OX - 2 * T, OY - 2 * T

    l1_w = IX * 0.45
    grate_w = IX - l1_w

    fig, ax = _fig(9.0, 7.5)
    ax.set_xlim(-2.5, OX + 3.2)
    ax.set_ylim(-3.0, OY + 2.2)

    # Concrete walls
    _rect(ax, 0, 0, OX, OY, fc=_CONCRETE, ec=_OUTLINE, lw=2.0)
    _rect(ax, T, T, IX, IY, fc="white", ec=_OUTLINE, lw=1.5)

    # L1 shaded area (left interior)
    _rect(ax, T, T, l1_w, IY, fc="#c8c8c8", ec=_OUTLINE, lw=0.5)
    for yy in [T, T + IY]:
        ax.plot([T, T + l1_w], [yy, yy], color=_OUTLINE, lw=0.8, ls="--", zorder=3)

    # Grate area (right interior -- vertical bar hatching)
    gx = T + l1_w
    _rect(ax, gx, T, grate_w, IY, fc="white", ec=_OUTLINE, lw=1.2)
    n_grate = 12
    for i in range(n_grate):
        bx = gx + grate_w * (i + 1) / (n_grate + 1)
        ax.plot([bx, bx], [T + 0.08, T + IY - 0.08], color=_OUTLINE, lw=0.7, zorder=3)

    # L1 dimension (inside shaded area)
    _dim_h(ax, T, T + l1_w, T + IY * 0.5, "L1", gap=0.15, fontsize=9)

    # -- X dimension (outer, top) --
    _ext_dim_h(ax, 0, OX, OY, OY + 0.8, "X")

    # -- Y dimension (outer, left) --
    _ext_dim_v(ax, 0, OY, 0, -0.9, "Y")

    # -- Inside Y dimension (right) --
    _ext_dim_v(ax, T, T + IY, OX, OX + 1.1, "Inside Y\nDimension")
    ax.text(OX + 1.35, T + IY * 0.30, "3'-0\" (2'-11 3/8\" min)",
            ha="left", va="center", fontsize=6.5, color=_DIM)

    # -- Inside X dimension (bottom) --
    _ext_dim_h(ax, T, T + IX, 0, -1.3, "Inside X Dimension", fontsize=8)
    ax.text(T + IX / 2, -1.7, "3'-0\" (2'-11 3/8\" min)  OR\nPipe penetration dia + 3\" min (90\" max)",
            ha="center", va="top", fontsize=6.5, color=_DIM)

    # T labels (bottom-left and bottom-right)
    _ext_dim_h(ax, 0, T, 0, -0.45, "T", fontsize=8)
    _ext_dim_h(ax, OX - T, OX, 0, -0.45, "T", fontsize=8)

    # T labels (vertical, right side)
    tr_x = OX + 0.25
    ax.annotate("", xy=(tr_x, OY), xytext=(tr_x, OY - T),
                arrowprops=dict(arrowstyle="<->", color=_DIM, lw=0.8, mutation_scale=7))
    ax.text(tr_x + 0.12, OY - T / 2, "T", ha="left", va="center", fontsize=8,
            color=_LABEL, fontweight="bold")

    ax.annotate("", xy=(tr_x, T), xytext=(tr_x, 0),
                arrowprops=dict(arrowstyle="<->", color=_DIM, lw=0.8, mutation_scale=7))
    ax.text(tr_x + 0.12, T / 2, "T", ha="left", va="center", fontsize=8,
            color=_LABEL, fontweight="bold")

    # Axes and title
    _axes_compass(ax, -2.0, -2.5)
    _title(ax, "G2 INLET -- PLAN VIEW")

    return _to_png(fig)


def _diag_expanded_inlet() -> bytes:
    """Plan view of G2 expanded inlet -- per Caltrans Expanded G2/G4 standard plan.

    Outer concrete box, dashed min-clear boundary, Grate Type 24 with horizontal
    stripes, bar-mark circles (F, H, G, C per Caltrans legend), T labels at
    corners, and L1 / L2 dimension callouts.
    """
    T   = 0.75   # wall thickness (ft) ≈ 9"
    OX  = 7.5    # exterior X width (ft)
    OY  = 6.5    # exterior Y depth (ft)
    IX  = OX - 2 * T
    IY  = OY - 2 * T

    # Grate Type 24 opening (plan dimensions)
    grate_w = 2.5
    grate_h = 3.5

    # Grate flush with left interior wall — no cavity on left
    grate_x = T
    L2      = (IY - grate_h) / 2          # symmetric top/bottom clearance
    grate_y = T + L2
    grate_cx = grate_x + grate_w / 2
    grate_cy = grate_y + grate_h / 2

    # L1 = open space to the RIGHT of the grate (inside, grate right edge → right interior wall)
    L1 = IX - grate_w

    fig, ax = _fig(10.5, 9.5)
    ax.set_xlim(-3.5, OX + 4.0)
    ax.set_ylim(-3.2, OY + 2.8)

    # ── Outer concrete box ────────────────────────────────────────────────
    _rect(ax, 0, 0, OX, OY, fc=_CONCRETE, ec=_OUTLINE, lw=2.0)

    # ── Interior void ─────────────────────────────────────────────────────
    _rect(ax, T, T, IX, IY, fc="white", ec=_OUTLINE, lw=1.5, zorder=3)

    # ── Grate opening (Type 24) with horizontal stripes ───────────────────
    ax.add_patch(mpatches.Rectangle(
        (grate_x, grate_y), grate_w, grate_h,
        linewidth=1.4, edgecolor=_OUTLINE, facecolor="#e0e0e0", zorder=5))
    for i in range(1, 11):
        yy = grate_y + i * grate_h / 11
        ax.plot([grate_x, grate_x + grate_w], [yy, yy],
                color="#999", lw=0.55, zorder=6)
    ax.text(grate_cx, grate_cy, "GRATE\nTYPE 24",
            ha="center", va="center", fontsize=7, color="#333", zorder=7,
            bbox=dict(boxstyle="round,pad=0.22", fc="white", ec="none", alpha=0.9))

    # ── Bar-mark circles (F, H, G, C per Caltrans legend) ─────────────────
    def _mark(x, y, letter, fs=8):
        ax.plot(x, y, "o", color="white", ms=16, mec=_OUTLINE, mew=1.0, zorder=8)
        ax.text(x, y, letter, ha="center", va="center",
                fontsize=fs, color=_LABEL, fontweight="bold", zorder=9)

    _mark(OX / 2, OY + 0.5, "G")                              # G — top center (curb ref)
    _mark(grate_cx, grate_cy + 0.55, "G", fs=7)               # G — inside grate
    _mark(-0.38, OY / 2, "F")                                  # F — left outer face
    _mark(OX + 0.38, OY / 2, "F")                             # F — right outer face
    _mark(grate_x + grate_w + 0.38, OY / 2, "H")              # H — right open zone
    _mark(grate_x + grate_w / 2, grate_y - 0.38, "C")         # C — bottom of grate
    _mark(grate_x + grate_w / 2, grate_y + grate_h + 0.38, "C")  # C — top of grate

    # ── T labels — vertical at right corners ──────────────────────────────
    tr_x = OX + 0.38
    for y0, y1 in [(OY - T, OY), (0.0, T)]:
        ax.annotate("", xy=(tr_x, y1), xytext=(tr_x, y0),
                    arrowprops=dict(arrowstyle="<->", color=_DIM, lw=0.8,
                                   mutation_scale=7))
        ax.text(tr_x + 0.14, (y0 + y1) / 2, "T",
                ha="left", va="center", fontsize=8, color=_LABEL, fontweight="bold")
    # T labels — horizontal at bottom corners
    _ext_dim_h(ax, 0, T, 0, -0.55, "T", fontsize=8)
    _ext_dim_h(ax, OX - T, OX, 0, -0.55, "T", fontsize=8)

    # ── L1 — open space RIGHT of grate ───────────────────────────────────
    if L1 > 0.05:
        _dim_h(ax, grate_x + grate_w, OX - T, grate_cy, "L\u2081", gap=0.14, fontsize=8)

    # ── L2 — symmetric top/bottom clearance (right side of grate) ────────
    rl_x = grate_x + grate_w + 0.25
    if L2 > 0.05:
        _dim_v(ax, T, grate_y, rl_x, "L\u2082", gap=0.12, fontsize=7.5)
        _dim_v(ax, grate_y + grate_h, OY - T, rl_x, "L\u2082",
               gap=0.12, fontsize=7.5)


    # ── Annotation: 2'-11 3/8" left side (vertical) ───────────────────────
    _ext_dim_v(ax, T, OY - T, 0, -2.1, "")
    ax.text(-2.7, OY / 2,
            "2\u2019-11\u215b\u201d Min OR\nPipe Penetration\nDiameter + 3\u201d Min\n(90\u201d Max)",
            ha="center", va="center", fontsize=6.5, color=_DIM, linespacing=1.3)

    # ── Annotation: 2'-11 3/8" bottom (horizontal) ────────────────────────
    _ext_dim_h(ax, T, OX - T, 0, -1.85, "")
    ax.text(OX / 2, -2.7,
            "2\u2019-11\u215b\u201d Min OR Pipe Penetration Diameter + 3\u201d Min (90\u201d Max)",
            ha="center", va="top", fontsize=6.5, color=_DIM)

    _axes_compass(ax, -3.0, -2.9)
    _title(ax, "G2 EXPANDED INLET \u2014 PLAN VIEW")

    return _to_png(fig)


def _diag_inlet_top() -> bytes:
    """Plan view of G2 inlet top slab -- matches G2 Inlet layout with H dimension."""
    OX, OY = 6.0, 5.0
    T = 0.50
    IX, IY = OX - 2 * T, OY - 2 * T
    H      = float(_LIVE_PARAMS.get("wall_height_ft", 5.917))
    Y_dim  = float(_LIVE_PARAMS.get("y_dim_ft", OY))
    scale  = OY / max(Y_dim, 0.1)
    H_rep  = max(1.5, min(H * scale, OY + 1.5))   # proportional, clamped to plot bounds

    l1_w = IX * 0.45
    grate_w = IX - l1_w

    fig, ax = _fig(9.5, 7.5)
    ax.set_xlim(-2.5, OX + 4.8)
    ax.set_ylim(-3.0, OY + 2.2)

    # Concrete walls
    _rect(ax, 0, 0, OX, OY, fc=_CONCRETE, ec=_OUTLINE, lw=2.0)
    _rect(ax, T, T, IX, IY, fc="white", ec=_OUTLINE, lw=1.5)

    # L1 shaded area (left interior)
    _rect(ax, T, T, l1_w, IY, fc="#c8c8c8", ec=_OUTLINE, lw=0.5)
    for yy in [T, T + IY]:
        ax.plot([T, T + l1_w], [yy, yy], color=_OUTLINE, lw=0.8, ls="--", zorder=3)

    # Grate area (right interior -- vertical bar hatching)
    gx = T + l1_w
    _rect(ax, gx, T, grate_w, IY, fc="white", ec=_OUTLINE, lw=1.2)
    n_grate = 12
    for i in range(n_grate):
        bx = gx + grate_w * (i + 1) / (n_grate + 1)
        ax.plot([bx, bx], [T + 0.08, T + IY - 0.08], color=_OUTLINE, lw=0.7, zorder=3)

    # L1 dimension (inside shaded area)
    _dim_h(ax, T, T + l1_w, T + IY * 0.5, "L1", gap=0.15, fontsize=9)

    # X dimension (outer, top)
    _ext_dim_h(ax, 0, OX, OY, OY + 0.8, "X")

    # Y dimension (outer, left)
    _ext_dim_v(ax, 0, OY, 0, -0.9, "Y")

    # Inside Y dimension (right)
    _ext_dim_v(ax, T, T + IY, OX, OX + 1.1, "Inside Y\nDimension")
    ax.text(OX + 1.35, T + IY * 0.30, "3'-0\" (2'-11 3/8\" min)",
            ha="left", va="center", fontsize=6.5, color=_DIM)

    # Inside X dimension (bottom)
    _ext_dim_h(ax, T, T + IX, 0, -1.3, "Inside X Dimension", fontsize=8)
    ax.text(T + IX / 2, -1.7, "3'-0\" (2'-11 3/8\" min)  OR\nPipe penetration dia + 3\" min (90\" max)",
            ha="center", va="top", fontsize=6.5, color=_DIM)

    # T labels (bottom)
    _ext_dim_h(ax, 0, T, 0, -0.45, "T", fontsize=8)
    _ext_dim_h(ax, OX - T, OX, 0, -0.45, "T", fontsize=8)

    # T labels (vertical, right side)
    tr_x = OX + 0.25
    ax.annotate("", xy=(tr_x, OY), xytext=(tr_x, OY - T),
                arrowprops=dict(arrowstyle="<->", color=_DIM, lw=0.8, mutation_scale=7))
    ax.text(tr_x + 0.12, OY - T / 2, "T", ha="left", va="center", fontsize=8,
            color=_LABEL, fontweight="bold")
    ax.annotate("", xy=(tr_x, T), xytext=(tr_x, 0),
                arrowprops=dict(arrowstyle="<->", color=_DIM, lw=0.8, mutation_scale=7))
    ax.text(tr_x + 0.12, T / 2, "T", ha="left", va="center", fontsize=8,
            color=_LABEL, fontweight="bold")

    # H dimension — moved further right to clear Inside Y annotation
    hx = OX + 3.5
    ax.annotate("", xy=(hx, 0), xytext=(hx, H_rep),
                arrowprops=dict(arrowstyle="<->", color=_DIM, lw=1.0, mutation_scale=9))
    h_label = _fmt_dim_value("wall_height_ft", H)
    ax.text(hx + 0.15, H_rep / 2,
            f"H = {h_label}\n(from top of existing\nbox to top of grade)",
            ha="left", va="center", fontsize=7.5, color=_LABEL, fontweight="bold",
            linespacing=1.35)
    ax.plot([hx - 0.35, hx], [0, 0],         color=_DIM, lw=0.6, ls=":", zorder=2)
    ax.plot([hx - 0.35, hx], [H_rep, H_rep], color=_DIM, lw=0.6, ls=":", zorder=2)

    _axes_compass(ax, -2.0, -2.5)
    _title(ax, "G2 INLET TOP -- PLAN VIEW")

    return _to_png(fig)


def _diag_expanded_inlet_top() -> bytes:
    """Plan view of G2 expanded inlet top.

    Same layout as G2 Expanded Inlet (bar-mark circles, grate, L1/L2, T labels)
    with an H dimension arrow added on the far right for the fill height.
    """
    T   = 0.75
    OX  = 7.5
    OY  = 6.5
    IX  = OX - 2 * T
    IY  = OY - 2 * T

    grate_w = 2.5
    grate_h = 3.5
    grate_x = T
    L2      = (IY - grate_h) / 2
    grate_y = T + L2
    grate_cx = grate_x + grate_w / 2
    grate_cy = grate_y + grate_h / 2
    L1 = IX - grate_w

    # Live H value
    H      = float(_LIVE_PARAMS.get("wall_height_ft", 5.917))
    Y_dim  = float(_LIVE_PARAMS.get("y_dim_ft", OY))
    scale  = OY / max(Y_dim, 0.1)
    H_rep  = max(1.5, min(H * scale, OY + 1.5))

    fig, ax = _fig(10.5, 9.5)
    ax.set_xlim(-3.5, OX + 5.5)
    ax.set_ylim(-3.2, OY + 2.8)

    # ── Outer concrete box ────────────────────────────────────────────────
    _rect(ax, 0, 0, OX, OY, fc=_CONCRETE, ec=_OUTLINE, lw=2.0)
    _rect(ax, T, T, IX, IY, fc="white", ec=_OUTLINE, lw=1.5, zorder=3)

    # ── Grate opening (Type 24) with horizontal stripes ───────────────────
    ax.add_patch(mpatches.Rectangle(
        (grate_x, grate_y), grate_w, grate_h,
        linewidth=1.4, edgecolor=_OUTLINE, facecolor="#e0e0e0", zorder=5))
    for i in range(1, 11):
        yy = grate_y + i * grate_h / 11
        ax.plot([grate_x, grate_x + grate_w], [yy, yy],
                color="#999", lw=0.55, zorder=6)
    ax.text(grate_cx, grate_cy, "GRATE\nTYPE 24",
            ha="center", va="center", fontsize=7, color="#333", zorder=7,
            bbox=dict(boxstyle="round,pad=0.22", fc="white", ec="none", alpha=0.9))

    # ── Bar-mark circles (F, H, G, C per Caltrans legend) ─────────────────
    def _mark(x, y, letter, fs=8):
        ax.plot(x, y, "o", color="white", ms=16, mec=_OUTLINE, mew=1.0, zorder=8)
        ax.text(x, y, letter, ha="center", va="center",
                fontsize=fs, color=_LABEL, fontweight="bold", zorder=9)

    _mark(OX / 2, OY + 0.5, "G")
    _mark(grate_cx, grate_cy + 0.55, "G", fs=7)
    _mark(-0.38, OY / 2, "F")
    _mark(OX + 0.38, OY / 2, "F")
    _mark(grate_x + grate_w + 0.38, OY / 2, "H")
    _mark(grate_x + grate_w / 2, grate_y - 0.38, "C")
    _mark(grate_x + grate_w / 2, grate_y + grate_h + 0.38, "C")

    # ── T labels ──────────────────────────────────────────────────────────
    tr_x = OX + 0.38
    for y0, y1 in [(OY - T, OY), (0.0, T)]:
        ax.annotate("", xy=(tr_x, y1), xytext=(tr_x, y0),
                    arrowprops=dict(arrowstyle="<->", color=_DIM, lw=0.8,
                                   mutation_scale=7))
        ax.text(tr_x + 0.14, (y0 + y1) / 2, "T",
                ha="left", va="center", fontsize=8, color=_LABEL, fontweight="bold")
    _ext_dim_h(ax, 0, T, 0, -0.55, "T", fontsize=8)
    _ext_dim_h(ax, OX - T, OX, 0, -0.55, "T", fontsize=8)

    # ── L1 / L2 dimensions ────────────────────────────────────────────────
    if L1 > 0.05:
        _dim_h(ax, grate_x + grate_w, OX - T, grate_cy, "L\u2081", gap=0.14, fontsize=8)
    rl_x = grate_x + grate_w + 0.25
    if L2 > 0.05:
        _dim_v(ax, T, grate_y, rl_x, "L\u2082", gap=0.12, fontsize=7.5)
        _dim_v(ax, grate_y + grate_h, OY - T, rl_x, "L\u2082", gap=0.12, fontsize=7.5)

    # ── Clearance annotations ─────────────────────────────────────────────
    _ext_dim_v(ax, T, OY - T, 0, -2.1, "")
    ax.text(-2.7, OY / 2,
            "2\u2019-11\u215b\u201d Min OR\nPipe Penetration\nDiameter + 3\u201d Min\n(90\u201d Max)",
            ha="center", va="center", fontsize=6.5, color=_DIM, linespacing=1.3)
    _ext_dim_h(ax, T, OX - T, 0, -1.85, "")
    ax.text(OX / 2, -2.7,
            "2\u2019-11\u215b\u201d Min OR Pipe Penetration Diameter + 3\u201d Min (90\u201d Max)",
            ha="center", va="top", fontsize=6.5, color=_DIM)

    # ── H arrow (far right, clear of bar-mark F circle) ───────────────────
    hx = OX + 3.0
    ax.annotate("", xy=(hx, 0), xytext=(hx, H_rep),
                arrowprops=dict(arrowstyle="<->", color=_DIM, lw=1.0, mutation_scale=9))
    h_label = _fmt_dim_value("wall_height_ft", H)
    ax.text(hx + 0.15, H_rep / 2,
            f"H = {h_label}\n(from top of existing\nbox to top of grade)",
            ha="left", va="center", fontsize=7.5, color=_LABEL, fontweight="bold",
            linespacing=1.35)
    ax.plot([hx - 0.35, hx], [0, 0],         color=_DIM, lw=0.6, ls=":", zorder=2)
    ax.plot([hx - 0.35, hx], [H_rep, H_rep], color=_DIM, lw=0.6, ls=":", zorder=2)

    _axes_compass(ax, -3.0, -2.9)
    _title(ax, "G2 EXPANDED INLET TOP \u2014 PLAN VIEW")

    return _to_png(fig)


def _diag_headwall() -> bytes:
    """Combined front elevation + typical section for a D89A straight headwall.

    Both views are drawn to H1 (= H + H1 extension) — the full physical wall height.
    Front elevation: H1 dimension on right side only (per D89A standard plan).
    Typical section: Design H on left, H1 on right.
    Dashed line at H marks the design height boundary in both views.
    H1 extension defaults to 1'-0\" (12\"); reads live value from _LIVE_PARAMS.
    """
    # Default preview dimensions (overridden when called live)
    L    = float(_LIVE_PARAMS.get("wall_width_ft", 8.0))
    H    = float(_LIVE_PARAMS.get("wall_height_ft", 5.917))
    H_in = H * 12.0
    H1   = float(_LIVE_PARAMS.get("h1_ft", H + 1.0))   # total physical height; default H + 1'-0"
    H1_in = H1 * 12.0

    # D89A table lookup
    try:
        from vistadetail.engine.rules.headwall_rules import _D89A_ROWS
        row = _D89A_ROWS[-1]
        for r in _D89A_ROWS:
            if r["H"] >= H_in - 0.1:
                row = r
                break
    except Exception:
        row = {"T": 10, "W": 64, "C": 16, "B": 48, "F": 12,
               "c_s": "#4", "c_p": 12, "d_s": "#5", "d_p": 8}

    T_in = row["T"];  W_in = row["W"];  C_in = row["C"]
    B_in = row["B"];  F_in = row["F"]
    c_sp = row["c_p"]; d_sp = row["d_p"]
    c_sz = row["c_s"]; d_sz = row["d_s"]

    T = T_in / 12.0;  W = W_in / 12.0;  C = C_in / 12.0
    B = B_in / 12.0;  F = F_in / 12.0
    cov  = 2.0 / 12.0
    fcov = 3.0 / 12.0

    # Scale to H1 so the 1'-0" extension fits
    s = min(4.5 / max(L, 1.0), 3.0 / max(H1 + F, 1.0))
    s = max(s, 0.30)

    fig, ax = _fig(w=13.0, h=6.5)

    # ── FRONT ELEVATION ──────────────────────────────────────────────────
    ex = 0.6
    ey = 0.5 + F * s

    # Footing strip
    _rect(ax, ex, ey - F*s, L*s, F*s, fc="#b0b8c0", ec=_OUTLINE, lw=1.0)
    # Wall body drawn to full H1 height
    _rect(ax, ex, ey, L*s, H1*s)

    # Dashed line at design H (marks boundary between H and the 1'-0" extension)
    ax.plot([ex, ex + L*s], [ey + H*s, ey + H*s],
            color=_OUTLINE, lw=0.9, ls="--", zorder=5)

    # LW horizontal bars at 12" oc — full H1 height
    n_lw = int(H1) + 1
    for i in range(n_lw + 1):
        yy = ey + i * s
        if yy > ey + H1*s: break
        ax.plot([ex + cov*s, ex + L*s - cov*s], [yy, yy],
                color=_REBAR, lw=0.7, zorder=4)

    # VW vertical bars at 12" oc
    n_vw = int(L - 2*cov) + 1
    for i in range(n_vw + 1):
        xx = ex + cov*s + i * s
        if xx > ex + L*s - cov*s: break
        ax.plot([xx, xx], [ey + cov*s, ey + H1*s - cov*s],
                color=_REBAR, lw=0.7, zorder=4)

    # TW dots — 3 at top of wall (H1)
    for frac in [0.25, 0.5, 0.75]:
        ax.plot(ex + L*s * frac, ey + H1*s - cov*s, "o",
                color=_REBAR, ms=5, zorder=5)

    # D1 transverse dots at footing junction
    n_d1 = math.floor(L / (d_sp / 12.0)) + 1
    for i in range(n_d1 + 1):
        xx = ex + i * (d_sp / 12.0) * s
        if xx > ex + L*s: break
        ax.plot(xx, ey, "o", color=_REBAR, ms=4, zorder=5)

    # Dimensions — front elevation: W below, H1 on left (avoids crowding the section gap)
    _ext_dim_h(ax, ex, ex + L*s, ey - F*s, ey - F*s - 0.32, "W")
    _ext_dim_v(ax, ey, ey + H1*s, ex, ex - 0.55, "H1")

    # Callouts
    ax.text(ex + L*s * 0.5, ey + H1*s + 0.22, "FRONT ELEVATION",
            ha="center", va="bottom", fontsize=8, color=_LABEL,
            fontweight="bold", zorder=6)
    ax.text(ex + L*s * 0.5, ey + H1*s + 0.08,
            f"LW/VW #{c_sz[1]}@12\"  |  TW {d_sz} Tot 3  |  D1 {d_sz}@{d_sp}\"",
            ha="center", va="top", fontsize=6.5, color=_REBAR, zorder=6)

    # ── TYPICAL SECTION ──────────────────────────────────────────────────
    gap = 1.2
    tx  = ex + L*s + gap
    ty  = ey
    wx  = tx + C * s

    # Footing
    _rect(ax, tx, ty - F*s, W*s, F*s, fc="#b0b8c0", ec=_OUTLINE, lw=1.0)

    # Earth hatching (heel side) — runs full H1 height
    earth_x = wx + T*s
    for i in range(9):
        ye = ty - F*s * 0.4 + i * (H1*s + F*s * 0.4) / 8
        ax.plot([earth_x + 0.04, earth_x + 0.22], [ye, ye - 0.15],
                color=_SOIL, lw=0.8, alpha=0.7, zorder=1)

    # Wall stem drawn to full H1 height
    _rect(ax, wx, ty, T*s, H1*s)

    # Dashed line at design H in section
    ax.plot([wx, wx + T*s], [ty + H*s, ty + H*s],
            color=_OUTLINE, lw=0.9, ls="--", zorder=5)

    # Bar dots both faces — full H1 height
    for i in range(n_lw + 1):
        yy = ty + i * s
        if yy > ty + H1*s: break
        ax.plot(wx + cov*s,         yy, "o", color=_REBAR, ms=4, zorder=5)
        ax.plot(wx + T*s - cov*s,   yy, "o", color=_REBAR, ms=4, zorder=5)

    # TW top center dot at H1
    ax.plot(wx + T*s / 2, ty + H1*s - cov*s, "o", color=_REBAR, ms=6, zorder=5)

    # TF dots across footing
    n_tf = math.floor(W) + 1
    for i in range(n_tf + 1):
        xx = tx + fcov*s + i * s
        if xx > tx + W*s - fcov*s: break
        ax.plot(xx, ty - F*s / 2, "o", color=_REBAR, ms=3.5, zorder=5)

    # CB c-bar — U-shape, extends to H1 top
    cb_leg  = 14.0 / 12.0 * s
    cb_lx   = wx - cb_leg
    cb_rx   = wx + T*s + cb_leg
    cb_top  = ty + H1*s + 0.12
    cb_base = ty + cov*s
    ax.plot([cb_lx, cb_lx], [cb_top, cb_base], color=_REBAR, lw=1.5, zorder=4)
    ax.plot([cb_lx, cb_rx], [cb_base, cb_base], color=_REBAR, lw=1.5, zorder=4)
    ax.plot([cb_rx, cb_rx], [cb_base, cb_top], color=_REBAR, lw=1.5, zorder=4)
    ax.text(cb_lx - 0.08, ty + H1*s * 0.75, f'"{c_sz}" C-BAR',
            ha="right", va="center", fontsize=6.5, color=_REBAR, zorder=6,
            bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85))
    ax.text(cb_rx + 0.08, cb_base + 0.04, "R=9\"",
            ha="left", va="center", fontsize=6, color=_REBAR, zorder=6)

    # Section dimensions — H (design) on left, H1 on right
    _ext_dim_v(ax, ty, ty + H*s,  wx,          wx - 0.55, "H")
    _ext_dim_v(ax, ty, ty + H1*s, tx + W*s,    tx + W*s + 0.55, "H1")
    _dim_v(ax, ty - F*s, ty, tx - 0.1, f"F={fmt_inches(F_in)}", gap=0.22, fontsize=7)
    _ext_dim_h(ax, tx, tx + W*s, ty - F*s, ty - F*s - 0.32, "W")
    ax.annotate(f"T={T_in:.0f}\"", xy=(wx + T*s/2, ty + H1*s*0.35),
                xytext=(wx + T*s + 0.75, ty + H1*s*0.5),
                fontsize=7.5, color=_LABEL, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=_DIM, lw=0.7),
                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=_DIM, lw=0.5))
    ax.text(tx + C*s/2, ty - F*s - 0.15, f"C={fmt_inches(C_in)}",
            ha="center", va="top", fontsize=7, color=_LABEL, fontweight="bold")
    ax.text(wx + T*s + B*s/2, ty - F*s - 0.15, f"B={fmt_inches(B_in)}",
            ha="center", va="top", fontsize=7, color=_LABEL, fontweight="bold")

    ax.text(wx + T*s / 2, ty + H1*s + 0.22, "TYPICAL SECTION",
            ha="center", va="bottom", fontsize=8, color=_LABEL,
            fontweight="bold", zorder=6)

    # ── Bounds ───────────────────────────────────────────────────────────
    ax.set_xlim(ex - 1.6, tx + W*s + 1.7)
    ax.set_ylim(ty - F*s - 0.75, ty + H1*s + 1.0)
    _title(ax, "STRAIGHT HEADWALL  (D89A)")

    return _to_png(fig)


def _diag_wing_wall() -> bytes:
    """Elevation of tapered wing wall -- L length, H1 (hw), H2 (tip)."""
    L, H1, H2 = 6.0, 3.5, 0.6

    fig, ax = _fig(7.5, 5.5)
    ax.set_xlim(-1.2, L + 1.8)
    ax.set_ylim(-1.2, H1 + 1.2)

    pts = [(0, 0), (L, 0), (L, H2), (0, H1)]
    poly = plt.Polygon(pts, closed=True, fc=_CONCRETE, ec=_OUTLINE, lw=2.0, zorder=2)
    ax.add_patch(poly)

    # Rebar hints (vertical bars following taper)
    for xi in [0.3, 0.8, 1.5, 3.0, 4.5, 5.5]:
        if xi < L:
            h_here = H1 + (H2 - H1) * xi / L
            ax.plot([xi, xi], [0.1, h_here - 0.1], color=_REBAR, lw=1.0, zorder=4)

    # Horizontal rebar
    for frac in [0.15, 0.45, 0.75]:
        yi = H1 * frac
        x_end = L * min(1.0, yi / H2) if H2 > 0 else L
        ax.plot([0.1, L - 0.1], [yi, yi], color=_REBAR, lw=0.8, zorder=4)

    _ext_dim_h(ax, 0, L, 0, -0.7, "L")
    _ext_dim_v(ax, 0, H1, 0, -0.8, "H\u2081", fontsize=10)
    _ext_dim_v(ax, 0, H2, L, L + 0.7, "H\u2082", fontsize=10)

    _axes_compass(ax, -0.9, -1.0)
    _title(ax, "WING WALL -- ELEVATION")

    return _to_png(fig)


def _diag_footing() -> bytes:
    """Plan view of spread footing -- L x W, with D depth callout."""
    L, W = 6.0, 4.5

    fig, ax = _fig(7.0, 5.5)
    ax.set_xlim(-1.2, L + 1.8)
    ax.set_ylim(-1.2, W + 1.5)

    _rect(ax, 0, 0, L, W, fc=_CONCRETE, ec=_OUTLINE, lw=2.0)
    _rebar_grid(ax, 0, 0, L, W, nx=6, ny=5, margin=0.2)

    # Column stub (center)
    col_w = L * 0.13
    cx = (L - col_w) / 2
    cy = (W - col_w) / 2
    _rect(ax, cx, cy, col_w, col_w, fc="#9aa8b0", ec=_OUTLINE, lw=1.5, zorder=3)
    ax.text(L / 2, W / 2, "col.", ha="center", va="center", fontsize=7, color="#555", zorder=4)

    _ext_dim_h(ax, 0, L, 0, -0.7, "L")
    _ext_dim_v(ax, 0, W, L, L + 0.7, "W")
    _callout(ax, L * 0.85, W * 0.15, "D", "depth", angle=30, dist=0.8)

    _axes_compass(ax, -0.9, -1.0)
    _title(ax, "SPREAD FOOTING -- PLAN VIEW")

    return _to_png(fig)


def _diag_box_culvert() -> bytes:
    """Cross-section of box culvert -- live span S, height H, cover, barrel B."""
    # --- Live inputs -----------------------------------------------------------
    span_ft   = float(_LIVE_PARAMS.get("span_ft",   8.0))
    height_ft = float(_LIVE_PARAMS.get("height_ft", 6.0))
    barrel_ft = float(_LIVE_PARAMS.get("barrel_length_ft", 20.0))
    cover_ft  = int(_LIVE_PARAMS.get("max_earth_cover_ft", 10))

    # Scale to plot coordinates (max inner dim → ~5 plot units)
    max_dim   = max(span_ft, height_ft, 1.0)
    sc        = 5.0 / max_dim
    S   = span_ft   * sc          # inner span (plot units)
    H   = height_ft * sc          # inner height (plot units)
    T   = max(0.35, min(0.65, sc * 0.75))   # wall thickness — proportional, clamped

    total_w = S + 2 * T
    total_h = H + 2 * T

    fig, ax = _fig(7.5, 6.5)
    ax.set_xlim(-1.5, total_w + 2.2)
    ax.set_ylim(-1.8, total_h + 1.5)

    # Outer section
    _rect(ax, 0, 0, total_w, total_h, fc=_CONCRETE, ec=_OUTLINE, lw=2.0)
    # Inner void
    _rect(ax, T, T, S, H, fc="white", ec=_OUTLINE, lw=1.2)

    # Rebar in walls (inside + outside face lines)
    for offset in [0.10, 0.25]:
        ax.plot([offset, offset], [T + 0.12, T + H - 0.12],
                color=_REBAR, lw=1.0, zorder=4)
        ax.plot([total_w - offset, total_w - offset], [T + 0.12, T + H - 0.12],
                color=_REBAR, lw=1.0, zorder=4)
    # Rebar in top/bottom slabs
    for offset in [0.10, 0.25]:
        ax.plot([T + 0.08, T + S - 0.08], [offset, offset],
                color=_REBAR, lw=0.8, zorder=4)
        ax.plot([T + 0.08, T + S - 0.08], [total_h - offset, total_h - offset],
                color=_REBAR, lw=0.8, zorder=4)

    # --- Dimension labels with live values ------------------------------------
    s_label = _fmt_dim_value("span_ft",   span_ft)
    h_label = _fmt_dim_value("height_ft", height_ft)
    b_label = _fmt_dim_value("barrel_length_ft", barrel_ft)

    _dim_h(ax, T, T + S, T + H * 0.5, f"S = {s_label}", gap=-0.38, fontsize=9)
    _dim_v(ax, T, T + H, T + S * 0.82, f"H = {h_label}", gap=0.18, fontsize=9)

    # Barrel label (centre of section)
    ax.text(total_w / 2, total_h / 2,
            f"B = {b_label}\n(Barrel Length)",
            ha="center", va="center", fontsize=7.5, color="#555",
            bbox=dict(boxstyle="round", fc="white", ec="#ccc", alpha=0.88), zorder=5)

    # Max earth cover label (bottom, below section)
    ax.text(total_w / 2, -1.35,
            f"Max Earth Cover = {cover_ft}'",
            ha="center", va="center", fontsize=8.0, color=_LABEL, fontweight="bold")

    _axes_compass(ax, -1.2, -1.4)
    _title(ax, "BOX CULVERT -- CROSS SECTION")

    return _to_png(fig)


def _diag_retaining_wall() -> bytes:
    """Cross-section of cantilever retaining wall -- H stem, L footing."""
    H, L, D, T = 5.0, 4.5, 0.5, 0.4
    stem_x = 1.0

    fig, ax = _fig(7.0, 6.5)
    ax.set_xlim(-1.5, L + 2.0)
    ax.set_ylim(-1.2, H + D + 1.2)

    # Footing
    _rect(ax, 0, 0, L, D, fc=_CONCRETE, ec=_OUTLINE, lw=2.0)
    # Stem
    _rect(ax, stem_x, D, T, H, fc=_CONCRETE, ec=_OUTLINE, lw=2.0)

    # Soil fill (behind stem)
    _rect(ax, stem_x + T, D, L - stem_x - T - 0.05, H * 0.7,
          fc=_SOIL, ec="#c4b498", lw=0.6, hatch="....", zorder=1)
    ax.text(stem_x + T + (L - stem_x - T) * 0.5, D + H * 0.35, "soil",
            ha="center", fontsize=7, color="#8b7355", style="italic")

    # Rebar (vertical in stem)
    for xi in [stem_x + 0.08, stem_x + T - 0.08]:
        ax.plot([xi, xi], [D + 0.1, D + H - 0.1], color=_REBAR, lw=1.2, zorder=4)
    # Rebar (horizontal in footing)
    for yi in [D * 0.25, D * 0.75]:
        ax.plot([0.1, L - 0.1], [yi, yi], color=_REBAR, lw=1.0, zorder=4)

    _ext_dim_v(ax, D, D + H, L, L + 0.8, "H")
    _ext_dim_h(ax, 0, L, 0, -0.7, "L")

    _axes_compass(ax, -1.2, -1.0)
    _title(ax, "RETAINING WALL -- CROSS SECTION")

    return _to_png(fig)


def _diag_caltrans_retaining_wall() -> bytes:
    """Cross-section of Caltrans retaining wall -- design H, wall length L."""
    H = 5.0
    L_foot = 3.5
    D = 0.6
    T_stem = 0.5
    T_toe = 1.0
    stem_x = T_toe

    fig, ax = _fig(7.5, 7.0)
    ax.set_xlim(-1.8, L_foot + 2.5)
    ax.set_ylim(-1.5, H + D + 1.5)

    # Footing
    _rect(ax, 0, 0, L_foot, D, fc=_CONCRETE, ec=_OUTLINE, lw=2.0)
    # Stem (tapered -- wider at base)
    T_base = T_stem + 0.15
    pts_stem = [
        (stem_x, D),
        (stem_x + T_base, D),
        (stem_x + T_stem, D + H),
        (stem_x, D + H),
    ]
    poly = plt.Polygon(pts_stem, closed=True, fc=_CONCRETE, ec=_OUTLINE, lw=2.0, zorder=2)
    ax.add_patch(poly)

    # Key below footing
    key_w = 0.3
    key_d = 0.4
    key_x = stem_x + T_base / 2 - key_w / 2
    _rect(ax, key_x, -key_d, key_w, key_d, fc=_CONCRETE, ec=_OUTLINE, lw=1.2)

    # Soil
    _rect(ax, stem_x + T_base, D, L_foot - stem_x - T_base - 0.05, H * 0.65,
          fc=_SOIL, ec="#c4b498", lw=0.6, hatch="....", zorder=1)
    ax.text(stem_x + T_base + (L_foot - stem_x - T_base) * 0.5, D + H * 0.3,
            "soil", ha="center", fontsize=7, color="#8b7355", style="italic")

    # Rebar
    for xi in [stem_x + 0.08, stem_x + T_stem - 0.08]:
        ax.plot([xi, xi], [D + 0.1, D + H - 0.1], color=_REBAR, lw=1.2, zorder=4)
    for yi in [D * 0.25, D * 0.75]:
        ax.plot([0.1, L_foot - 0.1], [yi, yi], color=_REBAR, lw=1.0, zorder=4)

    # H dimension (design height)
    _ext_dim_v(ax, 0, D + H, L_foot, L_foot + 0.9, "H\n(design)")
    # L dimension (wall length -- into page indicator)
    ax.text(L_foot / 2, D / 2, "L \u2192 wall length (into page)",
            ha="center", va="center", fontsize=7, color="#666",
            bbox=dict(boxstyle="round", fc="white", ec="#ccc", alpha=0.85), zorder=5)

    _axes_compass(ax, -1.5, -1.2)
    _title(ax, "CALTRANS RETAINING WALL -- CROSS SECTION")

    return _to_png(fig)


def _diag_sound_wall() -> bytes:
    """Elevation of sound wall -- H height, L length, with foundation."""
    H, L = 4.0, 8.0
    F_d = 0.6

    fig, ax = _fig(9.0, 6.0)
    ax.set_xlim(-1.5, L + 2.0)
    ax.set_ylim(-1.5, H + F_d + 1.5)

    # Foundation strip
    _rect(ax, -0.3, 0, L + 0.6, F_d, fc="#b0b8c0", ec=_OUTLINE, lw=1.5)

    # Wall panels
    n_panels = 4
    panel_gap = 0.08
    pw = (L - (n_panels - 1) * panel_gap) / n_panels
    for i in range(n_panels):
        px = i * (pw + panel_gap)
        _rect(ax, px, F_d, pw, H, fc=_CONCRETE, ec=_OUTLINE, lw=1.5)
        # Vertical rebar
        for xi in [px + 0.12, px + pw - 0.12]:
            ax.plot([xi, xi], [F_d + 0.15, F_d + H - 0.15],
                    color=_REBAR, lw=0.9, zorder=4)

    # Horizontal rebar across panels
    for frac in [0.2, 0.5, 0.8]:
        yi = F_d + H * frac
        ax.plot([0.1, L - 0.1], [yi, yi], color=_REBAR, lw=0.8, zorder=4)

    # Ground line
    ax.plot([-0.5, L + 0.5], [F_d, F_d], color="#555", lw=1.0, ls="-.", zorder=5)
    ax.text(L + 0.6, F_d, "GL", fontsize=7, color="#555", va="center")

    _ext_dim_v(ax, F_d, F_d + H, L, L + 0.9, "H")
    _ext_dim_h(ax, 0, L, F_d + H, F_d + H + 0.7, "L")

    _axes_compass(ax, -1.2, -1.2)
    _title(ax, "SOUND WALL -- ELEVATION")

    return _to_png(fig)


def _diag_cage() -> bytes:
    """Elevation + plan view of drilled shaft cage -- phi diameter, D depth."""
    D_depth = 5.0
    phi = 1.5
    n_rings = 5

    fig, ax = _fig(7.5, 5.5)
    ax.set_xlim(-1.0, D_depth + 3.5)
    ax.set_ylim(-1.2, phi * 1.6 + 1.0)

    cage_top = phi * 1.2
    cage_bot = 0.2

    # Elevation view frame
    ax.plot([0, D_depth], [cage_top, cage_top], color=_OUTLINE, lw=1.5)
    ax.plot([0, D_depth], [cage_bot, cage_bot], color=_OUTLINE, lw=1.5)
    ax.plot([0, 0], [cage_bot, cage_top], color=_OUTLINE, lw=1.5)
    ax.plot([D_depth, D_depth], [cage_bot, cage_top], color=_OUTLINE, lw=1.0, ls="--")

    # Hoops (vertical ticks)
    ring_gap = D_depth / n_rings
    for i in range(n_rings + 1):
        xr = i * ring_gap
        ax.plot([xr, xr], [cage_bot, cage_top], color=_REBAR, lw=1.4, zorder=4)

    # Longitudinal bars
    for yi in [cage_bot + 0.1, cage_top - 0.1]:
        ax.plot([0, D_depth], [yi, yi], color=_REBAR, lw=0.9, ls="--", zorder=4)

    # Plan view circle
    cx, cy = D_depth + 2.0, (cage_top + cage_bot) / 2
    r = (cage_top - cage_bot) / 2
    circ_outer = mpatches.Circle((cx, cy), r, fc=_CONCRETE, ec=_OUTLINE, lw=1.5, zorder=2)
    circ_inner = mpatches.Circle((cx, cy), r * 0.75, fc="white", ec=_OUTLINE, lw=0.8, zorder=3)
    ax.add_patch(circ_outer)
    ax.add_patch(circ_inner)

    # Vert bars as dots on circle
    n_v = 8
    for i in range(n_v):
        ang = 2 * math.pi * i / n_v
        bx = cx + r * 0.88 * math.cos(ang)
        by = cy + r * 0.88 * math.sin(ang)
        ax.plot(bx, by, "o", color=_REBAR, ms=4, zorder=5)

    # Phi dimension
    ax.annotate("", xy=(cx + r, cy), xytext=(cx - r, cy),
                arrowprops=dict(arrowstyle="<->", color=_DIM, lw=0.9, mutation_scale=8))
    _phi_label = _aug_label("\u03c6")
    ax.text(cx, cy + r + 0.25, _phi_label, ha="center", va="bottom", fontsize=12,
            color=_LABEL, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.92))

    # Depth dimension
    _ext_dim_h(ax, 0, D_depth, cage_bot, cage_bot - 0.6, "D (depth)")

    # Labels
    ax.text(D_depth / 2, (cage_top + cage_bot) / 2, "elevation",
            ha="center", fontsize=7, color="#888", style="italic", va="center")
    ax.text(cx, cy, "plan", ha="center", va="center",
            fontsize=7, color="#888", style="italic")

    _axes_compass(ax, -0.7, -1.0)
    _title(ax, "DRILLED SHAFT CAGE -- ELEVATION + PLAN")

    return _to_png(fig)


def _diag_rect_plan(title="FLAT SLAB -- PLAN VIEW") -> bytes:
    """Generic plan-view rectangle with L x W labels."""
    L, W = 6.0, 4.0

    fig, ax = _fig(7.0, 5.5)
    ax.set_xlim(-1.2, L + 1.8)
    ax.set_ylim(-1.2, W + 1.5)

    _rect(ax, 0, 0, L, W, fc=_CONCRETE, ec=_OUTLINE, lw=2.0)
    _rebar_grid(ax, 0, 0, L, W, nx=6, ny=5, margin=0.2)

    _ext_dim_h(ax, 0, L, 0, -0.7, "L")
    _ext_dim_v(ax, 0, W, L, L + 0.7, "W")

    _axes_compass(ax, -0.9, -1.0)
    _title(ax, title)

    return _to_png(fig)


def _diag_rect_plan_with_T(title="SLAB ON GRADE -- PLAN VIEW") -> bytes:
    """Rectangle plan with L x W + T thickness callout."""
    L, W = 6.0, 4.0

    fig, ax = _fig(7.0, 5.5)
    ax.set_xlim(-1.2, L + 1.8)
    ax.set_ylim(-1.2, W + 1.5)

    _rect(ax, 0, 0, L, W, fc=_CONCRETE, ec=_OUTLINE, lw=2.0)
    _rebar_grid(ax, 0, 0, L, W, nx=6, ny=5, margin=0.2)

    _ext_dim_h(ax, 0, L, 0, -0.7, "L")
    _ext_dim_v(ax, 0, W, L, L + 0.7, "W")
    _callout(ax, L * 0.82, W * 0.15, "T", "thickness", angle=30, dist=0.85)

    _axes_compass(ax, -0.9, -1.0)
    _title(ax, title)

    return _to_png(fig)


def _diag_wall_section(title="SEATWALL -- CROSS SECTION", hw=2.5, ww=1.5) -> bytes:
    """Cross-section of a wall: height H x width W."""
    fig, ax = _fig(5.5, 5.5)
    ax.set_xlim(-1.2, ww + 2.0)
    ax.set_ylim(-1.2, hw + 1.2)

    _rect(ax, 0, 0, ww, hw, fc=_CONCRETE, ec=_OUTLINE, lw=2.0)

    # Rebar (vertical near faces)
    for xi in [0.12, ww - 0.12]:
        ax.plot([xi, xi], [0.15, hw - 0.15], color=_REBAR, lw=1.2, zorder=4)
    # Rebar (horizontal ties)
    for yi in [hw * 0.15, hw * 0.5, hw * 0.85]:
        ax.plot([0.1, ww - 0.1], [yi, yi], color=_REBAR, lw=1.0, zorder=4)

    _ext_dim_v(ax, 0, hw, ww, ww + 0.7, "H")
    _ext_dim_h(ax, 0, ww, 0, -0.7, "W")

    # L callout (into page)
    ax.text(ww / 2, hw + 0.5, "L \u2192 length (into page)",
            ha="center", va="bottom", fontsize=7, color="#666",
            bbox=dict(boxstyle="round", fc="white", ec="#ccc", alpha=0.85))

    _axes_compass(ax, -0.9, -1.0)
    _title(ax, title)

    return _to_png(fig)


def _diag_pipe_encasement() -> bytes:
    """Cross-section of pipe encasement -- W x H with pipe inside."""
    W, H = 3.5, 3.5
    pipe_r = 1.0

    fig, ax = _fig(6.5, 5.5)
    ax.set_xlim(-1.2, W + 2.0)
    ax.set_ylim(-1.2, H + 1.5)

    _rect(ax, 0, 0, W, H, fc=_CONCRETE, ec=_OUTLINE, lw=2.0)

    # Pipe
    cx, cy = W / 2, H / 2
    pipe = mpatches.Circle((cx, cy), pipe_r, fc="white", ec=_OUTLINE, lw=2.0, zorder=3)
    pipe_void = mpatches.Circle((cx, cy), pipe_r * 0.8,
                                 fc="#dde8f0", ec="#889aaa", lw=0.8, zorder=4)
    ax.add_patch(pipe)
    ax.add_patch(pipe_void)
    ax.text(cx, cy, "pipe", ha="center", va="center", fontsize=7, color="#555", zorder=5)

    # Rebar hoops
    for r_off in [0.15, 0.30]:
        hoop = mpatches.Circle((cx, cy), pipe_r + r_off, fill=False,
                                ec=_REBAR, lw=1.2, ls="--", zorder=2)
        ax.add_patch(hoop)

    _ext_dim_h(ax, 0, W, 0, -0.7, "W")
    _ext_dim_v(ax, 0, H, W, W + 0.7, "H")
    _callout(ax, W * 0.85, H * 0.85, "L", "length (into page)", angle=45, dist=0.7)

    _axes_compass(ax, -0.9, -1.0)
    _title(ax, "PIPE ENCASEMENT -- CROSS SECTION")

    return _to_png(fig)


def _diag_junction() -> bytes:
    """Plan view of junction structure -- inside L x W, with wall T."""
    L, W, T = 5.0, 3.5, 0.5
    total_w = L + 2 * T
    total_h = W + 2 * T

    fig, ax = _fig(7.5, 6.0)
    ax.set_xlim(-1.5, total_w + 2.0)
    ax.set_ylim(-1.5, total_h + 1.5)

    # Outer walls
    _rect(ax, 0, 0, total_w, total_h, fc=_CONCRETE, ec=_OUTLINE, lw=2.0)
    # Inner void
    _rect(ax, T, T, L, W, fc="white", ec=_OUTLINE, lw=1.2)

    # Pipe stubs (openings on sides)
    stub_h = W * 0.3
    stub_w = T + 0.3
    for side_y in [T + W * 0.35]:
        # Left
        _rect(ax, -0.3, side_y, stub_w, stub_h, fc="white", ec=_OUTLINE, lw=1.0, zorder=3)
        # Right
        _rect(ax, total_w - T, side_y, stub_w + 0.3, stub_h, fc="white", ec=_OUTLINE, lw=1.0, zorder=3)

    # Inside L dimension (top)
    _ext_dim_h(ax, T, T + L, total_h, total_h + 0.6, "L (inside)")
    # Inside W dimension (right)
    _ext_dim_v(ax, T, T + W, total_w, total_w + 0.7, "W (inside)")
    # Depth callout
    ax.text(total_w / 2, total_h / 2, "D \u2192 depth",
            ha="center", va="center", fontsize=7, color="#666",
            bbox=dict(boxstyle="round", fc="white", ec="#ccc", alpha=0.85), zorder=5)
    # T callout
    _callout(ax, T / 2, T / 2, "T", "wall", angle=225, dist=0.6, fontsize=7)

    _axes_compass(ax, -1.2, -1.2)
    _title(ax, "JUNCTION STRUCTURE -- PLAN VIEW")

    return _to_png(fig)


def _diag_dual_slab() -> bytes:
    """Plan view of dual slab -- Slab A and Slab B side by side."""
    La, Wa = 5.0, 3.0
    Lb, Wb = 4.0, 2.5
    gap = 0.3

    fig, ax = _fig(8.5, 5.5)
    ax.set_xlim(-1.2, La + gap + Lb + 1.8)
    ax.set_ylim(-1.2, max(Wa, Wb) + 1.5)

    # Slab A
    _rect(ax, 0, 0, La, Wa, fc=_CONCRETE, ec=_OUTLINE, lw=2.0)
    _rebar_grid(ax, 0, 0, La, Wa, nx=5, ny=4, margin=0.2)
    ax.text(La / 2, Wa / 2, "Slab A", ha="center", va="center",
            fontsize=9, color=_LABEL, fontweight="bold", zorder=5)

    # Slab B
    bx = La + gap
    _rect(ax, bx, 0, Lb, Wb, fc="#bfc8d0", ec=_OUTLINE, lw=2.0)
    _rebar_grid(ax, bx, 0, Lb, Wb, nx=4, ny=3, margin=0.2)
    ax.text(bx + Lb / 2, Wb / 2, "Slab B", ha="center", va="center",
            fontsize=9, color=_LABEL, fontweight="bold", zorder=5)

    _ext_dim_h(ax, 0, La, 0, -0.7, "A-L")
    _ext_dim_v(ax, 0, Wa, La + 0.15, La + 0.35, "A-W", fontsize=8)
    _ext_dim_h(ax, bx, bx + Lb, max(Wa, Wb), max(Wa, Wb) + 0.6, "B-L")
    _ext_dim_v(ax, 0, Wb, bx + Lb, bx + Lb + 0.7, "B-W")

    _axes_compass(ax, -0.9, -1.0)
    _title(ax, "DUAL SLAB -- PLAN VIEW")

    return _to_png(fig)


def _diag_collar() -> bytes:
    """Plan view of pipe collar -- L x W rectangle around pipe."""
    L, W = 5.0, 4.2
    pipe_r = 1.0

    fig, ax = _fig(7.0, 5.5)
    ax.set_xlim(-1.2, L + 1.8)
    ax.set_ylim(-1.2, W + 1.5)

    _rect(ax, 0, 0, L, W, fc=_CONCRETE, ec=_OUTLINE, lw=2.0)

    # Pipe
    pipe = mpatches.Circle((L / 2, W / 2), pipe_r, fc="white", ec=_OUTLINE, lw=1.5, zorder=3)
    ax.add_patch(pipe)
    ax.text(L / 2, W / 2, "pipe", ha="center", va="center", fontsize=7, color="#555", zorder=4)

    # Rebar mat (avoiding pipe area)
    for xi in [0.5, 1.2, 3.8, 4.5]:
        ax.plot([xi, xi], [0.2, W - 0.2], color=_REBAR, lw=0.9, zorder=4)
    for yi in [0.5, 1.2, 3.0, 3.7]:
        ax.plot([0.2, L - 0.2], [yi, yi], color=_REBAR, lw=0.9, zorder=4)

    _ext_dim_h(ax, 0, L, 0, -0.7, "L")
    _ext_dim_v(ax, 0, W, L, L + 0.7, "W")

    _axes_compass(ax, -0.9, -1.0)
    _title(ax, "CONCRETE PIPE COLLAR -- PLAN VIEW")

    return _to_png(fig)


def _diag_d84_wingwall() -> bytes:
    """
    D84 Wingwall -- elevation view.
    Tapered wall: H at box face (left), ~0.5ft at toe (right).
    Footing mat below. LOL = horizontal length.
    """
    LOL, H, H_toe = 7.0, 3.5, 0.5
    ftg_h, ftg_w = 0.5, LOL
    box_w = 0.6  # box culvert wall stub at left

    fig, ax = _fig(8.0, 5.5)
    ax.set_xlim(-1.5, LOL + box_w + 2.0)
    ax.set_ylim(-1.5, H + 1.5)

    # Box culvert wall stub (left)
    _rect(ax, -box_w, -ftg_h, box_w, H + ftg_h, fc="#b0b8c0", ec=_OUTLINE, lw=1.5, zorder=2)
    ax.text(-box_w / 2, H / 2, "BOX\nWALL", ha="center", va="center",
            fontsize=6, color="#444", zorder=4)

    # Wingwall profile (trapezoid: tall at left, short at right)
    pts = [(0, -ftg_h), (LOL, -ftg_h), (LOL, H_toe), (0, H)]
    poly = plt.Polygon(pts, closed=True, fc=_CONCRETE, ec=_OUTLINE, lw=2.0, zorder=2)
    ax.add_patch(poly)

    # Footing mat below (B1/B2)
    _rect(ax, -box_w * 0.5, -ftg_h * 2, LOL + box_w * 0.5, ftg_h,
          fc=_CONCRETE, ec=_OUTLINE, lw=1.5, zorder=2)
    # Footing rebar
    for xi in [0.4, 1.5, 3.0, 4.5, 6.0]:
        ax.plot([xi, xi], [-ftg_h * 2 + 0.08, -ftg_h - 0.08],
                color=_REBAR, lw=0.9, zorder=4)
    ax.plot([0.1, LOL - 0.1], [-ftg_h * 1.5, -ftg_h * 1.5],
            color=_REBAR, lw=0.9, zorder=4)

    # Face bars F1 / F2 (horizontal, front and rear face)
    for xi in [0.3, 1.2, 2.8, 4.5, 6.2]:
        h_here = H + (H_toe - H) * xi / LOL
        ax.plot([xi, xi], [-ftg_h + 0.1, h_here - 0.1],
                color=_REBAR, lw=1.0, zorder=4)

    # Longitudinal L bars (parallel to slope along top and mid)
    for frac in [0.15, 0.50, 0.82]:
        yi = H * frac
        ax.plot([0.1, LOL - 0.1], [yi, yi + (H_toe - H) * 1.0],
                color=_REBAR, lw=0.8, ls="--", zorder=4)

    # Top bars
    ax.plot([0.1, LOL - 0.1], [H - 0.15, H_toe + 0.1],
            color=_REBAR, lw=1.3, zorder=4)

    # Dims
    _ext_dim_h(ax, 0, LOL, -ftg_h * 2, -ftg_h * 2 - 0.6, "LOL")
    _ext_dim_v(ax, -ftg_h, H, 0, -0.85, "H", fontsize=10)

    _callout(ax, LOL * 0.55, H * 0.55, "F1/F2", "#4@12\"", angle=35, dist=1.1, fontsize=7)
    _callout(ax, LOL * 0.25, H * 0.42, "L1/L2", "Long bars", angle=145, dist=1.0, fontsize=7)
    _callout(ax, LOL * 0.4, -ftg_h * 1.5, "B1/B2", "Ftg mat", angle=270, dist=0.7, fontsize=7)

    _axes_compass(ax, -1.2, -1.3)
    _title(ax, "D84 WINGWALL (A/B/C) -- ELEVATION")

    return _to_png(fig)


def _diag_d85_wingwall() -> bytes:
    """
    D85 Wingwall -- elevation view (Type E shown with step at box junction).
    H at box face, stepped profile, n-bars @ 12", o-bars longitudinal, hoops.
    """
    LOL, H, H_step = 7.0, 3.5, 1.5
    step_x = 1.2  # step offset from box face
    ftg_h = 0.45
    box_w = 0.6

    fig, ax = _fig(8.0, 5.5)
    ax.set_xlim(-1.5, LOL + box_w + 2.2)
    ax.set_ylim(-1.5, H + 1.6)

    # Box culvert wall stub
    _rect(ax, -box_w, -ftg_h, box_w, H + ftg_h, fc="#b0b8c0", ec=_OUTLINE, lw=1.5, zorder=2)
    ax.text(-box_w / 2, H / 2, "BOX\nWALL", ha="center", va="center",
            fontsize=6, color="#444", zorder=4)

    # Stepped wall profile (Type E): step down from H at x=step_x
    # Lower section: H at box to H_step at step_x, then H_step out to toe
    pts = [
        (0, -ftg_h),
        (LOL, -ftg_h),
        (LOL, 0.4),
        (step_x, H_step),
        (step_x, H),
        (0, H),
    ]
    poly = plt.Polygon(pts, closed=True, fc=_CONCRETE, ec=_OUTLINE, lw=2.0, zorder=2)
    ax.add_patch(poly)

    # Footing
    _rect(ax, -box_w * 0.5, -ftg_h * 2.2, LOL + box_w * 0.5, ftg_h,
          fc=_CONCRETE, ec=_OUTLINE, lw=1.5, zorder=2)
    # Footing rebar B1/B2
    for xi in [0.5, 1.8, 3.2, 5.0, 6.4]:
        ax.plot([xi, xi], [-ftg_h * 2.2 + 0.08, -ftg_h - 0.08],
                color=_REBAR, lw=0.9, zorder=4)
    ax.plot([0.1, LOL - 0.1], [-ftg_h * 1.7, -ftg_h * 1.7],
            color=_REBAR, lw=0.9, zorder=4)

    # n-bars: face bars both faces
    for xi in [0.25, 0.9, 2.0, 3.5, 5.0, 6.5]:
        h_here = H if xi < step_x else H_step + (0.4 - H_step) * (xi - step_x) / (LOL - step_x)
        ax.plot([xi, xi], [-ftg_h + 0.1, h_here - 0.1],
                color=_REBAR, lw=1.0, zorder=4)

    # o-bars: longitudinal both faces (dashed)
    for frac in [0.15, 0.55, 0.85]:
        yi = H * frac
        # Only in tall section (left of step)
        ax.plot([0.1, step_x - 0.05], [yi, yi],
                color=_REBAR, lw=0.9, ls="--", zorder=4)

    # L bars: 2-#5 additional at step (shown as bold dashes at step_x)
    ax.plot([step_x - 0.15, step_x + 0.15], [H_step + 0.2, H_step + 0.2],
            color=_REBAR, lw=2.5, zorder=5)
    ax.plot([step_x - 0.15, step_x + 0.15], [H_step + 0.5, H_step + 0.5],
            color=_REBAR, lw=2.5, zorder=5)

    # Dims
    _ext_dim_h(ax, 0, LOL, -ftg_h * 2.2, -ftg_h * 2.2 - 0.6, "LOL")
    _ext_dim_v(ax, -ftg_h, H, 0, -0.9, "H", fontsize=10)
    _ext_dim_v(ax, -ftg_h, H_step, step_x + 0.1, step_x + 0.85, "H\u2082", fontsize=9)

    _callout(ax, 0.5, H * 0.5, "n1/n2", "#@12\" ea face", angle=145, dist=1.1, fontsize=7)
    _callout(ax, 0.3, H * 0.25, "o1/o2", "Long bars", angle=200, dist=1.0, fontsize=7)
    _callout(ax, step_x, H_step + 0.35, "L1", "2-#5 @ step", angle=45, dist=1.0, fontsize=7)
    _callout(ax, LOL * 0.5, -ftg_h * 1.7, "B1/B2", "Ftg mat", angle=270, dist=0.6, fontsize=7)

    _axes_compass(ax, -1.2, -1.3)
    _title(ax, "D85 WINGWALL (D/E) -- ELEVATION")

    return _to_png(fig)


def _diag_g_type_inlet(title: str, bar_note: str, has_extension: bool = False,
                        same_slope: bool = False) -> bytes:
    """
    Plan view of a G-type CIP drainage inlet (D72B).

    Box dimensions: L (variable, shown as L1) × W=2'-11¾" (fixed std width).
    Grate opening shown as inner rectangle.
    """
    L   = 4.0   # representative inlet length (ft)
    W   = 2.98  # 2'-11¾" = 35.75" ÷ 12 ≈ 2.98ft
    T   = 0.75  # 9" wall thickness in ft
    grate_w = 2.0   # grate opening width (Type 24 = 2ft clear)
    grate_l = L - 2 * T - 0.4  # grate opening length

    fig, ax = _fig(7.5, 5.5)
    ax.set_xlim(-1.3, L + 2.0)
    ax.set_ylim(-1.2, W + 1.8)

    # Outer box (plan)
    _rect(ax, 0, 0, L, W, fc=_CONCRETE, ec=_OUTLINE, lw=2.0)

    # Grate opening (inner void)
    grate_x = T + 0.2
    grate_y = (W - grate_w) / 2
    _rect(ax, grate_x, grate_y, grate_l, grate_w, fc="white", ec=_OUTLINE, lw=1.2, zorder=3)
    ax.text(grate_x + grate_l / 2, grate_y + grate_w / 2, "GRATE\nOPENING",
            ha="center", va="center", fontsize=7, color="#444", zorder=4)

    # Wall rebar lines (horizontal bars in L-direction)
    for yi in [T * 0.4, W - T * 0.4]:
        ax.plot([T + 0.1, L - T - 0.1], [yi, yi], color=_REBAR, lw=0.9, zorder=4)

    # Wall rebar lines (vertical bars in W-direction, short walls)
    for xi in [T * 0.4, L - T * 0.4]:
        ax.plot([xi, xi], [T + 0.1, W - T - 0.1], color=_REBAR, lw=0.9, zorder=4)

    # Extension indicator for G3
    if has_extension:
        ext_w = 0.4
        _rect(ax, L, 0, ext_w, W, fc="#c8d4dc", ec=_OUTLINE, lw=1.2, zorder=2)
        ax.text(L + ext_w / 2, W / 2, "EXT\n2ft", ha="center", va="center",
                fontsize=7, color="#555", zorder=4)

    # Same-slope note for G6
    if same_slope:
        ax.text(L / 2, W + 0.35, "SAME SLOPE AS GUTTER -- no depression",
                ha="center", va="bottom", fontsize=7, style="italic", color="#555")

    # Standard width label
    ax.text(L + 0.15, W / 2, f"W=2'-11¾\"\n(std)", ha="left", va="center",
            fontsize=7, color="#333")

    # Bar note
    ax.text(L / 2, -0.55, bar_note, ha="center", va="center",
            fontsize=7.5, color="#333",
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#bbb", alpha=0.9))

    _ext_dim_h(ax, 0, L, 0, -0.75, "L1")
    _ext_dim_v(ax, 0, W, L, L + 0.55, "W")

    _axes_compass(ax, -1.0, -1.0)
    _title(ax, title)

    return _to_png(fig)


def _diag_g1_inlet() -> bytes:
    """Plan view of G1 inlet -- matches Caltrans D72B plan.

    Portrait rectangle.  Interior shows grate with X-diagonal pattern.
    Fixed standard W = 2'-11 3/8" interior.  Variable L1 (= x_dim_ft).
    """
    T   = 0.75   # representative 9" wall (ft)
    IW  = 2.948  # fixed interior clear W = 2'-11 3/8"
    OW  = IW + 2 * T        # = 4.448 exterior W (fixed standard)
    OX  = 4.0    # representative exterior L1 (= default x_dim_ft)
    IX  = OX - 2 * T        # = 2.5 interior clear L1

    # Grate opening: Type 24 = 2'-0" wide, full IW height, centred in IX
    grate_w = 2.0
    grate_x = T + (IX - grate_w) / 2
    grate_y = T

    fig, ax = _fig(7.5, 7.5)
    ax.set_xlim(-2.2, OX + 4.0)
    ax.set_ylim(-2.0, OW + 2.0)

    # ---- Geometry ----
    _rect(ax, 0, 0, OX, OW, fc=_CONCRETE, ec=_OUTLINE, lw=2.0)       # outer body
    _rect(ax, T, T, IX, IW,  fc="white",   ec=_OUTLINE, lw=1.5,       # interior clear
          zorder=3)

    # Grate frame (solid rectangle inside interior clear)
    ax.add_patch(mpatches.Rectangle(
        (grate_x, grate_y), grate_w, IW,
        linewidth=1.3, edgecolor=_OUTLINE, facecolor="none", zorder=4))
    # X diagonal lines (matches official Caltrans hatching style)
    ax.plot([grate_x, grate_x + grate_w], [grate_y, grate_y + IW],
            color=_DIM, lw=0.9, zorder=5)
    ax.plot([grate_x, grate_x + grate_w], [grate_y + IW, grate_y],
            color=_DIM, lw=0.9, zorder=5)
    ax.text(grate_x + grate_w / 2, grate_y + IW / 2, "GRATE\nTYPE 24",
            ha="center", va="center", fontsize=7.5, color="#333", zorder=6,
            bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="none", alpha=0.88))

    # ---- Dimension lines ----
    # X: exterior L1 (top, live)
    _ext_dim_h(ax, 0, OX, OW, OW + 0.8, "X")

    # T: bottom corners (live)
    _ext_dim_h(ax, 0, T, 0, -0.60, "T", fontsize=8)
    _ext_dim_h(ax, OX - T, OX, 0, -0.60, "T", fontsize=8)

    # Right side: T arrows top + bottom, then 2'-11 3/8" interior W (static)
    tr_x = OX + 0.35
    for y0, y1 in [(OW - T, OW), (0, T)]:
        ax.annotate("", xy=(tr_x, y1), xytext=(tr_x, y0),
                    arrowprops=dict(arrowstyle="<->", color=_DIM,
                                    lw=0.8, mutation_scale=7))
        ax.text(tr_x + 0.12, (y0 + y1) / 2, _aug_label("T"),
                ha="left", va="center", fontsize=8,
                color=_LABEL, fontweight="bold")
    # 2'-11 3/8" standard interior W
    ax.annotate("", xy=(tr_x, T + IW), xytext=(tr_x, T),
                arrowprops=dict(arrowstyle="<->", color=_DIM,
                                lw=1.0, mutation_scale=9))
    ax.text(tr_x + 0.12, T + IW / 2, "2\u2019-11\u215b\u201d\n(std)",
            ha="left", va="center", fontsize=8, color=_LABEL, fontweight="bold")

    # Inside X: interior clear L1 (live)
    _dim_h(ax, T, T + IX, grate_y + IW * 0.10, "Inside X", gap=0.14, fontsize=8)

    _axes_compass(ax, -1.8, -1.7)
    _title(ax, "G1 INLET -- PLAN VIEW (D72B)")

    return _to_png(fig)


def _diag_g3_inlet() -> bytes:
    return _diag_g_type_inlet(
        "G3 INLET -- PLAN VIEW (D72B)",
        "#4 ALL AROUND, EXTEND WALL, TOP 2'-0\" MIN",
        has_extension=True,
    )


def _diag_g4_inlet() -> bytes:
    return _diag_g_type_inlet(
        "G4 INLET -- PLAN VIEW (D72B)",
        "#5 ALL AROUND, TOP 2'-0\" MIN (concrete curb)",
    )


def _diag_g5_inlet() -> bytes:
    return _diag_g_type_inlet(
        "G5 INLET -- PLAN VIEW (D72B)",
        "#5 ALL AROUND (detail A profile)",
    )


def _diag_g6_inlet() -> bytes:
    return _diag_g_type_inlet(
        "G6 INLET -- PLAN VIEW (D72B)",
        "#4 ALL AROUND, TOP 2'-0\" MIN",
        same_slope=True,
    )


# ==============================================================================
# Registry
# ==============================================================================

_DIAGRAM_FN: dict[str, callable] = {
    "G1 Inlet":                _diag_g1_inlet,
    "G2 Inlet":                _diag_g2_inlet,
    "G3 Inlet":                _diag_g3_inlet,
    "G4 Inlet":                _diag_g4_inlet,
    "G5 Inlet":                _diag_g5_inlet,
    "G6 Inlet":                _diag_g6_inlet,
    "G2 Expanded Inlet":       _diag_expanded_inlet,
    "G2 Inlet Top":            _diag_inlet_top,
    "G2 Expanded Inlet Top":   _diag_expanded_inlet_top,
    "Straight Headwall":       _diag_headwall,
    "Wing Wall":               _diag_wing_wall,
    "Spread Footing":          _diag_footing,
    "Box Culvert":             _diag_box_culvert,
    "Retaining Wall":          _diag_retaining_wall,
    "Caltrans Retaining Wall": _diag_caltrans_retaining_wall,
    "Sound Wall":              _diag_sound_wall,
    "Flat Slab":               lambda: _diag_rect_plan("FLAT SLAB -- PLAN VIEW"),
    "Drilled Shaft Cage":      _diag_cage,
    "Concrete Pipe Collar":    _diag_collar,
    "Slab on Grade":           lambda: _diag_rect_plan_with_T("SLAB ON GRADE -- PLAN VIEW"),
    "Equipment Pad":           lambda: _diag_rect_plan_with_T("EQUIPMENT PAD -- PLAN VIEW"),
    "Switchboard Pad":         lambda: _diag_rect_plan_with_T("SWITCHBOARD PAD -- PLAN VIEW"),
    "Seatwall":                lambda: _diag_wall_section("SEATWALL -- CROSS SECTION", hw=1.5, ww=1.2),
    "Concrete Header":         lambda: _diag_wall_section("CONCRETE HEADER -- CROSS SECTION", hw=2.0, ww=1.0),
    "Pipe Encasement":         _diag_pipe_encasement,
    "Fuel Foundation":         lambda: _diag_rect_plan_with_T("FUEL FOUNDATION -- PLAN VIEW"),
    "Dual Slab":               _diag_dual_slab,
    "Junction Structure":      _diag_junction,
    "D84 Wingwall":            _diag_d84_wingwall,
    "D85 Wingwall":            _diag_d85_wingwall,
}


def get_diagram(template_name: str) -> bytes | None:
    """Return PNG bytes for the given template, or None if not found."""
    fn = _DIAGRAM_FN.get(template_name)
    return fn() if fn else None


# -- Field-to-label mappings for live annotation -------------------------------
# Maps template_name → {field_name: exact label string used in diagram helpers}
_FIELD_LABELS: dict[str, dict[str, str]] = {
    "G1 Inlet":              {"x_dim_ft": "X", "wall_thick_in": "T",
                              "_inside_x_ft": "Inside X"},
    "G2 Inlet":              {"x_dim_ft": "X", "wall_thick_in": "T", "_y_ext_ft": "Y"},
    "G3 Inlet":              {"x_dim_ft": "L1"},
    "G4 Inlet":              {"x_dim_ft": "L1"},
    "G5 Inlet":              {"x_dim_ft": "L1"},
    "G6 Inlet":              {"x_dim_ft": "L1"},
    "G2 Expanded Inlet":     {"x_dim_ft": "X", "y_dim_ft": "Y",
                              "y_expanded_ft": "Y exp", "wall_thick_in": "T",
                              "_inside_x_ft": "Inside X", "_inside_y_ft": "Inside Y"},
    "G2 Inlet Top":          {"x_dim_ft": "X", "y_dim_ft": "Y",
                              "wall_height_ft": "H"},
    "G2 Expanded Inlet Top": {"x_dim_ft": "X", "y_dim_ft": "Y",
                              "wall_height_ft": "H"},
    "Straight Headwall":     {"wall_width_ft": "W", "wall_height_ft": "H", "h1_ft": "H1"},
    "Wing Wall":             {"wing_length_ft": "L",
                              "hw_height_ft": "H\u2081",
                              "tip_height_ft": "H\u2082"},
    "Spread Footing":        {"footing_length_ft": "L", "footing_width_ft": "W",
                              "footing_depth_in": "D"},
    "Box Culvert":           {"clear_span_ft": "S", "clear_rise_ft": "R",
                              "wall_thick_in": "T"},
    "Retaining Wall":        {"wall_length_ft": "L", "stem_height_ft": "H"},
    "Caltrans Retaining Wall": {"design_h_ft": "H\n(design)"},
    "Sound Wall":            {"wall_height_ft": "H", "wall_length_ft": "L"},
    "Flat Slab":             {"slab_length_ft": "L", "slab_width_ft": "W"},
    "Drilled Shaft Cage":    {"hole_diameter_ft": "\u03c6",
                              "cage_depth_ft": "D (depth)"},
    "Concrete Pipe Collar":  {"collar_length_ft": "L", "collar_width_ft": "W"},
    "Slab on Grade":         {"slab_length_ft": "L", "slab_width_ft": "W",
                              "slab_thickness_in": "T"},
    "Equipment Pad":         {"pad_length_ft": "L", "pad_width_ft": "W",
                              "pad_thickness_in": "T"},
    "Switchboard Pad":       {"pad_length_ft": "L", "pad_width_ft": "W",
                              "pad_thickness_in": "T"},
    "Seatwall":              {"wall_height_in": "H", "wall_width_in": "W"},
    "Concrete Header":       {"header_height_in": "H", "header_width_in": "W"},
    "Pipe Encasement":       {"encasement_width_in": "W",
                              "encasement_height_in": "H",
                              "encasement_length_ft": "L"},
    "Fuel Foundation":       {"fdn_length_ft": "L", "fdn_width_ft": "W",
                              "fdn_thickness_in": "T"},
    "Dual Slab":             {"slab_a_length_ft": "A-L", "slab_a_width_ft": "A-W",
                              "slab_b_length_ft": "B-L", "slab_b_width_ft": "B-W"},
    "Junction Structure":    {"inside_length_ft": "L (inside)",
                              "inside_width_ft": "W (inside)"},
    "D84 Wingwall":          {"wall_length_ft": "LOL", "wall_height_ft": "H"},
    "D85 Wingwall":          {"wall_length_ft": "LOL", "wall_height_ft": "H"},
}


def get_diagram_live(template_name: str, params_dict: dict | None) -> bytes | None:
    """
    Return PNG bytes with dimension labels annotated with actual input values.

    Uses the module-level _DIM_VALUES context so all _dim_h / _dim_v / _callout
    calls inside the diagram function automatically pick up the values.
    Thread safety: acceptable for a single-user local Streamlit app.
    """
    global _DIM_VALUES, _LIVE_PARAMS
    if not params_dict:
        return get_diagram(template_name)

    field_map = _FIELD_LABELS.get(template_name, {})
    dim_vals: dict[str, str] = {}
    for field_name, label in field_map.items():
        val = params_dict.get(field_name)
        if val is not None:
            try:
                dim_vals[label] = _fmt_dim_value(field_name, float(val))
            except (ValueError, TypeError):
                pass


    _DIM_VALUES  = dim_vals
    _LIVE_PARAMS = dict(params_dict)
    try:
        fn = _DIAGRAM_FN.get(template_name)
        return fn() if fn else None
    finally:
        _DIM_VALUES  = {}
        _LIVE_PARAMS = {}
