#!/bin/bash

# Vercel Deployment Verification Script
# This script helps verify that the frontend will work correctly when deployed to Vercel

echo "=================================================="
echo "🔍 VERCEL DEPLOYMENT VERIFICATION"
echo "=================================================="
echo ""

# 1. Check backend is accessible
echo "1️⃣  Checking Railway Backend..."
echo "   URL: https://web-production-279f4.up.railway.app/metadata"
echo ""

BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://web-production-279f4.up.railway.app/metadata)

if [ "$BACKEND_STATUS" = "200" ]; then
    echo "   ✅ Backend is UP (HTTP $BACKEND_STATUS)"
    
    # Get latest CID
    LATEST_CID=$(curl -s https://web-production-279f4.up.railway.app/metadata | jq -r '.latest_cid')
    ROWS=$(curl -s https://web-production-279f4.up.railway.app/metadata | jq -r '.rows')
    LAST_UPDATED=$(curl -s https://web-production-279f4.up.railway.app/metadata | jq -r '.last_updated')
    
    echo "   📊 Latest CID: $LATEST_CID"
    echo "   📈 Rows: $ROWS"
    echo "   🕐 Last Updated: $LAST_UPDATED"
else
    echo "   ❌ Backend is DOWN (HTTP $BACKEND_STATUS)"
    exit 1
fi

echo ""
echo "2️⃣  Checking CORS Headers..."

CORS_HEADER=$(curl -s -I https://web-production-279f4.up.railway.app/metadata | grep -i "access-control-allow-origin")

if [[ "$CORS_HEADER" == *"*"* ]]; then
    echo "   ✅ CORS is configured correctly"
    echo "   $CORS_HEADER"
else
    echo "   ❌ CORS may not be configured correctly"
    echo "   Found: $CORS_HEADER"
fi

echo ""
echo "3️⃣  Checking Environment Files..."

if [ -f ".env.production" ]; then
    echo "   ✅ .env.production exists"
    
    PROD_API=$(grep "NEXT_PUBLIC_METADATA_API" .env.production | cut -d'=' -f2)
    echo "   📝 Production API: $PROD_API"
    
    if [[ "$PROD_API" == "https://web-production-279f4.up.railway.app" ]]; then
        echo "   ✅ Production API is correctly configured"
    else
        echo "   ❌ Production API mismatch!"
        echo "      Expected: https://web-production-279f4.up.railway.app"
        echo "      Found: $PROD_API"
    fi
else
    echo "   ❌ .env.production NOT FOUND"
    exit 1
fi

if [ -f ".env.local" ]; then
    echo "   ✅ .env.local exists (for local dev)"
    
    LOCAL_API=$(grep "NEXT_PUBLIC_METADATA_API" .env.local | cut -d'=' -f2)
    echo "   📝 Local API: $LOCAL_API"
else
    echo "   ⚠️  .env.local not found (optional)"
fi

echo ""
echo "4️⃣  Checking Frontend Build..."

if [ -d ".next" ]; then
    echo "   ✅ Build directory exists"
    
    # Check if build is recent (within last 10 minutes)
    BUILD_TIME=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" .next 2>/dev/null || stat -c "%y" .next 2>/dev/null | cut -d'.' -f1)
    echo "   📅 Last built: $BUILD_TIME"
else
    echo "   ⚠️  No build directory found (run 'npm run build')"
fi

echo ""
echo "5️⃣  Verification Summary"
echo "=================================================="

# Check all critical items
ALL_GOOD=true

if [ "$BACKEND_STATUS" != "200" ]; then
    echo "   ❌ Backend is not accessible"
    ALL_GOOD=false
fi

if [[ "$CORS_HEADER" != *"*"* ]]; then
    echo "   ❌ CORS not configured"
    ALL_GOOD=false
fi

if [ ! -f ".env.production" ]; then
    echo "   ❌ .env.production missing"
    ALL_GOOD=false
fi

PROD_API=$(grep "NEXT_PUBLIC_METADATA_API" .env.production 2>/dev/null | cut -d'=' -f2)
if [[ "$PROD_API" != "https://web-production-279f4.up.railway.app" ]]; then
    echo "   ❌ Production API incorrect"
    ALL_GOOD=false
fi

if [ "$ALL_GOOD" = true ]; then
    echo ""
    echo "   ✅✅✅ ALL CHECKS PASSED ✅✅✅"
    echo ""
    echo "   🚀 Ready to deploy to Vercel!"
    echo ""
    echo "   Next steps:"
    echo "   1. Commit changes: git add -A && git commit -m 'fix: production API config'"
    echo "   2. Push to GitHub: git push origin main"
    echo "   3. Deploy to Vercel: npx vercel --prod"
    echo ""
else
    echo ""
    echo "   ❌ SOME CHECKS FAILED"
    echo ""
    echo "   Please review the errors above before deploying."
    echo ""
    exit 1
fi

echo "=================================================="
