#!/usr/bin/env python3
"""
Quick test script to upload to Lighthouse from Railway.
Run this on Railway to test the integration.
"""

import os
import sys
from pathlib import Path

# Add apps/worker to path
sys.path.insert(0, str(Path(__file__).parent.parent / "apps/worker"))

from lighthouse_sdk_integration import LighthouseSDK

def main():
    print("=" * 60)
    print("LIGHTHOUSE UPLOAD TEST")
    print("=" * 60)
    
    # Get API key
    api_key = os.getenv("LIGHTHOUSE_API_KEY")
    if not api_key:
        print("❌ LIGHTHOUSE_API_KEY not found in environment")
        print("   Add it in Railway dashboard: Variables tab")
        return 1
    
    print(f"✓ API Key found: {api_key[:10]}...{api_key[-6:]}")
    
    # Initialize client
    print("\n📦 Initializing Lighthouse SDK...")
    try:
        lh = LighthouseSDK(api_key=api_key)
        print("✓ SDK initialized")
    except Exception as e:
        print(f"❌ SDK initialization failed: {e}")
        return 1
    
    # Check for file to upload
    test_file = Path(__file__).parent.parent / "apps/worker/out/dexarb_latest.jsonl"
    
    if not test_file.exists():
        print(f"\n⚠️  File not found: {test_file}")
        print("   Creating a test file...")
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text('{"test": "data", "timestamp": "2025-10-21"}\n')
    
    file_size = test_file.stat().st_size
    print(f"\n📄 File to upload: {test_file.name}")
    print(f"   Size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
    
    # Test 1: Encrypt
    print("\n🔐 Step 1: Encrypting file...")
    try:
        encrypted_file = test_file.parent / f"{test_file.name}.enc"
        stats = lh.encrypt_file(test_file, encrypted_file)
        print(f"✓ Encryption successful!")
        print(f"  Original:  {stats['original_size']:,} bytes")
        print(f"  Encrypted: {stats['encrypted_size']:,} bytes")
        print(f"  Time:      {stats['encryption_time']:.2f}s")
    except Exception as e:
        print(f"❌ Encryption failed: {e}")
        return 1
    
    # Test 2: Upload
    print(f"\n🚀 Step 2: Uploading to Lighthouse...")
    try:
        result = lh.upload_file(encrypted_file, tag="test_upload")
        print(f"✓ Upload successful!")
        print(f"\n🎯 RESULTS:")
        print(f"   CID: {result['cid']}")
        print(f"   Gateway: {result['gateway_url']}")
        print(f"   Explorer: {result['explorer_url']}")
        print(f"   Time: {result['upload_time']:.2f}s")
        
        print(f"\n✅ SUCCESS! Check Lighthouse dashboard:")
        print(f"   https://files.lighthouse.storage/dashboard")
        print(f"\n   Your file should now be visible!")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Upload failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
