"""
VistaDetail CLI — headless demo / smoke test.

Usage:
    python -m vistadetail.main
    python -m vistadetail.main --template "Inlet – 9in Wall" --out out/demo/barlist.csv
"""

from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="VistaDetail headless barlist generator"
    )
    parser.add_argument(
        "--template",
        default="Inlet – 9in Wall",
        help="Template name (default: 'Inlet – 9in Wall')",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Write barlist.csv to this path",
    )
    parser.add_argument(
        "--ai",
        action="store_true",
        help="Enable Claude reviewer notes (requires ANTHROPIC_API_KEY)",
    )
    args = parser.parse_args(argv)

    # Default demo params for the Inlet 9in Wall
    demo_params = {
        "wall_length_ft":  12.5,
        "wall_height_ft":  6.0,
        "wall_thick_in":   9,
        "cover_in":        2.0,
        "horiz_bar_size":  "#5",
        "horiz_spacing_in": 12.0,
        "vert_bar_size":   "#5",
        "vert_spacing_in": 12.0,
        "hook_type":       "std_90",
        "corner_bars":     "yes",
        "corner_bar_size": "#4",
    }

    from vistadetail.excel_bridge import run_headless
    from vistadetail.engine.calculator import barlist_total_weight_lb

    bars = run_headless(
        args.template,
        demo_params,
        call_ai=args.ai,
        out_path=args.out,
    )

    # Print summary table
    print("\n" + "─" * 72)
    print(f"{'Mark':<6} {'Size':<6} {'Qty':>5}  {'Length':<10} {'Shape':<6}  Notes")
    print("─" * 72)
    for b in bars:
        print(
            f"{b.mark:<6} {b.size:<6} {b.qty:>5}  "
            f"{b.length_ft_in:<10} {b.shape:<6}  {b.notes}"
        )
    print("─" * 72)
    total_qty = sum(b.qty for b in bars)
    total_wt  = barlist_total_weight_lb(bars)
    print(f"TOTAL  {total_qty} bars  |  {total_wt:.0f} lb  ({total_wt / 2000:.2f} tons)")
    print("─" * 72)

    if args.out:
        print(f"\nExported → {args.out}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
