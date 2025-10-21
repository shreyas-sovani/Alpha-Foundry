"""
Lighthouse file encryption and decentralized upload integration.

This module provides functionality to:
1. Encrypt files using AES-256-GCM (client-side encryption)
2. Upload encrypted files to Lighthouse/IPFS
3. Update metadata.json with the latest CID
4. Verify uploads via Lighthouse explorer

References:
- Lighthouse API Docs: https://docs.lighthouse.storage/
- Quick Start: https://docs.lighthouse.storage/lighthouse-1/quick-start
- SDK Reference: @lighthouse-web3/sdk
"""

import hashlib
import hmac
import json
import logging
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import httpx

logger = logging.getLogger(__name__)

# Lighthouse API endpoints
LIGHTHOUSE_API_BASE = "https://node.lighthouse.storage"
LIGHTHOUSE_EXPLORER_BASE = "https://gateway.lighthouse.storage/ipfs"


class LighthouseError(Exception):
    """Base exception for Lighthouse operations."""
    pass


class LighthouseClient:
    """
    Client for Lighthouse decentralized storage with encryption support.
    
    Features:
    - Client-side AES-256-GCM encryption
    - IPFS/Filecoin upload via Lighthouse
    - CID verification
    - Metadata management
    """
    
    def __init__(self, api_key: str, timeout: int = 300):
        """
        Initialize Lighthouse client.
        
        Args:
            api_key: Lighthouse API key (get from https://files.lighthouse.storage/)
            timeout: HTTP request timeout in seconds
        """
        if not api_key:
            raise LighthouseError("LIGHTHOUSE_API_KEY is required")
        
        self.api_key = api_key
        self.timeout = timeout
        # Configure httpx with proper timeouts for large file uploads
        self.client = httpx.Client(
            timeout=httpx.Timeout(
                timeout=timeout,
                connect=30.0,  # Connection timeout
                read=timeout,   # Read timeout
                write=timeout,  # Write timeout
            ),
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )
    
    def encrypt_file(
        self,
        input_path: Path,
        output_path: Path,
        password: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Encrypt file using AES-256-GCM with optional password.
        
        Args:
            input_path: Path to plaintext file
            output_path: Path to save encrypted file
            password: Optional encryption password (defaults to API key)
        
        Returns:
            Dict with:
                - original_size: Size of original file in bytes
                - encrypted_size: Size of encrypted file in bytes
                - encryption_time: Time taken in seconds
                - sha256_original: SHA-256 hash of original file
                - sha256_encrypted: SHA-256 hash of encrypted file
        
        Raises:
            LighthouseError: If encryption fails
        """
        start_time = time.time()
        
        try:
            # Validate input
            if not input_path.exists():
                raise LighthouseError(f"Input file not found: {input_path}")
            
            original_size = input_path.stat().st_size
            logger.info(f"Encrypting file: {input_path} ({original_size:,} bytes)")
            
            # Read plaintext
            with open(input_path, "rb") as f:
                plaintext = f.read()
            
            # Compute original hash
            sha256_original = hashlib.sha256(plaintext).hexdigest()
            
            # Derive encryption key from password (or API key)
            key_material = (password or self.api_key).encode("utf-8")
            salt = os.urandom(16)  # Random salt for key derivation
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,  # 256 bits
                salt=salt,
                iterations=100000,  # OWASP recommendation
            )
            key = kdf.derive(key_material)
            
            # Encrypt with AES-256-GCM
            aesgcm = AESGCM(key)
            nonce = os.urandom(12)  # 96-bit nonce for GCM
            
            ciphertext = aesgcm.encrypt(nonce, plaintext, None)
            
            # Package: salt (16) + nonce (12) + ciphertext
            encrypted_data = salt + nonce + ciphertext
            
            # Write encrypted file
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(encrypted_data)
                f.flush()
                os.fsync(f.fileno())
            
            encrypted_size = output_path.stat().st_size
            sha256_encrypted = hashlib.sha256(encrypted_data).hexdigest()
            
            encryption_time = time.time() - start_time
            
            logger.info(
                f"✓ Encryption complete: {original_size:,} → {encrypted_size:,} bytes "
                f"in {encryption_time:.2f}s"
            )
            logger.info(f"  SHA-256 (original): {sha256_original[:16]}...")
            logger.info(f"  SHA-256 (encrypted): {sha256_encrypted[:16]}...")
            
            return {
                "original_size": original_size,
                "encrypted_size": encrypted_size,
                "encryption_time": encryption_time,
                "sha256_original": sha256_original,
                "sha256_encrypted": sha256_encrypted,
            }
        
        except Exception as e:
            logger.error(f"Encryption failed: {e}", exc_info=True)
            raise LighthouseError(f"Encryption failed: {e}") from e
    
    def upload_file(
        self,
        file_path: Path,
        name: Optional[str] = None,
        retries: int = 3
    ) -> Dict[str, Any]:
        """
        Upload file to Lighthouse/IPFS with retry logic.
        
        Args:
            file_path: Path to file to upload
            name: Optional custom filename (defaults to file_path.name)
            retries: Number of retry attempts on failure
        
        Returns:
            Dict with:
                - cid: IPFS CID (Hash)
                - name: Filename
                - size: File size in bytes
                - upload_time: Time taken in seconds
        
        Raises:
            LighthouseError: If upload fails after all retries
        """
        if not file_path.exists():
            raise LighthouseError(f"File not found: {file_path}")
        
        file_size = file_path.stat().st_size
        file_name = name or file_path.name
        
        logger.info(f"Uploading to Lighthouse: {file_path} ({file_size:,} bytes)")
        
        last_error = None
        for attempt in range(retries):
            start_time = time.time()
            try:
                # Upload via multipart form - read file fresh each attempt
                with open(file_path, "rb") as f:
                    files = {"file": (file_name, f, "application/octet-stream")}
                    headers = {"Authorization": f"Bearer {self.api_key}"}
                    
                    logger.info(f"Upload attempt {attempt + 1}/{retries}...")
                    response = self.client.post(
                        f"{LIGHTHOUSE_API_BASE}/api/v0/add",
                        files=files,
                        headers=headers
                    )
                
                upload_time = time.time() - start_time
                
                if response.status_code != 200:
                    error_detail = response.text[:200]
                    raise LighthouseError(
                        f"Upload failed (HTTP {response.status_code}): {error_detail}"
                    )
                
                result = response.json()
                
                # Extract CID from response
                cid = result.get("Hash") or result.get("cid")
                if not cid:
                    raise LighthouseError(f"No CID in response: {result}")
                
                logger.info(f"✓ Upload complete: CID={cid} in {upload_time:.2f}s")
                logger.info(f"  Gateway URL: {LIGHTHOUSE_EXPLORER_BASE}/{cid}")
                
                return {
                    "cid": cid,
                    "name": result.get("Name", file_name),
                    "size": result.get("Size", file_size),
                    "upload_time": upload_time,
                }
            
            except (httpx.TimeoutException, httpx.ConnectError, httpx.ConnectTimeout) as e:
                upload_time = time.time() - start_time
                last_error = e
                logger.warning(
                    f"Upload attempt {attempt + 1}/{retries} failed after {upload_time:.1f}s: {e}"
                )
                if attempt < retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    logger.info(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                continue
            
            except httpx.HTTPError as e:
                logger.error(f"Upload HTTP error: {e}", exc_info=True)
                raise LighthouseError(f"Upload HTTP error: {e}") from e
            except Exception as e:
                logger.error(f"Upload failed: {e}", exc_info=True)
                raise LighthouseError(f"Upload failed: {e}") from e
        
        # All retries exhausted
        raise LighthouseError(
            f"Upload failed after {retries} attempts. Last error: {last_error}"
        )
    
    def verify_cid(self, cid: str) -> bool:
        """
        Verify CID is accessible via Lighthouse gateway.
        
        Args:
            cid: IPFS CID to verify
        
        Returns:
            True if CID is accessible, False otherwise
        """
        try:
            logger.info(f"Verifying CID: {cid}")
            
            # HEAD request to check if CID exists
            response = self.client.head(
                f"{LIGHTHOUSE_EXPLORER_BASE}/{cid}",
                timeout=30
            )
            
            accessible = response.status_code == 200
            
            if accessible:
                logger.info(f"✓ CID verified: {cid}")
            else:
                logger.warning(f"⚠️  CID not accessible (HTTP {response.status_code}): {cid}")
            
            return accessible
        
        except Exception as e:
            logger.error(f"CID verification failed: {e}")
            return False
    
    def close(self):
        """Close HTTP client."""
        self.client.close()


def update_metadata_with_cid(
    metadata_path: Path,
    cid: str,
    encrypted_file_path: Path,
    encryption_stats: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Atomically update metadata.json with latest CID and encryption stats.
    
    Args:
        metadata_path: Path to metadata.json
        cid: IPFS CID of encrypted file
        encrypted_file_path: Path to encrypted file
        encryption_stats: Stats from encrypt_file()
    
    Returns:
        Dict with before and after metadata (for diff logging)
    
    Raises:
        LighthouseError: If metadata update fails
    """
    try:
        # Read existing metadata
        if metadata_path.exists():
            with open(metadata_path, "r") as f:
                metadata_before = json.load(f)
        else:
            metadata_before = {}
        
        # Add Lighthouse fields
        metadata_after = metadata_before.copy()
        metadata_after["latest_cid"] = cid
        metadata_after["lighthouse_gateway"] = f"{LIGHTHOUSE_EXPLORER_BASE}/{cid}"
        metadata_after["encryption"] = {
            "enabled": True,
            "algorithm": "AES-256-GCM",
            "encrypted_file": str(encrypted_file_path.name),
            "encrypted_size": encryption_stats["encrypted_size"],
            "original_size": encryption_stats["original_size"],
            "sha256_encrypted": encryption_stats["sha256_encrypted"],
            "sha256_original": encryption_stats["sha256_original"],
        }
        metadata_after["last_lighthouse_upload"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        
        # Atomic write
        temp_path = metadata_path.with_suffix(".json.tmp")
        with open(temp_path, "w") as f:
            json.dump(metadata_after, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        
        temp_path.replace(metadata_path)
        
        logger.info(f"✓ Metadata updated: {metadata_path}")
        logger.info(f"  latest_cid: {cid}")
        
        return {
            "before": metadata_before,
            "after": metadata_after,
        }
    
    except Exception as e:
        logger.error(f"Metadata update failed: {e}", exc_info=True)
        raise LighthouseError(f"Metadata update failed: {e}") from e


def encrypt_and_upload_rolling_data(
    jsonl_path: Path,
    metadata_path: Path,
    api_key: str,
    password: Optional[str] = None,
    verify: bool = True
) -> Dict[str, Any]:
    """
    Complete workflow: encrypt dexarb_latest.jsonl and upload to Lighthouse.
    
    This is the main entry point for Lighthouse integration.
    
    Args:
        jsonl_path: Path to dexarb_latest.jsonl
        metadata_path: Path to metadata.json
        api_key: Lighthouse API key
        password: Optional encryption password (defaults to API key)
        verify: Whether to verify CID accessibility
    
    Returns:
        Dict with:
            - cid: IPFS CID
            - encrypted_file: Path to encrypted file
            - verified: Whether CID was verified
            - encryption_stats: Encryption statistics
            - upload_stats: Upload statistics
            - metadata_diff: Before/after metadata
    
    Raises:
        LighthouseError: If any step fails
    """
    start_time = time.time()
    
    try:
        # Validation
        if not jsonl_path.exists():
            raise LighthouseError(f"JSONL file not found: {jsonl_path}")
        
        file_size = jsonl_path.stat().st_size
        logger.info(f"Starting Lighthouse workflow for {jsonl_path}")
        logger.info(f"  File size: {file_size:,} bytes")
        logger.info(f"  Last modified: {time.ctime(jsonl_path.stat().st_mtime)}")
        
        # Initialize client
        client = LighthouseClient(api_key)
        
        # Step 1: Encrypt file
        encrypted_path = jsonl_path.with_suffix(".jsonl.enc")
        logger.info("Step 1/4: Encrypting file...")
        
        encryption_stats = client.encrypt_file(
            input_path=jsonl_path,
            output_path=encrypted_path,
            password=password
        )
        
        # Step 2: Upload encrypted file
        logger.info("Step 2/4: Uploading encrypted file to Lighthouse...")
        
        upload_stats = client.upload_file(
            file_path=encrypted_path,
            name=encrypted_path.name
        )
        
        cid = upload_stats["cid"]
        
        # Step 3: Verify CID (optional)
        verified = False
        if verify:
            logger.info("Step 3/4: Verifying CID accessibility...")
            verified = client.verify_cid(cid)
            if not verified:
                logger.warning(f"⚠️  CID not immediately accessible (may take a few seconds)")
        else:
            logger.info("Step 3/4: Skipping CID verification")
        
        # Step 4: Update metadata
        logger.info("Step 4/4: Updating metadata.json...")
        
        metadata_diff = update_metadata_with_cid(
            metadata_path=metadata_path,
            cid=cid,
            encrypted_file_path=encrypted_path,
            encryption_stats=encryption_stats
        )
        
        total_time = time.time() - start_time
        
        # Success summary
        logger.info("")
        logger.info("=" * 80)
        logger.info("✅ LIGHTHOUSE ENCRYPTION/UPLOAD COMPLETE")
        logger.info("=" * 80)
        logger.info(f"  CID: {cid}")
        logger.info(f"  Gateway: {LIGHTHOUSE_EXPLORER_BASE}/{cid}")
        logger.info(f"  Encrypted file: {encrypted_path}")
        logger.info(f"  Original size: {encryption_stats['original_size']:,} bytes")
        logger.info(f"  Encrypted size: {encryption_stats['encrypted_size']:,} bytes")
        logger.info(f"  Encryption time: {encryption_stats['encryption_time']:.2f}s")
        logger.info(f"  Upload time: {upload_stats['upload_time']:.2f}s")
        logger.info(f"  Total time: {total_time:.2f}s")
        logger.info(f"  Verified: {'✓' if verified else '⚠️  (not yet)'}")
        logger.info("=" * 80)
        logger.info("")
        
        # Clean up client
        client.close()
        
        return {
            "cid": cid,
            "encrypted_file": str(encrypted_path),
            "verified": verified,
            "encryption_stats": encryption_stats,
            "upload_stats": upload_stats,
            "metadata_diff": metadata_diff,
            "total_time": total_time,
        }
    
    except Exception as e:
        logger.error(f"❌ Lighthouse workflow failed: {e}", exc_info=True)
        raise LighthouseError(f"Lighthouse workflow failed: {e}") from e


def decrypt_file(
    encrypted_path: Path,
    output_path: Path,
    password: Optional[str] = None,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Decrypt file encrypted by encrypt_file().
    
    Args:
        encrypted_path: Path to encrypted file
        output_path: Path to save decrypted file
        password: Decryption password (must match encryption password)
        api_key: API key (used if password not provided)
    
    Returns:
        Dict with decryption stats
    
    Raises:
        LighthouseError: If decryption fails
    """
    start_time = time.time()
    
    try:
        if not encrypted_path.exists():
            raise LighthouseError(f"Encrypted file not found: {encrypted_path}")
        
        logger.info(f"Decrypting file: {encrypted_path}")
        
        # Read encrypted data
        with open(encrypted_path, "rb") as f:
            encrypted_data = f.read()
        
        # Extract: salt (16) + nonce (12) + ciphertext
        if len(encrypted_data) < 28:
            raise LighthouseError("Invalid encrypted file format")
        
        salt = encrypted_data[:16]
        nonce = encrypted_data[16:28]
        ciphertext = encrypted_data[28:]
        
        # Derive decryption key
        key_material = (password or api_key or "").encode("utf-8")
        if not key_material:
            raise LighthouseError("Password or API key required for decryption")
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = kdf.derive(key_material)
        
        # Decrypt
        aesgcm = AESGCM(key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        
        # Write decrypted file
        with open(output_path, "wb") as f:
            f.write(plaintext)
            f.flush()
            os.fsync(f.fileno())
        
        decryption_time = time.time() - start_time
        
        logger.info(f"✓ Decryption complete in {decryption_time:.2f}s")
        logger.info(f"  Decrypted file: {output_path}")
        
        return {
            "decrypted_size": len(plaintext),
            "decryption_time": decryption_time,
        }
    
    except Exception as e:
        logger.error(f"Decryption failed: {e}", exc_info=True)
        raise LighthouseError(f"Decryption failed: {e}") from e
