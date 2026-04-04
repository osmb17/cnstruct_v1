"""
diagram_gen.py — Engineering schematic diagrams for each template.
Returns PNG bytes for display via st.image().
"""

from __future__ import annotations

import io
import math

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

# ── Style constants ───────────────────────────────────────────────────────────
_CONCRETE = "#cdd4db"
_REBAR    = "#8b4513"
_OUTLINE  = "#1c3461"
_DIM      = "#444444"
_LABEL    = "#1c3461"
_BG       = "white"
_HATCH    = "////"


# ── Drawing helpers ───────────────────────────────────────────────────────────

def _fig(w=5.5, h=4.0):
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


def _dim_h(ax, x1, x2, y, label, gap=0.18, fontsize=9):
    """Horizontal dimension: double-headed arrow + label above."""
    ax.annotate("", xy=(x2, y), xytext=(x1, y),
                arrowprops=dict(arrowstyle="<->", color=_DIM, lw=1.0, mutation_scale=9))
    mid = (x1 + x2) / 2
    ax.text(mid, y + gap, label, ha="center", va="bottom", fontsize=fontsize,
            color=_LABEL, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.9))


def _dim_v(ax, y1, y2, x, label, gap=0.18, fontsize=9):
    """Vertical dimension: double-headed arrow + label to right."""
    ax.annotate("", xy=(x, y2), xytext=(x, y1),
                arrowprops=dict(arrowstyle="<->", color=_DIM, lw=1.0, mutation_scale=9))
    mid = (y1 + y2) / 2
    ax.text(x + gap, mid, label, ha="left", va="center", fontsize=fontsize,
            color=_LABEL, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.9))


def _callout(ax, x, y, label, text, angle=45, dist=0.5, fontsize=8):
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


def _title(ax, text, x=0.5, y=0.97):
    ax.text(x, y, text, transform=ax.transAxes, ha="center", va="top",
            fontsize=9, color="#555", style="italic")


def _to_png(fig) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight", facecolor=_BG)
    plt.close(fig)
    buf.seek(0)
    return buf.read()


# ── Individual diagram functions ──────────────────────────────────────────────

def _diag_g2_inlet() -> bytes:
    """Plan view of G2 inlet box — X (width) × Y (depth), T wall thickness."""
    X, Y, T = 5.5, 4.5, 0.9   # proportional, not real units

    fig, ax = _fig(6, 5)
    ax.set_xlim(-1.2, X + 1.5)
    ax.set_ylim(-0.9, Y + 1.1)

    # Outer concrete box
    _rect(ax, 0, 0, X, Y, fc=_CONCRETE)
    # Inner void
    _rect(ax, T, T, X - 2*T, Y - 2*T, fc="white", ec=_OUTLINE, lw=1.0)

    # Grate opening indication (top of interior)
    grate_w = (X - 2*T) * 0.45
    gx = T + (X - 2*T - grate_w) / 2
    _rect(ax, gx, T + (Y - 2*T)*0.65, grate_w, (Y - 2*T)*0.3,
          fc="#aab8c2", ec=_OUTLINE, lw=0.8, hatch="----")

    # Rebar hint lines
    for i in [0.5, 1.5]:
        ax.plot([T*0.3, T*0.7], [Y*i/3, Y*i/3], color=_REBAR, lw=1.2, zorder=4)

    # Dimension arrows
    _dim_h(ax, 0, X, -0.55, "X")
    _dim_v(ax, 0, Y, X + 0.45, "Y")

    # T callout (wall thickness)
    _callout(ax, T/2, Y/2, "T", "auto", angle=200, dist=0.7)

    ax.text(X/2, Y/2 - 0.3, "Interior", ha="center", va="center",
            fontsize=7, color="#888", style="italic")

    _title(ax, "G2 Inlet — Plan View")
    return _to_png(fig)


def _diag_headwall() -> bytes:
    """Front elevation of headwall — W wide × H tall."""
    W, H, T = 6.0, 4.0, 0.4

    fig, ax = _fig(6, 5)
    ax.set_xlim(-1.0, W + 1.5)
    ax.set_ylim(-0.8, H + 1.0)

    # Wall body
    _rect(ax, 0, 0, W, H, fc=_CONCRETE)

    # Rebar hint (vertical bars)
    for xi in [0.3, 0.6, W-0.6, W-0.3]:
        ax.plot([xi, xi], [0.3, H-0.3], color=_REBAR, lw=1.0, zorder=4)

    # Rebar hint (horizontal bars)
    for yi in [0.5, 1.2, 2.0, 2.8, 3.5]:
        ax.plot([0.1, W-0.1], [yi, yi], color=_REBAR, lw=0.8, zorder=4)

    # Pipe opening circle (center)
    circ = mpatches.Circle((W/2, H*0.38), 0.55, fc="white", ec=_OUTLINE, lw=1.2, zorder=3)
    ax.add_patch(circ)
    ax.text(W/2, H*0.38, "pipe\nopening", ha="center", va="center", fontsize=6.5, color="#666")

    # Dimension arrows
    _dim_h(ax, 0, W, -0.5, "W")
    _dim_v(ax, 0, H, W + 0.45, "H")

    # T callout (thickness, shown as depth on edge)
    ax.annotate("T (thickness)", xy=(0, H/2), xytext=(-0.85, H/2),
                fontsize=8, color=_LABEL, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=_DIM, lw=0.8),
                ha="right", va="center",
                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=_DIM, lw=0.6))

    _title(ax, "Straight Headwall — Front Elevation")
    return _to_png(fig)


def _diag_footing() -> bytes:
    """Plan view of spread footing — L × W, with D depth callout."""
    L, W = 6.0, 4.5

    fig, ax = _fig(6, 5)
    ax.set_xlim(-0.8, L + 1.5)
    ax.set_ylim(-1.0, W + 1.0)

    _rect(ax, 0, 0, L, W, fc=_CONCRETE)

    # Mat grid lines
    for xi in [1.0, 2.0, 3.0, 4.0, 5.0]:
        if xi < L:
            ax.plot([xi, xi], [0.2, W-0.2], color=_REBAR, lw=0.9, zorder=4)
    for yi in [0.9, 1.8, 2.7, 3.6]:
        if yi < W:
            ax.plot([0.2, L-0.2], [yi, yi], color=_REBAR, lw=0.9, zorder=4)

    # Column stub
    col_w = L * 0.15
    cx = (L - col_w) / 2
    _rect(ax, cx, (W-col_w)/2, col_w, col_w, fc="#9aa8b0", ec=_OUTLINE, lw=1.2, zorder=3)
    ax.text(L/2, W/2, "col.", ha="center", va="center", fontsize=7, color="#555")

    _dim_h(ax, 0, L, -0.6, "L")
    _dim_v(ax, 0, W, L + 0.45, "W")
    _callout(ax, L*0.85, W*0.15, "D", "depth", angle=30, dist=0.8)

    _title(ax, "Spread Footing — Plan View")
    return _to_png(fig)


def _diag_box_culvert() -> bytes:
    """Cross-section of box culvert — clear span S × clear rise R, barrel B."""
    S, R, T = 5.0, 3.5, 0.45

    fig, ax = _fig(6, 5)
    ax.set_xlim(-1.0, S + 2*T + 1.5)
    ax.set_ylim(-1.0, R + 2*T + 1.0)

    # Full outer section
    _rect(ax, 0, 0, S + 2*T, R + 2*T, fc=_CONCRETE)
    # Interior void
    _rect(ax, T, T, S, R, fc="white", ec=_OUTLINE, lw=1.0)

    # Rebar in walls
    for yi in [0.25, 0.45]:
        ax.plot([yi, yi], [T+0.2, T+R-0.2], color=_REBAR, lw=1.0, zorder=4)
        ax.plot([S+2*T-yi, S+2*T-yi], [T+0.2, T+R-0.2], color=_REBAR, lw=1.0, zorder=4)
    for xi in [0.2, 0.4]:
        ax.plot([T+0.1, T+S-0.1], [yi_s := R+2*T-xi, yi_s], color=_REBAR, lw=0.8, zorder=4)
        ax.plot([T+0.1, T+S-0.1], [xi, xi], color=_REBAR, lw=0.8, zorder=4)

    # Clear span arrow inside
    _dim_h(ax, T, T+S, T + R*0.5, "S (clear span)", gap=-0.3, fontsize=8)
    # Clear rise arrow inside
    _dim_v(ax, T, T+R, T + S*0.85, "R (clear rise)", gap=0.12, fontsize=8)
    # Barrel arrow (out of plane indicator)
    ax.text(S/2 + T, R/2 + T, "B →\nBarrel\nLength",
            ha="center", va="center", fontsize=7, color="#666",
            bbox=dict(boxstyle="round", fc="white", ec="#ccc", alpha=0.85))
    # T callout
    _callout(ax, T/2, T/2, "T", "wall thick", angle=225, dist=0.7, fontsize=7)

    _title(ax, "Box Culvert — Cross Section")
    return _to_png(fig)


def _diag_retaining_wall() -> bytes:
    """Cross-section of cantilever retaining wall — H stem, L footing, D depth."""
    H, L, D, T = 5.0, 4.5, 0.5, 0.4
    stem_x = 1.2  # x position of stem

    fig, ax = _fig(6, 5.5)
    ax.set_xlim(-1.0, L + 1.5)
    ax.set_ylim(-0.9, H + D + 0.8)

    # Footing
    _rect(ax, 0, 0, L, D, fc=_CONCRETE)
    # Stem
    _rect(ax, stem_x, D, T, H, fc=_CONCRETE)

    # Soil fill hint
    _rect(ax, stem_x + T, D, L - stem_x - T - 0.05, H*0.7,
          fc="#d4c4a8", ec="#c4b498", lw=0.6, hatch="....", zorder=1)
    ax.text(stem_x + T + (L - stem_x - T)*0.5, D + H*0.35, "soil",
            ha="center", fontsize=7, color="#8b7355", style="italic")

    # Rebar (vertical in stem)
    for xi in [stem_x + 0.08, stem_x + T - 0.08]:
        ax.plot([xi, xi], [D + 0.1, D + H - 0.1], color=_REBAR, lw=1.2, zorder=4)
    # Rebar (horizontal in footing)
    for yi in [D*0.25, D*0.75]:
        ax.plot([0.1, L-0.1], [yi, yi], color=_REBAR, lw=1.0, zorder=4)

    _dim_v(ax, D, D + H, L + 0.5, "H")
    _dim_h(ax, 0, L, -0.55, "L")
    _callout(ax, L*0.5, D*0.5, "D", "footing depth", angle=0, dist=0.8)

    _title(ax, "Retaining Wall — Cross Section")
    return _to_png(fig)


def _diag_cage() -> bytes:
    """Elevation + plan view of drilled shaft cage — φ diameter, D depth."""
    D_depth = 5.0
    phi = 1.5
    n_rings = 5

    fig, ax = _fig(6.5, 5)
    ax.set_xlim(-0.8, D_depth + 3.0)
    ax.set_ylim(-0.8, phi*1.6 + 0.8)

    # Elevation view (left side — horizontal = depth direction)
    cage_top = phi * 1.2
    cage_bot = 0.2

    ax.plot([0, D_depth], [cage_top, cage_top], color=_OUTLINE, lw=1.5)
    ax.plot([0, D_depth], [cage_bot, cage_bot], color=_OUTLINE, lw=1.5)
    ax.plot([0, 0], [cage_bot, cage_top], color=_OUTLINE, lw=1.5)
    # Open bottom
    ax.plot([D_depth, D_depth], [cage_bot, cage_top], color=_OUTLINE, lw=1.0, ls="--")

    # Hoops (rings shown as vertical ticks)
    ring_gap = D_depth / n_rings
    for i in range(n_rings + 1):
        xr = i * ring_gap
        ax.plot([xr, xr], [cage_bot, cage_top], color=_REBAR, lw=1.4, zorder=4)

    # Vertical bars (longitudinals)
    for yi in [cage_bot + 0.1, cage_top - 0.1]:
        ax.plot([0, D_depth], [yi, yi], color=_REBAR, lw=0.9, ls="--", zorder=4)

    # Plan view circle (far right)
    cx, cy = D_depth + 1.8, (cage_top + cage_bot) / 2
    r = (cage_top - cage_bot) / 2
    circ_outer = mpatches.Circle((cx, cy), r, fc=_CONCRETE, ec=_OUTLINE, lw=1.5, zorder=2)
    circ_inner = mpatches.Circle((cx, cy), r*0.75, fc="white", ec=_OUTLINE, lw=0.8, zorder=3)
    ax.add_patch(circ_outer)
    ax.add_patch(circ_inner)

    # Vert bars as dots on circle
    n_v = 8
    for i in range(n_v):
        ang = 2 * math.pi * i / n_v
        bx = cx + r*0.88 * math.cos(ang)
        by = cy + r*0.88 * math.sin(ang)
        ax.plot(bx, by, "o", color=_REBAR, ms=4, zorder=5)

    # Diameter arrow on plan
    ax.annotate("", xy=(cx + r, cy), xytext=(cx - r, cy),
                arrowprops=dict(arrowstyle="<->", color=_DIM, lw=0.9, mutation_scale=8))
    ax.text(cx, cy + r + 0.2, "φ", ha="center", va="bottom", fontsize=11,
            color=_LABEL, fontweight="bold")

    # Depth dimension
    _dim_h(ax, 0, D_depth, cage_bot - 0.5, "D (depth)")

    ax.text(D_depth/2, (cage_top+cage_bot)/2, "elevation", ha="center",
            fontsize=7, color="#888", style="italic", va="center")
    ax.text(cx, cy, "plan", ha="center", va="center",
            fontsize=7, color="#888", style="italic")

    _title(ax, "Drilled Shaft Cage — Elevation + Plan")
    return _to_png(fig)


def _diag_rect_plan(title="Flat Slab — Plan View") -> bytes:
    """Generic plan-view rectangle with L × W labels."""
    L, W = 6.0, 4.0

    fig, ax = _fig(6, 5)
    ax.set_xlim(-0.8, L + 1.5)
    ax.set_ylim(-0.8, W + 1.0)

    _rect(ax, 0, 0, L, W, fc=_CONCRETE)

    # Mat grid
    for xi in [1.2, 2.4, 3.6, 4.8]:
        if xi < L:
            ax.plot([xi, xi], [0.2, W-0.2], color=_REBAR, lw=0.9, zorder=4)
    for yi in [0.8, 1.6, 2.4, 3.2]:
        if yi < W:
            ax.plot([0.2, L-0.2], [yi, yi], color=_REBAR, lw=0.9, zorder=4)

    _dim_h(ax, 0, L, -0.5, "L")
    _dim_v(ax, 0, W, L + 0.45, "W")

    _title(ax, title)
    return _to_png(fig)


def _diag_rect_plan_with_T(title="Slab on Grade — Plan View") -> bytes:
    """Rectangle plan with L × W + T thickness callout."""
    L, W = 6.0, 4.0

    fig, ax = _fig(6, 5)
    ax.set_xlim(-0.8, L + 1.5)
    ax.set_ylim(-0.8, W + 1.0)

    _rect(ax, 0, 0, L, W, fc=_CONCRETE)

    for xi in [1.2, 2.4, 3.6, 4.8]:
        if xi < L:
            ax.plot([xi, xi], [0.2, W-0.2], color=_REBAR, lw=0.9, zorder=4)
    for yi in [0.8, 1.6, 2.4, 3.2]:
        if yi < W:
            ax.plot([0.2, L-0.2], [yi, yi], color=_REBAR, lw=0.9, zorder=4)

    _dim_h(ax, 0, L, -0.5, "L")
    _dim_v(ax, 0, W, L + 0.45, "W")
    _callout(ax, L*0.8, W*0.15, "T", "thickness", angle=30, dist=0.9)

    _title(ax, title)
    return _to_png(fig)


def _diag_wing_wall() -> bytes:
    """Elevation of tapered wing wall — L length, H₁/H₂ heights."""
    L, H1, H2 = 6.0, 3.5, 0.4

    fig, ax = _fig(6.5, 5)
    ax.set_xlim(-0.8, L + 1.5)
    ax.set_ylim(-0.8, H1 + 1.0)

    pts = [(0, 0), (L, 0), (L, H2), (0, H1)]
    poly = plt.Polygon(pts, closed=True, fc=_CONCRETE, ec=_OUTLINE, lw=1.5, zorder=2)
    ax.add_patch(poly)

    # Rebar hints
    for xi in [0.3, 0.7, 1.5, 3.0, 5.0]:
        if xi < L:
            h_here = H1 + (H2 - H1) * xi / L
            ax.plot([xi, xi], [0.1, h_here - 0.1], color=_REBAR, lw=1.0, zorder=4)

    _dim_h(ax, 0, L, -0.5, "L")
    _dim_v(ax, 0, H1, -0.5, "H₁")
    _dim_v(ax, 0, H2, L + 0.5, "H₂")

    _title(ax, "Wing Wall — Elevation")
    return _to_png(fig)


def _diag_wall_section(title="Seatwall — Cross Section", hw=2.5, ww=1.5) -> bytes:
    """Cross-section of a wall: height H × width W."""
    fig, ax = _fig(5, 5)
    ax.set_xlim(-0.8, ww + 1.5)
    ax.set_ylim(-0.8, hw + 1.0)

    _rect(ax, 0, 0, ww, hw, fc=_CONCRETE)

    # Rebar
    for xi in [0.12, ww-0.12]:
        ax.plot([xi, xi], [0.15, hw-0.15], color=_REBAR, lw=1.2, zorder=4)
    for yi in [hw*0.15, hw*0.85]:
        ax.plot([0.1, ww-0.1], [yi, yi], color=_REBAR, lw=1.0, zorder=4)

    _dim_v(ax, 0, hw, ww + 0.45, "H")
    _dim_h(ax, 0, ww, -0.5, "W")

    _title(ax, title)
    return _to_png(fig)


def _diag_pipe_encasement() -> bytes:
    """Cross-section of pipe encasement — W × H with pipe inside."""
    W, H = 3.5, 3.5
    pipe_r = 1.0

    fig, ax = _fig(6, 5)
    ax.set_xlim(-0.8, W + 1.5)
    ax.set_ylim(-0.8, H + 1.0)

    _rect(ax, 0, 0, W, H, fc=_CONCRETE)

    # Pipe
    cx, cy = W/2, H/2
    pipe = mpatches.Circle((cx, cy), pipe_r, fc="white", ec=_OUTLINE, lw=2.0, zorder=3)
    pipe_void = mpatches.Circle((cx, cy), pipe_r*0.8, fc="#dde8f0", ec="#889aaa", lw=0.8, zorder=4)
    ax.add_patch(pipe)
    ax.add_patch(pipe_void)
    ax.text(cx, cy, "pipe", ha="center", va="center", fontsize=7, color="#555")

    # Rebar hoops
    for r_off in [0.15, 0.3]:
        hoop = mpatches.Circle((cx, cy), pipe_r + r_off, fill=False,
                                ec=_REBAR, lw=1.4, ls="--", zorder=2)
        ax.add_patch(hoop)

    _dim_h(ax, 0, W, -0.5, "W")
    _dim_v(ax, 0, H, W + 0.45, "H")
    _callout(ax, W*0.85, H*0.85, "L", "length (into page)", angle=45, dist=0.7)

    _title(ax, "Pipe Encasement — Cross Section")
    return _to_png(fig)


def _diag_junction() -> bytes:
    """Plan view of junction structure — inside L × W, with wall T."""
    L, W, T = 5.0, 3.5, 0.5

    fig, ax = _fig(6, 5)
    ax.set_xlim(-0.8, L + 2*T + 1.5)
    ax.set_ylim(-0.8, W + 2*T + 1.0)

    # Outer
    _rect(ax, 0, 0, L + 2*T, W + 2*T, fc=_CONCRETE)
    # Inner void
    _rect(ax, T, T, L, W, fc="white", ec=_OUTLINE, lw=1.0)

    _dim_h(ax, T, T + L, T + W + T + 0.45, "L (inside)")
    _dim_v(ax, T, T + W, T + L + T + 0.5, "W (inside)")
    _callout(ax, T/2, T/2, "T", "wall", angle=225, dist=0.6, fontsize=7)

    _title(ax, "Junction Structure — Plan View")
    return _to_png(fig)


def _diag_dual_slab() -> bytes:
    """Plan view of dual slab — Slab A and Slab B side by side."""
    La, Wa = 5.0, 3.0
    Lb, Wb = 4.0, 2.5
    gap = 0.3

    fig, ax = _fig(7, 5)
    ax.set_xlim(-0.8, La + gap + Lb + 1.5)
    ax.set_ylim(-0.8, max(Wa, Wb) + 1.0)

    _rect(ax, 0, 0, La, Wa, fc=_CONCRETE)
    ax.text(La/2, Wa/2, "Slab A", ha="center", va="center",
            fontsize=8, color=_LABEL, fontweight="bold")
    _dim_h(ax, 0, La, -0.5, "A-L")
    _dim_v(ax, 0, Wa, La + 0.3, "A-W")

    _rect(ax, La + gap, 0, Lb, Wb, fc="#bfc8d0")
    ax.text(La + gap + Lb/2, Wb/2, "Slab B", ha="center", va="center",
            fontsize=8, color=_LABEL, fontweight="bold")
    _dim_h(ax, La + gap, La + gap + Lb, Wb + 0.45, "B-L")
    _dim_v(ax, 0, Wb, La + gap + Lb + 0.45, "B-W")

    _title(ax, "Dual Slab — Plan View")
    return _to_png(fig)


def _diag_collar() -> bytes:
    """Plan view of pipe collar — L × W rectangle around pipe."""
    L, W = 5.0, 4.2
    pipe_r = 1.0

    fig, ax = _fig(6, 5)
    ax.set_xlim(-0.8, L + 1.5)
    ax.set_ylim(-0.8, W + 1.0)

    _rect(ax, 0, 0, L, W, fc=_CONCRETE)
    pipe = mpatches.Circle((L/2, W/2), pipe_r, fc="white", ec=_OUTLINE, lw=1.5, zorder=3)
    ax.add_patch(pipe)
    ax.text(L/2, W/2, "pipe", ha="center", va="center", fontsize=7, color="#555")

    # Rebar mat
    for xi in [0.6, 1.5, 3.5, 4.4]:
        ax.plot([xi, xi], [0.2, W-0.2], color=_REBAR, lw=0.9, zorder=4)
    for yi in [0.6, 1.5, 2.7, 3.6]:
        ax.plot([0.2, L-0.2], [yi, yi], color=_REBAR, lw=0.9, zorder=4)

    _dim_h(ax, 0, L, -0.5, "L")
    _dim_v(ax, 0, W, L + 0.45, "W")

    _title(ax, "Concrete Pipe Collar — Plan View")
    return _to_png(fig)


# ── Registry ──────────────────────────────────────────────────────────────────

_DIAGRAM_FN: dict[str, callable] = {
    "G2 Inlet":              _diag_g2_inlet,
    "G2 Expanded Inlet":     _diag_g2_inlet,
    "G2 Inlet Top":          lambda: _diag_rect_plan("G2 Inlet Top — Plan View"),
    "G2 Expanded Inlet Top": lambda: _diag_rect_plan("G2 Expanded Inlet Top — Plan View"),
    "Straight Headwall":     _diag_headwall,
    "Wing Wall":             _diag_wing_wall,
    "Spread Footing":        _diag_footing,
    "Box Culvert":           _diag_box_culvert,
    "Retaining Wall":        _diag_retaining_wall,
    "Flat Slab":             lambda: _diag_rect_plan("Flat Slab — Plan View"),
    "Drilled Shaft Cage":    _diag_cage,
    "Concrete Pipe Collar":  _diag_collar,
    "Slab on Grade":         lambda: _diag_rect_plan_with_T("Slab on Grade — Plan View"),
    "Equipment Pad":         lambda: _diag_rect_plan_with_T("Equipment Pad — Plan View"),
    "Switchboard Pad":       lambda: _diag_rect_plan_with_T("Switchboard Pad — Plan View"),
    "Seatwall":              lambda: _diag_wall_section("Seatwall — Cross Section", hw=1.5, ww=1.2),
    "Concrete Header":       lambda: _diag_wall_section("Concrete Header — Cross Section", hw=2.0, ww=1.0),
    "Pipe Encasement":       _diag_pipe_encasement,
    "Fuel Foundation":       lambda: _diag_rect_plan_with_T("Fuel Foundation — Plan View"),
    "Dual Slab":             _diag_dual_slab,
    "Junction Structure":    _diag_junction,
}


def get_diagram(template_name: str) -> bytes | None:
    """Return PNG bytes for the given template, or None if not found."""
    fn = _DIAGRAM_FN.get(template_name)
    return fn() if fn else None
