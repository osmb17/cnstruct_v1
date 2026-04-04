"""
Cost estimating helpers for the rebar barlist.

compute_cost_estimate(bars, rate_per_lb) → CostEstimate

CostEstimate contains:
  - per-size weight and cost breakdown
  - total weight (lb) and total cost ($)
  - a formatted summary table ready for Excel or console output

Default material rate: $0.80 / lb (typical domestic mill rebar, 2024 market).
Fab + delivery markup is separate — estimator should adjust the rate cell.

Units:
  weight: lb
  cost:   USD
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from vistadetail.engine.schema import BarRow


# ---------------------------------------------------------------------------
# Default material rate
# ---------------------------------------------------------------------------

DEFAULT_RATE_PER_LB: float = 0.80   # $/lb — estimator should confirm with supplier


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class BarSizeCost:
    """Cost summary for one bar size."""
    size: str
    total_bars: int
    weight_lb: float
    rate_per_lb: float
    cost_usd: float


@dataclass
class CostEstimate:
    """
    Full cost breakdown for one generated barlist.

    Attributes:
        by_size:       one row per bar size, sorted by size number
        total_weight_lb: sum of all bar weights
        total_cost_usd:  total_weight_lb × rate_per_lb
        rate_per_lb:     material rate used ($/lb)
    """
    by_size: list[BarSizeCost] = field(default_factory=list)
    total_weight_lb: float = 0.0
    total_cost_usd: float = 0.0
    rate_per_lb: float = DEFAULT_RATE_PER_LB


# ---------------------------------------------------------------------------
# Main function
# ---------------------------------------------------------------------------

def compute_cost_estimate(
    bars: "list[BarRow]",
    rate_per_lb: float = DEFAULT_RATE_PER_LB,
) -> CostEstimate:
    """
    Compute weight and cost breakdown for a generated barlist.

    Args:
        bars:         BarRow list (output of generate_barlist)
        rate_per_lb:  material cost per pound (e.g. 0.80 for $0.80/lb)

    Returns:
        CostEstimate with per-size rows and totals.
    """
    from vistadetail.engine.hooks import BAR_WEIGHT_LB_FT

    # Accumulate weight per size
    size_totals: dict[str, dict] = {}
    for b in bars:
        w_per_ft = BAR_WEIGHT_LB_FT.get(b.size, 0.0)
        bar_weight = w_per_ft * (b.length_in / 12.0) * b.qty
        if b.size not in size_totals:
            size_totals[b.size] = {"bars": 0, "weight_lb": 0.0}
        size_totals[b.size]["bars"]      += b.qty
        size_totals[b.size]["weight_lb"] += bar_weight

    # Sort by numeric bar size  (#3 first, #11 last)
    def _sort_key(s: str) -> int:
        try:
            return int(s.lstrip("#"))
        except ValueError:
            return 99

    by_size: list[BarSizeCost] = []
    for size in sorted(size_totals.keys(), key=_sort_key):
        row = size_totals[size]
        w   = round(row["weight_lb"], 1)
        c   = round(w * rate_per_lb, 2)
        by_size.append(BarSizeCost(
            size=size,
            total_bars=row["bars"],
            weight_lb=w,
            rate_per_lb=rate_per_lb,
            cost_usd=c,
        ))

    total_weight = round(sum(r.weight_lb for r in by_size), 1)
    total_cost   = round(total_weight * rate_per_lb, 2)

    return CostEstimate(
        by_size=by_size,
        total_weight_lb=total_weight,
        total_cost_usd=total_cost,
        rate_per_lb=rate_per_lb,
    )


def format_cost_summary(est: CostEstimate) -> str:
    """Return a plain-text summary of the cost estimate (for console / log)."""
    lines = [
        f"{'Size':<6}  {'Bars':>5}  {'Weight (lb)':>12}  {'Rate ($/lb)':>12}  {'Cost ($)':>10}",
        "─" * 52,
    ]
    for row in est.by_size:
        lines.append(
            f"{row.size:<6}  {row.total_bars:>5}  {row.weight_lb:>12.1f}"
            f"  {row.rate_per_lb:>12.2f}  {row.cost_usd:>10.2f}"
        )
    lines += [
        "─" * 52,
        f"{'TOTAL':<6}  {'':>5}  {est.total_weight_lb:>12.1f}"
        f"  {'':>12}  {est.total_cost_usd:>10.2f}",
    ]
    return "\n".join(lines)
