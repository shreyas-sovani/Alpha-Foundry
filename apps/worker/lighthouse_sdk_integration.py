#!/usr/bin/env python3
"""
Complete Lighthouse integration using official Python SDK.

This module combines:
1. Our AES-256-GCM encryption (client-side)
2. Official lighthouseweb3 SDK for upload
3. CID tracking and verification

Usage:
    from lighthouse_sdk_integration import LighthouseSDK
    
    lh = LighthouseSDK(api_key="your_key")
    
    # Encrypt and upload
    result = lh.encrypt_and_upload("data.json", password="secret")
    print(f"CID: {result['cid']}")
    
    # Verify
    accessible = lh.verify_cid(result['cid'])
"""

import hashlib
import logging
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from lighthouseweb3 import Lighthouse

logger = logging.getLogger(__name__)


class LighthouseSDK:
    """
    Lighthouse integration using official SDK with client-side encryption.
    
    Features:
    - AES-256-GCM encryption before upload
    - Official lighthouseweb3 SDK for reliable uploads
    - CID tracking and verification
    - Metadata management
    """
    
    def __init__(self, api_key: str, upload_timeout: int = 180):
        """
        Initialize Lighthouse SDK client.
        
        Args:
            api_key: Lighthouse API key from https://files.lighthouse.storage/
            upload_timeout: Upload timeout in seconds (default: 180)
        """
        if not api_key:
            raise ValueError("LIGHTHOUSE_API_KEY is required")
        
        self.api_key = api_key
        self.upload_timeout = upload_timeout
        
        # Monkey-patch requests to add timeouts (SDK doesn't expose this)
        import requests as req_lib
        original_post = req_lib.post
        original_get = req_lib.get
        
        def post_with_timeout(*args, **kwargs):
            if 'timeout' not in kwargs:
                # (connect_timeout, read_timeout)
                kwargs['timeout'] = (15, self.upload_timeout)
            return original_post(*args, **kwargs)
        
        def get_with_timeout(*args, **kwargs):
            if 'timeout' not in kwargs:
                kwargs['timeout'] = (15, 30)
            return original_get(*args, **kwargs)
        
        req_lib.post = post_with_timeout
        req_lib.get = get_with_timeout
        
        self.client = Lighthouse(token=api_key)
        logger.info(f"Lighthouse SDK client initialized (upload timeout: {self.upload_timeout}s)")
    
    def encrypt_file(
        self,
        input_path: Path,
        output_path: Path,
        password: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Encrypt file using AES-256-GCM.
        
        Args:
            input_path: Path to plaintext file
            output_path: Path to save encrypted file
            password: Optional password (defaults to API key)
        
        Returns:
            Dict with encryption statistics
        """
        start_time = time.time()
        
        # Use password or API key for encryption
        key_material = (password or self.api_key).encode('utf-8')
        
        # Generate random salt
        salt = os.urandom(32)
        
        # Derive encryption key using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100_000,
        )
        key = kdf.derive(key_material)
        
        # Read plaintext
        with open(input_path, 'rb') as f:
            plaintext = f.read()
        
        original_size = len(plaintext)
        original_hash = hashlib.sha256(plaintext).hexdigest()
        
        # Encrypt with AES-256-GCM
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)  # 96-bit nonce for GCM
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)
        
        # Write encrypted file: salt + nonce + ciphertext
        encrypted_data = salt + nonce + ciphertext
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'wb') as f:
            f.write(encrypted_data)
        
        encrypted_size = len(encrypted_data)
        encrypted_hash = hashlib.sha256(encrypted_data).hexdigest()
        encryption_time = time.time() - start_time
        
        logger.info(f"✓ Encrypted: {input_path.name} → {output_path.name}")
        logger.info(f"  Size: {original_size:,} → {encrypted_size:,} bytes")
        logger.info(f"  Time: {encryption_time:.2f}s")
        
        return {
            "original_size": original_size,
            "encrypted_size": encrypted_size,
            "encryption_time": encryption_time,
            "sha256_original": original_hash,
            "sha256_encrypted": encrypted_hash,
            "salt": salt.hex(),
            "nonce": nonce.hex(),
        }
    
    def upload_file(self, file_path: Path, tag: str = "") -> Dict[str, Any]:
        """
        Upload file to Lighthouse using official SDK.
        
        Args:
            file_path: Path to file to upload
            tag: Optional tag for organization
        
        Returns:
            Dict with:
                - cid: IPFS CID
                - name: Filename
                - size: File size
                - upload_time: Time taken
                - gateway_url: Public gateway URL
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_size = file_path.stat().st_size
        logger.info(f"Uploading {file_path.name} ({file_size:,} bytes)...")
        
        start_time = time.time()
        
        # Upload using official SDK
        result = self.client.upload(source=str(file_path), tag=tag)
        
        upload_time = time.time() - start_time
        
        # Extract CID from response
        if isinstance(result, dict):
            data = result.get('data', result)
            cid = data.get('Hash') or data.get('cid')
        else:
            raise ValueError(f"Unexpected response format: {result}")
        
        if not cid:
            raise ValueError(f"No CID in response: {result}")
        
        gateway_url = f"https://gateway.lighthouse.storage/ipfs/{cid}"
        explorer_url = f"https://files.lighthouse.storage/viewFile/{cid}"
        
        logger.info(f"✓ Upload complete: CID={cid}")
        logger.info(f"  Gateway: {gateway_url}")
        logger.info(f"  Time: {upload_time:.2f}s")
        
        return {
            "cid": cid,
            "name": file_path.name,
            "size": file_size,
            "upload_time": upload_time,
            "gateway_url": gateway_url,
            "explorer_url": explorer_url,
        }
    
    def encrypt_and_upload(
        self,
        input_path: Path,
        password: Optional[str] = None,
        tag: str = "",
        keep_encrypted: bool = True
    ) -> Dict[str, Any]:
        """
        Encrypt file and upload to Lighthouse.
        
        Args:
            input_path: Path to plaintext file
            password: Optional encryption password
            tag: Optional tag for Lighthouse
            keep_encrypted: Whether to keep encrypted file after upload
        
        Returns:
            Dict with encryption + upload results
        """
        # Generate encrypted filename
        encrypted_path = input_path.parent / f"{input_path.name}.enc"
        
        # Step 1: Encrypt
        logger.info(f"Step 1/2: Encrypting {input_path.name}...")
        encryption_stats = self.encrypt_file(input_path, encrypted_path, password)
        
        # Step 2: Upload
        logger.info(f"Step 2/2: Uploading {encrypted_path.name}...")
        upload_stats = self.upload_file(encrypted_path, tag)
        
        # Cleanup if requested
        if not keep_encrypted:
            encrypted_path.unlink()
            logger.info(f"✓ Cleaned up temporary encrypted file")
        
        return {
            "encryption": encryption_stats,
            "upload": upload_stats,
            "total_time": encryption_stats["encryption_time"] + upload_stats["upload_time"],
        }
    
    def verify_cid(self, cid: str) -> bool:
        """
        Verify CID is accessible via Lighthouse gateway.
        
        Args:
            cid: IPFS CID to verify
        
        Returns:
            True if accessible, False otherwise
        """
        import requests
        
        try:
            url = f"https://gateway.lighthouse.storage/ipfs/{cid}"
            response = requests.head(url, timeout=30)
            accessible = response.status_code == 200
            
            if accessible:
                logger.info(f"✓ CID verified: {cid}")
            else:
                logger.warning(f"⚠️  CID not accessible (HTTP {response.status_code}): {cid}")
            
            return accessible
        
        except Exception as e:
            logger.error(f"CID verification failed: {e}")
            return False
    
    def get_uploads(self, cid: Optional[str] = None) -> Dict[str, Any]:
        """
        Get upload information.
        
        Args:
            cid: Optional specific CID to check
        
        Returns:
            Upload information from Lighthouse
        """
        result = self.client.getUploads(cid)
        return result


# Convenience function for quick usage
def quick_encrypt_and_upload(
    file_path: str,
    api_key: str,
    password: Optional[str] = None
) -> Dict[str, Any]:
    """
    Quick helper to encrypt and upload a file.
    
    Args:
        file_path: Path to file
        api_key: Lighthouse API key
        password: Optional encryption password
    
    Returns:
        Dict with CID and stats
    """
    lh = LighthouseSDK(api_key=api_key)
    return lh.encrypt_and_upload(Path(file_path), password=password)


if __name__ == "__main__":
    # Example usage
    import sys
    from dotenv import load_dotenv
    
    load_dotenv()
    
    api_key = os.getenv("LIGHTHOUSE_API_KEY")
    if not api_key:
        print("❌ LIGHTHOUSE_API_KEY not set")
        sys.exit(1)
    
    # Test file
    test_file = Path("apps/worker/out/dexarb_latest.jsonl")
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        sys.exit(1)
    
    # Initialize
    lh = LighthouseSDK(api_key=api_key)
    
    # Test encryption only (skip upload due to network issue)
    print("\n🔐 Testing encryption...")
    encrypted_path = test_file.parent / f"{test_file.name}.enc"
    stats = lh.encrypt_file(test_file, encrypted_path)
    
    print("\n✅ Encryption test complete!")
    print(f"   Original: {stats['original_size']:,} bytes")
    print(f"   Encrypted: {stats['encrypted_size']:,} bytes")
    print(f"   Time: {stats['encryption_time']:.2f}s")
    print(f"   SHA-256: {stats['sha256_encrypted'][:16]}...")
    
    print("\n⚠️  Upload skipped - network issue prevents connection to node.lighthouse.storage")
    print("   Deploy to Railway to test upload functionality")
