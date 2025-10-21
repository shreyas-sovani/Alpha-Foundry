#!/usr/bin/env python3
"""
Manual Lighthouse encryption and upload script.

Usage:
    python scripts/lighthouse_upload.py [--verify] [--password PASSWORD]

Environment variables required:
    LIGHTHOUSE_API_KEY: Your Lighthouse API key (from https://files.lighthouse.storage/)

Optional:
    LIGHTHOUSE_PASSWORD: Custom encryption password (defaults to API key)
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# Add apps/worker to path
sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "worker"))

from lighthouse_integration import (
    encrypt_and_upload_rolling_data,
    LighthouseError,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Encrypt and upload dexarb_latest.jsonl to Lighthouse"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify CID accessibility after upload"
    )
    parser.add_argument(
        "--password",
        type=str,
        help="Custom encryption password (defaults to LIGHTHOUSE_API_KEY)"
    )
    parser.add_argument(
        "--jsonl",
        type=str,
        default="apps/worker/out/dexarb_latest.jsonl",
        help="Path to JSONL file to encrypt and upload"
    )
    parser.add_argument(
        "--metadata",
        type=str,
        default="apps/worker/out/metadata.json",
        help="Path to metadata.json to update"
    )
    
    args = parser.parse_args()
    
    # Check environment
    api_key = os.getenv("LIGHTHOUSE_API_KEY")
    if not api_key:
        logger.error("❌ LIGHTHOUSE_API_KEY environment variable not set")
        logger.error("   Get your API key from: https://files.lighthouse.storage/")
        logger.error("   Then export it: export LIGHTHOUSE_API_KEY='your_key_here'")
        sys.exit(1)
    
    # Mask API key in logs
    masked_key = api_key[:6] + "..." + api_key[-4:] if len(api_key) > 10 else "***"
    logger.info(f"✓ LIGHTHOUSE_API_KEY found: {masked_key}")
    
    # Get password
    password = args.password or os.getenv("LIGHTHOUSE_PASSWORD")
    if password:
        logger.info("✓ Using custom encryption password")
    else:
        logger.info("  Using API key as encryption password (default)")
    
    # Resolve paths
    jsonl_path = Path(args.jsonl).resolve()
    metadata_path = Path(args.metadata).resolve()
    
    logger.info(f"JSONL file: {jsonl_path}")
    logger.info(f"Metadata file: {metadata_path}")
    
    # Run workflow
    try:
        result = encrypt_and_upload_rolling_data(
            jsonl_path=jsonl_path,
            metadata_path=metadata_path,
            api_key=api_key,
            password=password,
            verify=args.verify,
        )
        
        logger.info("")
        logger.info("✅ PASS: Lighthouse encryption/upload live, metadata CID synced")
        logger.info("")
        logger.info("Next steps:")
        logger.info(f"1. View file in explorer: {result['upload_stats']['cid']}")
        logger.info(f"   https://gateway.lighthouse.storage/ipfs/{result['upload_stats']['cid']}")
        logger.info(f"2. Check metadata.json: {metadata_path}")
        logger.info(f"3. Encrypted file saved: {result['encrypted_file']}")
        logger.info("")
        
        sys.exit(0)
    
    except LighthouseError as e:
        logger.error(f"❌ FAIL: {e}")
        logger.error("")
        logger.error("Troubleshooting:")
        logger.error("1. Check LIGHTHOUSE_API_KEY is valid")
        logger.error("2. Verify network connectivity")
        logger.error("3. Ensure dexarb_latest.jsonl exists and is not empty")
        logger.error("4. Check Lighthouse status: https://status.lighthouse.storage/")
        logger.error("")
        logger.error("Documentation:")
        logger.error("- https://docs.lighthouse.storage/")
        logger.error("- https://docs.lighthouse.storage/lighthouse-1/quick-start")
        logger.error("")
        sys.exit(1)
    
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
