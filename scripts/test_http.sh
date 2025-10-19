#!/bin/bash
# Test HTTP endpoints

echo "Testing HTTP endpoints..."
echo ""

echo "1. Health check:"
curl -s http://localhost:8787/health | jq
echo ""

echo "2. Metadata (with freshness):"
curl -s http://localhost:8787/metadata | jq
echo ""

echo "3. Preview (last 5 swaps):"
curl -s http://localhost:8787/preview | jq '.preview_rows | length'
echo ""

echo "Done!"
