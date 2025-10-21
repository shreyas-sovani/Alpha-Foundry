#!/bin/bash

# 🚂 Railway Pre-Deployment Check
# Run this before pushing to GitHub to verify everything is ready

set -e  # Exit on error

echo "=========================================="
echo "🔍 Railway Pre-Deployment Check"
echo "=========================================="
echo ""

# Check 1: Git initialized
echo "✓ Checking Git..."
if [ -d .git ]; then
    echo "  ✅ Git repository found"
else
    echo "  ⚠️  Git not initialized. Run: git init"
    exit 1
fi

# Check 2: .env file exists
echo "✓ Checking .env file..."
if [ -f .env ]; then
    echo "  ✅ .env file found"
    
    # Check critical variables
    if grep -q "BLOCKSCOUT_MCP_BASE=" .env && \
       grep -q "CHAIN_ID=" .env && \
       grep -q "DEX_POOL_A=" .env; then
        echo "  ✅ Critical environment variables present"
    else
        echo "  ⚠️  Missing critical variables in .env"
        exit 1
    fi
else
    echo "  ❌ .env file not found!"
    echo "  Create one from .env.example or .env.mainnet.recommended"
    exit 1
fi

# Check 3: requirements.txt
echo "✓ Checking requirements.txt..."
if [ -f apps/worker/requirements.txt ]; then
    echo "  ✅ requirements.txt found"
    
    # Check for aiohttp (critical for HTTP server)
    if grep -q "aiohttp" apps/worker/requirements.txt; then
        echo "  ✅ aiohttp included"
    else
        echo "  ⚠️  aiohttp missing - may cause issues"
    fi
else
    echo "  ❌ apps/worker/requirements.txt not found!"
    exit 1
fi

# Check 4: Railway config files
echo "✓ Checking Railway config files..."
if [ -f Procfile ] && [ -f railway.json ]; then
    echo "  ✅ Procfile and railway.json found"
else
    echo "  ⚠️  Railway config files missing (may auto-detect anyway)"
fi

# Check 5: Python files
echo "✓ Checking Python worker..."
if [ -f apps/worker/run.py ] && [ -f apps/worker/http_server.py ]; then
    echo "  ✅ Worker files found"
else
    echo "  ❌ Worker files missing!"
    exit 1
fi

# Check 6: .gitignore
echo "✓ Checking .gitignore..."
if [ -f .gitignore ]; then
    if grep -q ".env" .gitignore; then
        echo "  ✅ .env is gitignored (secure)"
    else
        echo "  ⚠️  .env not in .gitignore - SECURITY RISK!"
        echo "  Add '.env' to .gitignore before pushing"
        exit 1
    fi
else
    echo "  ⚠️  No .gitignore found"
fi

# Summary
echo ""
echo "=========================================="
echo "✅ ALL CHECKS PASSED!"
echo "=========================================="
echo ""
echo "📝 Next Steps:"
echo "  1. Commit your code:"
echo "     git add ."
echo "     git commit -m 'Railway deployment ready'"
echo ""
echo "  2. Create GitHub repo at:"
echo "     https://github.com/new"
echo ""
echo "  3. Push to GitHub:"
echo "     git remote add origin https://github.com/YOUR_USERNAME/dex-arbitrage-worker.git"
echo "     git branch -M main"
echo "     git push -u origin main"
echo ""
echo "  4. Deploy on Railway:"
echo "     https://railway.app"
echo ""
echo "  5. Follow the guide:"
echo "     See RAILWAY_QUICKSTART.md"
echo ""
echo "=========================================="
echo "🚂 Ready for Railway!"
echo "=========================================="
