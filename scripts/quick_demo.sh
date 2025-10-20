#!/bin/bash
# ============================================================================
# QUICK DEMO SCRIPT - Hackathon Optimized
# ============================================================================
# This script sets up and runs the DEX arbitrage worker in demo mode
# with live Ethereum Mainnet data for maximum impact.
#
# Usage:
#   ./scripts/quick_demo.sh [mainnet|sepolia]
#
# Default: mainnet (recommended for live demo)
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Parse arguments
MODE="${1:-mainnet}"

echo "============================================================================"
echo "🚀 DEX ARBITRAGE WORKER - QUICK DEMO SETUP"
echo "============================================================================"
echo "Mode: $MODE"
echo ""

# Select configuration
case "$MODE" in
  mainnet)
    echo "✅ Using MAINNET configuration (live, high-activity pools)"
    if [ -f ".env.mainnet.recommended" ]; then
      cp .env.mainnet.recommended .env
      echo "✅ Copied .env.mainnet.recommended → .env"
    else
      echo "❌ .env.mainnet.recommended not found!"
      exit 1
    fi
    ;;
  sepolia)
    echo "⚠️  Using SEPOLIA configuration (testnet, low activity)"
    echo "Note: Sepolia has very low swap activity. Mainnet recommended for demo."
    if [ -f ".env.example" ]; then
      cp .env.example .env
      echo "✅ Copied .env.example → .env"
    else
      echo "❌ .env.example not found!"
      exit 1
    fi
    ;;
  *)
    echo "❌ Unknown mode: $MODE"
    echo "Usage: $0 [mainnet|sepolia]"
    exit 1
    ;;
esac

echo ""
echo "============================================================================"
echo "📦 CHECKING DEPENDENCIES"
echo "============================================================================"

# Check Python
if ! command -v python3 &> /dev/null; then
  echo "❌ Python 3 not found. Please install Python 3.9+"
  exit 1
fi

echo "✅ Python: $(python3 --version)"

# Check virtual environment
if [ ! -d ".venv" ]; then
  echo "⚠️  Virtual environment not found. Creating..."
  python3 -m venv .venv
  echo "✅ Created .venv"
fi

# Activate venv
source .venv/bin/activate

# Install/upgrade dependencies
echo ""
echo "📦 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r apps/worker/requirements.txt

echo "✅ Dependencies installed"

# Clean old state for fresh demo
echo ""
echo "🧹 CLEANING OLD STATE (fresh demo)"
rm -f state/*.json
rm -f apps/worker/out/*.json
rm -f apps/worker/out/*.jsonl
echo "✅ State cleaned"

echo ""
echo "============================================================================"
echo "🎬 STARTING WORKER"
echo "============================================================================"
echo ""
echo "Preview endpoints:"
echo "  • http://localhost:8787/preview"
echo "  • http://localhost:8787/metadata"
echo "  • http://localhost:8787/health"
echo ""
echo "In another terminal, try:"
echo "  curl -s http://localhost:8787/preview | jq '.header'"
echo "  curl -s http://localhost:8787/preview | jq '.preview_rows[0]'"
echo ""
echo "Press Ctrl+C to stop"
echo "============================================================================"
echo ""

# Run worker
cd apps/worker
python3 run.py
