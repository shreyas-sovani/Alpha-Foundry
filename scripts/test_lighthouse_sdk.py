#!/usr/bin/env python3
"""
Test Lighthouse Python SDK with actual file upload.
Using official lighthouseweb3 package.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lighthouseweb3 import Lighthouse
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent / ".env.local")

def main():
    """Test Lighthouse SDK upload."""
    
    # Get API key
    api_key = os.getenv("LIGHTHOUSE_API_KEY")
    if not api_key:
        print("❌ LIGHTHOUSE_API_KEY not found in .env.local")
        return 1
    
    print(f"✓ API Key loaded: {api_key[:10]}...")
    
    # Initialize Lighthouse client
    print("\n📦 Initializing Lighthouse client...")
    lh = Lighthouse(token=api_key)
    print("✓ Client initialized")
    
    # File to upload
    file_path = Path(__file__).parent.parent / "apps/worker/out/dexarb_latest.jsonl"
    
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return 1
    
    file_size = file_path.stat().st_size
    print(f"\n📄 File to upload: {file_path.name}")
    print(f"   Size: {file_size:,} bytes ({file_size / 1024:.1f} KB)")
    
    # Upload file
    print("\n🚀 Uploading to Lighthouse...")
    try:
        upload_result = lh.upload(source=str(file_path))
        print("\n✅ Upload successful!")
        print(f"   Response: {upload_result}")
        
        # Extract CID if available
        if isinstance(upload_result, dict):
            cid = upload_result.get('Hash') or upload_result.get('data', {}).get('Hash')
            if cid:
                print(f"\n🎯 CID: {cid}")
                print(f"   Gateway URL: https://gateway.lighthouse.storage/ipfs/{cid}")
                print(f"   Explorer: https://files.lighthouse.storage/viewFile/{cid}")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Upload failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
