# Rebar Barlist Generator

Caltrans-standard rebar barlist generator for cast-in-place concrete structures.

## Two front-ends, one engine

This repo contains two separate front-ends that share a common rebar
calculation engine:

- **Web app (Streamlit)** — `app.py` at the repo root.
  Deployed on Streamlit Community Cloud. This is the active product.
- **Excel/xlwings tool** — `vistadetail/main.py` (CLI) drives the
  `Rebar Barlist Generator.xlsm` workbook locally. Kept around for
  spreadsheet workflows; not used by the web app.

Both front-ends import from `vistadetail/engine/`, which holds the
templates, rules, schema, and calculator.

## Layout

```
RebarGenerator/
├── app.py                  Streamlit entry point (deployed)
├── web/                    Web-app helpers (only used by app.py)
│   ├── assistant.py          AI assistant integration
│   ├── caltrans_tables.py    Caltrans D-sheet lookup tables
│   ├── defaults.py           Default field values per template
│   ├── diagram_gen.py        Live diagram rendering for the web UI
│   └── history.py            Run history (SQLite)
├── vistadetail/            Excel tool + shared engine
│   ├── main.py / cli.py      Excel CLI entry points
│   ├── excel_bridge.py       xlwings bridge to the workbook
│   ├── workbook/             Workbook layout + diagram rendering for Excel
│   └── engine/               Shared rebar engine
│       ├── calculator.py
│       ├── schema.py
│       ├── rules/            Per-structure-type bar rules
│       └── templates/        Template definitions (one per structure)
├── static/shapes/          Bar shape thumbnails (PNG)
├── requirements.txt        Web app + engine deps (Streamlit Cloud)
├── runtime.txt             Pinned Python version for Streamlit Cloud
├── setup.bat / setup.sh    Local Python venv installer
└── .streamlit/             Streamlit config
```

## Run the web app locally

```bash
python -m venv .venv
source .venv/bin/activate     # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
streamlit run app.py
```

## Deploy

The web app is hosted on Streamlit Community Cloud.
After pushing to `main`, reboot the app from the Streamlit dashboard.
