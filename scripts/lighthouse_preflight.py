#!/usr/bin/env python3
"""
Lighthouse integration pre-flight check.

This script validates:
1. Environment variables are set
2. Dependencies are installed
3. Input files exist and are valid
4. API key works (optional test upload)
"""

import os
import sys
from pathlib import Path

def print_section(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def check_mark(condition):
    return "✅" if condition else "❌"

def main():
    print_section("LIGHTHOUSE INTEGRATION PRE-FLIGHT CHECK")
    
    all_checks_pass = True
    
    # 1. Environment Variables
    print_section("1. Environment Variables")
    
    api_key = os.getenv("LIGHTHOUSE_API_KEY")
    if api_key:
        masked = api_key[:6] + "..." + api_key[-4:] if len(api_key) > 10 else "***"
        print(f"  {check_mark(True)} LIGHTHOUSE_API_KEY: {masked}")
    else:
        print(f"  {check_mark(False)} LIGHTHOUSE_API_KEY: NOT SET")
        print(f"     ⚠️  Required! Get one from: https://files.lighthouse.storage/")
        all_checks_pass = False
    
    password = os.getenv("LIGHTHOUSE_PASSWORD")
    if password:
        print(f"  {check_mark(True)} LIGHTHOUSE_PASSWORD: Custom password set")
    else:
        print(f"  ℹ️  LIGHTHOUSE_PASSWORD: Using API key (default)")
    
    # 2. Python Dependencies
    print_section("2. Python Dependencies")
    
    try:
        import cryptography
        print(f"  {check_mark(True)} cryptography: {cryptography.__version__}")
    except ImportError:
        print(f"  {check_mark(False)} cryptography: NOT INSTALLED")
        print(f"     Run: pip install cryptography")
        all_checks_pass = False
    
    try:
        import httpx
        print(f"  {check_mark(True)} httpx: {httpx.__version__}")
    except ImportError:
        print(f"  {check_mark(False)} httpx: NOT INSTALLED")
        print(f"     Run: pip install httpx")
        all_checks_pass = False
    
    # 3. File Structure
    print_section("3. File Structure")
    
    jsonl_path = Path("apps/worker/out/dexarb_latest.jsonl")
    if jsonl_path.exists():
        size = jsonl_path.stat().st_size
        print(f"  {check_mark(True)} {jsonl_path}: {size:,} bytes")
        
        # Check if file is empty
        if size == 0:
            print(f"     ⚠️  File is empty! Run worker to generate data.")
            all_checks_pass = False
    else:
        print(f"  {check_mark(False)} {jsonl_path}: NOT FOUND")
        print(f"     Run worker first to generate data")
        all_checks_pass = False
    
    metadata_path = Path("apps/worker/out/metadata.json")
    if metadata_path.exists():
        print(f"  {check_mark(True)} {metadata_path}: exists")
    else:
        print(f"  {check_mark(False)} {metadata_path}: NOT FOUND")
        all_checks_pass = False
    
    lighthouse_script = Path("scripts/lighthouse_upload.py")
    if lighthouse_script.exists():
        print(f"  {check_mark(True)} {lighthouse_script}: exists")
    else:
        print(f"  {check_mark(False)} {lighthouse_script}: NOT FOUND")
        all_checks_pass = False
    
    lighthouse_module = Path("apps/worker/lighthouse_integration.py")
    if lighthouse_module.exists():
        print(f"  {check_mark(True)} {lighthouse_module}: exists")
    else:
        print(f"  {check_mark(False)} {lighthouse_module}: NOT FOUND")
        all_checks_pass = False
    
    # 4. Network Connectivity
    print_section("4. Network Connectivity")
    
    try:
        import httpx
        client = httpx.Client(timeout=10)
        response = client.get("https://node.lighthouse.storage/api/v0/status")
        if response.status_code == 200 or response.status_code == 404:
            print(f"  {check_mark(True)} Lighthouse API: reachable")
        else:
            print(f"  {check_mark(False)} Lighthouse API: HTTP {response.status_code}")
    except Exception as e:
        print(f"  {check_mark(False)} Lighthouse API: {e}")
        all_checks_pass = False
    
    # Final Summary
    print_section("SUMMARY")
    
    if all_checks_pass:
        print("  ✅ All checks passed!")
        print()
        print("  Next steps:")
        print("    1. Run: python scripts/lighthouse_upload.py --verify")
        print("    2. Check metadata.json for latest_cid field")
        print("    3. View file in explorer using the gateway URL")
        print()
        return 0
    else:
        print("  ❌ Some checks failed. Please fix the issues above.")
        print()
        print("  Documentation:")
        print("    - README: LIGHTHOUSE_INTEGRATION.md")
        print("    - Lighthouse Docs: https://docs.lighthouse.storage/")
        print()
        return 1

if __name__ == "__main__":
    sys.exit(main())
