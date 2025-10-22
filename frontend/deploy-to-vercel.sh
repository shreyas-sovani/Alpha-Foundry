#!/bin/bash

# 🚀 Quick Deploy to Vercel
# Run this script to deploy the fixed frontend to Vercel

set -e  # Exit on any error

echo "=================================================="
echo "🚀 DEPLOYING FRONTEND TO VERCEL"
echo "=================================================="
echo ""

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: Not in frontend directory"
    echo "   Please run: cd frontend"
    exit 1
fi

# Step 1: Verify everything is ready
echo "1️⃣  Running pre-deployment checks..."
./verify-deployment.sh || exit 1

echo ""
echo "2️⃣  Checking git status..."
cd ..
if [[ -n $(git status -s) ]]; then
    echo "   📝 Uncommitted changes detected"
    echo ""
    echo "   Files to commit:"
    git status -s
    echo ""
    read -p "   Commit these changes? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git add -A
        git commit -m "fix: production API endpoint configuration for Vercel deployment"
        echo "   ✅ Changes committed"
    else
        echo "   ⚠️  Skipping commit (deploy may use old code)"
    fi
else
    echo "   ✅ Working directory clean"
fi

echo ""
echo "3️⃣  Pushing to GitHub..."
git push origin main || echo "   ⚠️  Push failed or already up to date"

echo ""
echo "4️⃣  Building production bundle..."
cd frontend
npm run build

echo ""
echo "5️⃣  Deploying to Vercel..."
echo ""
echo "   If this is your first deployment:"
echo "   - Vercel will ask you to login"
echo "   - Choose 'Link to existing project' or 'Create new'"
echo "   - Follow the prompts"
echo ""
read -p "   Press ENTER to start Vercel deployment..."

npx vercel --prod

echo ""
echo "=================================================="
echo "✅ DEPLOYMENT COMPLETE!"
echo "=================================================="
echo ""
echo "🔍 Next steps:"
echo ""
echo "1. Open the deployed URL in your browser"
echo "2. Open browser console (F12)"
echo "3. Check for these logs:"
echo "   ✅ Fetching from: https://web-production-279f4.up.railway.app/metadata"
echo "   ✅ Fetched metadata successfully"
echo ""
echo "4. Verify UI displays:"
echo "   ✅ Latest CID"
echo "   ✅ Row count"
echo "   ✅ Last updated timestamp"
echo "   ✅ Encryption status"
echo ""
echo "5. Test the full flow:"
echo "   ✅ Connect wallet"
echo "   ✅ Switch to Sepolia"
echo "   ✅ Claim DADC tokens"
echo "   ✅ Unlock and decrypt data"
echo ""
echo "=================================================="
