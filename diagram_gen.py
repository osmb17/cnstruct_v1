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
    dx = dist * math.cos(math.radians(angle))
    dy = dist * math.sin(math.radians(angle))
    ax.annotate(
        f"{label} = {text}",
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
    ax.text(OX + 1.35, T + IY * 0.30, "2'-11 3/8\" min",
            ha="left", va="center", fontsize=6.5, color=_DIM)

    # -- Inside X dimension (bottom) --
    _ext_dim_h(ax, T, T + IX, 0, -1.3, "Inside X Dimension", fontsize=8)
    ax.text(T + IX / 2, -1.7, "2'-11 3/8\" min  OR\nPipe penetration dia + 3\" min (90\" max)",
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
    """Plan view of G2 expanded inlet -- X, Y, Y_exp, T."""
    OX, OY_narrow = 6.0, 3.0
    OY_exp = 5.5
    T = 0.45

    fig, ax = _fig(9.0, 7.5)
    ax.set_xlim(-2.0, OX + 2.5)
    ax.set_ylim(-1.5, OY_exp + 1.8)

    # Lower narrow section
    _rect(ax, 0, 0, OX, OY_narrow, fc=_CONCRETE, ec=_OUTLINE, lw=2.0)
    _rect(ax, T, T, OX - 2 * T, OY_narrow - T, fc="white", ec=_OUTLINE, lw=1.0)

    # Upper expanded section
    exp_w = OX + 1.5
    exp_x = (OX - exp_w) / 2
    _rect(ax, exp_x, OY_narrow, exp_w, OY_exp - OY_narrow,
          fc=_CONCRETE, ec=_OUTLINE, lw=2.0)
    _rect(ax, exp_x + T, OY_narrow, exp_w - 2 * T, OY_exp - OY_narrow - T,
          fc="white", ec=_OUTLINE, lw=1.0)

    # Taper lines
    ax.plot([0, exp_x], [OY_narrow, OY_narrow], color=_OUTLINE, lw=1.5)
    ax.plot([OX, exp_x + exp_w], [OY_narrow, OY_narrow], color=_OUTLINE, lw=1.5)

    # X dimension
    _ext_dim_h(ax, 0, OX, OY_exp, OY_exp + 0.7, "X")
    # Y dimension (narrow)
    _ext_dim_v(ax, 0, OY_narrow, 0, -0.8, "Y")
    # Y_exp dimension
    _ext_dim_v(ax, 0, OY_exp, exp_x, exp_x - 0.9, "Y_exp", fontsize=8)
    # T callout
    _callout(ax, T / 2, OY_narrow / 2, "T", "wall thick", angle=135, dist=0.7, fontsize=7)

    _axes_compass(ax, -1.5, -1.2)
    _title(ax, "G2 EXPANDED INLET -- PLAN VIEW")

    return _to_png(fig)


def _diag_inlet_top() -> bytes:
    """Plan view of inlet top slab -- X, Y, T."""
    X, Y = 6.0, 5.0
    T = 0.45

    fig, ax = _fig(7.5, 6.5)
    ax.set_xlim(-1.8, X + 2.0)
    ax.set_ylim(-1.5, Y + 1.5)

    # Slab
    _rect(ax, 0, 0, X, Y, fc=_CONCRETE, ec=_OUTLINE, lw=2.0)
    _rebar_grid(ax, 0, 0, X, Y, nx=6, ny=5, margin=0.25)

    # Opening/grate in center
    gw, gh = X * 0.35, Y * 0.30
    gx, gy = (X - gw) / 2, (Y - gh) / 2
    _rect(ax, gx, gy, gw, gh, fc="white", ec=_OUTLINE, lw=1.2, zorder=3)
    ax.text(X / 2, Y / 2, "grate\nopening", ha="center", va="center",
            fontsize=7, color="#666", zorder=4)

    _ext_dim_h(ax, 0, X, Y, Y + 0.7, "X")
    _ext_dim_v(ax, 0, Y, 0, -0.8, "Y")
    _callout(ax, X * 0.9, Y * 0.1, "T", "slab thick", angle=30, dist=0.7, fontsize=7)

    _axes_compass(ax, -1.3, -1.2)
    _title(ax, "G2 INLET TOP -- PLAN VIEW")

    return _to_png(fig)


def _diag_headwall() -> bytes:
    """Front elevation of straight headwall -- W wide x H tall."""
    W, H = 6.0, 4.0

    fig, ax = _fig(7.0, 6.0)
    ax.set_xlim(-1.5, W + 2.0)
    ax.set_ylim(-1.2, H + 1.5)

    _rect(ax, 0, 0, W, H, fc=_CONCRETE, ec=_OUTLINE, lw=2.0)

    # Rebar hints
    for xi in [0.3, 0.6, W - 0.6, W - 0.3]:
        ax.plot([xi, xi], [0.3, H - 0.3], color=_REBAR, lw=1.0, zorder=4)
    for yi in [0.5, 1.2, 2.0, 2.8, 3.5]:
        ax.plot([0.1, W - 0.1], [yi, yi], color=_REBAR, lw=0.8, zorder=4)

    # Pipe opening
    circ = mpatches.Circle((W / 2, H * 0.38), 0.55,
                            fc="white", ec=_OUTLINE, lw=1.5, zorder=3)
    ax.add_patch(circ)
    ax.text(W / 2, H * 0.38, "pipe\nopening", ha="center", va="center",
            fontsize=6.5, color="#666", zorder=4)

    # Dimensions
    _ext_dim_h(ax, 0, W, 0, -0.7, "W")
    _ext_dim_v(ax, 0, H, W, W + 0.7, "H")

    # T callout
    ax.annotate("T (thickness)", xy=(0, H / 2), xytext=(-1.0, H / 2),
                fontsize=8, color=_LABEL, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=_DIM, lw=0.8),
                ha="right", va="center",
                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=_DIM, lw=0.6))

    _axes_compass(ax, -1.2, -1.0)
    _title(ax, "STRAIGHT HEADWALL -- FRONT ELEVATION")

    return _to_png(fig)


def _diag_caltrans_headwall() -> bytes:
    """Front elevation of Caltrans headwall -- pipe D, wall W."""
    W, H = 6.0, 4.5
    pipe_d_ratio = 0.45

    fig, ax = _fig(7.5, 6.5)
    ax.set_xlim(-1.5, W + 2.0)
    ax.set_ylim(-1.5, H + 1.5)

    # Trapezoidal headwall shape (wider at base)
    taper = 0.4
    pts = [(taper, 0), (W - taper, 0), (W, H), (0, H)]
    poly = plt.Polygon(pts, closed=True, fc=_CONCRETE, ec=_OUTLINE, lw=2.0, zorder=2)
    ax.add_patch(poly)

    # Pipe opening
    pipe_r = H * pipe_d_ratio / 2
    cx, cy = W / 2, H * 0.42
    circ = mpatches.Circle((cx, cy), pipe_r, fc="white", ec=_OUTLINE, lw=2.0, zorder=3)
    ax.add_patch(circ)
    ax.text(cx, cy, "pipe", ha="center", va="center", fontsize=7, color="#555", zorder=4)

    # Pipe diameter dimension
    ax.annotate("", xy=(cx + pipe_r, cy), xytext=(cx - pipe_r, cy),
                arrowprops=dict(arrowstyle="<->", color=_DIM, lw=1.0, mutation_scale=9))
    ax.text(cx, cy - pipe_r - 0.25, "D", ha="center", va="top", fontsize=10,
            color=_LABEL, fontweight="bold")

    # Rebar hints
    for xi in [0.5, 1.0, W - 1.0, W - 0.5]:
        h_at = H * (1 - abs(xi - W / 2) / (W / 2) * taper / W)
        ax.plot([xi, xi], [0.3, h_at - 0.3], color=_REBAR, lw=0.9, zorder=4)

    _ext_dim_h(ax, 0, W, H, H + 0.7, "W")
    _ext_dim_v(ax, 0, H, W, W + 0.7, "H")

    _axes_compass(ax, -1.2, -1.2)
    _title(ax, "CALTRANS HEADWALL -- FRONT ELEVATION")

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
    """Cross-section of box culvert -- clear span S, clear rise R, barrel B."""
    S, R, T = 5.0, 3.5, 0.45
    total_w = S + 2 * T
    total_h = R + 2 * T

    fig, ax = _fig(7.5, 6.0)
    ax.set_xlim(-1.5, total_w + 2.0)
    ax.set_ylim(-1.5, total_h + 1.5)

    # Outer section
    _rect(ax, 0, 0, total_w, total_h, fc=_CONCRETE, ec=_OUTLINE, lw=2.0)
    # Inner void
    _rect(ax, T, T, S, R, fc="white", ec=_OUTLINE, lw=1.2)

    # Rebar in walls
    for offset in [0.12, 0.30]:
        ax.plot([offset, offset], [T + 0.15, T + R - 0.15],
                color=_REBAR, lw=1.0, zorder=4)
        ax.plot([total_w - offset, total_w - offset], [T + 0.15, T + R - 0.15],
                color=_REBAR, lw=1.0, zorder=4)
    # Rebar in top/bottom slabs
    for offset in [0.12, 0.30]:
        ax.plot([T + 0.1, T + S - 0.1], [offset, offset],
                color=_REBAR, lw=0.8, zorder=4)
        ax.plot([T + 0.1, T + S - 0.1], [total_h - offset, total_h - offset],
                color=_REBAR, lw=0.8, zorder=4)

    # Clear span / rise inside
    _dim_h(ax, T, T + S, T + R * 0.5, "S", gap=-0.35, fontsize=10)
    _dim_v(ax, T, T + R, T + S * 0.82, "R", gap=0.15, fontsize=10)

    # Barrel label
    ax.text(total_w / 2, total_h / 2, "B \u2192\nBarrel Length",
            ha="center", va="center", fontsize=7, color="#666",
            bbox=dict(boxstyle="round", fc="white", ec="#ccc", alpha=0.85), zorder=5)

    # T callout
    _callout(ax, T / 2, T / 2, "T", "wall thick", angle=225, dist=0.7, fontsize=7)

    _axes_compass(ax, -1.2, -1.2)
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
    ax.text(cx, cy + r + 0.25, "\u03c6", ha="center", va="bottom", fontsize=12,
            color=_LABEL, fontweight="bold")

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


# ==============================================================================
# Registry
# ==============================================================================

_DIAGRAM_FN: dict[str, callable] = {
    "G2 Inlet":                _diag_g2_inlet,
    "G2 Expanded Inlet":       _diag_expanded_inlet,
    "G2 Inlet Top":            _diag_inlet_top,
    "G2 Expanded Inlet Top":   lambda: _diag_rect_plan("G2 EXPANDED INLET TOP -- PLAN VIEW"),
    "Straight Headwall":       _diag_headwall,
    "Caltrans Headwall":       _diag_caltrans_headwall,
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
}


def get_diagram(template_name: str) -> bytes | None:
    """Return PNG bytes for the given template, or None if not found."""
    fn = _DIAGRAM_FN.get(template_name)
    return fn() if fn else None
