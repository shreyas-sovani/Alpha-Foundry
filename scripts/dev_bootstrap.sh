#!/usr/bin/env bash
set -euo pipefail

echo "=== Development Bootstrap ==="
echo "Creating Python virtual environment at .venv..."

python3 -m venv .venv

echo "Activating virtual environment..."
source .venv/bin/activate

echo "Installing worker dependencies..."
pip install --upgrade pip
pip install -r apps/worker/requirements.txt

echo ""
echo "=== Bootstrap Complete ==="
python -V
echo "Installed packages: $(pip freeze | wc -l | tr -d ' ')"
echo ""
echo "Virtual environment is ready at .venv"
echo "To activate: source .venv/bin/activate"
