"""
Core bar list generator.

generate_barlist(template, params_raw, log) → list[BarRow]

Flow:
  1. Validate raw inputs via template
  2. Run each rule function in order
  3. Assign sequential marks (H1, V1, C1…)
  4. Merge identical rows (same mark/size/length/shape)
  5. Evaluate Claude triggers; call AI for edge-case notes
  6. Optionally log run to CorrectionStore
  7. Return ordered BarRow list
"""

from __future__ import annotations

from vistadetail.engine.claude_assistant import call_claude_for_notes
from vistadetail.engine.gold_overrides import load_gold_override
from vistadetail.engine.reasoning_logger import ReasoningLogger
from vistadetail.engine.rules import RULE_REGISTRY
from vistadetail.engine.schema import BarRow
from vistadetail.engine.templates.base import BaseTemplate


def generate_barlist(
    template: BaseTemplate,
    params_raw: dict,
    log: ReasoningLogger,
    *,
    call_ai: bool = True,
    store=None,           # optional CorrectionStore instance for Feature A/C logging
) -> list[BarRow]:
    """
    Run the full deterministic pipeline for one template invocation.

    Args:
        template:   loaded template instance
        params_raw: dict of raw user input values (strings / floats from Excel)
        log:        ReasoningLogger instance (writes to Excel or stdout)
        call_ai:    if False, skip the Claude annotation step

    Returns:
        Ordered list of BarRow objects ready for the BarList tab.

    Raises:
        ValueError: if any required input is missing or out of bounds.
    """
    log.section(f"Template: {template.name}  (v{template.version})")
    log.step(f"Inputs received: {list(params_raw.keys())}")

    # ── 0. Gold override check ────────────────────────────────────────────
    gold_bars = load_gold_override(template.name, log)
    if gold_bars is not None:
        # Override replaces computed output entirely — skip rules and AI
        total = sum(b.qty for b in gold_bars)
        log.done(f"{len(gold_bars)} mark types, {total} total bars  [GOLD OVERRIDE]")
        if store is not None:
            try:
                params_stub = template.parse_and_validate(params_raw)
                store.log_run(template.name, template.version,
                              params_stub.to_dict(), gold_bars)
            except Exception:
                pass
        return gold_bars

    # ── 1. Validate ──────────────────────────────────────────────────────
    params = template.parse_and_validate(params_raw)
    log.step("All inputs validated ✓")
    log.blank()

    # ── 2. Run rules ─────────────────────────────────────────────────────
    all_bars: list[BarRow] = []
    for rule_name in template.rules:
        rule_fn = RULE_REGISTRY.get(rule_name)
        if rule_fn is None:
            log.warn(f"Rule '{rule_name}' not found in RULE_REGISTRY — skipped")
            continue
        log.section(rule_name)
        result = rule_fn(params, log)
        all_bars.extend(result)
        log.blank()

    # ── 3. Merge identical rows ──────────────────────────────────────────
    all_bars = _merge_identical(all_bars)

    # ── 3b. Populate Ref column from source_rule lookup ──────────────────
    _apply_refs(all_bars)

    # ── 4. Apply learned adjustments (Feature A) ─────────────────────────
    if store is not None:
        _apply_learned_adjustments(all_bars, template.name, store, log)

    # ── 5. Claude edge-case notes ────────────────────────────────────────
    if call_ai:
        triggers = template.evaluate_triggers(params)
        if triggers:
            log.section("REVIEWER NOTES  (AI-assisted)")
            notes = call_claude_for_notes(
                template.name, params.to_dict(), triggers
            )
            for note in notes:
                log.ai_note(note)
            log.blank()

    # ── 6. Summary ───────────────────────────────────────────────────────
    mark_count = len({b.mark for b in all_bars})
    total_bars = sum(b.qty for b in all_bars)
    log.done(f"{mark_count} mark types, {total_bars} total bars")

    # ── 7. Log run to CorrectionStore (Feature A/C) ──────────────────────
    if store is not None:
        try:
            store.log_run(template.name, template.version, params.to_dict(), all_bars)
        except Exception:
            pass   # never let logging errors break generation

    return all_bars


# ---------------------------------------------------------------------------
# Post-processing helpers
# ---------------------------------------------------------------------------

def _apply_learned_adjustments(
    bars: list[BarRow],
    template_name: str,
    store,
    log: ReasoningLogger,
) -> None:
    """
    Feature A: Apply learned qty/length offsets from correction history.

    Adjustments are applied in-place. Each applied change is written to the
    ReasoningLog in pale green so estimators can see exactly what was changed
    and why. Only consistent patterns (same direction, >= 3 corrections) are applied.
    """
    adjustments = store.get_adjustments(template_name)
    if not adjustments:
        return

    bar_map = {b.mark: b for b in bars}
    log.section("LEARNED ADJUSTMENTS")

    for adj in adjustments:
        bar = bar_map.get(adj["mark"])
        if bar is None:
            continue

        if adj["field"] == "qty":
            original = bar.qty
            bar.qty = max(1, bar.qty + int(adj["delta"]))
            log.learned_adj(
                adj["mark"], "qty",
                original, bar.qty,
                adj["count"],
            )

        elif adj["field"] == "length_in":
            from vistadetail.engine.schema import fmt_inches
            original_len = bar.length_in
            bar.length_in = max(1.0, bar.length_in + adj["delta"])
            log.learned_adj(
                adj["mark"], "length",
                fmt_inches(original_len), fmt_inches(bar.length_in),
                adj["count"],
            )

    log.blank()


# ---------------------------------------------------------------------------
# Ref column — maps source_rule → governing ACI 318-19 / Caltrans BDS clause
# ---------------------------------------------------------------------------

_REF_MAP: dict[str, str] = {
    # ── Headwall (D89A) ───────────────────────────────────────────────────
    "rule_hw_d_bars":           "Caltrans D89A D1 — top invert transverse #5 @8\"",
    "rule_hw_trans_footing":    "Caltrans D89A TF — transverse footing #4 @12\"",
    "rule_hw_long_invert":      "Caltrans D89A LI — longitudinal invert #4 @8\", 2 layers",
    "rule_hw_long_wall":        "Caltrans D89A LW — longitudinal wall #4 @12\", 2 faces",
    "rule_hw_top_wall":         "Caltrans D89A TW — top of wall #5 Tot 3",
    "rule_hw_vert_wall":        "Caltrans D89A VW — vertical wall #4 @12\"",
    "rule_hw_c_bars":           "Caltrans D89A CB — C-bar hairpin #4 @12\"; ACI 318-19 §25.3",
    "rule_hw_spreaders":        "Caltrans D89A WS — wall spreaders U-shape #4 @24\"",
    "rule_hw_standees":         "Caltrans D89A ST — mat standees S-shape #5 @12\"",
    "rule_validate_headwall":   "Caltrans D89A — height validation vs. table max",
    # ── Wing Wall ────────────────────────────────────────────────────────
    "rule_wing_horiz":          "ACI 318-19 §11.7.2, §24.3.2",
    "rule_wing_vert":           "ACI 318-19 §11.7.2",
    "rule_wing_corner":         "ACI 318-19 §26.6.2 (corner bar development)",
    # ── Spread Footing ───────────────────────────────────────────────────
    "rule_bottom_transverse":   "ACI 318-19 §13.3.1 (footing flexural reinf.)",
    "rule_bottom_longitudinal": "ACI 318-19 §13.3.1 (footing flexural reinf.)",
    "rule_dowels":              "ACI 318-19 §25.5.2, §10.7.6 (col. base splice)",
    # ── Inlet – 9in Wall ─────────────────────────────────────────────────
    "rule_horizontal_bars_EF":  "ACI 318-19 §11.7.2, §24.3.2",
    "rule_vertical_bars_EF":    "ACI 318-19 §11.7.2",
    "rule_corner_L_bars":       "ACI 318-19 §26.6.2 (corner bar development)",
    # ── Box Culvert ──────────────────────────────────────────────────────
    "rule_top_slab_top":        "ACI 318-19 §7.6.1; Caltrans BDS §8.4",
    "rule_top_slab_bottom":     "ACI 318-19 §7.6.1; Caltrans BDS §8.4",
    "rule_wall_vertical":       "ACI 318-19 §11.7.2; Caltrans BDS §8.4",
    "rule_bottom_slab_top":     "ACI 318-19 §13.3.1; Caltrans BDS §8.4",
    "rule_bottom_slab_bottom":  "ACI 318-19 §13.3.1; Caltrans BDS §8.4",
    "rule_haunch_bars":         "ACI 318-19 §26.6.2 (haunch corner reinf.)",
    # ── Retaining Wall ───────────────────────────────────────────────────
    "rule_stem_horiz":          "ACI 318-19 §11.7.2, §24.3.2",
    "rule_stem_vert":           "ACI 318-19 §11.7.3.1 (cantilever wall primary reinf.)",
    "rule_toe_bars":            "ACI 318-19 §13.3.1 (footing flexural reinf.)",
    "rule_heel_bars":           "ACI 318-19 §13.3.1 (footing flexural reinf.)",
    "rule_stem_dowels":         "ACI 318-19 §25.5.2, §16.3.2 (wall-footing interface)",
    "rule_shear_key":           "Caltrans GS §6 (shear key sliding resistance)",
    # ── Flat Slab ────────────────────────────────────────────────────────
    "rule_slab_long_bars":      "ACI 318-19 §26.4.1 (slab EW reinf., max spacing min(2t,18in))",
    "rule_slab_short_bars":     "ACI 318-19 §26.4.1 (slab EW reinf., max spacing min(2t,18in))",
    # ── Drilled Shaft Cage ───────────────────────────────────────────────
    "rule_cage_verticals":      "ACI 318-19 §18.8.5 (drilled shaft longitudinal reinf.)",
    "rule_cage_hoops_standard": "ACI 318-19 §26.7.2; Caltrans Seismic Design Criteria §8.2",
    "rule_cage_hoops_confinement": "ACI 318-19 §18.8.5; Caltrans SDC §8.2 (confinement zone)",
    # ── Concrete Pipe Collar ─────────────────────────────────────────────
    "rule_collar_long_bars":    "ACI 318-19 §26.4.1 (slab/mat EW reinf., max spacing min(2t,18in))",
    "rule_collar_short_bars":   "ACI 318-19 §26.4.1 (slab/mat EW reinf., max spacing min(2t,18in))",
    # ── Slab on Grade ────────────────────────────────────────────────────
    "rule_sog_long_bars":       "ACI 360R-10 §5.3; ACI 318-19 §26.4.1 (SOG EW mat reinf.)",
    "rule_sog_short_bars":      "ACI 360R-10 §5.3; ACI 318-19 §26.4.1 (SOG EW mat reinf.)",
    "rule_sog_edge_bars":       "ACI 360R-10 §5.5 (thickened edge / perimeter beam reinf.)",
    # ── Equipment / Concrete Pad ─────────────────────────────────────────────
    "rule_pad_bottom_long":     "ACI 318-19 §26.4.1; Table 20.6.1.3.1 (EW mat, 3in cover cast-against-earth)",
    "rule_pad_bottom_short":    "ACI 318-19 §26.4.1; Table 20.6.1.3.1 (EW mat, 3in cover cast-against-earth)",
    "rule_pad_top_long":        "ACI 318-19 §26.4.1 (double mat — top EW bars)",
    "rule_pad_top_short":       "ACI 318-19 §26.4.1 (double mat — top EW bars)",
    "rule_pad_vertical_dowels": "ACI 318-19 §25.5.2 (dev. length, tension — equipment anchor dowels)",
    # ── Seatwall ─────────────────────────────────────────────────────────────
    "rule_seatwall_top_long":    "ACI 318-19 §11.7.2; Table 20.6.1.3.1 (seatwall top longitudinal)",
    "rule_seatwall_bot_long":    "ACI 318-19 §11.7.2; Table 20.6.1.3.1 (seatwall bottom longitudinal)",
    "rule_seatwall_transverse":  "ACI 318-19 §11.7.3; §26.7 (transverse bars across seat width)",
    # ── Concrete Header ───────────────────────────────────────────────────────
    "rule_header_top_long":      "ACI 318-19 §11.7.2; Table 20.6.1.3.1 (header top longitudinal)",
    "rule_header_bot_long":      "ACI 318-19 §11.7.2; Table 20.6.1.3.1 (header bottom longitudinal)",
    "rule_header_transverse":    "ACI 318-19 §11.7.3; §26.7 (transverse bars across header width)",
    # ── Pipe Encasement ───────────────────────────────────────────────────────
    "rule_encasement_hoops":        "ACI 318-19 §25.3 (hoops around pipe cross-section); Table 20.6.1.3.1",
    "rule_encasement_longitudinals": "ACI 318-19 §11.7.2; Table 20.6.1.3.1 (buried encasement long bars)",
    # ── Fuel Foundation ───────────────────────────────────────────────────────
    "rule_fuel_bottom_long":        "ACI 318-19 §13.3.1; Table 20.6.1.3.1 (fuel fdn bottom EW mat)",
    "rule_fuel_bottom_short":       "ACI 318-19 §13.3.1; Table 20.6.1.3.1 (fuel fdn bottom EW mat)",
    "rule_fuel_top_long":           "ACI 318-19 §13.3.1 (fuel fdn top EW mat)",
    "rule_fuel_top_short":          "ACI 318-19 §13.3.1 (fuel fdn top EW mat)",
    # ── Dual Slab ─────────────────────────────────────────────────────────────
    "rule_dual_slab_A_long":        "ACI 318-19 §26.4.1; Table 20.6.1.3.1 (Slab A long EW mat)",
    "rule_dual_slab_A_short":       "ACI 318-19 §26.4.1; Table 20.6.1.3.1 (Slab A short EW mat)",
    "rule_dual_slab_B_long":        "ACI 318-19 §26.4.1; Table 20.6.1.3.1 (Slab B long EW mat)",
    "rule_dual_slab_B_short":       "ACI 318-19 §26.4.1; Table 20.6.1.3.1 (Slab B short EW mat)",
    # ── G2 Inlet Top / G2 Expanded Inlet Top ─────────────────────────────────
    "rule_inlet_top_long_bars":     "Caltrans G2 inlet top slab — long bars, ACI §24.3.2",
    "rule_inlet_top_short_bars":    "Caltrans G2 inlet top slab — short bars, ACI §24.3.2",
    "rule_validate_inlet_top":      "ACI 318-19 §24.3.2; §20.6.1.3 (inlet top slab cover + spacing)",
    # ── Junction Structure ────────────────────────────────────────────────────
    "rule_junction_long_wall_horiz":  "ACI 318-19 §11.7.2, §24.3.2 (junction long wall horiz EF)",
    "rule_junction_long_wall_vert":   "ACI 318-19 §11.7.2 (junction long wall vert EF)",
    "rule_junction_short_wall_horiz": "ACI 318-19 §11.7.2, §24.3.2 (junction short wall horiz EF)",
    "rule_junction_short_wall_vert":  "ACI 318-19 §11.7.2 (junction short wall vert EF)",
    "rule_junction_floor_long":       "ACI 318-19 §13.3.1; Table 20.6.1.3.1 (junction floor long bars)",
    "rule_junction_floor_short":      "ACI 318-19 §13.3.1; Table 20.6.1.3.1 (junction floor short bars)",
    "rule_validate_junction":         "ACI 318-19 §24.3.2; §20.6.1.3 (junction structure validation)",
}


def _apply_refs(bars: list[BarRow]) -> None:
    """
    Populate the ref field on each bar from the centralized _REF_MAP.
    Only sets ref if the bar doesn't already have one (rules may set their own).
    """
    for bar in bars:
        if not bar.ref and bar.source_rule:
            bar.ref = _REF_MAP.get(bar.source_rule, f"See {bar.source_rule}")


def _merge_identical(bars: list[BarRow]) -> list[BarRow]:
    """
    Merge rows with the same (mark, size, length_in, shape) into one row,
    summing quantities.  Preserves first-seen row order.
    """
    seen: dict[tuple, BarRow] = {}
    for bar in bars:
        key = (bar.mark, bar.size, round(bar.length_in, 3), bar.shape)
        if key in seen:
            seen[key].qty += bar.qty
        else:
            seen[key] = bar
    return list(seen.values())


def barlist_to_rows(bars: list[BarRow]) -> list[list]:
    """
    Convert BarRow list to flat list-of-lists for writing to Excel.
    Header row is index 0.
    """
    header = ["Mark", "Size", "Qty", "Length", "Shape", "Leg A", "Leg B", "Leg C", "Notes", "Ref", "Review Flag"]
    rows = [header] + [b.to_row() for b in bars]
    return rows


def barlist_total_weight_lb(bars: list[BarRow]) -> float:
    """Compute total rebar weight in lbs for the generated bar list."""
    from vistadetail.engine.hooks import BAR_WEIGHT_LB_FT
    total = 0.0
    for b in bars:
        weight_per_ft = BAR_WEIGHT_LB_FT.get(b.size, 0.0)
        total += weight_per_ft * (b.length_in / 12.0) * b.qty
    return round(total, 1)
