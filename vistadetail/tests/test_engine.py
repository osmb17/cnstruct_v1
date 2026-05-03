"""
Unit tests for the VistaDetail rebar engine.

Groups:
  1. Schema / BarRow
  2. Inlet 9in Wall rule functions
  3. Spread Footing rule functions
  4. Calculator / generate_barlist
  5. Cut optimizer
  6. Gold override I/O
  7. Correction store
"""

from __future__ import annotations

import math
import pathlib

import pytest

# ---------------------------------------------------------------------------
# Shared test fixture — a no-op ReasoningLogger (no Excel required)
# ---------------------------------------------------------------------------
from vistadetail.engine.reasoning_logger import ReasoningLogger


@pytest.fixture()
def log():
    return ReasoningLogger(sheet=None)


# ===========================================================================
# 1. Schema / BarRow tests
# ===========================================================================

from vistadetail.engine.schema import BarRow, InputField, fmt_inches


class TestFmtInches:
    def test_barrow_length_ft_in(self):
        """81.0 in → 6'-9"."""
        assert fmt_inches(81.0) == "6'-9\""

    def test_zero_feet(self):
        """Values < 12 in should show 0'-N"."""
        assert fmt_inches(6.0) == "0'-6\""

    def test_even_feet(self):
        """120.0 in → 10'-0"."""
        assert fmt_inches(120.0) == "10'-0\""

    def test_fractional_eighth(self):
        """81.125 in = 6 ft 9.125 in → 6'-9 1/8"."""
        result = fmt_inches(81.125)
        assert result.startswith("6'-9")


class TestBarRowToRow:
    def test_to_row_length(self):
        """to_row() must return exactly 12 elements (added bend_type column)."""
        bar = BarRow(mark="H1", size="#5", qty=12, length_in=81.0)
        row = bar.to_row()
        assert len(row) == 12

    def test_to_row_first_element(self):
        """First element of to_row() is the mark."""
        bar = BarRow(mark="H1", size="#5", qty=12, length_in=81.0)
        assert bar.to_row()[0] == "H1"

    def test_to_row_size(self):
        bar = BarRow(mark="V1", size="#4", qty=6, length_in=60.0)
        assert bar.to_row()[1] == "#4"

    def test_to_row_qty(self):
        bar = BarRow(mark="V1", size="#4", qty=6, length_in=60.0)
        assert bar.to_row()[2] == 6


class TestInputFieldValidate:
    def test_validate_choices_invalid(self):
        """Passing a value not in choices should raise ValueError."""
        field = InputField("bar_size", str, choices=["#4", "#5", "#6"])
        with pytest.raises(ValueError, match="not in"):
            field.validate("#99")

    def test_validate_choices_valid(self):
        field = InputField("bar_size", str, choices=["#4", "#5", "#6"])
        assert field.validate("#5") == "#5"

    def test_validate_range_below_min(self):
        """Value below min should raise ValueError."""
        field = InputField("spacing", float, min=6.0, max=18.0)
        with pytest.raises(ValueError, match="< min"):
            field.validate(3.0)

    def test_validate_range_above_max(self):
        """Value above max should raise ValueError."""
        field = InputField("spacing", float, min=6.0, max=18.0)
        with pytest.raises(ValueError, match="> max"):
            field.validate(24.0)

    def test_validate_range_at_boundary(self):
        """Boundary values (exactly min / max) should be accepted."""
        field = InputField("spacing", float, min=6.0, max=18.0)
        assert field.validate(6.0) == 6.0
        assert field.validate(18.0) == 18.0

    def test_validate_type_cast(self):
        """dtype coercion: string "12" → float 12.0."""
        field = InputField("spacing", float, min=6.0, max=18.0)
        assert field.validate("12") == 12.0


# ===========================================================================
# 2. Inlet 9in Wall rule tests
# ===========================================================================

from vistadetail.engine.schema import Params
from vistadetail.engine.rules.inlet_wall_rules import (
    rule_horizontal_bars_EF,
    rule_vertical_bars_EF,
    rule_corner_L_bars,
)


def _inlet_params(**overrides) -> Params:
    """Build a minimal valid Params for the inlet wall rules."""
    defaults = dict(
        wall_length_ft=10.0,
        wall_height_ft=8.0,
        wall_thick_in=9,
        cover_in=2.0,
        horiz_bar_size="#5",
        horiz_spacing_in=12.0,
        vert_bar_size="#5",
        vert_spacing_in=12.0,
        hook_type="std_90",
        corner_bars="yes",
        corner_bar_size="#4",
    )
    defaults.update(overrides)
    return Params(defaults)


class TestInletHorizQty:
    def test_horiz_qty_8ft_wall(self, log):
        """
        wall_height=8 ft, spacing=12 in, cover=2 in:
          usable = 96 - 4 = 92 in
          per_face = floor(92/12) + 1 = 7 + 1 = 8
          total = 8 * 2 = 16
        """
        p = _inlet_params(wall_height_ft=8.0, horiz_spacing_in=12.0, cover_in=2.0)
        bars = rule_horizontal_bars_EF(p, log)
        assert len(bars) == 1
        bar = bars[0]
        usable = 8 * 12 - 2 * 2   # 92
        expected_per_face = math.floor(usable / 12) + 1   # 8
        assert bar.qty == expected_per_face * 2

    def test_horiz_mark_is_H1(self, log):
        p = _inlet_params()
        bars = rule_horizontal_bars_EF(p, log)
        assert bars[0].mark == "H1"

    def test_horiz_source_rule(self, log):
        p = _inlet_params()
        bars = rule_horizontal_bars_EF(p, log)
        assert bars[0].source_rule == "rule_horizontal_bars_EF"


class TestInletVertQty:
    def test_vert_qty_10ft_length(self, log):
        """
        wall_length=10 ft, spacing=12 in, cover=2 in:
          usable = 120 - 4 = 116 in
          per_face = floor(116/12) + 1 = 9 + 1 = 10
          total = 10 * 2 = 20
        """
        p = _inlet_params(wall_length_ft=10.0, vert_spacing_in=12.0, cover_in=2.0)
        bars = rule_vertical_bars_EF(p, log)
        assert len(bars) == 1
        usable = 10 * 12 - 2 * 2   # 116
        expected_per_face = math.floor(usable / 12) + 1   # 10
        assert bars[0].qty == expected_per_face * 2

    def test_vert_mark_is_V1(self, log):
        p = _inlet_params()
        bars = rule_vertical_bars_EF(p, log)
        assert bars[0].mark == "V1"


class TestInletCorner:
    def test_corner_disabled_returns_empty(self, log):
        """corner_bars='no' must return an empty list."""
        p = _inlet_params(corner_bars="no")
        bars = rule_corner_L_bars(p, log)
        assert bars == []

    def test_corner_enabled_returns_4(self, log):
        """corner_bars='yes' must return qty=4."""
        p = _inlet_params(corner_bars="yes", wall_length_ft=10.0)
        bars = rule_corner_L_bars(p, log)
        assert len(bars) == 1
        assert bars[0].qty == 4

    def test_corner_shape_is_L(self, log):
        p = _inlet_params(corner_bars="yes")
        bars = rule_corner_L_bars(p, log)
        assert bars[0].shape == "L"

    def test_corner_mark_is_C1(self, log):
        p = _inlet_params(corner_bars="yes")
        bars = rule_corner_L_bars(p, log)
        assert bars[0].mark == "C1"


# ===========================================================================
# 3. Spread Footing rule tests
# ===========================================================================

from vistadetail.engine.rules.footing_rules import (
    rule_bottom_transverse,
    rule_bottom_longitudinal,
    rule_dowels,
)
from vistadetail.engine.hooks import development_length_tension


def _footing_params(**overrides) -> Params:
    """Build a minimal valid Params for the footing rules."""
    defaults = dict(
        footing_length_ft=10.0,
        footing_width_ft=8.0,
        footing_depth_in=18.0,
        cover_in=3.0,
        bot_bar_size="#5",
        bot_spacing_in=12.0,
        dowel_qty=4,
        dowel_bar_size="#5",
    )
    defaults.update(overrides)
    return Params(defaults)


class TestFootingTransverseQty:
    def test_transverse_qty_10ft_length(self, log):
        """
        footing_length=10 ft, spacing=12 in, cover=3 in:
          usable = 120 - 6 = 114 in
          qty = floor(114/12) + 1 = 9 + 1 = 10
        """
        p = _footing_params(footing_length_ft=10.0, bot_spacing_in=12.0, cover_in=3.0)
        bars = rule_bottom_transverse(p, log)
        assert len(bars) == 1
        usable = 10 * 12 - 2 * 3   # 114
        expected = math.floor(usable / 12) + 1   # 10
        assert bars[0].qty == expected

    def test_transverse_mark_is_BT1(self, log):
        p = _footing_params()
        bars = rule_bottom_transverse(p, log)
        assert bars[0].mark == "BT1"

    def test_transverse_bar_length_is_width_minus_cover(self, log):
        """Bar length = footing_width - 2*cover (in inches)."""
        p = _footing_params(footing_width_ft=8.0, cover_in=3.0)
        bars = rule_bottom_transverse(p, log)
        expected_len = 8 * 12 - 2 * 3   # 90 in
        assert bars[0].length_in == pytest.approx(expected_len)


class TestFootingDowelLength:
    def test_dowel_length_formula(self, log):
        """
        DW1 length = (depth - cover) + ld + lap
        where ld = development_length_tension('#5', cover_in=3)
              lap = max(ld, 18)
        """
        depth_in = 18.0
        cover_in = 3.0
        bar_size = "#5"
        ld = development_length_tension(bar_size, cover_in=cover_in)
        lap = max(ld, 18.0)
        expected_len = (depth_in - cover_in) + ld + lap

        p = _footing_params(footing_depth_in=depth_in, cover_in=cover_in,
                            dowel_bar_size=bar_size, dowel_qty=4)
        bars = rule_dowels(p, log)
        assert len(bars) == 1
        assert bars[0].length_in == pytest.approx(expected_len, abs=0.01)

    def test_dowel_qty_zero_returns_empty(self, log):
        """dowel_qty=0 must return empty list."""
        p = _footing_params(dowel_qty=0)
        bars = rule_dowels(p, log)
        assert bars == []

    def test_dowel_mark_is_DW1(self, log):
        p = _footing_params(dowel_qty=4)
        bars = rule_dowels(p, log)
        assert bars[0].mark == "DW1"


# ===========================================================================
# 4. Calculator / generate_barlist tests
# ===========================================================================

from vistadetail.engine.calculator import generate_barlist
from vistadetail.engine.templates.inlet_9in_wall import TEMPLATE as INLET_TEMPLATE
from vistadetail.engine.templates import TEMPLATE_REGISTRY


def _inlet_defaults() -> dict:
    return INLET_TEMPLATE.input_defaults()


class TestGenerateInletBarlist:
    def test_returns_expected_marks(self, log):
        """Default inlet params should produce the full G2 Inlet mark set."""
        bars = generate_barlist(INLET_TEMPLATE, _inlet_defaults(), log, call_ai=False)
        marks = {b.mark for b in bars}
        assert marks == {
            "A1", "B1", "BM1", "BM2", "H1", "H2", "H3", "H4",
            "HP1", "RA1", "V1", "V2",
        }

    def test_returns_12_barrow_objects(self, log):
        bars = generate_barlist(INLET_TEMPLATE, _inlet_defaults(), log, call_ai=False)
        assert len(bars) == 12

    def test_all_bars_have_nonempty_ref(self, log):
        """After generate_barlist, every bar must have a non-empty ref."""
        bars = generate_barlist(INLET_TEMPLATE, _inlet_defaults(), log, call_ai=False)
        for bar in bars:
            assert bar.ref, f"Bar {bar.mark} has empty ref"

    def test_generate_validates_bad_input(self, log):
        """Passing an out-of-range value should raise ValueError."""
        bad_params = _inlet_defaults()
        bad_params["wall_height_ft"] = 999.0   # exceeds max=20
        with pytest.raises(ValueError):
            generate_barlist(INLET_TEMPLATE, bad_params, log, call_ai=False)

    def test_corner_bars_no_excludes_C1(self, log):
        """With corner_bars='no', C1 should not be produced."""
        params = _inlet_defaults()
        params["corner_bars"] = "no"
        bars = generate_barlist(INLET_TEMPLATE, params, log, call_ai=False)
        marks = {b.mark for b in bars}
        assert "C1" not in marks
        assert "H1" in marks
        assert "V1" in marks


class TestRefMapCoverage:
    def test_all_templates_produce_nonempty_refs(self, log):
        """
        Every bar produced by every template using defaults must have a
        non-empty ref field after generation.
        """
        for name, template in TEMPLATE_REGISTRY.items():
            defaults = template.input_defaults()
            bars = generate_barlist(template, defaults, log, call_ai=False)
            for bar in bars:
                assert bar.ref, (
                    f"Template '{name}', mark '{bar.mark}' "
                    f"(source_rule='{bar.source_rule}') has empty ref"
                )


# ===========================================================================
# 5. Cut optimizer tests
# ===========================================================================

from vistadetail.engine.cut_optimizer import CutRequest, optimize_cuts


class TestCutOptimizer:
    def test_cut_simple_uses_multiple_stock_bars(self):
        """
        72-in pieces from 240-in stock: each stock bar holds floor(240/72)=3 cuts
        (with kerf: floor((240 - 0.125*n) / 72) ≈ 3).
        12 pieces should require ceil(12/3)=4 stock bars.
        """
        reqs = [CutRequest("#5", 72.0, 12)]
        plan = optimize_cuts(reqs, stock_lengths_ft=[20])   # 240 in
        bars = plan.by_size["#5"]
        assert len(bars) > 0
        # Total cuts must equal 12
        total_cuts = sum(len(b.cuts) for b in bars)
        assert total_cuts == 12

    def test_cut_waste_pct_reasonable(self):
        """Waste should be >= 0% and <= 100%."""
        reqs = [CutRequest("#5", 72.0, 6)]
        plan = optimize_cuts(reqs, stock_lengths_ft=[20])
        wp = plan.waste_pct().get("#5", 0.0)
        assert 0.0 <= wp <= 100.0

    def test_cut_all_fit_zero_waste(self):
        """One piece exactly equal to stock length → 0 waste."""
        reqs = [CutRequest("#4", 120.0, 1)]   # 10 ft piece, 10 ft stock
        plan = optimize_cuts(reqs, stock_lengths_ft=[10])
        bars = plan.by_size["#4"]
        assert len(bars) == 1
        # Waste = remaining after cuts
        assert bars[0].waste_in == pytest.approx(0.0, abs=0.2)

    def test_cut_total_bars_used_is_dict(self):
        reqs = [CutRequest("#5", 60.0, 3), CutRequest("#4", 48.0, 2)]
        plan = optimize_cuts(reqs, stock_lengths_ft=[20])
        totals = plan.total_bars_used()
        assert "#5" in totals
        assert "#4" in totals

    def test_cut_to_rows_has_header(self):
        reqs = [CutRequest("#5", 60.0, 2)]
        plan = optimize_cuts(reqs, stock_lengths_ft=[20])
        rows = plan.to_rows()
        assert rows[0][0] == "Size"

    @pytest.mark.parametrize("length_in,qty,stock_ft", [
        (60.0, 1, 5),
        (120.0, 2, 20),
        (180.0, 3, 20),
    ])
    def test_cut_parametric_cases(self, length_in, qty, stock_ft):
        """All pieces must be accounted for in cuts."""
        reqs = [CutRequest("#5", length_in, qty)]
        plan = optimize_cuts(reqs, stock_lengths_ft=[stock_ft])
        total_cuts = sum(len(b.cuts) for b in plan.by_size["#5"])
        assert total_cuts == qty


# ===========================================================================
# 6. Gold override tests
# ===========================================================================

from vistadetail.engine.gold_overrides import (
    _slug,
    delete_gold_override,
    load_gold_override,
    override_path,
    save_gold_override,
)
import vistadetail.engine.gold_overrides as _gold_mod


@pytest.fixture()
def gold_tmp(tmp_path, monkeypatch):
    """Redirect the gold overrides directory to a tmp_path for isolation."""
    monkeypatch.setattr(_gold_mod, "_OVERRIDES_DIR", tmp_path)
    return tmp_path


class TestGoldSlug:
    def test_slug_inlet(self):
        """'Inlet – 9in Wall' should become 'Inlet_9in_Wall'."""
        assert _slug("Inlet – 9in Wall") == "Inlet_9in_Wall"

    def test_slug_box_culvert(self):
        assert _slug("Box Culvert") == "Box_Culvert"

    def test_slug_no_special_chars(self):
        s = _slug("Spread Footing")
        assert " " not in s
        assert "–" not in s


class TestGoldSaveLoad:
    def test_save_load_roundtrip(self, log, gold_tmp):
        """Save 3 bars, load back, verify mark / qty / size."""
        bars = [
            BarRow(mark="H1", size="#5", qty=18, length_in=165.0),
            BarRow(mark="V1", size="#5", qty=20, length_in=110.0),
            BarRow(mark="C1", size="#4", qty=4,  length_in=36.0, shape="L",
                   leg_a_in=18.0, leg_b_in=18.0),
        ]
        save_gold_override("Test Template", bars)
        loaded = load_gold_override("Test Template", log)
        assert loaded is not None
        assert len(loaded) == 3
        by_mark = {b.mark: b for b in loaded}
        assert by_mark["H1"].qty == 18
        assert by_mark["H1"].size == "#5"
        assert by_mark["V1"].qty == 20
        assert by_mark["C1"].qty == 4

    def test_gold_delete(self, log, gold_tmp):
        """Save then delete — load should return None."""
        bars = [BarRow(mark="X1", size="#4", qty=2, length_in=48.0)]
        save_gold_override("Temp Template", bars)
        assert load_gold_override("Temp Template", log) is not None
        delete_gold_override("Temp Template")
        assert load_gold_override("Temp Template", log) is None

    def test_gold_no_override(self, log, gold_tmp):
        """load_gold_override returns None when no file exists."""
        result = load_gold_override("Nonexistent Template", log)
        assert result is None

    def test_gold_roundtrip_length(self, log, gold_tmp):
        """Length is preserved through save→load within 0.5 in rounding."""
        bars = [BarRow(mark="H1", size="#5", qty=6, length_in=81.0)]
        save_gold_override("Length Test", bars)
        loaded = load_gold_override("Length Test", log)
        assert loaded is not None
        assert loaded[0].length_in == pytest.approx(81.0, abs=0.5)


# ===========================================================================
# 7. Correction store tests
# ===========================================================================

from vistadetail.engine.correction_store import CorrectionStore


@pytest.fixture()
def store(tmp_path):
    """Create an in-tmp_path CorrectionStore for each test."""
    db = str(tmp_path / "test_corrections.db")
    return CorrectionStore(db_path=db)


def _make_bar(mark: str, qty: int, size: str = "#5", length_in: float = 100.0) -> BarRow:
    return BarRow(mark=mark, size=size, qty=qty, length_in=length_in)


class TestCorrectionStore:
    def test_log_run_returns_int(self, store):
        """log_run must return an integer run_id."""
        bars = [_make_bar("H1", 18)]
        run_id = store.log_run("Inlet – 9in Wall", "2.1", {"wall_height_ft": 8.0}, bars)
        assert isinstance(run_id, int)
        assert run_id > 0

    def test_acceptance_starts_at_100_pct(self, store):
        """A fresh template with one run and no corrections = 100% acceptance."""
        bars = [_make_bar("H1", 18)]
        store.log_run("Inlet – 9in Wall", "2.1", {}, bars)
        conf = store.get_confidence("Inlet – 9in Wall")
        assert conf.uses == 1
        assert conf.corrections == 0
        assert conf.acceptance_pct == pytest.approx(100.0)

    def test_corrections_diff_returns_count(self, store):
        """
        Two bar lists differing in qty for H1 should produce exactly 1 correction.
        """
        generated = [_make_bar("H1", 18), _make_bar("V1", 20)]
        final = [_make_bar("H1", 20), _make_bar("V1", 20)]   # H1 qty changed
        run_id = store.log_run("Inlet – 9in Wall", "2.1", {}, generated)
        count = store.log_corrections_from_diff(run_id, generated, final)
        assert count == 1

    def test_get_adjustments_below_min_returns_empty(self, store):
        """With only 2 corrections, get_adjustments(min_count=3) returns []."""
        generated = [_make_bar("H1", 18)]
        final = [_make_bar("H1", 20)]
        for _ in range(2):
            run_id = store.log_run("MyTemplate", "1.0", {}, generated)
            store.log_corrections_from_diff(run_id, generated, final)
        adjustments = store.get_adjustments("MyTemplate", min_count=3)
        assert adjustments == []

    def test_get_adjustments_triggers_on_3_consistent(self, store):
        """
        Three consistent +1 qty corrections on H1 should produce an adjustment
        with field='qty' and delta=+1.
        """
        generated = [_make_bar("H1", 18)]
        final = [_make_bar("H1", 19)]   # always +1
        for _ in range(3):
            run_id = store.log_run("MyTemplate", "1.0", {}, generated)
            store.log_corrections_from_diff(run_id, generated, final)

        adjustments = store.get_adjustments("MyTemplate", min_count=3)
        assert len(adjustments) == 1
        adj = adjustments[0]
        assert adj["mark"] == "H1"
        assert adj["field"] == "qty"
        assert adj["delta"] == 1
        assert adj["count"] == 3

    def test_get_adjustments_mixed_direction_suppressed(self, store):
        """
        Mixed +1 / -1 corrections should NOT produce an adjustment
        (inconsistent direction → no learned signal).
        """
        bars_orig = [_make_bar("H1", 18)]
        for i in range(4):
            run_id = store.log_run("MixedTemplate", "1.0", {}, bars_orig)
            # Alternate +1 and -1 each run
            delta = 1 if i % 2 == 0 else -1
            final = [_make_bar("H1", 18 + delta)]
            store.log_corrections_from_diff(run_id, bars_orig, final)

        adjustments = store.get_adjustments("MixedTemplate", min_count=3)
        assert adjustments == []

    def test_get_all_confidence_returns_list(self, store):
        """get_all_confidence returns a list (possibly empty, possibly populated)."""
        result = store.get_all_confidence()
        assert isinstance(result, list)

    def test_multiple_templates_tracked_separately(self, store):
        """Confidence stats must be isolated per template name."""
        bars = [_make_bar("H1", 10)]
        store.log_run("Template A", "1.0", {}, bars)
        store.log_run("Template A", "1.0", {}, bars)
        store.log_run("Template B", "1.0", {}, bars)

        conf_a = store.get_confidence("Template A")
        conf_b = store.get_confidence("Template B")
        assert conf_a.uses == 2
        assert conf_b.uses == 1


# ===========================================================================
# 8. Drilled Shaft Cage rule tests
# ===========================================================================

import math as _math
from vistadetail.engine.rules.cage_rules import (
    rule_cage_verticals,
    rule_cage_hoops_standard,
    rule_cage_hoops_confinement,
    rule_validate_cage,
)
from vistadetail.engine.templates.cage import TEMPLATE as CAGE_TEMPLATE


def _cage_params(**overrides):
    """Return a Params object using CAGE_TEMPLATE defaults, with optional overrides."""
    defaults = CAGE_TEMPLATE.input_defaults()
    defaults.update(overrides)
    return CAGE_TEMPLATE.parse_and_validate(defaults)


class TestCageVerticals:
    def test_vert_length_includes_embed(self, log):
        """V1 length = cage_depth_ft*12 + embed_in."""
        p = _cage_params(cage_depth_ft=5.0, embed_in=6.0)
        bars = rule_cage_verticals(p, log)
        assert bars[0].length_in == pytest.approx(66.0)

    def test_vert_qty_from_input(self, log):
        """V1 qty should exactly equal vert_count."""
        p = _cage_params(vert_count=6.0)
        bars = rule_cage_verticals(p, log)
        assert bars[0].qty == 6

    def test_vert_mark_is_V1(self, log):
        p = _cage_params()
        bars = rule_cage_verticals(p, log)
        assert bars[0].mark == "V1"

    def test_vert_shape_straight(self, log):
        p = _cage_params()
        bars = rule_cage_verticals(p, log)
        assert bars[0].shape == "Str"


class TestCageHoopsStandard:
    def test_ring_qty_5ft_16oc(self, log):
        """5ft cage @16oc: floor(60/16)+1 = 4 rings."""
        p = _cage_params(cage_depth_ft=5.0, ring_spacing_in=16.0)
        bars = rule_cage_hoops_standard(p, log)
        assert bars[0].qty == 4

    def test_ring_qty_6ft_12oc(self, log):
        """6ft cage @12oc: floor(72/12)+1 = 7 rings."""
        p = _cage_params(cage_depth_ft=6.0, ring_spacing_in=12.0)
        bars = rule_cage_hoops_standard(p, log)
        assert bars[0].qty == 7

    def test_ring_OD_and_length(self, log):
        """3ft hole, 3in cover → OD=30in; ring_len = π*30 + 36 = 130.25in."""
        p = _cage_params(hole_diameter_ft=3.0, cover_in=3.0, lap_ft=3.0)
        bars = rule_cage_hoops_standard(p, log)
        expected = _math.pi * 30.0 + 36.0
        assert bars[0].length_in == pytest.approx(expected, abs=0.01)

    def test_ring_shape_is_Rng(self, log):
        p = _cage_params()
        bars = rule_cage_hoops_standard(p, log)
        assert bars[0].shape == "Rng"

    def test_ring_mark_is_H1(self, log):
        p = _cage_params()
        bars = rule_cage_hoops_standard(p, log)
        assert bars[0].mark == "H1"


class TestCageHoopsConfinement:
    def test_no_confinement_returns_empty(self, log):
        """has_confinement_zone=0 → H2 list is empty."""
        p = _cage_params(has_confinement_zone=0.0)
        bars = rule_cage_hoops_confinement(p, log)
        assert bars == []

    def test_confinement_qty_3oc_6in(self, log):
        """Top 6in @3in oc: floor(6/3)+1 = 3 rings."""
        p = _cage_params(has_confinement_zone=1.0,
                         conf_spacing_in=3.0, confinement_depth_in=6.0)
        bars = rule_cage_hoops_confinement(p, log)
        assert bars[0].qty == 3

    def test_confinement_mark_is_H2(self, log):
        p = _cage_params(has_confinement_zone=1.0)
        bars = rule_cage_hoops_confinement(p, log)
        assert bars[0].mark == "H2"

    def test_confinement_same_ring_length_as_H1(self, log):
        """H2 ring length must equal H1 ring length (same OD, same lap)."""
        p = _cage_params(has_confinement_zone=1.0)
        h1 = rule_cage_hoops_standard(p, log)
        h2 = rule_cage_hoops_confinement(p, log)
        assert h1[0].length_in == pytest.approx(h2[0].length_in, abs=0.01)


class TestGenerateCageBarlist:
    def test_standard_cage_returns_V1_H1(self, log):
        """No confinement → exactly V1, H1."""
        bars = generate_barlist(CAGE_TEMPLATE, CAGE_TEMPLATE.input_defaults(),
                                log, call_ai=False)
        marks = {b.mark for b in bars}
        assert marks == {"V1", "H1"}

    def test_confinement_cage_returns_V1_H1_H2(self, log):
        """With confinement → V1, H1, H2."""
        params = CAGE_TEMPLATE.input_defaults()
        params["has_confinement_zone"] = 1.0
        bars = generate_barlist(CAGE_TEMPLATE, params, log, call_ai=False)
        marks = {b.mark for b in bars}
        assert marks == {"V1", "H1", "H2"}

    def test_all_bars_have_ref(self, log):
        """All cage bars must have a non-empty ref (ACI / SDC clause)."""
        bars = generate_barlist(CAGE_TEMPLATE, CAGE_TEMPLATE.input_defaults(),
                                log, call_ai=False)
        for b in bars:
            assert b.ref, f"{b.mark} missing ref"

    def test_gold_5ft_3ft_cage(self, log):
        """End-to-end gold check: 5ft×3ft cage → V1 66in × 4, H1 ~130.25in × 4."""
        params = {
            "cage_depth_ft": 5.0, "hole_diameter_ft": 3.0,
            "vert_bar_size": "#5", "vert_count": 4.0, "embed_in": 6.0,
            "ring_bar_size": "#5", "ring_spacing_in": 16.0,
            "lap_ft": 3.0, "cover_in": 3.0,
            "has_confinement_zone": 0.0, "conf_spacing_in": 3.0,
            "confinement_depth_in": 6.0,
        }
        bars = generate_barlist(CAGE_TEMPLATE, params, log, call_ai=False)
        bar_map = {b.mark: b for b in bars}
        assert bar_map["V1"].qty == 4
        assert bar_map["V1"].length_in == pytest.approx(66.0)
        assert bar_map["H1"].qty == 4
        assert bar_map["H1"].length_in == pytest.approx(_math.pi * 30 + 36, abs=0.01)


# ===========================================================================
# 11. Equipment Pad rule functions
# ===========================================================================

import math as _epad_math

from vistadetail.engine.rules.equipment_pad_rules import (
    rule_pad_bottom_long,
    rule_pad_bottom_short,
    rule_pad_top_long,
    rule_pad_top_short,
    rule_validate_equipment_pad,
)
from vistadetail.engine.templates.equipment_pad import TEMPLATE as EPAD_TEMPLATE
from vistadetail.engine.schema import Params


def _epad_params(**overrides):
    """Build a Params object for equipment pad tests."""
    defaults = EPAD_TEMPLATE.input_defaults()
    defaults.update(overrides)
    return EPAD_TEMPLATE.parse_and_validate(defaults)


class TestPadBottomLong:
    def test_length_formula(self, log):
        """P1 length = pad_length_in − 2×cover."""
        p = _epad_params(pad_length_ft=8.5, pad_width_ft=4.0,
                         spacing_in=12.0, cover_in=3.0, has_double_mat=0.0)
        bars = rule_pad_bottom_long(p, log)
        assert len(bars) == 1
        assert bars[0].mark == "P1"
        expected_len = 8.5 * 12 - 2 * 3.0   # 102 - 6 = 96.0 in
        assert bars[0].length_in == pytest.approx(expected_len)

    def test_qty_formula(self, log):
        """P1 qty = floor(pad_width_in / spacing_in)."""
        p = _epad_params(pad_length_ft=8.5, pad_width_ft=4.0,
                         spacing_in=12.0, cover_in=3.0, has_double_mat=0.0)
        bars = rule_pad_bottom_long(p, log)
        expected_qty = _epad_math.floor(4.0 * 12 / 12.0)   # floor(48/12) = 4
        assert bars[0].qty == expected_qty

    def test_mark_is_P1(self, log):
        """Mark must be P1."""
        p = _epad_params()
        bars = rule_pad_bottom_long(p, log)
        assert bars[0].mark == "P1"


class TestPadBottomShort:
    def test_length_formula(self, log):
        """P2 length = pad_width_in − 2×cover."""
        p = _epad_params(pad_length_ft=8.5, pad_width_ft=4.0,
                         spacing_in=12.0, cover_in=3.0)
        bars = rule_pad_bottom_short(p, log)
        expected_len = 4.0 * 12 - 2 * 3.0   # 48 - 6 = 42.0 in
        assert bars[0].length_in == pytest.approx(expected_len)

    def test_qty_formula(self, log):
        """P2 qty = floor(pad_length_in / spacing_in)."""
        p = _epad_params(pad_length_ft=8.5, pad_width_ft=4.0,
                         spacing_in=12.0, cover_in=3.0)
        bars = rule_pad_bottom_short(p, log)
        expected_qty = _epad_math.floor(8.5 * 12 / 12.0)   # floor(102/12) = 8
        assert bars[0].qty == expected_qty

    def test_mark_is_P2(self, log):
        p = _epad_params()
        bars = rule_pad_bottom_short(p, log)
        assert bars[0].mark == "P2"


class TestPadTopMat:
    def test_single_mat_produces_no_top_bars(self, log):
        """Equipment pad has_double_mat hardcoded 0.0 → P3 and P4 always return empty."""
        p = _epad_params()
        assert rule_pad_top_long(p, log) == []
        assert rule_pad_top_short(p, log) == []


class TestGenerateEquipmentPadBarlist:
    def test_single_mat_marks(self, log):
        """Equipment pad hardcodes single mat → only P1 and P2."""
        params = EPAD_TEMPLATE.input_defaults()
        bars = generate_barlist(EPAD_TEMPLATE, params, log, call_ai=False)
        marks = {b.mark for b in bars}
        assert marks == {"P1", "P2"}

    def test_all_bars_have_ref(self, log):
        """All generated bars must have a populated ref field."""
        bars = generate_barlist(EPAD_TEMPLATE, EPAD_TEMPLATE.input_defaults(),
                                log, call_ai=False)
        for b in bars:
            assert b.ref, f"{b.mark} missing ref"

    def test_gold_concrete_pad_8ft6_by_4ft1(self, log):
        """
        Gold check: PDF 1 (1.s3.concrete.pad.plans.pdf)
        8'-6" × 4'-1" pad, 6" thick. cover=3.0 and spacing=12.0 now hardcoded.
          P1: qty = floor(49/12) = 4, len = 102-6 = 96.0 in  (8'-0")
          P2: qty = floor(102/12) = 8, len = 49-6  = 43.0 in  (3'-7")
        Note: 8'-6" = 102 in, 4'-1" = 49 in.
        """
        params = {
            "pad_length_ft": 8.5,
            "pad_width_ft":  4.0833,   # ≈ 4'-1"
            "pad_thickness_in": 6.0,
        }
        bars = generate_barlist(EPAD_TEMPLATE, params, log, call_ai=False)
        bar_map = {b.mark: b for b in bars}

        # P1 long bars
        assert bar_map["P1"].length_in == pytest.approx(96.0, abs=0.1)
        assert bar_map["P1"].qty == 4

        # P2 short bars (4'-1" = 49in, 49-6=43in)
        assert bar_map["P2"].length_in == pytest.approx(43.0, abs=0.2)
        assert bar_map["P2"].qty == 8


# ===========================================================================
# 12. Switchboard Pad template (double mat + vertical dowels)
# ===========================================================================

from vistadetail.engine.rules.equipment_pad_rules import rule_pad_vertical_dowels
from vistadetail.engine.templates.switchboard_pad import TEMPLATE as SWBD_TEMPLATE


def _swbd_params(**overrides):
    defaults = SWBD_TEMPLATE.input_defaults()
    defaults.update(overrides)
    return SWBD_TEMPLATE.parse_and_validate(defaults)


class TestPadVerticalDowels:
    def test_no_dowels_when_disabled(self, log):
        p = _swbd_params(has_vertical_dowels=0.0)
        assert rule_pad_vertical_dowels(p, log) == []

    def test_dowel_length_formula(self, log):
        """D1 length = embed(12) + project(18) = 30 in (hardcoded)."""
        p = _swbd_params(has_vertical_dowels=1.0)
        bars = rule_pad_vertical_dowels(p, log)
        assert bars[0].length_in == pytest.approx(30.0)

    def test_dowel_qty_grid(self, log):
        """D1 qty = floor(L/12) × floor(W/12) (spacing hardcoded 12)."""
        import math as _m
        p = _swbd_params(pad_length_ft=9.6, pad_width_ft=4.0,
                         has_vertical_dowels=1.0)
        bars = rule_pad_vertical_dowels(p, log)
        expected = _m.floor(9.6 * 12 / 12) * _m.floor(4.0 * 12 / 12)
        assert bars[0].qty == expected

    def test_mark_is_D1(self, log):
        p = _swbd_params(has_vertical_dowels=1.0)
        bars = rule_pad_vertical_dowels(p, log)
        assert bars[0].mark == "D1"


class TestGenerateSwitchboardPadBarlist:
    def test_always_double_mat(self, log):
        """Switchboard pad always generates P1–P4 (double mat fixed)."""
        bars = generate_barlist(SWBD_TEMPLATE, SWBD_TEMPLATE.input_defaults(),
                                log, call_ai=False)
        marks = {b.mark for b in bars}
        assert {"P1", "P2", "P3", "P4"}.issubset(marks)

    def test_with_dowels_adds_D1(self, log):
        params = SWBD_TEMPLATE.input_defaults()
        params["has_vertical_dowels"] = 1.0
        bars = generate_barlist(SWBD_TEMPLATE, params, log, call_ai=False)
        marks = {b.mark for b in bars}
        assert "D1" in marks

    def test_without_dowels_no_D1(self, log):
        params = SWBD_TEMPLATE.input_defaults()
        params["has_vertical_dowels"] = 0.0
        bars = generate_barlist(SWBD_TEMPLATE, params, log, call_ai=False)
        marks = {b.mark for b in bars}
        assert "D1" not in marks

    def test_gold_9ft6_by_4ft_double_mat(self, log):
        """
        Gold check: Doublemat.verticaldowels.9.6x4.clean.pdf
        9.6' × 4', double mat, #4@12oc, 3" cover (all hardcoded), vertical dowels.
          P1 (bot long):  qty=floor(48/12)=4,  len=115.2-6=109.2 in
          P2 (bot short): qty=floor(115.2/12)=9, len=48-6=42 in
          P3 (top long):  qty=4, len=109.2 in
          P4 (top short): qty=9, len=42 in
          D1 (dowels):    qty=floor(115.2/12)×floor(48/12)=9×4=36
        """
        params = {
            "pad_length_ft": 9.6, "pad_width_ft": 4.0,
            "pad_thickness_in": 8.0,
            "has_vertical_dowels": 1.0,
        }
        bars = generate_barlist(SWBD_TEMPLATE, params, log, call_ai=False)
        bar_map = {b.mark: b for b in bars}

        assert bar_map["P1"].qty == 4
        assert bar_map["P1"].length_in == pytest.approx(9.6 * 12 - 6, abs=0.1)
        assert bar_map["P2"].qty == 9
        assert bar_map["P2"].length_in == pytest.approx(4.0 * 12 - 6, abs=0.1)
        assert bar_map["D1"].qty == 4 * 9   # 36 total dowels
        assert bar_map["D1"].length_in == pytest.approx(30.0)


# ===========================================================================
# 13. Seatwall rule functions
# ===========================================================================

import math as _sw_math

from vistadetail.engine.rules.seatwall_rules import (
    rule_seatwall_top_long,
    rule_seatwall_bot_long,
    rule_seatwall_transverse,
)
from vistadetail.engine.templates.seatwall import TEMPLATE as SW_TEMPLATE


def _sw_params(**overrides):
    defaults = SW_TEMPLATE.input_defaults()
    defaults.update(overrides)
    return SW_TEMPLATE.parse_and_validate(defaults)


class TestSeatwallTopLong:
    def test_length_formula(self, log):
        """S1 length = wall_length_in − 2×cover."""
        p = _sw_params(wall_length_ft=31.0, cover_in=1.5)
        bars = rule_seatwall_top_long(p, log)
        assert bars[0].length_in == pytest.approx(31.0 * 12 - 3.0, abs=0.01)

    def test_qty_equals_top_bar_count(self, log):
        p = _sw_params(top_bar_count=3.0)
        bars = rule_seatwall_top_long(p, log)
        assert bars[0].qty == 3

    def test_mark_is_S1(self, log):
        p = _sw_params()
        assert rule_seatwall_top_long(p, log)[0].mark == "S1"


class TestSeatwallBotLong:
    def test_length_matches_top(self, log):
        """S1 and S2 share the same length formula."""
        p = _sw_params(wall_length_ft=15.0, cover_in=1.5)
        top = rule_seatwall_top_long(p, log)
        bot = rule_seatwall_bot_long(p, log)
        assert top[0].length_in == pytest.approx(bot[0].length_in)

    def test_mark_is_S2(self, log):
        p = _sw_params()
        assert rule_seatwall_bot_long(p, log)[0].mark == "S2"


class TestSeatwallTransverse:
    def test_length_formula(self, log):
        """S3 length = wall_width_in − 2×cover."""
        p = _sw_params(wall_width_in=14.0, cover_in=1.5)
        bars = rule_seatwall_transverse(p, log)
        assert bars[0].length_in == pytest.approx(14.0 - 3.0)

    def test_qty_formula(self, log):
        """S3 qty = floor(wall_length_in / tie_spacing)."""
        p = _sw_params(wall_length_ft=31.0, tie_spacing_in=18.0)
        bars = rule_seatwall_transverse(p, log)
        expected = _sw_math.floor(31.0 * 12 / 18.0)
        assert bars[0].qty == expected

    def test_mark_is_S3(self, log):
        p = _sw_params()
        assert rule_seatwall_transverse(p, log)[0].mark == "S3"


class TestGenerateSeatwallBarlist:
    def test_marks_present(self, log):
        bars = generate_barlist(SW_TEMPLATE, SW_TEMPLATE.input_defaults(),
                                log, call_ai=False)
        marks = {b.mark for b in bars}
        assert marks == {"S1", "S2", "S3"}

    def test_all_bars_have_ref(self, log):
        bars = generate_barlist(SW_TEMPLATE, SW_TEMPLATE.input_defaults(),
                                log, call_ai=False)
        for b in bars:
            assert b.ref, f"{b.mark} missing ref"

    def test_gold_31ft_seatwall(self, log):
        """
        Gold check: Portola.ES.seatwall.31x2 → 31' wall, 18" height, 14" width.
          S1: qty=2, len=31*12-3=369 in (30'-9")
          S2: qty=2, len=369 in
          S3: qty=floor(372/18)=20, len=14-3=11 in
        """
        params = {
            "wall_length_ft": 31.0, "wall_height_in": 18.0, "wall_width_in": 14.0,
            "top_bar_size": "#4", "top_bar_count": 2.0,
            "bot_bar_size": "#4", "bot_bar_count": 2.0,
            "tie_bar_size": "#3", "tie_spacing_in": 18.0, "cover_in": 1.5,
        }
        bars = generate_barlist(SW_TEMPLATE, params, log, call_ai=False)
        bar_map = {b.mark: b for b in bars}
        assert bar_map["S1"].qty == 2
        assert bar_map["S1"].length_in == pytest.approx(369.0)
        assert bar_map["S2"].qty == 2
        assert bar_map["S3"].qty == _sw_math.floor(372 / 18)
        assert bar_map["S3"].length_in == pytest.approx(11.0)


# ===========================================================================
# 14. Pipe Encasement, Fuel Foundation, Dual Slab smoke tests
# ===========================================================================

from vistadetail.engine.templates.pipe_encasement import TEMPLATE as PE_TEMPLATE
from vistadetail.engine.templates.fuel_foundation import TEMPLATE as FF_TEMPLATE
from vistadetail.engine.templates.dual_slab import TEMPLATE as DS_TEMPLATE
import math as _m3


class TestPipeEncasement:
    def test_hoop_length_formula(self, log):
        """E1 hoop length = 2(W-2c) + 2(H-2c)."""
        params = PE_TEMPLATE.input_defaults()
        params.update({"encasement_width_in": 44.0, "encasement_height_in": 44.0,
                        "cover_in": 2.0})
        bars = generate_barlist(PE_TEMPLATE, params, log, call_ai=False)
        e1 = next(b for b in bars if b.mark == "E1")
        expected = 2 * (44.0 - 4.0) + 2 * (44.0 - 4.0)   # = 160 in
        assert e1.length_in == pytest.approx(expected)

    def test_hoop_qty_formula(self, log):
        """E1 qty = floor(length_in / spacing)."""
        params = PE_TEMPLATE.input_defaults()
        params.update({"encasement_length_ft": 234.0, "hoop_spacing_in": 9.0})
        bars = generate_barlist(PE_TEMPLATE, params, log, call_ai=False)
        e1 = next(b for b in bars if b.mark == "E1")
        expected = _m3.floor(234.0 * 12 / 9.0)
        assert e1.qty == expected

    def test_marks_present(self, log):
        bars = generate_barlist(PE_TEMPLATE, PE_TEMPLATE.input_defaults(),
                                log, call_ai=False)
        marks = {b.mark for b in bars}
        assert {"E1", "E2"}.issubset(marks)

    def test_all_bars_have_ref(self, log):
        bars = generate_barlist(PE_TEMPLATE, PE_TEMPLATE.input_defaults(),
                                log, call_ai=False)
        for b in bars:
            assert b.ref, f"{b.mark} missing ref"

    def test_gold_route118_234ft_encasement(self, log):
        """
        Gold: Route 118 Sand Canyon encasement — 234 linear ft, #5@9oc, n_long_bars=12.
          E1 qty = floor(2808/9) = 312
          E2: run = 2808-4 = 2804", ld=#4=12", lap=ceil(1.3*12)=16",
              effective/piece = 720-16 = 704", pieces = ceil(2804/704) = 4
              qty = 12 positions * 4 pieces = 48 bars @ 60'-0" (stock)
        """
        params = {
            "encasement_length_ft": 234.0,
            "encasement_width_in": 44.0, "encasement_height_in": 44.0,
            "hoop_bar_size": "#5", "hoop_spacing_in": 9.0,
            "long_bar_size": "#4", "n_long_bars": 12.0, "cover_in": 2.0,
        }
        bars = generate_barlist(PE_TEMPLATE, params, log, call_ai=False)
        bar_map = {b.mark: b for b in bars}
        assert bar_map["E1"].qty == _m3.floor(2808 / 9)
        assert bar_map["E2"].qty == 48          # 12 positions x 4 pieces (spliced run)
        assert bar_map["E2"].length_in == 720.0 # 60ft stock bar per piece


class TestFuelFoundation:
    def test_double_mat_marks(self, log):
        """Fuel foundation always double mat (has_top_mat hardcoded 1.0)."""
        params = FF_TEMPLATE.input_defaults()
        bars = generate_barlist(FF_TEMPLATE, params, log, call_ai=False)
        marks = {b.mark for b in bars}
        assert {"F1", "F2", "F3", "F4"}.issubset(marks)

    def test_all_bars_have_ref(self, log):
        bars = generate_barlist(FF_TEMPLATE, FF_TEMPLATE.input_defaults(),
                                log, call_ai=False)
        for b in bars:
            assert b.ref, f"{b.mark} missing ref"


class TestDualSlab:
    def test_marks_A_and_B_present(self, log):
        bars = generate_barlist(DS_TEMPLATE, DS_TEMPLATE.input_defaults(),
                                log, call_ai=False)
        marks = {b.mark for b in bars}
        assert marks == {"A1", "A2", "B1", "B2"}

    def test_all_bars_have_ref(self, log):
        bars = generate_barlist(DS_TEMPLATE, DS_TEMPLATE.input_defaults(),
                                log, call_ai=False)
        for b in bars:
            assert b.ref, f"{b.mark} missing ref"


# ===========================================================================
# 15. Bend Reduction table + C-bar headwall tests
# ===========================================================================

from vistadetail.engine.hooks import bend_reduce
from vistadetail.engine.rules.headwall_rules import (
    _d89_by_height,
    rule_hw_d_bars,
    rule_hw_trans_footing,
    rule_hw_long_invert,
    rule_hw_long_wall,
    rule_hw_top_wall,
    rule_hw_vert_wall,
    rule_hw_c_bars,
    rule_hw_spreaders,
    rule_hw_standees,
)
from vistadetail.engine.templates.headwall import TEMPLATE as HW_TEMPLATE


class TestBendReduction:
    def test_shape2_no4(self):
        """#4 U-shape (C-bar): deduct 2 in."""
        assert bend_reduce("shape_2", "#4") == pytest.approx(2.0)

    def test_shape2_no5(self):
        """#5 U-shape (C-bar): deduct 3 in — from Vista Steel scan table."""
        assert bend_reduce("shape_2", "#5") == pytest.approx(3.0)

    def test_shape4_no4(self):
        """#4 closed rectangular hoop (4 bends): deduct 4 in."""
        assert bend_reduce("shape_4", "#4") == pytest.approx(4.0)

    def test_shape1_no6(self):
        """#6 L-bar (1 bend): deduct 2 in."""
        assert bend_reduce("shape_1", "#6") == pytest.approx(2.0)

    def test_per_90_no5(self):
        """#5 per-90 deduction: 1.25 in per bend."""
        assert bend_reduce("per_90", "#5") == pytest.approx(1.25)

    def test_unknown_shape_raises(self):
        with pytest.raises(ValueError, match="Unknown bend shape"):
            bend_reduce("shape_9", "#4")

    def test_unknown_size_raises(self):
        with pytest.raises(ValueError, match="#99"):
            bend_reduce("shape_2", "#99")


def _hw_params(**overrides):
    defaults = HW_TEMPLATE.input_defaults()
    defaults.update(overrides)
    return HW_TEMPLATE.parse_and_validate(defaults)


class TestHeadwallD89A:
    """
    Gold tests for Straight Headwall (D89A) template.

    Reference case: wall_height_ft=5'-11\" (71\"), wall_width=8'-0\".
    D89A table row H=71\": W=64\", T=10\", F=12\", B=48\", C=16\".
    H1 = 71+12 = 83\".
    """

    def test_d1_mark_and_size(self, log):
        # H=71 → D89A row H=71 → d_s="#6".  No-pipe doesn't change bar size.
        p = _hw_params(wall_width_ft=8.0, wall_height_ft=5 + 11/12)
        bars = rule_hw_d_bars(p, log)
        assert bars[0].mark == "D1"
        assert bars[0].size == "#6"

    def test_d1_gold(self, log):
        """D1: qty=floor(96/8)+1=13, len=W-4=64-4=60\"=5'-0\"."""
        p = _hw_params(wall_width_ft=8.0, wall_height_ft=5 + 11/12)
        bars = rule_hw_d_bars(p, log)
        assert bars[0].qty == 13
        assert bars[0].length_in == pytest.approx(60.0)

    def test_tf_gold(self, log):
        """TF: qty=floor(96/12)+1=9, len=W-4=64-4=60\"."""
        p = _hw_params(wall_width_ft=8.0, wall_height_ft=5 + 11/12)
        bars = rule_hw_trans_footing(p, log)
        assert bars[0].mark == "TF"
        assert bars[0].qty == 9
        assert bars[0].length_in == pytest.approx(60.0)

    def test_li_gold(self, log):
        """LI: qty=2*floor(64/8)=16, len=96-6=90\"=7'-6\"."""
        p = _hw_params(wall_width_ft=8.0, wall_height_ft=5 + 11/12)
        bars = rule_hw_long_invert(p, log)
        assert bars[0].mark == "LI"
        assert bars[0].qty == 16
        assert bars[0].length_in == pytest.approx(90.0)

    def test_lw_gold(self, log):
        """LW: qty=2*(floor(83/12)+1)=14, len=92\"=7'-8\"."""
        p = _hw_params(wall_width_ft=8.0, wall_height_ft=5 + 11/12)
        bars = rule_hw_long_wall(p, log)
        assert bars[0].mark == "LW"
        assert bars[0].qty == 14
        assert bars[0].length_in == pytest.approx(92.0)

    def test_tw_gold(self, log):
        """TW: 3 × #5 @ 7'-8\"."""
        p = _hw_params(wall_width_ft=8.0, wall_height_ft=5 + 11/12)
        bars = rule_hw_top_wall(p, log)
        assert bars[0].mark == "TW"
        assert bars[0].qty == 3
        assert bars[0].size == "#5"
        assert bars[0].length_in == pytest.approx(92.0)

    def test_vw_gold(self, log):
        """VW: qty=9 (TABLE D=0,H=71 → nearest (D=0,H=60) → vert=9),
        len=ceil((71+18)/6)*6=ceil(89/6)*6=15*6=90\"=7'-6\"."""
        p = _hw_params(wall_width_ft=8.0, wall_height_ft=5 + 11/12)
        bars = rule_hw_vert_wall(p, log)
        assert bars[0].mark == "VW"
        assert bars[0].qty == 9
        assert bars[0].length_in == pytest.approx(90.0)

    def test_cb_gold(self, log):
        """CB: H=71 → c_s="#5" (D89A row H=71), qty=9 (TABLE D=0,H=71→(D=0,H=60)→c_bar=9),
        body=ceil((71+9)/2)*2=80\", leg_b=T+2=12\", leg_c=T+4=14\", stock=80+28-3=105\"."""
        p = _hw_params(wall_width_ft=8.0, wall_height_ft=5 + 11/12)
        bars = rule_hw_c_bars(p, log)
        assert bars[0].mark == "CB"
        assert bars[0].size == "#5"
        assert bars[0].shape == "C"
        assert bars[0].qty == 9
        assert bars[0].length_in == pytest.approx(105.0)
        assert bars[0].leg_a_in == pytest.approx(80.0)
        assert bars[0].leg_b_in == pytest.approx(12.0)   # B = T+2 (C-2)
        assert bars[0].leg_c_in == pytest.approx(14.0)   # C = T+4
        assert bars[0].leg_d_in == pytest.approx(71.0)

    def test_ws_gold(self, log):
        """WS: qty=floor(96/24)=4, stock=12\"."""
        p = _hw_params(wall_width_ft=8.0, wall_height_ft=5 + 11/12)
        bars = rule_hw_spreaders(p, log)
        assert bars[0].mark == "WS"
        assert bars[0].qty == 4
        assert bars[0].length_in == pytest.approx(12.0)

    def test_st_gold(self, log):
        """ST: no-pipe → #5, qty=L_ft=8, stock=5+5.5+5.5+18-bend_reduce(shape_3,#5)=34-4.5=29.5\"."""
        p = _hw_params(wall_width_ft=8.0, wall_height_ft=5 + 11/12)
        bars = rule_hw_standees(p, log)
        assert bars[0].mark == "ST"
        assert bars[0].size == "#5"
        assert bars[0].qty == 8
        assert bars[0].length_in == pytest.approx(29.5)

    def test_d89_rounds_up(self, log):
        """H=5'-0\" (60\") rounds up to row H=62\", W=64\" → D1 len=60\"."""
        p = _hw_params(wall_width_ft=8.0, wall_height_ft=5.0)
        bars = rule_hw_d_bars(p, log)
        assert bars[0].length_in == pytest.approx(60.0)

    def test_d89_exact_match(self, log):
        """H=5'-11\" (71\") exact row match → W=64\" → D1 len=60\"."""
        p = _hw_params(wall_width_ft=8.0, wall_height_ft=5 + 11/12)
        bars = rule_hw_d_bars(p, log)
        assert bars[0].length_in == pytest.approx(60.0)


# ---------------------------------------------------------------------------
# 16. Headwall D89A — full table coverage (all 13 rows)
# ---------------------------------------------------------------------------

class TestHeadwallTableCoverage:
    """
    Verifies D1 length (= W-4), VW length (= H1-4 = H+8), and
    CB body/inner across every D89A table row at exact matching heights.
    """

    # (wall_height_in, W, T, F, B)  — B+F = D1/TF transverse length
    _TABLE_ROWS = [
        (47,  58, 10, 12, 46),   # 3'-11"
        (50,  58, 10, 12, 46),   # 4'-2"
        (53,  60, 10, 12, 48),   # 4'-5"
        (56,  64, 10, 12, 48),   # 4'-8"
        (59,  64, 10, 12, 48),   # 4'-11"
        (62,  64, 10, 12, 48),   # 5'-2"
        (65,  64, 10, 12, 48),   # 5'-5"
        (68,  64, 10, 12, 48),   # 5'-8"
        (71,  64, 10, 12, 48),   # 5'-11"  ← gold reference
        (74,  64, 12, 14, 48),   # 6'-2"   T and F change
        (77,  66, 12, 14, 48),   # 6'-5"   W widens
        (80,  69, 12, 14, 51),   # 6'-8"   B widens
        (83,  72, 12, 14, 54),   # 6'-11"  max row
    ]

    @pytest.mark.parametrize("H_in,W,T,F,B", _TABLE_ROWS)
    def test_d1_length_all_rows(self, log, H_in, W, T, F, B):
        """D1 length = B+F across every table row."""
        p = _hw_params(wall_width_ft=8.0, wall_height_ft=H_in / 12.0)
        bars = rule_hw_d_bars(p, log)
        assert bars[0].length_in == pytest.approx(B + F), \
            f"H={H_in}\" → expected B+F={B+F}\" (B={B}, F={F})"

    @pytest.mark.parametrize("H_in,W,T,F,B", _TABLE_ROWS)
    def test_vw_length_all_rows(self, log, H_in, W, T, F, B):
        """VW length = H + F + 7 across every table row (H=input height, F from table)."""
        p = _hw_params(wall_width_ft=8.0, wall_height_ft=H_in / 12.0)
        bars = rule_hw_vert_wall(p, log)
        assert bars[0].length_in == pytest.approx(H_in + F + 7.0), \
            f"H={H_in}\" → VW expected H+F+7={H_in+F+7}\""

    @pytest.mark.parametrize("H_in,W,T,F,B", _TABLE_ROWS)
    def test_cb_body_inner_all_rows(self, log, H_in, W, T, F, B):
        """CB body = ceil((H+9)/2)*2; CB inner = H across every table row."""
        p = _hw_params(wall_width_ft=8.0, wall_height_ft=H_in / 12.0)
        bars = rule_hw_c_bars(p, log)
        expected_body = math.ceil((H_in + 9) / 2) * 2
        assert bars[0].leg_a_in == pytest.approx(expected_body), \
            f"H={H_in}\" → CB body expected ceil(({H_in}+9)/2)*2={expected_body}\""
        assert bars[0].leg_d_in == pytest.approx(float(H_in)), \
            f"H={H_in}\" → CB inner expected {H_in}\""


# ---------------------------------------------------------------------------
# 17. Headwall D89A — height rounding (inputs between rows)
# ---------------------------------------------------------------------------

class TestHeadwallHeightRounding:
    """
    Inputs between table rows should round UP to the next row.
    Tests that the lookup selects the correct row W and H+8 VW length.
    """

    @pytest.mark.parametrize("h_ft", [
        3 + 10/12,   # 3'-10" → row H=47"
        4 + 0/12,    # 4'-0"  → row H=50"  (48<50)
        4 + 3/12,    # 4'-3"  → row H=53"  (51<53)
        4 + 6/12,    # 4'-6"  → row H=56"  (54<56)
        5 + 0/12,    # 5'-0"  → row H=62"  (60<62)
        5 + 6/12,    # 5'-6"  → row H=68"  (66<68)
        6 + 0/12,    # 6'-0"  → row H=74"  (72<74)
        6 + 4/12,    # 6'-4"  → row H=77"  (76<77)
    ])
    def test_rounding_d1_and_vw(self, log, h_ft):
        """D1 = B+F and VW = H_input+F+7 after rounding up to the next table row."""
        row = _d89_by_height(h_ft * 12, "I")
        p   = _hw_params(wall_width_ft=8.0, wall_height_ft=h_ft)
        d1  = rule_hw_d_bars(p, log)
        vw  = rule_hw_vert_wall(p, log)
        expected_d1 = row["B"] + row["F"]
        expected_vw = h_ft * 12 + row["F"] + 7.0
        assert d1[0].length_in == pytest.approx(expected_d1), \
            f"h_ft={h_ft:.3f} → D1 expected B+F={expected_d1}\""
        assert vw[0].length_in == pytest.approx(expected_vw), \
            f"h_ft={h_ft:.3f} → VW expected h_in+F+7={expected_vw}\""


# ---------------------------------------------------------------------------
# 18. Headwall D89A — wall width variation
# ---------------------------------------------------------------------------

class TestHeadwallWidthVariants:
    """
    Holds H fixed at 5'-11\" (71\", row W=64\") and varies wall_width_ft.
    Tests bar counts and lengths that depend on L.
    """

    # (wall_width_ft, L_in,  D1_qty, TF_qty, LI_qty, LW_len, VW_qty, WS_qty, ST_qty)
    _WIDTHS = [
        (4.0,   48, 7,  5,  16, 44,  5,  2,  4),
        (8.0,   96, 13, 9,  16, 92,  9,  4,  8),
        (12.0, 144, 19, 13, 16, 140, 13, 6, 12),
        (16.0, 192, 25, 17, 16, 188, 17, 8, 16),
        (20.0, 240, 31, 21, 16, 236, 21, 10, 20),
    ]

    @pytest.mark.parametrize(
        "w_ft,L,D1q,TFq,LIq,LWlen,VWq,WSq,STq", _WIDTHS
    )
    def test_all_qty_and_length(self, log, w_ft, L, D1q, TFq, LIq, LWlen, VWq, WSq, STq):
        """Verify every mark's qty/length for a range of wall widths."""
        H_ft = 5 + 11/12   # fixed at 5'-11"
        p    = _hw_params(wall_width_ft=w_ft, wall_height_ft=H_ft)

        d1 = rule_hw_d_bars(p, log)
        tf = rule_hw_trans_footing(p, log)
        li = rule_hw_long_invert(p, log)
        lw = rule_hw_long_wall(p, log)
        vw = rule_hw_vert_wall(p, log)
        ws = rule_hw_spreaders(p, log)
        st = rule_hw_standees(p, log)

        assert d1[0].qty    == D1q,   f"D1 qty w={w_ft}'"
        assert tf[0].qty    == TFq,   f"TF qty w={w_ft}'"
        assert li[0].qty    == LIq,   f"LI qty w={w_ft}'"
        assert lw[0].length_in == pytest.approx(LWlen), f"LW len w={w_ft}'"
        assert vw[0].qty    == VWq,   f"VW qty w={w_ft}'"
        assert ws[0].qty    == WSq,   f"WS qty w={w_ft}'"
        assert st[0].qty    == STq,   f"ST qty w={w_ft}'"

    @pytest.mark.parametrize("w_ft", [4.0, 8.0, 12.0, 16.0, 20.0])
    def test_vw_length_independent_of_width(self, log, w_ft):
        """VW length depends only on H, not on wall width.
        H=71\", F=12\" → VW = 71+12+7 = 90\" = 7'-6\"."""
        p  = _hw_params(wall_width_ft=w_ft, wall_height_ft=5 + 11/12)
        vw = rule_hw_vert_wall(p, log)
        assert vw[0].length_in == pytest.approx(90.0), \
            f"VW length should be 90\" regardless of width (got {vw[0].length_in})"


# ---------------------------------------------------------------------------
# 19. Headwall D89A — end-to-end full barlist generation
# ---------------------------------------------------------------------------

class TestHeadwallEndToEnd:
    """Full generate_barlist() calls to catch any integration issues."""

    @pytest.mark.parametrize("h_ft,w_ft", [
        (3 + 11/12, 4.0),    # min height, min width
        (5 + 2/12,  8.0),    # common 5'-2" case
        (5 + 11/12, 8.0),    # gold reference
        (6 + 2/12, 12.0),    # T/F change row, wider wall
        (6 + 11/12, 16.0),   # max table row
    ])
    def test_full_barlist_generates_9_marks(self, log, h_ft, w_ft):
        """All 9 marks (D1 TF LI LW TW VW CB WS ST) present in every barlist."""
        from vistadetail.engine.calculator import generate_barlist
        params = {"wall_width_ft": w_ft, "wall_height_ft": h_ft,
                  "pipe_qty": 0, "pipe_dia_in": "24\""}
        from vistadetail.engine.templates.headwall import TEMPLATE as HW
        bars = generate_barlist(HW, params, log, call_ai=False)
        marks = {b.mark for b in bars}
        for mark in ("D1", "TF", "LI", "LW", "TW", "VW", "CB", "WS", "ST"):
            assert mark in marks, \
                f"Mark {mark} missing from barlist h={h_ft:.2f} w={w_ft}"

    def test_no_zero_qty_bars(self, log):
        """No bar row should have qty <= 0 for any valid input."""
        from vistadetail.engine.calculator import generate_barlist
        from vistadetail.engine.templates.headwall import TEMPLATE as HW
        for h_ft in [3 + 11/12, 5 + 2/12, 5 + 11/12, 6 + 2/12, 6 + 11/12]:
            for w_ft in [4.0, 8.0, 16.0]:
                params = {"wall_width_ft": w_ft, "wall_height_ft": h_ft,
                          "pipe_qty": 0, "pipe_dia_in": "24\""}
                bars = generate_barlist(HW, params, log, call_ai=False)
                for b in bars:
                    assert b.qty > 0, \
                        f"Zero qty on {b.mark} h={h_ft:.2f} w={w_ft}"


# ---------------------------------------------------------------------------
# 20. Headwall D89A — pipe-case gold tests (from physical barlists)
# ---------------------------------------------------------------------------

class TestHeadwallPipeGold:
    """
    Gold tests using physical barlists for headwalls with pipes.

    Formula for pipe VW length: ceil((H+18)/6)*6  (VistaProgram reference).

    References:
      schoolhouse: sb.county.schoolhouse.road.headwall.8ft.long.barlist.pdf
        D=36\", H=5'-11\" (71\"), L=8'-0\" (96\")
        VW: qty=12, len=ceil(89/6)*6=90\"=7'-6\"
      vista: vista.headwall.10ft.48inpipe.barlist.pdf
        D=48\", H=7'-6\" (90\"), L=10'-0\" (120\")
        VW: qty=10, len=ceil(108/6)*6=108\"=9'-0\"
    """

    def test_vw_pipe_schoolhouse(self, log):
        """Schoolhouse gold: D=36\", H=71\" → VW qty=12, len=90\" (=7'-6\")."""
        p  = _hw_params(wall_width_ft=8.0, wall_height_ft=71/12,
                        pipe_qty=1, pipe_dia_in='36"')
        vw = rule_hw_vert_wall(p, log)
        assert vw[0].qty == 12, f"VW qty: expected 12, got {vw[0].qty}"
        assert vw[0].length_in == pytest.approx(90.0), \
            f"VW len: expected 90\" (7'-6\"), got {vw[0].length_in}\""

    def test_vw_pipe_vista_10ft(self, log):
        """Vista gold: D=48\", H=90\" → VW qty=10, len=108\" (=9'-0\")."""
        p  = _hw_params(wall_width_ft=10.0, wall_height_ft=90/12,
                        pipe_qty=1, pipe_dia_in='48"')
        vw = rule_hw_vert_wall(p, log)
        assert vw[0].qty == 10, f"VW qty: expected 10, got {vw[0].qty}"
        assert vw[0].length_in == pytest.approx(108.0), \
            f"VW len: expected 108\" (9'-0\"), got {vw[0].length_in}\""

    @pytest.mark.parametrize("H_in,D_in,expected_len", [
        (71,  36,  90),   # ceil((71+18)/6)*6 = ceil(89/6)*6 = 15*6 = 90  (schoolhouse gold)
        (90,  48, 108),   # ceil((90+18)/6)*6 = ceil(108/6)*6 = 18*6 = 108 (vista gold)
        (60,  24,  78),   # ceil((60+18)/6)*6 = ceil(78/6)*6  = 13*6 = 78  (formula check)
        (65,  36,  84),   # ceil((65+18)/6)*6 = ceil(83/6)*6  = 14*6 = 84  (formula check)
    ])
    def test_vw_pipe_formula_parametric(self, log, H_in, D_in, expected_len):
        """VW pipe formula ceil((H+18)/6)*6 across confirmed and derived cases."""
        dia_str = f'{D_in}"'
        p = _hw_params(wall_width_ft=8.0, wall_height_ft=H_in/12,
                       pipe_qty=1, pipe_dia_in=dia_str)
        vw = rule_hw_vert_wall(p, log)
        assert vw[0].length_in == pytest.approx(expected_len), \
            f"H={H_in}\", D={D_in}\" → VW expected {expected_len}\""


# ===========================================================================
# 16. G2 Inlet — DS400 gold barlist tests
# ===========================================================================

from vistadetail.engine.rules.inlet_wall_rules import (
    rule_g2_geometry,
    rule_g2_bottom_mat,
    rule_g2_horizontals,
    rule_g2_verticals,
    rule_g2_ab_bars,
    rule_g2_right_angle,
    rule_g2_hoops,
)
from vistadetail.engine.templates.inlet_9in_wall import TEMPLATE as G2_TEMPLATE


def _g2_params(**overrides):
    """Build Params for G2 Inlet using template defaults + geometry pre-run."""
    defaults = G2_TEMPLATE.input_defaults()
    defaults.update(overrides)
    p = G2_TEMPLATE.parse_and_validate(defaults)
    from vistadetail.engine.reasoning_logger import ReasoningLogger
    dummy_log = ReasoningLogger(sheet=None)
    rule_g2_geometry(p, dummy_log)
    return p


class TestG2InletGoldEx1:
    """
    DS400 ex1 gold barlist: T=9", H=6', X_int=60", Y_int=36" (fixed).

    X_ext = 78" (x_dim_ft = 6.5), y_ext = 54", h_adj = 77"
    gut_dim = 60 + 9 - 29 = 40", ab_bar_len = 54 - 4.5 + 16 = 65.5"
    y_bar = 48", x_bar = 72"

    Reference: /data/gold/g2_inlet/ds400.ex1.g2.barlist.pdf
    """

    @pytest.fixture
    def p(self):
        # x_dim_ft = (60 + 2×9) / 12 = 78/12 = 6.5 ft
        return _g2_params(x_dim_ft=78 / 12, wall_height_ft=6.0, wall_thick_in=9,
                          grate_type="Type 24", num_structures=1)

    def test_geometry_derived_values(self, p):
        assert p.x_ext_in == pytest.approx(78.0)
        assert p.y_ext_in == pytest.approx(54.0)
        assert p.x_inside_in == pytest.approx(60.0)
        assert p.y_inside_in == pytest.approx(36.0)
        assert p.h_adj == pytest.approx(77.0)
        assert p.gut_dim == pytest.approx(40.0)
        assert p.ab_bar_len == pytest.approx(65.5)
        assert p.y_bar == pytest.approx(48.0)
        assert p.x_bar == pytest.approx(72.0)

    def test_bottom_mat(self, p, log):
        bars = rule_g2_bottom_mat(p, log)
        bm1 = next(b for b in bars if b.mark == "BM1")
        bm2 = next(b for b in bars if b.mark == "BM2")
        assert bm1.qty == 15    # CEIL(72/5) = 15
        assert bm1.length_in == pytest.approx(48.0)
        assert bm2.qty == 10    # CEIL(48/5) = 10
        assert bm2.length_in == pytest.approx(72.0)

    def test_horizontals_top(self, p, log):
        bars = rule_g2_horizontals(p, log)
        h1 = next(b for b in bars if b.mark == "H1")
        h2 = next(b for b in bars if b.mark == "H2")
        assert h1.qty == 12     # 24/4 × 2 = 12
        assert h1.length_in == pytest.approx(72.0)   # 48 + 2×12 = 72
        assert h2.qty == 12
        assert h2.length_in == pytest.approx(96.0)   # 72 + 2×12 = 96

    def test_horizontals_below(self, p, log):
        # CEIL((72-14)/5)*2 = CEIL(58/5)*2 = 12*2 = 24
        bars = rule_g2_horizontals(p, log)
        h3 = next(b for b in bars if b.mark == "H3")
        h4 = next(b for b in bars if b.mark == "H4")
        assert h3.qty == 24
        assert h3.length_in == pytest.approx(72.0)
        assert h4.qty == 24
        assert h4.length_in == pytest.approx(96.0)

    def test_verticals(self, p, log):
        # V1: CEIL((72*2 - 48 + 48 + 6)/5) = CEIL(150/5) = 30
        # V1 len = h_adj + 12 - 2 = 77 + 10 = 87"
        # V2: CEIL((48 + 48 + 4)/5) = CEIL(100/5) = 20
        # V2 len = h_adj = 77"
        bars = rule_g2_verticals(p, log)
        v1 = next(b for b in bars if b.mark == "V1")
        v2 = next(b for b in bars if b.mark == "V2")
        assert v1.qty == 30
        assert v1.length_in == pytest.approx(87.0)
        assert v2.qty == 20
        assert v2.length_in == pytest.approx(77.0)

    def test_ab_bars(self, p, log):
        # A1: CEIL(40/5)=8, #5, len=65.5"
        # B1: CEIL(40/6)=7, #5, len=65.5"
        bars = rule_g2_ab_bars(p, log)
        a1 = next(b for b in bars if b.mark == "A1")
        b1 = next(b for b in bars if b.mark == "B1")
        assert a1.qty == 8
        assert a1.size == "#5"
        assert a1.length_in == pytest.approx(65.5)
        assert b1.qty == 7
        assert b1.size == "#5"
        assert b1.length_in == pytest.approx(65.5)

    def test_right_angle(self, p, log):
        # RA1: (FLOOR(54/6)+1)*1 = (9+1) = 10, len = 40+60 = 100"
        bars = rule_g2_right_angle(p, log)
        ra1 = bars[0]
        assert ra1.qty == 10
        assert ra1.length_in == pytest.approx(100.0)

    def test_hoops(self, p, log):
        # HP1: CEIL(48/5)*1 = 10, S6 stock = 2*40+11.5 = 91.5"
        bars = rule_g2_hoops(p, log)
        hp1 = bars[0]
        assert hp1.qty == 10
        assert hp1.length_in == pytest.approx(91.5)


class TestG2InletGoldEx2:
    """
    DS400 ex2 gold barlist: T=9", H=5', X_int=60", Y_int=36".

    Same X/Y as ex1, only wall_height_ft differs (5 vs 6 ft).
    h_adj = 65", H3/H4 qty drops to 20, V1 len=75", V2 len=65".

    Reference: /data/gold/g2_inlet/ds400.ex2.g2.barlist.pdf
    """

    @pytest.fixture
    def p(self):
        return _g2_params(x_dim_ft=78 / 12, wall_height_ft=5.0, wall_thick_in=9,
                          grate_type="Type 24", num_structures=1)

    def test_geometry_h_adj(self, p):
        assert p.h_adj == pytest.approx(65.0)

    def test_horizontals_below_h5(self, p, log):
        # CEIL((60-14)/5)*2 = CEIL(46/5)*2 = 10*2 = 20
        bars = rule_g2_horizontals(p, log)
        h3 = next(b for b in bars if b.mark == "H3")
        assert h3.qty == 20

    def test_verticals_h5(self, p, log):
        # V1 len = 65 + 12 - 2 = 75"  V2 len = 65"
        bars = rule_g2_verticals(p, log)
        v1 = next(b for b in bars if b.mark == "V1")
        v2 = next(b for b in bars if b.mark == "V2")
        assert v1.length_in == pytest.approx(75.0)
        assert v2.length_in == pytest.approx(65.0)

    def test_ab_bars_unchanged(self, p, log):
        # A/B bars are geometry-only, same as ex1
        bars = rule_g2_ab_bars(p, log)
        a1 = next(b for b in bars if b.mark == "A1")
        assert a1.qty == 8
        assert a1.length_in == pytest.approx(65.5)


@pytest.mark.parametrize("H_ft,expected_h3_qty", [
    (5.0, 20),   # CEIL((60-14)/5)*2 = 20
    (6.0, 24),   # CEIL((72-14)/5)*2 = 24
    (7.0, 28),   # CEIL((84-14)/5)*2 = 28
    (8.0, 34),   # CEIL((96-14)/5)*2 = 34
])
def test_g2_h3_qty_parametric(log, H_ft, expected_h3_qty):
    """H3/H4 qty formula verified across DS400 height range."""
    p = _g2_params(x_dim_ft=78 / 12, wall_height_ft=H_ft, wall_thick_in=9)
    bars = rule_g2_horizontals(p, log)
    h3 = next(b for b in bars if b.mark == "H3")
    assert h3.qty == expected_h3_qty, \
        f"H={H_ft}ft → H3 qty: expected {expected_h3_qty}, got {h3.qty}"


# ===========================================================================
# 9. Box Culvert gold tests
# ===========================================================================

from vistadetail.engine.rules.box_culvert_rules import (
    rule_bc_a_bars,
    rule_bc_b_bars,
    rule_bc_e_bars,
    rule_bc_h_bars,
    rule_bc_f_bars,
    rule_bc_i_bars,
    rule_bc_roof_long_bars,
    rule_bc_well_spreaders,
)


def _bc_params(**kw):
    """Build a Params object for box culvert rules."""
    from vistadetail.engine.schema import Params
    defaults = dict(
        span_ft=8,
        height_ft=6.0,
        barrel_length_ft=20.0,
        max_earth_cover_ft=10,
        notch_ends="None",
        notch_depth_in=0.0,
    )
    defaults.update(kw)
    return Params(defaults)


class TestBoxCulvertGoldRCB8x6x20:
    """
    Gold barlist: RCB Single Box Culvert  Span=8'  H=6'  L=20'  cover=10'
    D80 table: T1=9-1/2"  T2=8-1/2"  T3=8-1/2"
    a_s=#6 @5"  b_s=#6 @4.5"  e_s=#4 @7.5"  B=43"

    Confirmed from handwritten gold barlist (IMG_8310.HEIC, 2026-05-01):
      A1 (invert C-bar): 50 #6  J=0'-4"  A=0'-6"  B=8'-11"
      A2 (roof   C-bar): 50 #6  J=0'-5"  A=0'-6"  B=8'-11"
      B1 (wall   L-bar): 110 #6  long=7'-0"  short=3'-7"
      E1 (wall vertical): 66 #4  7'-0"

    Potential discrepancies pending user verification:
      H1 (wall horiz):   code=32 #4 @ 19'-6"  gold note unclear (38?)
      F1 (roof transv):  code=22 #4 @ 8'-11"  gold note unclear (24?)
      I1 (invert long):  code=11 #4 @ 19'-8"  gold note unclear (different)
    """

    @pytest.fixture
    def p(self):
        return _bc_params()

    # -----------------------------------------------------------------------
    # D80 table verification
    # -----------------------------------------------------------------------
    def test_a_bar_size_is_6(self, p, log):
        bars = rule_bc_a_bars(p, log)
        for b in bars:
            assert b.size == "#6", f"{b.mark} size: expected #6"

    def test_a1_qty(self, p, log):
        """A1 invert: qty = floor(240/5)+2 = 50."""
        bars = rule_bc_a_bars(p, log)
        a1 = next(b for b in bars if b.mark == "A1")
        assert a1.qty == 50

    def test_a2_qty(self, p, log):
        """A2 roof: same formula → 50."""
        bars = rule_bc_a_bars(p, log)
        a2 = next(b for b in bars if b.mark == "A2")
        assert a2.qty == 50

    def test_a1_b_flat(self, p, log):
        """A1 B leg (flat span) = S + 2×T2 − 6 = 96 + 17 − 6 = 107\" = 8'-11\"."""
        bars = rule_bc_a_bars(p, log)
        a1 = next(b for b in bars if b.mark == "A1")
        assert a1.leg_c_in == pytest.approx(107.0)

    def test_a1_j_hook(self, p, log):
        """A1 invert hook tail J = 4\"."""
        bars = rule_bc_a_bars(p, log)
        a1 = next(b for b in bars if b.mark == "A1")
        assert a1.leg_a_in == pytest.approx(4.0)

    def test_a2_j_hook(self, p, log):
        """A2 roof hook tail J = 5\"."""
        bars = rule_bc_a_bars(p, log)
        a2 = next(b for b in bars if b.mark == "A2")
        assert a2.leg_a_in == pytest.approx(5.0)

    # -----------------------------------------------------------------------
    # B bars
    # -----------------------------------------------------------------------
    def test_b1_size_is_6(self, p, log):
        bars = rule_bc_b_bars(p, log)
        assert bars[0].size == "#6"

    def test_b1_qty(self, p, log):
        """B1: 2 × (floor(240/4.5)+2) = 2×55 = 110."""
        bars = rule_bc_b_bars(p, log)
        assert bars[0].qty == 110

    def test_b1_long_leg(self, p, log):
        """B1 long leg = H + 12 = 72 + 12 = 84\" = 7'-0\"."""
        bars = rule_bc_b_bars(p, log)
        assert bars[0].leg_a_in == pytest.approx(84.0)

    def test_b1_short_leg(self, p, log):
        """B1 short leg = table B = 43\" = 3'-7\"."""
        bars = rule_bc_b_bars(p, log)
        assert bars[0].leg_b_in == pytest.approx(43.0)

    # -----------------------------------------------------------------------
    # E bars
    # -----------------------------------------------------------------------
    def test_e1_size_is_4(self, p, log):
        bars = rule_bc_e_bars(p, log)
        assert bars[0].size == "#4"

    def test_e1_qty(self, p, log):
        """E1: 2 × (floor(240/7.5)+1) = 2×33 = 66."""
        bars = rule_bc_e_bars(p, log)
        assert bars[0].qty == 66

    def test_e1_length(self, p, log):
        """E1 len = T1 + H + T3 − 6 = 9.5 + 72 + 8.5 − 6 = 84\" = 7'-0\"."""
        bars = rule_bc_e_bars(p, log)
        assert bars[0].length_in == pytest.approx(84.0)

    # -----------------------------------------------------------------------
    # H bars (wall horizontal distribution, longitudinal)
    # -----------------------------------------------------------------------
    def test_h1_qty(self, p, log):
        """H1: 4 faces × (floor(90/12)+1) = 4×8 = 32."""
        bars = rule_bc_h_bars(p, log)
        assert bars[0].qty == 32

    def test_h1_length(self, p, log):
        """H1 len = L − 6 = 234\" = 19'-6\"."""
        bars = rule_bc_h_bars(p, log)
        assert bars[0].length_in == pytest.approx(234.0)

    # -----------------------------------------------------------------------
    # F bars (roof slab transverse)
    # -----------------------------------------------------------------------
    def test_f1_qty(self, p, log):
        """F1: floor(240/12)+2 = 22."""
        bars = rule_bc_f_bars(p, log)
        assert bars[0].qty == 22

    def test_f1_length(self, p, log):
        """F1 len = S + 2×T2 − 6 = 107\" = 8'-11\"."""
        bars = rule_bc_f_bars(p, log)
        assert bars[0].length_in == pytest.approx(107.0)

    # -----------------------------------------------------------------------
    # I bars (invert longitudinal)
    # -----------------------------------------------------------------------
    def test_i1_qty(self, p, log):
        """I1: floor((96-4)/4)+1 = 24.  Gold confirmed."""
        bars = rule_bc_i_bars(p, log)
        assert bars[0].qty == 24

    def test_i1_length(self, p, log):
        """I1 len = L − 6 = 234\" = 19'-6\".  Gold confirmed."""
        bars = rule_bc_i_bars(p, log)
        assert bars[0].length_in == pytest.approx(234.0)

    def test_i1_shape_straight(self, p, log):
        bars = rule_bc_i_bars(p, log)
        assert bars[0].shape == "Str"

    # -----------------------------------------------------------------------
    # RL1 (roof longitudinal bars)
    # -----------------------------------------------------------------------
    def test_rl1_qty(self, p, log):
        """RL1: same formula as I1 → 24.  Gold confirmed (second 24-bar entry)."""
        bars = rule_bc_roof_long_bars(p, log)
        assert bars[0].qty == 24

    def test_rl1_length(self, p, log):
        """RL1 len = L − 6 = 234\" = 19'-6\"."""
        bars = rule_bc_roof_long_bars(p, log)
        assert bars[0].length_in == pytest.approx(234.0)

    def test_rl1_shape_straight(self, p, log):
        bars = rule_bc_roof_long_bars(p, log)
        assert bars[0].shape == "Str"

    # -----------------------------------------------------------------------
    # WS1 (wall spreaders)
    # -----------------------------------------------------------------------
    def test_ws1_qty(self, p, log):
        """WS1: floor(240/7)+2 = 36.  Gold confirmed."""
        bars = rule_bc_well_spreaders(p, log)
        assert bars[0].qty == 36

    def test_ws1_leg(self, p, log):
        """WS1 side leg = 6\" (0'-6\" right and left)."""
        bars = rule_bc_well_spreaders(p, log)
        assert bars[0].leg_b_in == pytest.approx(6.0)

    def test_ws1_top(self, p, log):
        """WS1 top tab = 4\" (0'-4\" on top)."""
        bars = rule_bc_well_spreaders(p, log)
        assert bars[0].leg_a_in == pytest.approx(4.0)
