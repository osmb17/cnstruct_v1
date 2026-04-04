"""
ReasoningLogger — streams computation steps in real time to Excel (via xlwings)
with a graceful plain-text fallback when xlwings is unavailable.

Usage:
    # With xlwings (live Excel)
    import xlwings as xw
    sheet = xw.Book("VistaDetail.xlsm").sheets["ReasoningLog"]
    log = ReasoningLogger(sheet)

    # Without xlwings (console / testing)
    log = ReasoningLogger(None)
"""

from __future__ import annotations

import sys
from datetime import datetime
from typing import Any


def _now() -> str:
    return datetime.now().strftime("%H:%M:%S")


# ANSI colours for console fallback
_RESET  = "\033[0m"
_CYAN   = "\033[36m"
_YELLOW = "\033[33m"
_RED    = "\033[31m"
_DIM    = "\033[2m"


class ReasoningLogger:
    """
    Write timestamped log lines to:
      - Excel sheet (via xlwings) if a sheet is provided
      - stdout otherwise

    Row layout in Excel (5 columns):
      Col A: Timestamp   Col B: Tag   Col C: Message
      Col D: Detail / Formula   Col E: Source
    """

    HEADER_ROW = 1   # row 1 = column headers; data starts at row 2

    # Background colours for Excel cells (RGB tuples)
    _COLOUR_AI      = (255, 255, 200)   # pale yellow  — Claude notes
    _COLOUR_WARN    = (255, 220, 200)   # pale orange  — warnings
    _COLOUR_HDR     = (220, 230, 255)   # pale blue    — section headers
    _COLOUR_LEARNED = (200, 240, 215)   # pale green   — learned adjustments
    _COLOUR_NONE    = None              # default / no fill

    def __init__(self, sheet: Any | None):
        self._sheet = sheet
        self._row = self.HEADER_ROW + 1
        self._lines: list[tuple[str, str, str, str, str]] = []  # (ts, tag, msg, detail, source)

        if sheet is not None:
            try:
                import xlwings as xw  # noqa: F401
                self._xlwings_available = True
                self._init_sheet()
            except ImportError:
                self._xlwings_available = False
                self._sheet = None
        else:
            self._xlwings_available = False

    # ── Public API ──────────────────────────────────────────────────────────

    def section(self, name: str) -> None:
        """Print a section divider (separator row)."""
        self._write(_now(), "────", "━" * 28, detail="", source="",
                    colour=self._COLOUR_HDR, bold=True)

    def rule(self, rule_name: str, description: str, source: str = "Calculator") -> None:
        """Log rule application."""
        self._write(_now(), "RULE", rule_name, detail=description, source=source)

    def step(self, text: str, detail: str = "", source: str = "") -> None:
        """Ordinary computation step."""
        self._write(_now(), "CALC", f"  {text}", detail=detail, source=source)

    def result(self, mark: str, summary: str, detail: str = "", source: str = "BarGenerator") -> None:
        """Finalised bar row."""
        self._write(_now(), "OUT", f"  → {mark}: {summary}",
                    detail=detail, source=source)

    def ok(self, text: str, detail: str = "", source: str = "Validator") -> None:
        """Validation pass."""
        self._write(_now(), "✓ OK", f"  {text}", detail=detail, source=source)

    def ai_note(self, text: str, detail: str = "", source: str = "ClaudeAssistant") -> None:
        """Claude-generated reviewer note."""
        self._write(_now(), "AI ✦", text, detail=detail, source=source,
                    colour=self._COLOUR_AI)

    def learned_adj(self, mark: str, field: str, original, adjusted, count: int) -> None:
        """Applied learned adjustment — shown in pale green."""
        self._write(
            _now(), "◆ LEARN",
            f"  {mark}: {field} {original} → {adjusted}",
            detail=f"learned from {count} prior correction{'s' if count != 1 else ''}",
            source="CorrectionStore",
            colour=self._COLOUR_LEARNED,
        )

    def warn(self, text: str, detail: str = "", source: str = "Validator") -> None:
        """Detailer-facing warning."""
        self._write(_now(), "WARN", text, detail=detail, source=source,
                    colour=self._COLOUR_WARN)

    def init(self, text: str, detail: str = "", source: str = "TemplateLoader") -> None:
        """Initialisation / startup message."""
        self._write(_now(), "INIT", text, detail=detail, source=source)

    def blank(self) -> None:
        """Insert a blank spacer row."""
        self._write("", "", "", detail="", source="")

    def done(self, summary: str, detail: str = "", source: str = "Engine") -> None:
        """Final completion message."""
        self.blank()
        self._write(_now(), "DONE", f"Generation complete — {summary}",
                    detail=detail, source=source, bold=True)

    def clear(self) -> None:
        """Erase all log rows (keep header)."""
        self._lines.clear()
        self._row = self.HEADER_ROW + 1
        if self._sheet is not None and self._xlwings_available:
            self._sheet.range(f"A{self.HEADER_ROW + 1}:E2000").clear_contents()
            self._sheet.range(f"A{self.HEADER_ROW + 1}:E2000").color = None

    def get_lines(self) -> list[tuple[str, str, str, str, str]]:
        """Return all logged lines as (timestamp, tag, message, detail, source) tuples."""
        return list(self._lines)

    # ── Internal helpers ────────────────────────────────────────────────────

    def _init_sheet(self) -> None:
        """Write 5-column headers to row 1 with styling."""
        r = self.HEADER_ROW
        hdr_vals = [["Timestamp", "Tag", "Message", "Detail / Formula", "Source"]]
        self._sheet.range(f"A{r}").value = hdr_vals
        # Style header row: navy bg, white bold text
        _NAVY = (28, 52, 97)
        self._sheet.range(f"A{r}:E{r}").color = _NAVY
        self._sheet.range(f"A{r}:E{r}").font.bold  = True
        self._sheet.range(f"A{r}:E{r}").font.color = (255, 255, 255)
        # Column widths
        self._sheet.range("A:A").column_width = 10
        self._sheet.range("B:B").column_width = 10
        self._sheet.range("C:C").column_width = 52
        self._sheet.range("D:D").column_width = 42
        self._sheet.range("E:E").column_width = 16
        # Note: freeze_panes is set by the openpyxl static builder (reasoning_layout.py)

    def _write(self, ts: str, tag: str, msg: str,
               detail: str = "", source: str = "",
               colour: tuple[int, int, int] | None = None,
               bold: bool = False) -> None:
        self._lines.append((ts, tag, msg, detail, source))

        if self._sheet is not None and self._xlwings_available:
            r = self._row
            self._sheet.range(f"A{r}").value = [
                [ts, tag, msg, detail, source]
            ]
            if colour is not None:
                self._sheet.range(f"A{r}:E{r}").color = colour
            if bold:
                self._sheet.range(f"A{r}:E{r}").font.bold = True
            # Force Excel repaint so user sees each line as it appears
            try:
                import xlwings as xw
                xw.apps.active.screen_updating = True
            except Exception:
                pass
            self._row += 1
        else:
            # Console fallback
            colour_code = ""
            if colour == self._COLOUR_AI:
                colour_code = _YELLOW
            elif colour == self._COLOUR_WARN:
                colour_code = _RED
            elif colour == self._COLOUR_HDR:
                colour_code = _CYAN
            bold_start = "\033[1m" if bold else ""
            src = f"  [{source}]" if source else ""
            print(f"{_DIM}[{ts}]{_RESET} {bold_start}{colour_code}{tag:<8}{_RESET}  {msg}"
                  f"  {_DIM}{detail}{src}{_RESET}",
                  file=sys.stdout)
