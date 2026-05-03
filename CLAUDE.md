# CNSTRUCT — Rebar Barlist Generator
## Claude Working Context

---

## What This Is

**CNSTRUCT** is a Streamlit web app that generates Caltrans-standard rebar barlists for cast-in-place concrete structures (headwalls, box culverts, inlet structures, junction structures, wingwalls, etc.).

- **Live app**: Streamlit Community Cloud. After every push to `main`, reboot the app from the Streamlit dashboard.
- **Rebar expert / reviewer**: Dane Rios (emails shared in conversation threads). His feedback takes priority over any formula assumptions.
- **Test suite**: `python3 -m pytest vistadetail/tests/test_engine.py -x -q` — must stay at 243 passed before any commit.

---

## Repo Layout

```
app.py                          Streamlit entry point (deployed)
web/
  defaults.py                   PRIMARY_INPUTS dict — controls which fields appear inline vs. in Advanced expander
  assistant.py                  AI assistant integration
  caltrans_tables.py            Caltrans lookup tables (D-sheet)
  diagram_gen.py                Live diagram rendering for web UI
  history.py                    SQLite run history
vistadetail/engine/
  schema.py                     BarRow, InputField, Params, fmt_inches
  calculator.py                 generate_barlist() — runs templates + rules
  hooks.py                      Bend deductions, hook extensions, bar weight tables
  reasoning_logger.py           ReasoningLogger(sheet=None) for smoke tests
  templates/                    One .py per structure type (template definition)
  rules/                        One .py per structure type (calculation rules)
    __init__.py                 RULE_REGISTRY dict — maps rule name → function
vistadetail/tests/
  test_engine.py                243 unit tests — run before every push
static/shapes/                  Bar shape PNG thumbnails
```

---

## Architecture: How Generation Works

```
User inputs → Template.parse_and_validate() → Params object
           → calculator.generate_barlist()
           → runs each rule_name from template.rules list
           → each rule returns list[BarRow]
           → combined into full barlist
```

### Template file (e.g. `templates/headwall.py`)
- Defines `InputField` list (name, dtype, label, choices, min, max, default, group, hint)
- Defines `self.rules` list of rule function name strings
- Must end with `TEMPLATE = MyTemplate()`

### Rule file (e.g. `rules/headwall_rules.py`)
- Each function signature: `def rule_xxx(p: Params, log: ReasoningLogger) -> list[BarRow]`
- `p.field_name` accesses validated input values
- `log.step(...)`, `log.result(...)`, `log.warn(...)`, `log.ok(...)` for reasoning trace
- Returns `[]` for geometry/validate rules (side effects via `setattr(p, ...)`)

### RULE_REGISTRY (`rules/__init__.py`)
Every rule function must be imported and registered:
```python
from vistadetail.engine.rules.headwall_rules import rule_hw_c_bars
RULE_REGISTRY["rule_hw_c_bars"] = rule_hw_c_bars
```

### PRIMARY_INPUTS (`web/defaults.py`)
Controls which fields show inline vs. inside the "Advanced" expander.
If a field is not in the template's `PRIMARY_INPUTS` list it goes into Advanced.
To show all fields inline, list all field names:
```python
"Junction Structure": ["d1_in", "d2_in", "span_ft", "hb_ft", "max_earth_cover_ft", "num_structures"],
```

---

## BarRow — Key Fields

```python
BarRow(
    mark="CB",           # bar mark label, e.g. "TF", "JA1", "CB"
    size="#5",           # "#3" through "#11"
    qty=12,
    length_in=105.0,     # always inches internally; fmt_inches() converts to 6'-9"
    shape="C",           # "Str", "U", "C", "L", "Hook", "S", "Rng", "Rect", "S6", "T14"
    bend_type="11",      # Caltrans/CRSI bend type number: "2"=U-bar, "11"=C-bar, etc.
    leg_a_in=80.0,       # A dimension (shown in A column)
    leg_b_in=12.0,       # B dimension
    leg_c_in=14.0,       # C dimension
    leg_d_in=71.0,       # D dimension (shown in D column)
    leg_g_in=9.0,        # G dimension (shown in G column)
    notes="...",         # shown in Notes column — use var(=value) format (see below)
    source_rule="...",
)
```

**Streamlit table columns**: Mark | Size | Qty | Length | Type(SVG) | Bend # | A | B | C | D | G | Notes | Ref | Review

**Notes format** (Dane's preferred style — show formula with actual values):
```
"H(=60\") + F(=12\") + 7\"(hook) = 6'-7\""
"A(=6'-8\") + B(=T+2=1'-0\") + C(=T+4=1'-2\") = 8'-9\""
"E(=0'-11\") = Y_exp/2 - 18\"(grate) - 5\"(clr)  C = E-2\" = 0'-9\""
```

---

## InputField — Choices Validation Rule

`choices` must always be a `list[str]` even if the dtype is `int` or `float`.
The validator does `str(value) in choices` then casts to dtype.
```python
# Correct:
InputField("max_earth_cover_ft", int, choices=["10", "20"], default="10")
# Wrong (breaks validation):
InputField("max_earth_cover_ft", int, choices=[10, 20], default=10)
```

---

## Bend Deductions (`hooks.py`)

```python
bend_reduce("shape_1", "#5")  # 1 bend (90°) → 1.5"
bend_reduce("shape_2", "#5")  # 2 bends (U / C-bar) → 3.0"
bend_reduce("shape_3", "#5")  # 3 bends → 4.5"
bend_reduce("shape_4", "#5")  # 4 bends (closed hoop) → 6.0"
```

Stock = sum of all leg dimensions − bend_reduce(shape, size)

---

## Template Accuracy Status (as of 2026-05-03)

| Template | Standard Plan | Status |
|---|---|---|
| Caltrans Headwall | D89A / D89B | Confirmed vs 3 gold barlists |
| Junction Structure | D91A / D91B | Table corrected, A-bars U-shape |
| Box Culvert | D80 | Confirmed |
| D84 Wingwall | D84 (2025) | Rewritten from plan sections v3.0 |
| D85 Wingwall | D85 (2025) | Current |
| G2 Expanded Inlet | D73A | T14 notched hoop formula confirmed by Dane |
| G-type Inlets (G1–G6) | D74/D75 | Current |

---

## Key Rules to Know

### Headwall (D89A/D89B) — `headwall_rules.py`
- **CB bar**: shape="C", bend_type="11", `leg_b = T+2` (B = inside face), `leg_c = T+4` (C = outside face). Stock uses 2×(T+4).
- **VW bar**: no-pipe length = `H + F + 7"(hook)`; pipe length = `ceil((H+18)/6)*6`
- **Count table** `_D89A_COUNT_TABLE`: {(D_in, H_in): {vert, c_bar, wall_horz, li}}. Only 3 confirmed entries — all others use nearest-neighbour (ASSUMPTION).

### Junction Structure (D91A/D91B) — `junction_structure_rules.py`
- **JA1/JA2**: shape="U", bend_type="2", `leg_a = leg_g = slab_thick − 3"`, `leg_b = body`
- **JB1**: shape="U", `leg_a = B` (slab lap), `leg_b = Hb`
- **a-bar qty**: `2 × (floor(S_in / a_sp) + 2)` per slab (×2 because square plan, both directions)
- **JX1 Note 12**: `ceil(floor(D_in/a_sp)+1) / 2) × 2 sides × 2 slabs` per pipe

### G2 Expanded Inlet — `inlet_wall_rules.py`
- **HP1**: shape="S6", regular hoop at grate level
- **HP2**: shape="T14", notched hoop. `E = Y_exp_ext/2 − 18"(grate/2) − 5"(clr)`, `C = E − 2"`. Stock = `3E + 3` for #5.

---

## Adding a New Template

1. Create `vistadetail/engine/templates/new_thing.py` — subclass `BaseTemplate`, define `self.inputs` and `self.rules`, end with `TEMPLATE = NewThingTemplate()`
2. Create `vistadetail/engine/rules/new_thing_rules.py` — write `def rule_xxx(p, log) → list[BarRow]`
3. Register in `vistadetail/engine/rules/__init__.py` — import and add to `RULE_REGISTRY`
4. Add to `web/defaults.py` `PRIMARY_INPUTS` dict with all field names
5. Run tests: `python3 -m pytest vistadetail/tests/test_engine.py -x -q`

---

## Commit & Push Conventions

- No `Co-Authored-By` lines in commit messages
- Never push without explicit user approval ("push")
- Streamlit Cloud requires a **manual reboot** after every push (Streamlit dashboard)
- Test suite must pass (243 tests) before any commit

---

## Common Pitfalls

- `ReasoningLogger()` requires `sheet=None` arg in smoke tests: `ReasoningLogger(sheet=None)`
- `fmt_inches(None)` returns `""` — guard with `if x is not None` before calling
- `choices` fields always validate as strings even for int/float dtypes
- `leg_d_in` and `leg_g_in` do NOT appear in `to_row()` CSV export — they are UI/PDF only
- The "Advanced" expander appears when any field is NOT in `PRIMARY_INPUTS`. To remove it, add all fields to `PRIMARY_INPUTS`.
- After changing `to_row()` column count, update `TestBarRowToRow::test_to_row_length` in test_engine.py
