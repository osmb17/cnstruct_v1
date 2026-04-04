"""
BaseTemplate — abstract base class for all VistaDetail rebar templates.

Each concrete template subclass defines:
  - inputs:          ordered list of InputField descriptors
  - rules:           ordered list of rule function names
  - claude_triggers: functions that inspect Params and return trigger strings
  - version:         semver string for logging / traceability

Templates are stateless data containers. All state lives in Params + BarRow lists.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Callable

from vistadetail.engine.schema import InputField, Params


@dataclass
class BaseTemplate(ABC):
    name: str = ""
    version: str = "1.0"
    description: str = ""

    # Ordered list of InputField objects (defines the Inputs tab form)
    inputs: list[InputField] = field(default_factory=list)

    # Rule function names in evaluation order (registered in RULE_REGISTRY)
    rules: list[str] = field(default_factory=list)

    def parse_and_validate(self, raw: dict) -> Params:
        """
        Validate and coerce a dict of raw user inputs.
        Raises ValueError with a descriptive message on the first bad field.
        Returns a Params object with fully typed attributes.
        """
        validated: dict = {}
        for f in self.inputs:
            raw_val = raw.get(f.name, f.default)
            if raw_val is None:
                raise ValueError(f"Required input missing: '{f.name}' ({f.label or f.name})")
            validated[f.name] = f.validate(raw_val)
        return Params(validated)

    def evaluate_triggers(self, params: Params) -> list[str]:
        """
        Run all trigger checks and return a list of trigger keys that fired.
        Override in subclasses to add template-specific checks.
        """
        return []

    def input_defaults(self) -> dict:
        """Return a dict of field name → default value for pre-filling the form."""
        return {f.name: f.default for f in self.inputs if f.default is not None}

    def input_labels(self) -> dict[str, str]:
        """Return field name → human label for the Inputs tab."""
        return {f.name: (f.label or f.name) for f in self.inputs}
