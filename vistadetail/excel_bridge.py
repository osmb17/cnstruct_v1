"""
Excel bridge — xlwings button handlers wired to Rebar Barlist Generator.xlsm.

These functions are called by xlwings UDF / RunPython buttons in Excel.
They bridge the Python engine to live Excel cells.

Usage from Excel VBA macro (xlwings RunPython):
    Sub GenerateDraft()
        RunPython "from vistadetail.excel_bridge import on_generate; on_generate()"
    End Sub
"""

from __future__ import annotations

import csv
import io
import os
import traceback
from datetime import datetime


def _get_book():
    """Return the active xlwings Book, or raise ImportError if xlwings not available."""
    import xlwings as xw
    return xw.Book.caller()


def _set_status(ws_dash, message: str, colour: tuple = (46, 125, 50)) -> None:
    """
    Write a live status message to Dashboard B8 and force an immediate screen repaint
    so the user sees progress feedback during generation (not just at the end).
    """
    try:
        import xlwings as xw
        ws_dash.range("B8").value = message
        ws_dash.range("B8").font.color = colour
        # Force Excel to repaint immediately so the user can see the update
        xw.apps.active.screen_updating = True
    except Exception:
        pass  # never let status updates crash generation


def _write_barlist_to_sheet(ws_barlist, bars) -> None:
    """
    Write BarRow list to the BarList sheet in Vista Steel format.

    Data rows start at row 10 (after the 8-row company header + col-header row).
    Columns A-Q: S/H/L, NO.OF UNITS, NO.PER UNIT, TOTAL, SIZE, GRADE,
                 LENGTH, MARK, TYPE, A, B, C', D, E, F, G, H.
    Column R (row numbers 1-60) is pre-filled — not touched.

    Below the data rows: a cost estimate summary block is written.

    Row colours:
      light pink   → auto mark (no mark found on drawing)
      light yellow → needs review / flagged
      alternating  → clean rows
    """
    from vistadetail.workbook.barlist_layout import DATA_START, DATA_ROWS, bar_to_vista_row

    _YELLOW = (255, 252, 210)
    _PINK   = (255, 230, 230)
    _EVEN   = (250, 250, 250)
    _ODD    = (255, 255, 255)

    # Clear data area + cost section (rows DATA_START to DATA_START+DATA_ROWS+20)
    end_row = DATA_START + DATA_ROWS + 20
    ws_barlist.range(f"A{DATA_START}:Q{end_row}").clear_contents()
    ws_barlist.range(f"A{DATA_START}:Q{end_row}").color = None

    max_bars = min(len(bars), DATA_ROWS)
    for i, bar in enumerate(bars[:max_bars]):
        row_excel = DATA_START + i
        row_data  = bar_to_vista_row(bar)
        ws_barlist.range(f"A{row_excel}").value = row_data   # 17 columns

        # Colour coding
        is_auto   = "auto" in str(bar.mark).lower()
        is_review = bool(bar.review_flag)
        if is_auto or is_review:
            colour = _PINK if is_auto else _YELLOW
        else:
            colour = _EVEN if (i % 2 == 0) else _ODD
        ws_barlist.range(f"A{row_excel}:Q{row_excel}").color = colour

    # ── Cost estimate section ─────────────────────────────────────────────
    _write_cost_section(ws_barlist, bars, start_row=DATA_START + DATA_ROWS + 2)


def _write_cost_section(ws_barlist, bars, start_row: int) -> None:
    """
    Write a cost estimate summary block below the barlist data rows.

    Layout (starting at start_row):
      Row +0: [COST ESTIMATE] header (navy bg, white bold)
      Row +1: Material Rate:  [rate $/lb]  (editable — user can change)
      Row +2: blank
      Row +3: col headers: Size | Bars | Weight (lb) | Rate ($/lb) | Cost ($)
      Row +4…+N: one row per bar size
      Row +N+1: blank
      Row +N+2: TOTAL row (bold)
    """
    from vistadetail.engine.cost_estimate import compute_cost_estimate, DEFAULT_RATE_PER_LB

    _NAVY   = (28,  52,  97)
    _WHITE  = (255, 255, 255)
    _BLUE_L = (219, 229, 241)
    _GOLD   = (255, 243, 200)
    _BOLD_GREEN = (0, 97, 0)

    # Try to read a user-entered rate from cell E{start_row+1} (from previous run)
    try:
        saved_rate = float(ws_barlist.range(f"E{start_row + 1}").value or 0)
        rate = saved_rate if saved_rate > 0 else DEFAULT_RATE_PER_LB
    except Exception:
        rate = DEFAULT_RATE_PER_LB

    est = compute_cost_estimate(bars, rate_per_lb=rate)

    r = start_row

    # ── Header row ────────────────────────────────────────────────────────
    ws_barlist.range(f"A{r}").value = [["COST ESTIMATE", None, None, None, None]]
    ws_barlist.range(f"A{r}:E{r}").color = _NAVY
    ws_barlist.range(f"A{r}:E{r}").font.bold  = True
    ws_barlist.range(f"A{r}:E{r}").font.color = _WHITE
    r += 1

    # ── Rate input row ────────────────────────────────────────────────────
    ws_barlist.range(f"A{r}").value = [["Material Rate ($/lb):", None, None, None, rate]]
    ws_barlist.range(f"A{r}:D{r}").color = _BLUE_L
    ws_barlist.range(f"A{r}").font.bold  = True
    ws_barlist.range(f"E{r}").color      = _GOLD   # gold = editable input cell
    ws_barlist.range(f"E{r}").font.bold  = True
    r += 1

    # ── Blank spacer ─────────────────────────────────────────────────────
    r += 1

    # ── Column headers ────────────────────────────────────────────────────
    ws_barlist.range(f"A{r}").value = [["Size", "Bars", "Weight (lb)", "Rate ($/lb)", "Cost ($)"]]
    ws_barlist.range(f"A{r}:E{r}").color      = _NAVY
    ws_barlist.range(f"A{r}:E{r}").font.bold  = True
    ws_barlist.range(f"A{r}:E{r}").font.color = _WHITE
    r += 1

    # ── Per-size rows ─────────────────────────────────────────────────────
    for sz in est.by_size:
        ws_barlist.range(f"A{r}").value = [[
            sz.size, sz.total_bars, sz.weight_lb, sz.rate_per_lb, sz.cost_usd
        ]]
        ws_barlist.range(f"A{r}:E{r}").color = (240, 248, 255)  # light blue tint
        r += 1

    # ── Blank spacer ─────────────────────────────────────────────────────
    r += 1

    # ── Totals row ────────────────────────────────────────────────────────
    ws_barlist.range(f"A{r}").value = [[
        "TOTAL", None, est.total_weight_lb, None, est.total_cost_usd
    ]]
    ws_barlist.range(f"A{r}:E{r}").color      = (198, 224, 180)   # pale green
    ws_barlist.range(f"A{r}:E{r}").font.bold  = True
    ws_barlist.range(f"A{r}").font.color       = _BOLD_GREEN
    ws_barlist.range(f"E{r}").font.color       = _BOLD_GREEN


def _write_validation_to_sheet(ws_validation, bars) -> None:
    """Write any review-flagged rows to the Validation tab."""
    ws_validation.range("A3:B2000").clear_contents()
    flagged = [(b.mark, b.review_flag) for b in bars if b.review_flag]
    if flagged:
        ws_validation.range("A3").value = flagged
    else:
        ws_validation.range("A3").value = "✓ No flags"


def _write_heatmap(ws_validation, bars, params) -> None:
    """Feature B: write bar-spacing heatmap grids to Validation tab."""
    try:
        from vistadetail.engine.heatmap import build_heatmap_grids, write_heatmap_to_sheet
        grids = build_heatmap_grids(bars, params)
        if grids:
            # Clear old heatmap area first
            ws_validation.range("A4:AQ200").clear_contents()
            ws_validation.range("A4:AQ200").color = None
            write_heatmap_to_sheet(ws_validation, grids, start_row=4)
    except Exception:
        pass   # heatmap is visual-only; never break generation


def _write_results_section(ws_dash, bars) -> None:
    """
    Write bar count, weight, and estimated cost into the Dashboard Results block.
    Row 11: Total Bars (B11) + Total Weight (D11)
    Row 12: Est. Material Cost (B12) — reads rate from D12
    """
    try:
        from vistadetail.engine.calculator import barlist_total_weight_lb
        from vistadetail.engine.cost_estimate import compute_cost_estimate

        total_qty = sum(b.qty for b in bars)
        weight    = barlist_total_weight_lb(bars)

        # Read user-entered rate from D12 (pale yellow editable cell)
        try:
            rate = float(ws_dash.range("D12").value or 0.80)
            if rate <= 0:
                rate = 0.80
        except Exception:
            rate = 0.80

        est  = compute_cost_estimate(bars, rate_per_lb=rate)
        cost = est.total_cost_usd

        _GREEN = (46, 125, 50)
        ws_dash.range("B11").value       = total_qty
        ws_dash.range("B11").font.color  = _GREEN
        ws_dash.range("B11").font.bold   = True
        ws_dash.range("D11").value       = f"{weight:,.1f}"
        ws_dash.range("D11").font.color  = _GREEN
        ws_dash.range("D11").font.bold   = True
        ws_dash.range("B12").value       = f"${cost:,.2f}"
        ws_dash.range("B12").font.color  = _GREEN
        ws_dash.range("B12").font.bold   = True
    except Exception:
        pass   # never let results display crash generation


def _write_confidence(ws_dash, store, template_name: str) -> None:
    """Feature C: write acceptance rate for this template to Dashboard row 14."""
    try:
        conf = store.get_confidence(template_name)
        if conf.uses == 0:
            ws_dash.range("A14").value = ""
            return
        ws_dash.range("A14").value = (
            f"{template_name}  —  "
            f"{conf.uses} uses  |  "
            f"{conf.acceptance_pct:.0f}% accepted as-is"
        )
        colour = (46, 125, 50) if conf.acceptance_pct >= 90 else \
                 (245, 124, 0) if conf.acceptance_pct >= 70 else \
                 (198, 40, 40)
        ws_dash.range("A14").font.color  = colour
        ws_dash.range("A14").font.italic = True
    except Exception:
        pass


def _read_inputs(ws_inputs) -> dict:
    """
    Read the Inputs sheet into a param dict.
    Expects column A = label, column B = value.
    Input fields start at _DIAGRAM_ROWS + 1 (below diagram area).
    """
    start = _DIAGRAM_ROWS + 1
    data = ws_inputs.range(f"A{start}:B{start + 60}").value or []
    result = {}
    for row in data:
        if row and row[0] and row[1] is not None:
            # Convert label → field name by lowercasing and replacing spaces
            label = str(row[0]).strip()
            val = row[1]
            result[label] = val
    return result


def _read_inputs_by_field_name(ws_inputs, template) -> dict:
    """
    Read inputs keyed by field name using the template's input field list.
    Column A = label, column B = value, rows 3..N.
    """
    label_to_name = {v: k for k, v in template.input_labels().items()}
    raw_labeled = _read_inputs(ws_inputs)

    result = {}
    for label, val in raw_labeled.items():
        field_name = label_to_name.get(label, label)
        result[field_name] = val
    return result


# ---------------------------------------------------------------------------
# Button handlers
# ---------------------------------------------------------------------------

def on_generate(call_ai: bool = True) -> None:
    """
    Called by the GENERATE DRAFT button.
    Reads Dashboard + Inputs, runs the engine, writes BarList + ReasoningLog.
    """
    try:
        import xlwings as xw
        book = _get_book()

        ws_dash      = book.sheets["Dashboard"]
        ws_inputs    = book.sheets["Inputs"]
        ws_barlist   = book.sheets["BarList"]
        ws_log       = book.sheets["ReasoningLog"]
        ws_validation = book.sheets["Validation"]

        # Read selected template name
        from vistadetail.engine.templates import TEMPLATE_REGISTRY
        template_name = ws_dash.range("B3").value or ""
        template = TEMPLATE_REGISTRY.get(template_name)
        if template is None:
            xw.apps.active.alert(
                f"Unknown template: '{template_name}'\n"
                f"Available: {list(TEMPLATE_REGISTRY.keys())}",
                "Rebar Generator Error"
            )
            return

        # ── Step 1: Initialising ─────────────────────────────────────────
        _set_status(ws_dash, "⏳ Reading inputs…", colour=(100, 100, 100))

        # Set up logger
        from vistadetail.engine.reasoning_logger import ReasoningLogger
        log = ReasoningLogger(ws_log)
        log.clear()

        # Read params
        params_raw = _read_inputs_by_field_name(ws_inputs, template)

        # ── Step 2: Running engine ────────────────────────────────────────
        _set_status(ws_dash, f"⏳ Running rules for {template.name}…", colour=(100, 100, 100))

        from vistadetail.engine.calculator import generate_barlist
        from vistadetail.engine.correction_store import CorrectionStore
        store = CorrectionStore()
        params = template.parse_and_validate(params_raw)
        bars = generate_barlist(template, params_raw, log, call_ai=call_ai, store=store)

        # ── Step 3: Writing results ───────────────────────────────────────
        _set_status(ws_dash, "⏳ Writing bar list…", colour=(100, 100, 100))
        _write_barlist_to_sheet(ws_barlist, bars)

        # Write Validation tab: flags + heatmap
        _set_status(ws_dash, "⏳ Running validation…", colour=(100, 100, 100))
        _write_validation_to_sheet(ws_validation, bars)
        _write_heatmap(ws_validation, bars, params)

        # Feature C: confidence score on Dashboard
        _write_confidence(ws_dash, store, template.name)

        # Results block: bar count, weight, cost
        _write_results_section(ws_dash, bars)

        # ── Done — final status ───────────────────────────────────────────
        total_qty = sum(b.qty for b in bars)
        from vistadetail.engine.calculator import barlist_total_weight_lb
        weight = barlist_total_weight_lb(bars)
        _set_status(
            ws_dash,
            f"✓ Done — {total_qty} bars | {weight:,.0f} lb | "
            f"{datetime.now().strftime('%H:%M')}",
            colour=(46, 125, 50),
        )

        # Switch focus to BarList
        ws_barlist.activate()

    except Exception as exc:
        # Write error to status then re-raise so xlwings shows the traceback
        try:
            book = _get_book()
            _set_status(book.sheets["Dashboard"], f"⚠ Error: {exc}", colour=(198, 40, 40))
        except Exception:
            pass
        raise


def on_template_change() -> None:
    """
    Called when the user changes the template dropdown on Dashboard (B3).
    Repopulates the Inputs tab with the new template's fields and defaults,
    and regenerates the structure diagram at the top of the Inputs tab.
    """
    try:
        book = _get_book()
        ws_dash   = book.sheets["Dashboard"]
        ws_inputs = book.sheets["Inputs"]

        from vistadetail.engine.templates import TEMPLATE_REGISTRY
        template_name = ws_dash.range("B3").value or ""
        template = TEMPLATE_REGISTRY.get(template_name)
        if template is None:
            return

        # Collect current param values (defaults for the selected template)
        params = {f.name: f.default for f in template.inputs}

        _populate_inputs_tab(ws_inputs, template)
        _embed_diagram(ws_inputs, template_name, params)

        ws_dash.range("B8").value = f"Template changed → {template_name}  (inputs refreshed)"
        ws_dash.range("B8").font.color = (13, 71, 161)   # blue

    except Exception:
        raise


def _embed_diagram(ws_inputs, template_name: str, params: dict) -> None:
    """
    Generate a structure schematic PNG and embed it at the top of the Inputs sheet.
    Replaces any previously embedded diagram named 'StructureDiagram'.
    """
    try:
        from vistadetail.workbook.diagram_generator import generate_diagram_png
        import tempfile, os

        png_bytes = generate_diagram_png(template_name, params)

        # Write to temp file (xlwings pictures.add needs a path)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(png_bytes)
            tmp_path = tmp.name

        try:
            # Remove old diagram if present
            for pic in list(ws_inputs.pictures):
                if pic.name == "StructureDiagram":
                    pic.delete()

            # Anchor at A1, fixed display size
            top  = ws_inputs.range("A1").top
            left = ws_inputs.range("A1").left
            ws_inputs.pictures.add(
                tmp_path,
                name="StructureDiagram",
                top=top,
                left=left,
                width=520,
                height=280,
                update=True,
            )
        finally:
            os.unlink(tmp_path)

    except Exception:
        # Never let diagram failure break the inputs refresh
        pass


_DIAGRAM_ROWS = 22   # rows 1-21 reserved for diagram; inputs start at row 22


def _populate_inputs_tab(ws_inputs, template) -> None:
    """
    Write template input fields to the Inputs tab.
    Rows 1-21 are the diagram area (managed by _embed_diagram).
    Input fields start at row 22.
    Preserves any existing user values where field names match.
    """
    start = _DIAGRAM_ROWS

    # Read existing values before clearing
    existing_data = ws_inputs.range(f"A{start}:B{start+60}").value or []
    existing_vals: dict[str, object] = {}
    for row in existing_data:
        if row and row[0]:
            existing_vals[str(row[0]).strip()] = row[1]

    # Clear old inputs below diagram area (allow for 60 fields + up to 15 group headers)
    ws_inputs.range(f"A{start}:C{start+80}").clear_contents()
    ws_inputs.range(f"A{start}:C{start+80}").color = None

    # Subheader
    ws_inputs.range(f"A{start}").value = f"Template: {template.name}  (v{template.version})"
    ws_inputs.range(f"A{start}").font.italic = True
    ws_inputs.range(f"A{start}").font.color = (100, 100, 100)

    GREY_LIGHT  = (242, 242, 242)
    WHITE       = (255, 255, 255)
    _NAVY       = (28, 52, 97)
    _BLUE_LIGHT = (214, 228, 240)

    current_group = None
    row_offset = 0   # extra rows consumed by group headers

    for i, field in enumerate(template.inputs):
        # ── Group header row ────────────────────────────────────────────────
        if field.group and field.group != current_group:
            current_group = field.group
            hdr_row = i + start + 1 + row_offset
            hdr = ws_inputs.range(f"A{hdr_row}")
            hdr.value = field.group.upper()
            hdr.font.bold  = True
            hdr.font.color = _NAVY
            hdr.color      = _BLUE_LIGHT
            ws_inputs.range(f"B{hdr_row}").color = _BLUE_LIGHT
            ws_inputs.range(f"C{hdr_row}").color = _BLUE_LIGHT
            row_offset += 1

        row = i + start + 1 + row_offset
        label = field.label or field.name

        # Label cell
        lbl = ws_inputs.range(f"A{row}")
        lbl.value = label
        lbl.font.bold = False
        lbl.color = GREY_LIGHT if i % 2 == 0 else WHITE

        # Value cell — reuse existing value if label matches, else use default
        val = existing_vals.get(label, field.default)
        val_cell = ws_inputs.range(f"B{row}")
        val_cell.value = val

        # Hint cell
        if field.hint:
            ws_inputs.range(f"C{row}").value = f"  {field.hint}"
            ws_inputs.range(f"C{row}").font.italic = True
            ws_inputs.range(f"C{row}").font.color = (150, 150, 150)

        # Choices dropdown hint
        if field.choices:
            ws_inputs.range(f"C{row}").value = (
                f"  Options: {', '.join(field.choices)}"
                + (f"  | {field.hint}" if field.hint else "")
            )


def on_clear() -> None:
    """Clear BarList, ReasoningLog, and Validation tabs."""
    try:
        book = _get_book()
        book.sheets["BarList"].range("A9:Q68").clear_contents()
        book.sheets["BarList"].range("A9:Q68").color = None
        book.sheets["ReasoningLog"].range("A2:D2000").clear_contents()
        book.sheets["Validation"].range("A3:B2000").clear_contents()

        ws_dash = book.sheets["Dashboard"]
        ws_dash.range("B8").value = "✓ Ready"
        ws_dash.range("B8").font.color = (46, 125, 50)
    except Exception:
        raise


def on_export_csv(out_dir: str | None = None) -> str:
    """
    Export the BarList tab to a barlist.csv file.
    Returns the path written.  Compatible with the pipeline's OUTPUT_CONTRACT.
    """
    try:
        book = _get_book()
        ws_barlist = book.sheets["BarList"]
        ws_dash    = book.sheets["Dashboard"]

        project_no = (ws_dash.range("B4").value or "project").strip()

        # Vista Steel format: col header row 8, data rows 9-68 (17 cols A-Q)
        header = ["S/H/L", "No.Units", "Per Unit", "Total", "Size", "Grade",
                  "Length", "Mark", "Type", "A", "B", "C'", "D", "E", "F", "G", "H"]
        data = ws_barlist.range("A9:Q68").value or []
        rows = [header] + [r for r in data if r and any(
            c is not None and c != "" for c in r[:8]
        )]

        if out_dir is None:
            out_dir = os.path.join(
                os.path.dirname(__file__), "..", "out", project_no
            )
        os.makedirs(out_dir, exist_ok=True)

        path = os.path.join(out_dir, "barlist.csv")
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(rows)

        ws_dash.range("B8").value = f"✓ Exported → {path}"
        return path

    except Exception:
        raise


# ---------------------------------------------------------------------------
# Feature A: Log corrections from edited BarList
# ---------------------------------------------------------------------------

def on_log_corrections() -> None:
    """
    Compare the current BarList contents against the last stored run for this
    template and record any changed rows as corrections.

    Called by the LogCorrections button (or on workbook close).
    """
    try:
        book = _get_book()
        ws_barlist = book.sheets["BarList"]
        ws_dash    = book.sheets["Dashboard"]

        from vistadetail.engine.correction_store import CorrectionStore
        from vistadetail.engine.schema import BarRow
        import json, sqlite3

        store = CorrectionStore()

        # Read current BarList rows
        data = ws_barlist.range("A2:K2000").value or []
        current_bars: list[BarRow] = []
        for row in data:
            if not row or row[0] is None:
                continue
            try:
                current_bars.append(BarRow(
                    mark=str(row[0]), size=str(row[1]),
                    qty=int(row[2] or 0),
                    length_in=_parse_ft_in(str(row[3] or "0")),
                    shape=str(row[4] or "Str"),
                    notes=str(row[8] or ""),   # col 8 = Notes (not 7 = Leg C)
                    ref=str(row[9] or ""),
                ))
            except Exception:
                continue

        if not current_bars:
            return

        # Get last run_id for the selected template
        template_name = ws_dash.range("B3").value or ""
        with sqlite3.connect(store.db_path) as conn:
            row = conn.execute(
                "SELECT id, bars_json FROM runs WHERE template_name=? ORDER BY id DESC LIMIT 1",
                (template_name,)
            ).fetchone()

        if row is None:
            ws_dash.range("B8").value = "No prior run found to diff against"
            return

        run_id, bars_json = row
        original_bars = [
            BarRow(
                mark=d["mark"], size=d["size"], qty=d["qty"],
                length_in=d["length_in"], shape=d["shape"], notes=d["notes"],
            )
            for d in json.loads(bars_json)
        ]

        n = store.log_corrections_from_diff(run_id, original_bars, current_bars)
        ws_dash.range("B8").value = f"✓ {n} correction(s) logged"

    except Exception as exc:
        raise


def _parse_ft_in(s: str) -> float:
    """
    Parse a feet-inches string back to decimal inches.

    Handles formats produced by fmt_inches():
        "13'-9"    → 165.0
        "7'-1 4/8" → 85.5
        "6'-11"    → 83.0
        "0'-5"     →  5.0
    """
    import re
    s = s.strip().replace('"', '')   # strip trailing double-quote only
    # Pattern: feet ' - inches [frac_num / frac_den]
    m = re.match(r"(\d+)'-(\d+)(?:\s+(\d+)/(\d+))?", s)
    if m:
        ft      = int(m.group(1))
        inches  = int(m.group(2))
        if m.group(3) and m.group(4):
            inches += int(m.group(3)) / int(m.group(4))
        return ft * 12 + inches
    # Fallback: bare number treated as feet
    try:
        return float(s) * 12
    except ValueError:
        return 0.0


# ---------------------------------------------------------------------------
# Feature C: Show template confidence on Dashboard
# ---------------------------------------------------------------------------

def on_show_confidence() -> None:
    """
    Write an all-templates confidence/acceptance table to Dashboard rows 18+.
    Rows 1-16 are the fixed layout (inputs, buttons, results, secondary buttons).
    Row 17 is a spacer.  Row 18+ is safe to use for this supplemental table.
    """
    try:
        book = _get_book()
        ws_dash = book.sheets["Dashboard"]

        from vistadetail.engine.correction_store import CorrectionStore
        store = CorrectionStore()
        all_conf = store.get_all_confidence()

        # Row 18 = section header, row 19 = column headers, rows 20+ = data
        start = 18
        ws_dash.range(f"A{start}:D{start + 30}").clear_contents()
        ws_dash.range(f"A{start}:D{start + 30}").color = None

        # Section title
        ws_dash.range(f"A{start}").value = "TEMPLATE ACCEPTANCE HISTORY"
        ws_dash.range(f"A{start}").font.bold = True
        ws_dash.range(f"A{start}").font.color = (28, 52, 97)   # navy

        # Column headers
        ws_dash.range(f"A{start + 1}").value = [
            ["Template", "Uses", "Accepted", "Acceptance %"]
        ]
        for col in ("A", "B", "C", "D"):
            cell = ws_dash.range(f"{col}{start + 1}")
            cell.font.bold = True
            cell.color = (242, 242, 242)

        if not all_conf:
            ws_dash.range(f"A{start + 2}").value = "No history yet — generate a barlist first."
            ws_dash.range(f"A{start + 2}").font.italic = True
            return

        for i, c in enumerate(all_conf):
            row = start + 2 + i
            pct = c.acceptance_pct
            colour = (46, 125, 50) if pct >= 90 else \
                     (245, 124, 0) if pct >= 70 else \
                     (198, 40, 40)
            ws_dash.range(f"A{row}").value = [
                [c.template_name, c.uses, c.accepted_runs, f"{pct:.1f}%"]
            ]
            ws_dash.range(f"D{row}").font.color = colour
            ws_dash.range(f"D{row}").font.bold = True

    except Exception:
        raise


# ---------------------------------------------------------------------------
# Feature D: Multi-structure composer
# ---------------------------------------------------------------------------

def on_compose_project() -> None:
    """
    Read the _Templates tab and run the multi-structure composer.

    _Templates tab layout (maintained by SetupDropdowns VBA + patch_workbook.py):
      Rows 1-21  — template names for the Dashboard B3 dropdown (col A only)
      Row  22    — blank separator
      Row  23    — "COMPOSE PROJECT INPUT AREA" heading
      Row  24    — column headers: Prefix | Template | Label | key1 | val1 | …
      Row  25    — example / hint row (italic grey)
      Row  26+   — USER DATA — one row per structure to compose:
                     Col A: Prefix   (e.g. "HW")
                     Col B: Template (e.g. "Straight Headwall")
                     Col C: Label    (e.g. "Headwall – Sta 12+50")
                     Col D+: alternating key / value param overrides
                             e.g. D="wall_width_ft"  E=8  F="wall_height_ft"  G=5

    Rows with empty col B, or col B not matching a template name, are silently skipped.
    Any param not listed uses the template default.
    Output is written to BarList + ReasoningLog exactly like a single generate.
    """
    try:
        import xlwings as xw
        book = _get_book()
        ws_dash       = book.sheets["Dashboard"]
        ws_barlist    = book.sheets["BarList"]
        ws_log        = book.sheets["ReasoningLog"]
        ws_validation = book.sheets["Validation"]

        # Find _Templates sheet
        sheet_names = [s.name for s in book.sheets]
        if "_Templates" not in sheet_names:
            xw.apps.active.alert(
                "No '_Templates' sheet found.\n"
                "Create a sheet named '_Templates' with columns:\n"
                "  A=Prefix  B=Template  C=Label  D/E=key/val overrides...",
                "Rebar Generator"
            )
            return

        ws_tpl = book.sheets["_Templates"]
        # Rows 1-25 are template-name list + compose header block.
        # User compose data starts at row 26. Rows with empty/non-matching col B
        # are silently skipped by the loop below, so reading from row 4 is safe.
        raw = ws_tpl.range("A4:Z80").value or []

        from vistadetail.engine.composer import Composer
        from vistadetail.engine.reasoning_logger import ReasoningLogger
        from vistadetail.engine.templates import TEMPLATE_REGISTRY

        comp = Composer()
        for row in raw:
            if not row or not row[0] or not row[1]:
                continue
            prefix   = str(row[0]).strip()
            tpl_name = str(row[1]).strip()
            label    = str(row[2]).strip() if row[2] else ""

            # Skip header/hint rows silently
            if tpl_name not in TEMPLATE_REGISTRY:
                continue

            # Build param overrides from alternating key/value columns (D onwards)
            params: dict = {}
            for i in range(3, len(row) - 1, 2):
                key = row[i]
                val = row[i + 1]
                if key and val is not None:
                    params[str(key).strip()] = val

            comp.add(tpl_name, prefix, params, label=label or f"{prefix} ({tpl_name})")

        if comp.slot_count == 0:
            xw.apps.active.alert(
                "No valid structures found in _Templates sheet.\n"
                "Check that column A (Prefix) and column B (Template name) are filled.",
                "Rebar Generator"
            )
            return

        # Run
        log = ReasoningLogger(ws_log)
        log.clear()
        result = comp.generate(log, call_ai=False)

        # Write combined bar list
        _write_barlist_to_sheet(ws_barlist, result.combined)
        _write_validation_to_sheet(ws_validation, result.combined)

        # Status
        total_qty = result.total_qty()
        from vistadetail.engine.calculator import barlist_total_weight_lb
        weight = barlist_total_weight_lb(result.combined)
        structure_summary = "  +  ".join(
            f"{s['prefix']}({s['total_qty']})" for s in result.per_structure_summary()
        )
        ws_dash.range("B8").value = (
            f"✓ COMPOSED  {len(result.slots)} structures  |  "
            f"{result.mark_count()} marks  |  {total_qty} bars  |  {weight:.0f} lb\n"
            f"  {structure_summary}"
        )
        ws_dash.range("B8").font.color = (13, 71, 161)   # blue — distinct from single generate
        ws_barlist.activate()

    except Exception as exc:
        try:
            book = _get_book()
            book.sheets["Dashboard"].range("B8").value = f"⚠ Compose error: {exc}"
            book.sheets["Dashboard"].range("B8").font.color = (198, 40, 40)
        except Exception:
            pass
        raise


# ---------------------------------------------------------------------------
# Feature E: Run cut optimizer and write CutList tab
# ---------------------------------------------------------------------------

def on_cut_optimize(stock_lengths_ft: list[int] | None = None) -> None:
    """
    Read the current BarList (Vista Steel format, rows 9-68),
    run the cut optimizer, write a richly formatted plan to the CutList sheet.
    """
    try:
        import xlwings as xw
        book      = _get_book()
        ws_barlist = book.sheets["BarList"]
        ws_dash    = book.sheets["Dashboard"]

        from vistadetail.engine.cut_optimizer import (
            optimize_cuts, optimize_cuts_from_barlist, CutRequest,
        )
        from vistadetail.engine.schema import BarRow
        from vistadetail.workbook.barlist_layout import DATA_START, DATA_ROWS

        # ── Read bars from the new Vista Steel BarList format (A9:Q68) ──
        # Col layout: A=SHL B=Units C=PerUnit D=Total E=Size F=Grade
        #             G=Length H=Mark I=Type J-Q=legs A-H
        data_end  = DATA_START + DATA_ROWS - 1
        raw = ws_barlist.range(f"A{DATA_START}:Q{data_end}").value or []

        bars: list[BarRow] = []
        requests: list[CutRequest] = []
        for row in raw:
            if not row or all(c is None or c == "" for c in row[:8]):
                continue
            try:
                mark    = str(row[7] or "").strip()   # H: MARK
                size    = str(row[4] or "").strip()   # E: SIZE
                qty_raw = row[3]                       # D: TOTAL
                len_raw = str(row[6] or "").strip()   # G: LENGTH
                if not mark or not size or not len_raw:
                    continue
                qty     = int(float(qty_raw or 0))
                len_in  = _parse_ft_in(len_raw)
                if qty <= 0 or len_in <= 0:
                    continue
                bars.append(BarRow(mark=mark, size=size, qty=qty,
                                   length_in=len_in, shape="Str"))
                requests.append(CutRequest(size, len_in, qty))
            except Exception:
                continue

        if not bars:
            ws_dash.range("B8").value = "⚠ BarList is empty — generate first"
            return

        # Default stock lengths: 20 and 40 ft enabled, 60 ft disabled
        if stock_lengths_ft is None:
            stock_lengths_ft = [20, 40]

        plan = optimize_cuts_from_barlist(bars, stock_lengths_ft=stock_lengths_ft)

        # ── Get or create CutList sheet ───────────────────────────────────
        sheet_names = [s.name for s in book.sheets]
        if "CutList" not in sheet_names:
            book.sheets.add("CutList", after=book.sheets["Validation"])
        ws_cut = book.sheets["CutList"]
        ws_cut.range("A1:J2000").clear_contents()
        ws_cut.range("A1:J2000").color = None
        # Hide gridlines via xlwings .api (COM on Windows, appscript on Mac)
        try:
            ws_cut.api.DisplayGridlines = False   # Windows COM
        except Exception:
            try:
                ws_cut.api.display_gridlines = False   # macOS appscript
            except Exception:
                pass  # non-critical cosmetic setting

        # ── Colour constants (RGB tuples for xlwings) ─────────────────────
        _NAVY  = (28,  52,  97)
        _BLUE  = (46, 117, 182)
        _WHITE = (255, 255, 255)
        _GOLD  = (255, 217, 102)
        _GRAY  = (242, 242, 242)
        _GREEN = (198, 239, 206)
        _RED   = (255, 199, 206)
        _HDR   = (68, 114, 196)
        _ALT   = (248, 251, 255)

        # ── Column widths ─────────────────────────────────────────────────
        ws_cut.range("A:A").column_width = 13
        ws_cut.range("B:B").column_width = 16
        ws_cut.range("C:C").column_width = 16
        ws_cut.range("D:D").column_width = 16
        ws_cut.range("E:E").column_width = 12
        ws_cut.range("F:F").column_width = 12
        ws_cut.range("G:G").column_width = 10

        # ── Helper: write a section header row ────────────────────────────
        def _sec_hdr(row: int, text: str, n_cols: int = 7) -> int:
            end_col = chr(ord("A") + n_cols - 1)
            rng = ws_cut.range(f"A{row}:{end_col}{row}")
            rng.merge()
            rng.value = text
            rng.font.bold  = True
            rng.font.size  = 11
            rng.font.color = _WHITE
            rng.color      = _NAVY
            rng.row_height = 22
            return row + 1

        def _col_hdr(row: int, headers: list[str]) -> int:
            ws_cut.range(f"A{row}").value = [headers]
            rng = ws_cut.range(f"A{row}:{chr(ord('A')+len(headers)-1)}{row}")
            rng.font.bold  = True
            rng.font.color = _WHITE
            rng.color      = _HDR
            rng.row_height = 18
            return row + 1

        def _data_row(row: int, values: list, colour=None) -> int:
            ws_cut.range(f"A{row}").value = [values]
            if colour:
                n = len(values)
                ws_cut.range(f"A{row}:{chr(ord('A')+n-1)}{row}").color = colour
            ws_cut.range(f"A{row}:G{row}").row_height = 16
            return row + 1

        def _blank(row: int) -> int:
            ws_cut.range(f"A{row}:G{row}").row_height = 8
            return row + 1

        def _totals_row(row: int, label: str, value) -> int:
            ws_cut.range(f"A{row}").value = label
            ws_cut.range(f"B{row}").value = value
            ws_cut.range(f"A{row}").font.bold = True
            ws_cut.range(f"A{row}:G{row}").row_height = 16
            return row + 1

        # ── Row 1: Title banner ───────────────────────────────────────────
        r = 1
        ws_cut.range("A1:G1").merge()
        ws_cut.range("A1").value     = ("CUT LIST OPTIMIZER  |  "
                                        "Minimum Waste Bar Cutting Plan (Feature E)")
        ws_cut.range("A1").font.bold = True
        ws_cut.range("A1").font.size = 13
        ws_cut.range("A1").font.color = _WHITE
        ws_cut.range("A1").color      = _NAVY
        ws_cut.range("A1").api.HorizontalAlignment = -4108  # xlCenter
        ws_cut.range("A1:G1").row_height = 28
        r = 2

        # ── Row 2: Subtitle ───────────────────────────────────────────────
        ws_cut.range("A2:G2").merge()
        ws_cut.range("A2").value = ("Optimal cut patterns from stock lengths. "
                                    "Minimizes waste and material cost.")
        ws_cut.range("A2").font.italic = True
        ws_cut.range("A2").font.color  = _WHITE
        ws_cut.range("A2").color       = _BLUE
        ws_cut.range("A2").api.HorizontalAlignment = -4108
        ws_cut.range("A2:G2").row_height = 18
        r = _blank(3)

        # ── STOCK LENGTHS section ─────────────────────────────────────────
        r = _sec_hdr(r, "STOCK LENGTHS", n_cols=3)
        r = _col_hdr(r, ["Stock Option", "Length (ft)", "Use?"])
        stock_labels = ["Stock A", "Stock B", "Stock C"]
        all_stocks   = [20, 40, 60]
        for label, length in zip(stock_labels, all_stocks):
            use = "Yes" if length in stock_lengths_ft else "No"
            c   = _GRAY if use == "No" else None
            r   = _data_row(r, [label, length, use], colour=c)
        r = _blank(r)

        # ── REQUIRED CUTS section ─────────────────────────────────────────
        r = _sec_hdr(r, "REQUIRED CUTS (from BarList)", n_cols=4)
        r = _col_hdr(r, ["Mark", "Size", "Req Length (ft)", "Qty Needed"])
        # Unique bars (deduplicated by mark)
        seen: set[str] = set()
        for bar in bars:
            if bar.mark not in seen:
                seen.add(bar.mark)
                r = _data_row(r, [bar.mark, bar.size,
                                   round(bar.length_in / 12, 4), bar.qty])
        r = _blank(r)

        # ── PER-SIZE optimized sections ───────────────────────────────────
        waste_pcts = plan.waste_pct()
        for size in sorted(plan.by_size.keys()):
            size_bars = plan.by_size[size]
            if not size_bars:
                continue
            stock_len_ft = round(size_bars[0].stock_len_in / 12, 1)

            title = (f"OPTIMIZED CUT PLAN — {size} Bars "
                     f"({int(stock_len_ft)}ft Stock)")
            r = _sec_hdr(r, title)
            r = _col_hdr(r, ["Stock Bar #", "Cut 1", "Cut 2", "Cut 3",
                              "Used (ft)", "Waste (ft)", "Waste %"])

            for idx, sbar in enumerate(size_bars, start=1):
                # Determine which mark this cut belongs to by matching length
                def _cut_label(length_in: float) -> str:
                    for req in requests:
                        if req.size == size and abs(req.length_in - length_in) < 0.5:
                            # Find matching mark from bars
                            for b in bars:
                                if b.size == size and abs(b.length_in - length_in) < 0.5:
                                    return f"{b.mark} → {round(length_in/12, 4)}ft"
                    return f"{round(length_in/12, 4)}ft"

                cut_labels = [_cut_label(c) for c in sbar.cuts]
                while len(cut_labels) < 3:
                    cut_labels.append("—")

                used_ft  = round((sbar.stock_len_in - sbar.waste_in) / 12, 2)
                waste_ft = round(sbar.waste_in / 12, 2)
                waste_pct_val = round(sbar.waste_in / sbar.stock_len_in * 100, 1)
                waste_str = f"{waste_pct_val}%"

                # Colour by waste severity
                if waste_pct_val >= 50:
                    row_colour = _RED
                elif waste_pct_val <= 15:
                    row_colour = _GREEN
                elif idx % 2 == 0:
                    row_colour = _ALT
                else:
                    row_colour = None

                r = _data_row(r, [f"Bar {idx:02d}",
                                   cut_labels[0], cut_labels[1], cut_labels[2],
                                   used_ft, waste_ft, waste_str],
                              colour=row_colour)

            # Totals block
            r = _blank(r)
            ws_cut.range(f"A{r}:G{r}").color      = (220, 230, 255)
            ws_cut.range(f"A{r}").value            = f"TOTALS — {size}"
            ws_cut.range(f"A{r}").font.bold        = True
            ws_cut.range(f"A{r}:G{r}").row_height  = 18
            r += 1

            n_bars     = len(size_bars)
            total_mat  = round(n_bars * size_bars[0].stock_len_in / 12, 1)
            total_used = round(sum(
                (b.stock_len_in - b.waste_in) / 12 for b in size_bars
            ), 1)
            total_wst  = round(sum(b.waste_in / 12 for b in size_bars), 1)
            ovr_waste  = f"{waste_pcts.get(size, 0):.1f}%"

            r = _totals_row(r, "Stock bars needed:", n_bars)
            r = _totals_row(r, "Total material (ft):", total_mat)
            r = _totals_row(r, "Total used (ft):", total_used)
            r = _totals_row(r, "Total waste (ft):", total_wst)
            r = _totals_row(r, "Overall waste %:", ovr_waste)
            r = _blank(r)

        # ── OPTIMIZATION NOTES ────────────────────────────────────────────
        notes = plan.generate_notes(requests=requests,
                                    stock_lengths_ft=stock_lengths_ft)
        r = _blank(r)
        ws_cut.range(f"A{r}:G{r}").merge()
        ws_cut.range(f"A{r}").value      = "OPTIMIZATION NOTES"
        ws_cut.range(f"A{r}").font.bold  = True
        ws_cut.range(f"A{r}").font.size  = 11
        ws_cut.range(f"A{r}").color      = _GOLD
        ws_cut.range(f"A{r}:G{r}").row_height = 20
        r += 1
        for note in notes:
            ws_cut.range(f"A{r}:G{r}").merge()
            ws_cut.range(f"A{r}").value     = note
            ws_cut.range(f"A{r}").font.size = 10
            ws_cut.range(f"A{r}").color     = (255, 248, 220)
            ws_cut.range(f"A{r}:G{r}").row_height = 18
            r += 1

        ws_cut.activate()
        n_marks = len({b.mark for b in bars})
        n_total = sum(b.qty for b in bars)
        ws_dash.range("B8").value = (
            f"✓ Cut list generated — {n_marks} marks, {n_total} bars total"
        )
        ws_dash.range("B8").font.color = (0, 102, 0)

    except Exception:
        raise


# ---------------------------------------------------------------------------
# Feature G: Gold CSV override — save / clear from Excel
# ---------------------------------------------------------------------------

def on_export_gold() -> None:
    """
    Save the current BarList as a permanent gold override CSV for this template.
    Next Generate run will return the gold output instead of re-computing.
    Called by the SAVE AS GOLD button on Dashboard.
    """
    try:
        book = _get_book()
        ws_dash    = book.sheets["Dashboard"]
        ws_barlist = book.sheets["BarList"]

        tpl_name = ws_dash.range("B3").value
        if not tpl_name:
            ws_dash.range("B8").value = "⚠ No template selected"
            return

        data = ws_barlist.range("A2:K500").value or []
        rows = [r for r in data if r and r[0]]
        if not rows:
            ws_dash.range("B8").value = "⚠ BarList is empty — generate first"
            return

        import csv as _csv
        import pathlib
        from vistadetail.engine.gold_overrides import _OVERRIDES_DIR, override_path
        _OVERRIDES_DIR.mkdir(parents=True, exist_ok=True)
        path = override_path(tpl_name)
        header = ["Mark", "Size", "Qty", "Length", "Shape",
                  "Leg A", "Leg B", "Leg C", "Notes", "Ref", "Review Flag"]
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = _csv.writer(f)
            writer.writerow(header)
            for row in rows:
                writer.writerow([
                    row[0] or "", row[1] or "", int(row[2] or 0),
                    row[3] or "", row[4] or "Str",
                    row[5] or "", row[6] or "", row[7] or "",
                    row[8] or "", row[9] or "", row[10] or "",
                ])

        ws_dash.range("B8").value = (
            f"⭐ Gold override saved for '{tpl_name}'  ({len(rows)} rows)"
        )
        ws_dash.range("B8").font.color = (0, 102, 0)

    except Exception:
        raise


def on_clear_gold() -> None:
    """
    Delete the gold override for the current template, restoring computed output.
    Called by the CLEAR GOLD button on Dashboard.
    """
    try:
        book   = _get_book()
        ws_dash = book.sheets["Dashboard"]

        tpl_name = ws_dash.range("B3").value
        if not tpl_name:
            ws_dash.range("B8").value = "⚠ No template selected"
            return

        from vistadetail.engine.gold_overrides import delete_gold_override, override_path
        deleted = delete_gold_override(tpl_name)

        if deleted:
            ws_dash.range("B8").value = (
                f"✓ Gold override cleared for '{tpl_name}' — using computed output"
            )
        else:
            ws_dash.range("B8").value = (
                f"ℹ No gold override found for '{tpl_name}'"
            )
        ws_dash.range("B8").font.color = (46, 125, 50)

    except Exception:
        raise


# ---------------------------------------------------------------------------
# Headless runner — no Excel required (for testing / CLI)
# ---------------------------------------------------------------------------

def run_headless(
    template_name: str,
    params: dict,
    *,
    call_ai: bool = False,
    out_path: str | None = None,
) -> list:
    """
    Run the engine without Excel.  Returns list of BarRow objects.
    Optionally writes barlist.csv to out_path.
    """
    from vistadetail.engine.calculator import barlist_to_rows, generate_barlist
    from vistadetail.engine.reasoning_logger import ReasoningLogger
    from vistadetail.engine.templates import TEMPLATE_REGISTRY

    template = TEMPLATE_REGISTRY[template_name]
    log = ReasoningLogger(None)   # console output
    bars = generate_barlist(template, params, log, call_ai=call_ai)

    if out_path:
        rows = barlist_to_rows(bars)
        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows(rows)

    return bars
