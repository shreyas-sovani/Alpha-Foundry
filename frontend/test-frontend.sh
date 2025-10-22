#!/bin/bash

# Frontend Test & Development Script

echo "🔍 Frontend Test & Development"
echo "================================"
echo ""

# Change to frontend directory
cd "$(dirname "$0")" || exit 1

# Check Node.js
echo "📦 Node.js version: $(node -v)"
echo "📦 npm version: $(npm -v)"
echo ""

# Check files
echo "📁 Checking frontend structure..."
if [ -f "package.json" ]; then
    echo "✅ package.json exists"
else
    echo "❌ package.json missing"
    exit 1
fi

if [ -d "app" ]; then
    echo "✅ app directory exists"
else
    echo "❌ app directory missing"
    exit 1
fi

if [ -f "app/page.tsx" ]; then
    echo "✅ app/page.tsx exists"
else
    echo "❌ app/page.tsx missing"
    exit 1
fi

echo ""

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

echo ""
echo "🏗️  Building production app..."
npm run build

if [ $? -eq 0 ]; then
    echo "✅ Build successful!"
    echo ""
    echo "🚀 Starting production server..."
    echo "   Access at: http://localhost:3000"
    echo ""
    npm run start
else
    echo "❌ Build failed"
    exit 1
fi
