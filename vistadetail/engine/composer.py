"""
Feature D: Multi-Structure Composer.

Lets detailers stack multiple templates into one project (e.g. an inlet
that has a headwall + two wing walls + a spread footing).

Each structure gets a mark namespace prefix so marks never collide:
  Inlet:    I_H1, I_V1, I_C1
  Headwall: HW_FF1, HW_FF2 ...
  Wing L:   WL_WH1, WL_WV1 ...
  Footing:  FT_BT1, FT_BL1 ...

The composer:
  1. Runs each child template through generate_barlist
  2. Prefixes all marks
  3. Merges the combined bar lists
  4. Returns one flat list + a per-structure breakdown for reporting

Usage:
    from vistadetail.engine.composer import Composer, StructureSlot

    comp = Composer()
    comp.add("Inlet – 9in Wall", "I", inlet_params)
    comp.add("Headwall",          "HW", hw_params)
    comp.add("Wing Wall",         "WL", wing_params_left)
    comp.add("Wing Wall",         "WR", wing_params_right)
    comp.add("Spread Footing",    "FT", footing_params)

    combined, breakdown = comp.generate(log)
"""

from __future__ import annotations

from dataclasses import dataclass, field

from vistadetail.engine.calculator import generate_barlist
from vistadetail.engine.reasoning_logger import ReasoningLogger
from vistadetail.engine.schema import BarRow
from vistadetail.engine.templates import TEMPLATE_REGISTRY


@dataclass
class StructureSlot:
    template_name: str
    prefix: str        # mark namespace prefix, e.g. "HW" → "HW_FF1"
    params: dict
    label: str = ""    # human label for log/report

    def __post_init__(self):
        if not self.label:
            self.label = f"{self.prefix} ({self.template_name})"


@dataclass
class ComposedResult:
    """Combined result from a multi-structure generation."""
    combined: list[BarRow]                  # flat merged list, prefixed marks
    by_structure: dict[str, list[BarRow]]   # prefix → bars for that structure
    slots: list[StructureSlot]              # original slot definitions

    def mark_count(self) -> int:
        return len({b.mark for b in self.combined})

    def total_qty(self) -> int:
        return sum(b.qty for b in self.combined)

    def per_structure_summary(self) -> list[dict]:
        result = []
        for slot in self.slots:
            bars = self.by_structure.get(slot.prefix, [])
            result.append({
                "label":     slot.label,
                "prefix":    slot.prefix,
                "template":  slot.template_name,
                "marks":     len({b.mark for b in bars}),
                "total_qty": sum(b.qty for b in bars),
            })
        return result


class Composer:
    """
    Accumulate structure slots and generate a combined, namespace-safe bar list.
    """

    def __init__(self):
        self._slots: list[StructureSlot] = []

    def add(
        self,
        template_name: str,
        prefix: str,
        params: dict,
        label: str = "",
    ) -> "Composer":
        """Add a structure. Returns self for chaining."""
        prefix = prefix.upper().strip("_")  # normalise
        self._slots.append(StructureSlot(
            template_name=template_name,
            prefix=prefix,
            params=params,
            label=label,
        ))
        return self

    def generate(
        self,
        log: ReasoningLogger,
        call_ai: bool = True,
    ) -> ComposedResult:
        """
        Run all slots, apply mark prefixes, merge into combined list.
        """
        combined: list[BarRow] = []
        by_structure: dict[str, list[BarRow]] = {}

        for slot in self._slots:
            template = TEMPLATE_REGISTRY.get(slot.template_name)
            if template is None:
                log.warn(f"Unknown template '{slot.template_name}' for prefix '{slot.prefix}' — skipped")
                continue

            log.section(f"STRUCTURE: {slot.label}")
            bars = generate_barlist(template, slot.params, log, call_ai=call_ai)

            # Apply mark prefix
            prefixed = _apply_prefix(bars, slot.prefix)
            by_structure[slot.prefix] = prefixed
            combined.extend(prefixed)
            log.blank()

        # Resolve any remaining mark collisions (e.g. same prefix used twice)
        combined = _resolve_collisions(combined)

        return ComposedResult(
            combined=combined,
            by_structure=by_structure,
            slots=list(self._slots),
        )

    def clear(self) -> None:
        self._slots.clear()

    @property
    def slot_count(self) -> int:
        return len(self._slots)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _apply_prefix(bars: list[BarRow], prefix: str) -> list[BarRow]:
    """Return new BarRow list with mark prefixed: 'H1' → 'I_H1'."""
    result = []
    for b in bars:
        import dataclasses
        new_bar = dataclasses.replace(b, mark=f"{prefix}_{b.mark}")
        result.append(new_bar)
    return result


def _resolve_collisions(bars: list[BarRow]) -> list[BarRow]:
    """
    If two bars share a mark (shouldn't happen with prefixes, but belt-and-suspenders),
    append a numeric suffix to the second.
    """
    seen: dict[str, int] = {}
    result = []
    import dataclasses
    for b in bars:
        if b.mark in seen:
            seen[b.mark] += 1
            new_bar = dataclasses.replace(b, mark=f"{b.mark}_{seen[b.mark]}")
        else:
            seen[b.mark] = 0
            new_bar = b
        result.append(new_bar)
    return result
