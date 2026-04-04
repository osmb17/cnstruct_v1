"""
Feature E: Cut-List Optimizer.

Given a list of required bar lengths and available stock lengths,
computes the most material-efficient cutting pattern using a
First-Fit Decreasing (FFD) bin-packing heuristic.

This is entirely deterministic — no LLM involved.

Usage:
    from vistadetail.engine.cut_optimizer import optimize_cuts, CutPlan

    bars = [
        CutRequest("#5", 165.0, 12),   # H1: 12 × 13'-9"
        CutRequest("#5",  85.5, 26),   # V1: 26 × 7'-1.5"
        CutRequest("#4",  48.0,  4),   # C1: 4 × 4'-0"
    ]
    plan = optimize_cuts(bars, stock_lengths_ft=[20, 40])
    plan.print_summary()
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import NamedTuple

from vistadetail.engine.hooks import BAR_WEIGHT_LB_FT
from vistadetail.engine.schema import BarRow, fmt_inches


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

class CutRequest(NamedTuple):
    size: str          # e.g. "#5"
    length_in: float   # required piece length
    qty: int           # number of pieces needed


@dataclass
class StockBar:
    """One physical stock bar being cut."""
    size: str
    stock_len_in: float
    cuts: list[float] = field(default_factory=list)   # lengths of pieces cut from this bar

    @property
    def remaining_in(self) -> float:
        return self.stock_len_in - sum(self.cuts)

    @property
    def waste_in(self) -> float:
        return self.remaining_in  # after all pieces assigned; end cut-off


@dataclass
class CutPlan:
    """Complete cutting plan for all bar sizes."""
    by_size: dict[str, list[StockBar]] = field(default_factory=dict)

    # ── Summary metrics ─────────────────────────────────────────────────

    def total_bars_used(self) -> dict[str, int]:
        return {size: len(bars) for size, bars in self.by_size.items()}

    def total_waste_in(self) -> dict[str, float]:
        return {
            size: sum(b.waste_in for b in bars)
            for size, bars in self.by_size.items()
        }

    def waste_pct(self) -> dict[str, float]:
        result = {}
        for size, bars in self.by_size.items():
            total_stock = sum(b.stock_len_in for b in bars)
            total_waste = sum(b.waste_in for b in bars)
            result[size] = round(100.0 * total_waste / max(total_stock, 0.001), 1)
        return result

    def total_weight_lb(self) -> float:
        total = 0.0
        wt = BAR_WEIGHT_LB_FT
        for size, bars in self.by_size.items():
            lb_per_ft = wt.get(size, 0.0)
            for bar in bars:
                total += lb_per_ft * (bar.stock_len_in / 12.0)
        return round(total, 1)

    def print_summary(self) -> None:
        """Print a human-readable cut diagram to stdout."""
        print("\n" + "=" * 72)
        print("CUT-LIST OPTIMIZER RESULTS")
        print("=" * 72)
        for size, bars in sorted(self.by_size.items()):
            stock_len = bars[0].stock_len_in if bars else 0
            print(f"\n  {size}  |  {len(bars)} stock bars @ {fmt_inches(stock_len)} each")
            print(f"  {'Bar #':<6} {'Cuts':<48} {'Waste':>8}")
            print(f"  {'─'*5}  {'─'*48}  {'─'*7}")
            for i, bar in enumerate(bars, start=1):
                cut_str = "  ".join(fmt_inches(c) for c in bar.cuts)
                if len(cut_str) > 46:
                    cut_str = cut_str[:43] + "..."
                print(f"  {i:<6} {cut_str:<48} {fmt_inches(bar.waste_in):>8}")
            wp = self.waste_pct().get(size, 0.0)
            print(f"  Waste: {wp:.1f}%  |  {self.total_bars_used()[size]} bars total")
        print("\n" + "=" * 72)
        print(f"  Total stock weight: {self.total_weight_lb():.0f} lb")
        print("=" * 72 + "\n")

    def generate_notes(
        self,
        requests: list[CutRequest] | None = None,
        stock_lengths_ft: list[int] | None = None,
    ) -> list[str]:
        """
        Generate deterministic estimator notes based on the cut plan results.
        Each note is a plain string starting with '•'.
        """
        notes: list[str] = []
        if stock_lengths_ft is None:
            stock_lengths_ft = [20, 40, 60]

        req_map: dict[str, CutRequest] = {}
        if requests:
            for r in requests:
                req_map[r.size] = r   # last wins per size

        waste_pcts = self.waste_pct()
        bars_used  = self.total_bars_used()

        for size, bars in sorted(self.by_size.items()):
            if not bars:
                continue
            wp   = waste_pcts.get(size, 0)
            used = bars_used.get(size, 0)
            stock_len_ft = bars[0].stock_len_in / 12.0

            # Check if cuts could be paired on shorter stock
            cuts_per_bar = [len(b.cuts) for b in bars]
            single_cut_bars = sum(1 for c in cuts_per_bar if c == 1)

            if wp > 50:
                # Recommend longer stock
                for alt_ft in sorted(stock_lengths_ft, reverse=True):
                    if alt_ft > stock_len_ft:
                        req = req_map.get(size)
                        if req:
                            pieces_per_alt = int(alt_ft * 12 / req.length_in)
                            if pieces_per_alt > 1:
                                saving = round(100 * (1 - 1 / pieces_per_alt), 0)
                                notes.append(
                                    f"• {size} bars ({req.length_in / 12:.2g}ft) cannot be"
                                    f" paired from {int(stock_len_ft)}ft stock."
                                    f" Consider {alt_ft}ft stock for {saving:.0f}% better yield."
                                )
                                break
            elif wp < 10:
                req = req_map.get(size)
                label = req_map.get(size)
                notes.append(
                    f"• {size} bars pair efficiently from {int(stock_len_ft)}ft stock."
                    f" Current plan is near-optimal at {wp:.1f}% waste."
                )
            elif 10 <= wp <= 35:
                req = req_map.get(size)
                if req and (req.length_in / 12) < 5:
                    per_bar = int(stock_len_ft * 12 / req.length_in)
                    notes.append(
                        f"• {size} bars are short ({req.length_in / 12:.3g}ft)."
                        f" Bundle order: request pre-cut or cut {per_bar} per {int(stock_len_ft)}ft bar."
                    )
                else:
                    notes.append(
                        f"• {size} bars: {wp:.1f}% waste on {int(stock_len_ft)}ft stock"
                        f" using {used} bar{'s' if used != 1 else ''}."
                    )

        if not notes:
            notes.append("• Cut plan optimized. No significant waste reduction opportunities found.")

        return notes

    def to_rows(self) -> list[list]:
        """Flat list-of-lists for writing to Excel cut-list tab."""
        header = ["Size", "Bar #", "Stock Length", "Cut 1", "Cut 2", "Cut 3",
                  "Cut 4", "Cut 5", "Waste", "Waste %"]
        rows = [header]
        for size, bars in sorted(self.by_size.items()):
            for i, bar in enumerate(bars, start=1):
                cuts_fmt = [fmt_inches(c) for c in bar.cuts]
                # Pad to 5 cut columns
                while len(cuts_fmt) < 5:
                    cuts_fmt.append("")
                rows.append([
                    size, i,
                    fmt_inches(bar.stock_len_in),
                    *cuts_fmt[:5],
                    fmt_inches(bar.waste_in),
                    f"{bar.waste_in / bar.stock_len_in * 100:.1f}%",
                ])
        return rows


# ---------------------------------------------------------------------------
# Core optimizer
# ---------------------------------------------------------------------------

# Standard stock lengths in feet → inches
STANDARD_STOCK_FT = [20, 40, 60]


def optimize_cuts(
    requests: list[CutRequest],
    stock_lengths_ft: list[int] | None = None,
    kerf_in: float = 0.125,   # saw blade kerf
) -> CutPlan:
    """
    Compute an optimized cut plan using First-Fit Decreasing (FFD) bin-packing.

    For each bar size:
      1. Sort required pieces descending by length
      2. For each piece, find the shortest stock bar it fits in (best-fit)
      3. If none fits, open a new stock bar (prefer shorter stock to minimise waste)

    Args:
        requests:          list of CutRequest (size, length_in, qty)
        stock_lengths_ft:  available stock lengths in feet (default: [20, 40, 60])
        kerf_in:           saw kerf deducted per cut (default 1/8 in)

    Returns:
        CutPlan with per-size cutting assignments.
    """
    if stock_lengths_ft is None:
        stock_lengths_ft = STANDARD_STOCK_FT

    stock_lengths_in = sorted(l * 12 for l in stock_lengths_ft)

    # Group by bar size
    by_size: dict[str, list[CutRequest]] = {}
    for req in requests:
        by_size.setdefault(req.size, []).append(req)

    plan = CutPlan()

    for size, reqs in by_size.items():
        # Expand into individual pieces, sort descending
        pieces: list[float] = []
        for req in reqs:
            pieces.extend([req.length_in] * req.qty)
        pieces.sort(reverse=True)

        # Choose shortest stock length that can hold the longest piece
        max_piece = pieces[0] if pieces else 0.0
        chosen_stock = next(
            (s for s in stock_lengths_in if s >= max_piece),
            stock_lengths_in[-1]  # fall back to longest available
        )

        open_bars: list[StockBar] = []

        for piece_len in pieces:
            # Best-fit: find bar with smallest remaining space that still fits
            best: StockBar | None = None
            best_remaining = float("inf")
            for bar in open_bars:
                space = bar.remaining_in - kerf_in   # account for kerf
                if space >= piece_len and space < best_remaining:
                    best = bar
                    best_remaining = space

            if best is None:
                # Open a new stock bar (pick shortest stock that fits)
                stock_len = next(
                    (s for s in stock_lengths_in if s >= piece_len + kerf_in),
                    stock_lengths_in[-1]
                )
                best = StockBar(size=size, stock_len_in=stock_len)
                open_bars.append(best)

            best.cuts.append(piece_len)

        plan.by_size[size] = open_bars

    return plan


def optimize_cuts_from_barlist(
    bars: list[BarRow],
    stock_lengths_ft: list[int] | None = None,
) -> CutPlan:
    """Convenience wrapper: build CutRequests from a generated BarRow list."""
    reqs = [
        CutRequest(b.size, b.length_in, b.qty)
        for b in bars
        if b.qty > 0 and b.length_in > 0
    ]
    return optimize_cuts(reqs, stock_lengths_ft=stock_lengths_ft)
