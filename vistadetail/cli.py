"""
VistaDetail CLI — connect to the open Excel workbook from Terminal.

No buttons, no VBA macros needed.  Open VistaDetail.xlsx in Excel,
then run any command from Terminal and watch the results appear live.

Usage:
    python3 -m vistadetail generate          # generate barlist for current template
    python3 -m vistadetail generate --no-ai  # skip Claude annotations
    python3 -m vistadetail refresh           # refresh Inputs tab for current template
    python3 -m vistadetail clear             # clear all output tabs
    python3 -m vistadetail export            # export BarList to barlist.csv
    python3 -m vistadetail cut               # run cut optimizer on current BarList
    python3 -m vistadetail compose           # run multi-structure composer (_Templates tab)
    python3 -m vistadetail corrections       # log corrections from edited BarList
    python3 -m vistadetail confidence        # show template confidence table on Dashboard
    python3 -m vistadetail status            # show current workbook state
    python3 -m vistadetail export-gold       # save current BarList as permanent gold override
    python3 -m vistadetail clear-gold        # delete gold override for current template
    python3 -m vistadetail list-gold         # list all active gold overrides
"""

from __future__ import annotations

import argparse
import sys


def _get_workbook():
    """
    Find the VistaDetail workbook among all open Excel workbooks.
    Raises SystemExit with a helpful message if not found.
    """
    try:
        import xlwings as xw
    except ImportError:
        print("ERROR: xlwings not installed.  Run: pip install xlwings")
        sys.exit(1)

    app = xw.apps.active
    if app is None:
        print("ERROR: Excel is not open.  Open VistaDetail.xlsx first.")
        sys.exit(1)

    # Look for any open book whose name contains 'VistaDetail'
    for book in app.books:
        if "vistadetail" in book.name.lower():
            return book

    # Fall back to active book if only one is open
    if len(app.books) == 1:
        return app.books[0]

    print("ERROR: Could not find VistaDetail workbook.")
    print(f"  Open books: {[b.name for b in app.books]}")
    print("  Open VistaDetail.xlsx in Excel first.")
    sys.exit(1)


def _inject_caller(book):
    """
    Make the book available to excel_bridge functions that call _get_book().
    xlwings' Book.caller() works when called from VBA; this patches it for CLI use.
    """
    import xlwings as xw
    # Monkey-patch Book.caller to return our book for CLI invocations
    xw.Book.caller = staticmethod(lambda: book)


# ---------------------------------------------------------------------------
# Command implementations
# ---------------------------------------------------------------------------

def cmd_generate(args):
    book = _get_workbook()
    _inject_caller(book)
    from vistadetail.excel_bridge import on_generate
    print(f"Generating barlist for: {book.sheets['Dashboard'].range('B3').value}")
    on_generate(call_ai=not args.no_ai)
    status = book.sheets["Dashboard"].range("B9").value
    print(f"Done → {status}")


def cmd_refresh(args):
    book = _get_workbook()
    _inject_caller(book)
    from vistadetail.excel_bridge import on_template_change
    tpl = book.sheets["Dashboard"].range("B3").value
    print(f"Refreshing inputs for: {tpl}")
    on_template_change()
    print("Done → Inputs tab updated")


def cmd_clear(args):
    book = _get_workbook()
    _inject_caller(book)
    from vistadetail.excel_bridge import on_clear
    print("Clearing all output tabs...")
    on_clear()
    print("Done → BarList, ReasoningLog, Validation cleared")


def cmd_export(args):
    book = _get_workbook()
    _inject_caller(book)
    from vistadetail.excel_bridge import on_export_csv
    print("Exporting barlist.csv...")
    path = on_export_csv()
    print(f"Done → {path}")


def cmd_cut(args):
    book = _get_workbook()
    _inject_caller(book)
    from vistadetail.excel_bridge import on_cut_optimize
    print("Running cut optimizer...")
    on_cut_optimize()
    status = book.sheets["Dashboard"].range("B9").value
    print(f"Done → {status}")


def cmd_compose(args):
    book = _get_workbook()
    _inject_caller(book)
    from vistadetail.excel_bridge import on_compose_project
    print("Running multi-structure composer from _Templates tab...")
    on_compose_project()
    status = book.sheets["Dashboard"].range("B9").value
    print(f"Done → {status}")


def cmd_corrections(args):
    book = _get_workbook()
    _inject_caller(book)
    from vistadetail.excel_bridge import on_log_corrections
    print("Logging corrections from current BarList...")
    on_log_corrections()
    status = book.sheets["Dashboard"].range("B9").value
    print(f"Done → {status}")


def cmd_confidence(args):
    book = _get_workbook()
    _inject_caller(book)
    from vistadetail.excel_bridge import on_show_confidence
    print("Writing confidence table to Dashboard...")
    on_show_confidence()
    print("Done → see Dashboard rows 12+")


def cmd_status(args):
    book = _get_workbook()
    tpl    = book.sheets["Dashboard"].range("B3").value
    status = book.sheets["Dashboard"].range("B9").value
    conf   = book.sheets["Dashboard"].range("A11").value

    # Count BarList rows
    data = book.sheets["BarList"].range("A2:A500").value or []
    bar_rows = sum(1 for r in data if r)

    print(f"  Workbook:  {book.name}")
    print(f"  Template:  {tpl}")
    print(f"  Status:    {status}")
    print(f"  BarList:   {bar_rows} mark rows")
    if conf:
        print(f"  Confidence: {conf}")


def cmd_export_gold(args):
    """Save the current BarList as a gold override CSV for the active template."""
    book = _get_workbook()
    _inject_caller(book)
    tpl = book.sheets["Dashboard"].range("B3").value
    if not tpl:
        print("ERROR: No template selected on Dashboard.")
        sys.exit(1)

    # Read current BarList from Excel
    from vistadetail.engine.gold_overrides import save_gold_override
    from vistadetail.engine.schema import BarRow

    header_row = book.sheets["BarList"].range("A1:K1").value or []
    data = book.sheets["BarList"].range("A2:K500").value or []
    bars = []
    for row in data:
        if not row or not row[0]:
            continue
        bars.append(BarRow(
            mark=str(row[0]),
            size=str(row[1] or ""),
            qty=int(row[2] or 0),
            length_in=0.0,   # will be formatted from length string column
            shape=str(row[4] or "Str"),
            notes=str(row[8] or ""),
            ref=str(row[9] or ""),
            review_flag=str(row[10] or ""),
        ))

    if not bars:
        print("ERROR: BarList is empty. Generate first, then export-gold.")
        sys.exit(1)

    # For gold export, use the raw BarList data directly (bypass length parsing)
    # Write CSV manually to preserve formatted lengths
    import csv
    import pathlib
    from vistadetail.engine.gold_overrides import override_path, _OVERRIDES_DIR
    _OVERRIDES_DIR.mkdir(parents=True, exist_ok=True)
    path = override_path(tpl)
    header = ["Mark", "Size", "Qty", "Length", "Shape",
              "Leg A", "Leg B", "Leg C", "Notes", "Ref", "Review Flag"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for row in data:
            if not row or not row[0]:
                continue
            writer.writerow([
                row[0] or "",   # Mark
                row[1] or "",   # Size
                int(row[2] or 0),  # Qty
                row[3] or "",   # Length (formatted string)
                row[4] or "Str", # Shape
                row[5] or "",   # Leg A
                row[6] or "",   # Leg B
                row[7] or "",   # Leg C
                row[8] or "",   # Notes
                row[9] or "",   # Ref
                row[10] or "",  # Review Flag
            ])

    print(f"Gold override saved for '{tpl}'")
    print(f"  Path: {path}")
    print(f"  {len([r for r in data if r and r[0]])} rows written.")
    print("Next Generate for this template will use the override.")


def cmd_clear_gold(args):
    """Delete the gold override CSV for the active template."""
    book = _get_workbook()
    tpl = book.sheets["Dashboard"].range("B3").value
    if not tpl:
        print("ERROR: No template selected on Dashboard.")
        sys.exit(1)

    from vistadetail.engine.gold_overrides import delete_gold_override, override_path
    deleted = delete_gold_override(tpl)
    if deleted:
        print(f"Gold override deleted for '{tpl}'.")
        print("Next Generate will use the computed barlist.")
    else:
        print(f"No gold override found for '{tpl}'.")
        print(f"  (Expected at: {override_path(tpl)})")


def cmd_list_gold(args):
    """List all active gold override CSV files."""
    from vistadetail.engine.gold_overrides import list_gold_overrides
    overrides = list_gold_overrides()
    if not overrides:
        print("No gold overrides active.")
        return
    print(f"Active gold overrides ({len(overrides)}):")
    for o in overrides:
        print(f"  {o['file']:<35}  {o['rows']:>3} rows   {o['path']}")


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

COMMANDS = {
    "generate":    (cmd_generate,    "Generate barlist for the current template"),
    "refresh":     (cmd_refresh,     "Refresh Inputs tab for the current template"),
    "clear":       (cmd_clear,       "Clear all output tabs"),
    "export":      (cmd_export,      "Export BarList to barlist.csv"),
    "cut":         (cmd_cut,         "Run cut optimizer on current BarList"),
    "compose":     (cmd_compose,     "Run multi-structure composer from _Templates tab"),
    "corrections": (cmd_corrections, "Log corrections from edited BarList"),
    "confidence":  (cmd_confidence,  "Show template confidence table on Dashboard"),
    "status":      (cmd_status,      "Show current workbook state"),
    "export-gold": (cmd_export_gold, "Save current BarList as gold override for this template"),
    "clear-gold":  (cmd_clear_gold,  "Delete gold override for the current template"),
    "list-gold":   (cmd_list_gold,   "List all active gold override files"),
}


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="python3 -m vistadetail",
        description="VistaDetail CLI — control Excel from Terminal",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="\n".join(
            f"  {cmd:<14} {desc}" for cmd, (_, desc) in COMMANDS.items()
        ),
    )
    parser.add_argument("command", choices=list(COMMANDS.keys()), help="Command to run")
    parser.add_argument("--no-ai", action="store_true", help="Skip Claude annotations (generate only)")

    args = parser.parse_args(argv)
    fn, _ = COMMANDS[args.command]

    try:
        fn(args)
    except SystemExit:
        raise
    except Exception as exc:
        print(f"ERROR: {exc}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
