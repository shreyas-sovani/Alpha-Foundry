#!/usr/bin/env python3
"""
Hackathon Demo Verification Script
===================================
Validates that the worker is producing dynamic, live, actionable data.

Self-reflection questions answered:
1. Are swaps changing every 30s?
2. Is each preview noticeably different?
3. Are signals (MEV, arb, USD value) compelling for judges?
"""
import json
import time
import sys
from pathlib import Path
from datetime import datetime

PREVIEW_PATH = Path("apps/worker/out/preview.json")
WAIT_SECONDS = 30

def load_preview():
    """Load preview.json if it exists."""
    if not PREVIEW_PATH.exists():
        return None
    
    with open(PREVIEW_PATH, 'r') as f:
        return json.load(f)

def extract_metrics(preview):
    """Extract key metrics from preview."""
    if not preview:
        return None
    
    header = preview.get("header", {})
    rows = preview.get("preview_rows", [])
    
    tx_hashes = [r.get("tx_hash") for r in rows if r.get("tx_hash")]
    
    return {
        "updated_ago": header.get("updated_ago_seconds", 999999),
        "activity": header.get("activity_swaps_per_min", 0),
        "spread": header.get("spread_percent"),
        "status": header.get("status_emoji", "?"),
        "alert": header.get("alert"),
        "trend": header.get("price_trend"),
        "total_rows": preview.get("total_rows", 0),
        "preview_count": len(rows),
        "tx_hashes": set(tx_hashes),
        "new_flags": sum(1 for r in rows if r.get("is_new")),
        "emoji_markers": [r.get("emoji_marker") for r in rows if r.get("emoji_marker")],
        "usd_values": [r.get("swap_value_usd", 0) for r in rows],
        "latest_ts": rows[0].get("timestamp", 0) if rows else 0
    }

def compare_metrics(m1, m2):
    """Compare two metric snapshots."""
    if not m1 or not m2:
        return None
    
    differences = {
        "updated_ago_delta": m2["updated_ago"] - m1["updated_ago"],
        "activity_delta": m2["activity"] - m1["activity"],
        "total_rows_delta": m2["total_rows"] - m1["total_rows"],
        "new_tx_count": len(m2["tx_hashes"] - m1["tx_hashes"]),
        "repeated_tx_count": len(m2["tx_hashes"] & m1["tx_hashes"]),
        "new_flags_delta": m2["new_flags"] - m1["new_flags"],
        "latest_ts_delta": m2["latest_ts"] - m1["latest_ts"]
    }
    
    return differences

def print_metrics(label, metrics):
    """Pretty print metrics."""
    print(f"\n{label}")
    print("=" * 70)
    print(f"  Status: {metrics['status']}")
    print(f"  Updated ago: {metrics['updated_ago']}s")
    print(f"  Activity: {metrics['activity']:.2f} swaps/min")
    print(f"  Spread: {metrics['spread']}%")
    if metrics['alert']:
        print(f"  🎯 {metrics['alert']}")
    if metrics['trend']:
        print(f"  Trend: {metrics['trend']}")
    print(f"  Total rows: {metrics['total_rows']}")
    print(f"  Preview: {metrics['preview_count']} rows ({metrics['new_flags']} new)")
    print(f"  TX hashes: {len(metrics['tx_hashes'])} unique")
    print(f"  Emoji markers: {' '.join(metrics['emoji_markers'][:5])}")
    print(f"  USD values: ${min(metrics['usd_values']):.2f} - ${max(metrics['usd_values']):.2f}")
    print(f"  Latest timestamp: {datetime.fromtimestamp(metrics['latest_ts']).isoformat() if metrics['latest_ts'] > 0 else 'N/A'}")

def print_diff(diff):
    """Pretty print differences."""
    print("\nΔ CHANGES BETWEEN SNAPSHOTS")
    print("=" * 70)
    print(f"  New transactions: {diff['new_tx_count']}")
    print(f"  Repeated transactions: {diff['repeated_tx_count']}")
    print(f"  Total rows delta: +{diff['total_rows_delta']}")
    print(f"  New flags delta: {diff['new_flags_delta']:+d}")
    print(f"  Latest timestamp delta: +{diff['latest_ts_delta']}s")
    print(f"  Updated_ago drift: {diff['updated_ago_delta']:+d}s")

def assess_quality(m1, m2, diff):
    """Assess data quality for demo."""
    score = 100
    issues = []
    
    # Critical: Data must be fresh
    if m2["updated_ago"] > 300:
        score -= 50
        issues.append(f"❌ STALE: Data {m2['updated_ago']}s old (>5 min)")
    elif m2["updated_ago"] > 120:
        score -= 20
        issues.append(f"⚠️  Aging: Data {m2['updated_ago']}s old")
    
    # Critical: Must have new transactions
    if diff["new_tx_count"] == 0:
        score -= 40
        issues.append("❌ NO CHANGE: No new transactions between snapshots")
    
    # Important: Must have activity
    if m2["activity"] == 0:
        score -= 30
        issues.append("❌ IDLE: No swap activity detected")
    elif m2["activity"] < 0.1:
        score -= 10
        issues.append(f"⚠️  Low activity: {m2['activity']:.2f} swaps/min")
    
    # Good to have: Fresh data growth
    if diff["total_rows_delta"] == 0:
        score -= 10
        issues.append("⚠️  No new rows added")
    
    # Good to have: Arbitrage signals
    if m2["alert"]:
        score += 10
        issues.append(f"✅ ARB SIGNAL: {m2['alert']}")
    
    # Good to have: Visual markers
    if m2["new_flags"] > 0:
        score += 5
        issues.append(f"✅ Visual markers: {m2['new_flags']} new swaps flagged")
    
    return score, issues

def main():
    """Run two-snapshot verification."""
    print("=" * 70)
    print("🔍 HACKATHON DEMO VERIFICATION")
    print("=" * 70)
    print(f"Preview path: {PREVIEW_PATH.absolute()}")
    print(f"Wait interval: {WAIT_SECONDS}s")
    print("")
    
    # Snapshot 1
    print("📸 Taking snapshot 1...")
    preview1 = load_preview()
    if not preview1:
        print(f"❌ Preview file not found: {PREVIEW_PATH}")
        print("Start the worker first: python apps/worker/run.py")
        sys.exit(1)
    
    metrics1 = extract_metrics(preview1)
    print_metrics("SNAPSHOT 1", metrics1)
    
    # Wait
    print(f"\n⏳ Waiting {WAIT_SECONDS}s for worker cycle...")
    for i in range(WAIT_SECONDS, 0, -5):
        print(f"  {i}s...", end="\r")
        time.sleep(5)
    print("  Done!   ")
    
    # Snapshot 2
    print("\n📸 Taking snapshot 2...")
    preview2 = load_preview()
    if not preview2:
        print(f"❌ Preview file disappeared!")
        sys.exit(1)
    
    metrics2 = extract_metrics(preview2)
    print_metrics("SNAPSHOT 2", metrics2)
    
    # Compare
    diff = compare_metrics(metrics1, metrics2)
    print_diff(diff)
    
    # Assess
    print("\n" + "=" * 70)
    print("🎯 DEMO QUALITY ASSESSMENT")
    print("=" * 70)
    
    score, issues = assess_quality(metrics1, metrics2, diff)
    
    for issue in issues:
        print(f"  {issue}")
    
    print("")
    print(f"Overall Score: {score}/100")
    
    if score >= 80:
        print("✅ PASS: Excellent - Ready for demo!")
    elif score >= 60:
        print("⚠️  PASS: Good - Minor improvements recommended")
    elif score >= 40:
        print("⚠️  WARN: Fair - Needs attention before demo")
    else:
        print("❌ FAIL: Poor - Major issues detected")
        print("\n💡 RECOMMENDED ACTIONS:")
        print("  1. Switch to Ethereum Mainnet (.env.mainnet.recommended)")
        print("  2. Use active router: 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D")
        print("  3. Set WINDOW_MINUTES=2 for tighter refresh")
        print("  4. Verify network connectivity to Blockscout API")
    
    print("=" * 70)
    
    sys.exit(0 if score >= 60 else 1)

if __name__ == "__main__":
    main()
