#!/usr/bin/env bash
set -euo pipefail

echo "=== Starting Worker ==="

# Check if .env exists
if [ ! -f .env ]; then
    echo "ERROR: .env file not found!"
    echo "Please copy .env.example to .env and configure required variables."
    exit 1
fi

# Check required variables
required_vars=(
    "BLOCKSCOUT_MCP_BASE"
    "AUTOSCOUT_BASE"
    "CHAIN_ID"
    "DEX_POOL_A"
    "DEX_POOL_B"
)

for var in "${required_vars[@]}"; do
    if ! grep -q "^${var}=" .env; then
        echo "ERROR: Required variable ${var} not set in .env"
        exit 1
    fi
done

echo "Activating virtual environment..."
source .venv/bin/activate

echo "Running worker..."
python apps/worker/run.py
