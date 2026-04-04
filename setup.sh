#!/usr/bin/env bash
# ============================================================
# Rebar Barlist Generator — Mac/Linux Setup Script
# Run once to install Python environment and dependencies.
#
# Usage:
#   chmod +x setup.sh
#   ./setup.sh
# ============================================================

set -e

echo ""
echo "============================================"
echo "  Rebar Barlist Generator — Setup"
echo "============================================"
echo ""

# ── Check Python 3.11+ ───────────────────────────────────────
PYTHON=""
for cmd in python3.12 python3.11 python3; do
    if command -v "$cmd" &>/dev/null; then
        VER=$("$cmd" -c "import sys; print(sys.version_info[:2])")
        if "$cmd" -c "import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)" 2>/dev/null; then
            PYTHON="$cmd"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo "ERROR: Python 3.11 or newer is required."
    echo ""
    echo "Install it from: https://www.python.org/downloads/"
    echo "Then run this script again."
    exit 1
fi

echo "Using Python: $PYTHON  ($($PYTHON --version))"
echo ""

# ── Create virtual environment ────────────────────────────────
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    "$PYTHON" -m venv .venv
    echo "  .venv created."
else
    echo "Virtual environment already exists (.venv)."
fi

# ── Install dependencies ──────────────────────────────────────
echo ""
echo "Installing Python packages (this may take a minute)..."
.venv/bin/pip install --upgrade pip --quiet
.venv/bin/pip install -r requirements.txt --quiet
echo "  Packages installed."

# ── xlwings addin ─────────────────────────────────────────────
echo ""
echo "Configuring xlwings (Excel bridge)..."
.venv/bin/xlwings runpython install 2>/dev/null || true
echo "  xlwings configured."

# ── Done ──────────────────────────────────────────────────────
echo ""
echo "============================================"
echo "  Setup complete!"
echo "============================================"
echo ""
echo "To use the Rebar Barlist Generator:"
echo "  1. Open 'Rebar Barlist Generator.xlsm' in Excel"
echo "  2. Enable macros when prompted"
echo "  3. Select a structure type and fill in dimensions"
echo "  4. Click 'Generate Barlist'"
echo ""
echo "If Excel shows a security warning about macros,"
echo "click 'Enable Content' to allow the buttons to work."
echo ""
