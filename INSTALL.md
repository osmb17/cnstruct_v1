# Rebar Barlist Generator — Installation Guide

## What You Need

- **Windows 10/11** or **macOS 11+**
- **Microsoft Excel** (2016 or newer, with macros enabled)
- **Python 3.11 or newer** — free download at [python.org](https://www.python.org/downloads/)

---

## Quick Start (5 minutes)

### Step 1 — Install Python

**Windows:**
1. Go to [python.org/downloads](https://www.python.org/downloads/)
2. Click "Download Python 3.12.x" (latest stable)
3. Run the installer
4. **IMPORTANT: Check the box "Add Python to PATH"** before clicking Install

**Mac:**
1. Go to [python.org/downloads](https://www.python.org/downloads/)
2. Download and run the macOS installer
3. Follow the prompts (defaults are fine)

---

### Step 2 — Run Setup

**Windows:** Double-click `setup.bat`

**Mac:** Open Terminal, navigate to the folder, then run:
```
chmod +x setup.sh
./setup.sh
```

The setup script will:
- Create a local Python environment (`.venv` folder)
- Install all required packages automatically
- Configure the Excel–Python bridge

---

### Step 3 — Open the Workbook

1. Open **`Rebar Barlist Generator.xlsm`** in Excel
2. When prompted about macros, click **"Enable Content"** or **"Enable Macros"**
3. The workbook is ready to use

---

## Using the Generator

1. **Select Structure Type** — Use the dropdown on the Input sheet
2. **Fill in Dimensions** — Enter wall dimensions, bar sizes, spacing, cover, etc.
3. **Click "Generate Barlist"** — Results appear on the Barlist sheet
4. **Review the output** — Check bar marks, quantities, and cut lengths
5. **Export if needed** — Copy/paste the barlist table into your estimate

---

## Troubleshooting

**"Macro not found" or button doesn't work:**
- Make sure the `.venv` folder is in the same folder as the `.xlsm` file
- Run `setup.bat` (Windows) or `setup.sh` (Mac) again
- In Excel: File → Options → Trust Center → Trust Center Settings → Macro Settings → Enable all macros

**Python not found:**
- Re-run the Python installer from python.org
- On Windows: make sure "Add Python to PATH" was checked

**Excel says file is from untrusted location:**
- Right-click the `.xlsm` file → Properties → check "Unblock" → OK

---

## Files Included

```
Rebar Barlist Generator.xlsm   ← Main workbook (open this)
setup.bat                       ← Windows installer (run first)
setup.sh                        ← Mac installer (run first)
requirements.txt                ← Python package list
vistadetail/                    ← Python engine (do not modify)
INSTALL.md                      ← This file
```

---

## What Gets Installed (automatically)

- `openpyxl` — Excel file read/write
- `xlwings` — Live Excel–Python button bridge
- `anthropic` — Claude AI assistant integration
- `python-dotenv` — API key loading

No internet connection is required after setup (except for the optional AI assistant feature).

---

## Sharing with a Colleague

To share the generator:
1. Zip the **entire folder** (including `vistadetail/`, `.xlsm`, `setup.bat`, `setup.sh`, `requirements.txt`)
2. Send the zip file
3. Recipient runs `setup.bat` (Windows) or `setup.sh` (Mac) once, then opens the `.xlsm`

**Do not** send just the `.xlsm` — it needs the Python engine folder alongside it.

---

## Developer — Refreshing the Workbook After Code Changes

After editing Python code (new templates, rule changes, layout tweaks), you may need to
re-patch the workbook and/or re-inject the VBA.

### Full automated refresh

```bash
# Close the workbook in Excel first, then:
python refresh_workbook.py
```

This patches the worksheet layouts **and** re-injects VBA in one shot.

> **macOS only — one-time permission step:**
> If you see an error `-1743` or "Python is not allowed to send Apple events to Microsoft Excel",
> you need to grant Terminal automation access once:
> 1. Open **System Settings → Privacy & Security → Automation**
> 2. Find **Terminal** (or your Python launcher) in the list
> 3. Enable the checkbox next to **Microsoft Excel**
> 4. Quit and reopen Terminal, then re-run `python refresh_workbook.py`

### Manual VBA update (if automation is blocked)

1. Close and reopen the workbook to let Excel repair it
2. Press **Alt+F11** to open the Visual Basic Editor
3. In the left panel, find the **VistaDetail** module (under Modules)
4. Select all code (Cmd+A / Ctrl+A) and replace it with the output of:
   ```bash
   python -c "from vistadetail.setup_xlwings import _VBA_MODULE; print(_VBA_MODULE)"
   ```
5. Also open **ThisWorkbook** and ensure `Workbook_Open` calls `SetupDropdowns`
6. Save (Ctrl+S), close the VBA editor, save the workbook
7. Reopen — `SetupDropdowns` will run automatically and rebuild the Structure Type dropdown

### Layout-only patch (no Excel required)

To rebuild Dashboard / BarList / ReasoningLog cell layouts without touching VBA:

```bash
python -m vistadetail.workbook.patch_workbook
```

This runs entirely via openpyxl with Excel closed.  VBA and buttons are preserved.
