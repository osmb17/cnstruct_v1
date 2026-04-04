@echo off
REM ============================================================
REM Rebar Barlist Generator — Windows Setup Script
REM Run once to install Python environment and dependencies.
REM
REM Usage: Double-click setup.bat  OR  run from Command Prompt
REM ============================================================

echo.
echo ============================================
echo   Rebar Barlist Generator -- Setup
echo ============================================
echo.

REM ── Check Python ─────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not on PATH.
    echo.
    echo Download Python 3.11 or newer from:
    echo   https://www.python.org/downloads/
    echo.
    echo IMPORTANT: During install, check "Add Python to PATH"
    echo Then run this script again.
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo Using Python %PYVER%
echo.

REM ── Create virtual environment ────────────────────────────────
if not exist ".venv\" (
    echo Creating virtual environment...
    python -m venv .venv
    echo   .venv created.
) else (
    echo Virtual environment already exists ^(.venv^).
)

echo.
echo Installing Python packages ^(this may take a minute^)...
.venv\Scripts\pip install --upgrade pip --quiet
.venv\Scripts\pip install -r requirements.txt --quiet
echo   Packages installed.

REM ── xlwings addin ─────────────────────────────────────────────
echo.
echo Configuring xlwings ^(Excel bridge^)...
.venv\Scripts\xlwings runpython install 2>nul
echo   xlwings configured.

REM ── Done ──────────────────────────────────────────────────────
echo.
echo ============================================
echo   Setup complete!
echo ============================================
echo.
echo To use the Rebar Barlist Generator:
echo   1. Open "Rebar Barlist Generator.xlsm" in Excel
echo   2. Enable macros when prompted
echo   3. Select a structure type and fill in dimensions
echo   4. Click "Generate Barlist"
echo.
echo If Excel shows a security warning about macros,
echo click "Enable Content" to allow the buttons to work.
echo.
pause
