"""
Core data types for the VistaDetail rebar engine.

BarRow     — one mark/size/qty/length entry in the generated bar list
InputField — describes a user-facing input slot in a template
Params     — validated, typed parameter bundle passed to rule functions
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Bar size constants
# ---------------------------------------------------------------------------

BAR_SIZES = ["#3", "#4", "#5", "#6", "#7", "#8", "#9", "#10", "#11"]

HOOK_TYPES = ["std_90", "std_180", "none"]


# ---------------------------------------------------------------------------
# Input field descriptor
# ---------------------------------------------------------------------------

@dataclass
class InputField:
    name: str
    dtype: type                          # float | int | str | bool
    label: str = ""                      # human-readable label for Excel
    min: float | None = None
    max: float | None = None
    choices: list[str] | None = None     # for enum-style fields
    default: Any = None
    hint: str = ""                       # shown as tooltip in Excel
    group: str = ""                      # optional section header (shown when group changes)

    def validate(self, value: Any) -> Any:
        """Cast and validate a raw value. Raises ValueError on failure."""
        if self.choices is not None:
            # Choices are always strings in the schema; compare string representation
            if str(value) not in self.choices:
                raise ValueError(
                    f"{self.name}: '{value}' not in {self.choices}"
                )
            # Cast the string choice value to the proper dtype
            v = self.dtype(str(value))
            if self.min is not None and v < self.min:
                raise ValueError(f"{self.name}: {v} < min {self.min}")
            if self.max is not None and v > self.max:
                raise ValueError(f"{self.name}: {v} > max {self.max}")
            return v

        try:
            v = self.dtype(value)
        except (TypeError, ValueError):
            raise ValueError(f"{self.name}: cannot cast '{value}' to {self.dtype.__name__}")

        if self.min is not None and v < self.min:
            raise ValueError(f"{self.name}: {v} < min {self.min}")
        if self.max is not None and v > self.max:
            raise ValueError(f"{self.name}: {v} > max {self.max}")

        return v


# ---------------------------------------------------------------------------
# Params — validated parameter bundle
# ---------------------------------------------------------------------------

class Params:
    """Typed, validated parameter bundle.  Attributes set dynamically by template."""

    def __init__(self, validated: dict[str, Any]):
        for k, v in validated.items():
            setattr(self, k, v)
        self._raw = validated

    def to_dict(self) -> dict[str, Any]:
        return dict(self._raw)

    def get(self, key: str, default: Any = None) -> Any:
        return self._raw.get(key, default)


# ---------------------------------------------------------------------------
# BarRow — one entry in the generated bar list
# ---------------------------------------------------------------------------

@dataclass
class BarRow:
    mark: str                           # e.g. "H1", "V1", "C1"
    size: str                           # e.g. "#5"
    qty: int
    length_in: float                    # always stored in inches internally
    shape: str = "Str"                  # "Str", "L", "U", "Hook"
    leg_a_in: float | None = None       # for shaped bars
    leg_b_in: float | None = None
    leg_c_in: float | None = None
    leg_d_in: float | None = None       # bend chart D dimension (e.g. S6 hoops)
    leg_g_in: float | None = None       # bend chart G dimension (e.g. S6 hoops)
    notes: str = ""
    ref: str = ""                       # Feature F: shop drawing reference pin (e.g. "Sht 3, Det 4/S3")
    source_rule: str = ""               # which rule produced this row
    review_flag: str = ""               # non-empty = needs detailer review

    # ── Formatted accessors ──────────────────────────────────────────────

    @property
    def length_ft_in(self) -> str:
        """Return length as feet-inches string, e.g. 13'-6"."""
        return fmt_inches(self.length_in)

    @property
    def leg_a_ft_in(self) -> str:
        return fmt_inches(self.leg_a_in) if self.leg_a_in is not None else ""

    @property
    def leg_b_ft_in(self) -> str:
        return fmt_inches(self.leg_b_in) if self.leg_b_in is not None else ""

    @property
    def leg_c_ft_in(self) -> str:
        return fmt_inches(self.leg_c_in) if self.leg_c_in is not None else ""

    @property
    def leg_d_ft_in(self) -> str:
        return fmt_inches(self.leg_d_in) if self.leg_d_in is not None else ""

    @property
    def leg_g_ft_in(self) -> str:
        return fmt_inches(self.leg_g_in) if self.leg_g_in is not None else ""

    def to_row(self) -> list[Any]:
        """Flat list for writing to Excel / CSV."""
        return [
            self.mark,
            self.size,
            self.qty,
            self.length_ft_in,
            self.shape,
            self.leg_a_ft_in,
            self.leg_b_ft_in,
            self.leg_c_ft_in,
            self.notes,
            self.ref,            # Feature F: shop drawing reference pin
            self.review_flag,
        ]


# ---------------------------------------------------------------------------
# Utility formatters
# ---------------------------------------------------------------------------

def fmt_inches(total_in: float) -> str:
    """Convert decimal inches to feet-inches string: 81.0 → 6'-9"."""
    if total_in is None:
        return ""
    feet = int(total_in // 12)
    inches = total_in % 12
    # round to nearest 1/8 inch
    frac = round(inches * 8) / 8
    # carry over if rounding pushes inches to 12 (e.g. 59.996 → 5'-0" not 4'-12")
    if frac >= 12.0:
        feet += 1
        frac = 0.0
    if frac == int(frac):
        inch_str = f'{int(frac)}"'
    else:
        whole = int(frac)
        num = round((frac - whole) * 8)
        inch_str = f'{whole} {num}/8"'
    if feet == 0:
        return f'0\'-{inch_str}'
    return f"{feet}'-{inch_str}"


def fmt_ft(ft: float) -> str:
    """Round to nearest 1/8-inch and format as feet-inches."""
    return fmt_inches(ft * 12)
