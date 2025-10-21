#!/usr/bin/env python3
"""
Direct Lighthouse upload using requests (bypasses SDK's broken node URL).

The official SDK uses node.lighthouse.storage which is currently down.
This module uploads directly to api.lighthouse.storage using their REST API.
"""

import logging
import requests
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)


def upload_file_direct(
    file_path: Path,
    api_key: str,
    timeout: int = 180
) -> Dict[str, Any]:
    """
    Upload file directly to Lighthouse API (bypasses SDK).
    
    Args:
        file_path: Path to file to upload
        api_key: Lighthouse API key
        timeout: Upload timeout in seconds
    
    Returns:
        Dict with:
            - cid: IPFS CID
            - name: Filename
            - size: File size
    
    Raises:
        Exception: If upload fails
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    url = "https://upload.lighthouse.storage/api/v0/add"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
    }
    
    file_size = file_path.stat().st_size
    logger.info(f"Uploading {file_path.name} ({file_size:,} bytes) to Lighthouse...")
    
    try:
        with open(file_path, 'rb') as f:
            files = {
                'file': (file_path.name, f, 'application/octet-stream')
            }
            
            # Upload with timeout
            response = requests.post(
                url,
                headers=headers,
                files=files,
                timeout=(15, timeout)  # (connect, read) timeout
            )
            response.raise_for_status()
        
        # Parse response
        data = response.json()
        
        # Lighthouse API returns different formats, handle both
        if 'data' in data:
            cid = data['data'].get('Hash') or data['data'].get('cid')
        else:
            cid = data.get('Hash') or data.get('cid')
        
        if not cid:
            raise ValueError(f"No CID in response: {data}")
        
        logger.info(f"✓ Upload complete: CID={cid}")
        
        return {
            "cid": cid,
            "name": file_path.name,
            "size": file_size,
            "gateway_url": f"https://gateway.lighthouse.storage/ipfs/{cid}",
            "explorer_url": f"https://files.lighthouse.storage/viewFile/{cid}",
        }
    
    except requests.exceptions.Timeout:
        logger.error(f"Upload timed out after {timeout}s")
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Upload failed: {e}")
        raise
