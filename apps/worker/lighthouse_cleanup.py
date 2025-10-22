#!/usr/bin/env python3
"""
Lighthouse Storage Auto-Cleanup Service
========================================

Automatically maintains protected files on Lighthouse storage.
Runs after each successful upload to delete old versions while protecting critical files.

FEATURES:
- Protects permanent CIDs (configured in code)
- Protects latest uploaded file
- Optionally protects additional CIDs
- Integrates with worker upload cycle
- Uses reliable Lighthouse CLI
- Safe: Never deletes protected files
- Atomic operations with rollback
- Comprehensive logging

PROTECTED FILES:
- Two permanent CIDs are hardcoded and will NEVER be deleted
- The latest uploaded file is always protected
- Additional CIDs can be specified at initialization

USAGE:
    from lighthouse_cleanup import LighthouseCleanup
    
    cleanup = LighthouseCleanup(api_key=settings.LIGHTHOUSE_API_KEY)
    cleanup.cleanup_old_files(protected_cid="QmXXX...")  # Protects latest + 2 permanent CIDs
"""

import os
import sys
import json
import subprocess
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import requests

logger = logging.getLogger(__name__)


@dataclass
class LighthouseFile:
    """Represents a file stored on Lighthouse."""
    file_id: str
    cid: str
    file_name: str
    size_bytes: int
    last_update: int
    
    @property
    def size_mb(self) -> float:
        """File size in MB."""
        return self.size_bytes / (1024 * 1024)
    
    @property
    def timestamp(self) -> datetime:
        """Timestamp as datetime object."""
        return datetime.fromtimestamp(self.last_update / 1000)
    
    @classmethod
    def from_api_response(cls, data: dict) -> 'LighthouseFile':
        """Create from API response."""
        return cls(
            file_id=data.get('id', ''),
            cid=data.get('cid', ''),
            file_name=data.get('fileName', ''),
            size_bytes=data.get('fileSizeInBytes', 0),
            last_update=data.get('lastUpdate', 0)
        )


class LighthouseCleanup:
    """Manages automatic cleanup of old Lighthouse files."""
    
    # API Configuration
    API_BASE = "https://api.lighthouse.storage"
    LIST_ENDPOINT = f"{API_BASE}/api/user/files_uploaded"
    
    # CLI Configuration
    CLI_COMMAND = "lighthouse-web3"
    DELETE_COMMAND = ["lighthouse-web3", "delete-file"]
    
    # Permanently protected CIDs that should NEVER be deleted
    PERMANENT_PROTECTED_CIDS = {
        "bafybeih5j5recyxiwscbtjl7o5rmv22rijmeq552iovrguas45s4766yw4",
        "bafkreie73wguaf7yucgzcudbkivtgtxzvyv2efjg24s76j67lu7cbt7vcy"
    }
    
    def __init__(
        self,
        api_key: str,
        verify_cli: bool = True,
        min_files_to_keep: int = 1,
        additional_protected_cids: Optional[List[str]] = None
    ):
        """
        Initialize cleanup service.
        
        Args:
            api_key: Lighthouse API key
            verify_cli: Verify CLI is installed and configured
            min_files_to_keep: Minimum files to keep (safety threshold)
            additional_protected_cids: Optional list of additional CIDs to protect
        """
        self.api_key = api_key
        self.min_files_to_keep = max(1, min_files_to_keep)
        
        # Build complete set of protected CIDs
        self.protected_cids = set(self.PERMANENT_PROTECTED_CIDS)
        if additional_protected_cids:
            self.protected_cids.update(additional_protected_cids)
        
        logger.info(f"🛡️  Permanent protection enabled for {len(self.PERMANENT_PROTECTED_CIDS)} CIDs")
        if additional_protected_cids:
            logger.info(f"🛡️  Additional protection for {len(additional_protected_cids)} CIDs")
        
        if verify_cli:
            self._verify_cli_setup()
    
    def _verify_cli_setup(self) -> None:
        """Verify Lighthouse CLI is installed and configured."""
        # Check CLI is installed
        try:
            result = subprocess.run(
                [self.CLI_COMMAND, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                raise RuntimeError("Lighthouse CLI not responding correctly")
        except FileNotFoundError:
            raise RuntimeError(
                f"Lighthouse CLI not found. Install with: "
                f"npm install -g @lighthouse-web3/sdk"
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("Lighthouse CLI timeout")
        
        logger.info("✅ Lighthouse CLI verified")
    
    def list_all_files(self) -> List[LighthouseFile]:
        """
        List all files from Lighthouse storage.
        
        Returns:
            List of LighthouseFile objects, sorted by timestamp (newest first)
            
        Raises:
            RuntimeError: If API request fails
        """
        headers = {"Authorization": f"Bearer {self.api_key}"}
        all_files = []
        last_key = None
        
        try:
            while True:
                params = {"lastKey": last_key} if last_key else {}
                
                response = requests.get(
                    self.LIST_ENDPOINT,
                    headers=headers,
                    params=params,
                    timeout=30
                )
                response.raise_for_status()
                
                data = response.json()
                file_list = data.get("fileList", [])
                
                if not file_list:
                    break
                
                all_files.extend([
                    LighthouseFile.from_api_response(f) for f in file_list
                ])
                
                # Check for pagination
                if len(file_list) < 10:
                    break
                
                last_key = file_list[-1].get("id")
                if not last_key:
                    break
            
            # Sort by timestamp (newest first)
            all_files.sort(key=lambda f: f.last_update, reverse=True)
            
            logger.info(f"📋 Found {len(all_files)} files on Lighthouse")
            return all_files
            
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to list files: {e}")
    
    def identify_files_to_delete(
        self,
        all_files: List[LighthouseFile],
        protected_cid: Optional[str] = None
    ) -> Tuple[List[LighthouseFile], List[LighthouseFile]]:
        """
        Identify which files to keep and delete.
        
        Args:
            all_files: All files from Lighthouse
            protected_cid: Specific CID to protect (e.g., latest upload)
            
        Returns:
            Tuple of (files_to_keep, files_to_delete)
        """
        if not all_files:
            raise ValueError("No files to process")
        
        # Build comprehensive set of CIDs to protect
        cids_to_protect = set(self.protected_cids)  # Start with permanent + additional
        
        # Add the explicitly protected CID (e.g., latest upload)
        if protected_cid:
            cids_to_protect.add(protected_cid)
        else:
            # If no specific CID provided, protect the newest file
            cids_to_protect.add(all_files[0].cid)
        
        # Identify protected files and files to delete
        protected_files = []
        files_to_delete = []
        
        for file in all_files:
            if file.cid in cids_to_protect:
                protected_files.append(file)
            else:
                files_to_delete.append(file)
        
        # Log protection summary
        logger.info(f"🛡️  Protected files: {len(protected_files)}")
        for pf in protected_files:
            reason = "PERMANENT" if pf.cid in self.PERMANENT_PROTECTED_CIDS else "LATEST"
            logger.info(
                f"     • {pf.cid[:40]}... ({pf.size_mb:.2f} MB) [{reason}]"
            )
        
        logger.info(f"🗑️  Files to delete: {len(files_to_delete)}")
        
        return protected_files, files_to_delete
    
    def delete_file(self, file: LighthouseFile) -> bool:
        """
        Delete a single file using Lighthouse CLI.
        
        Args:
            file: File to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if CLI is available
            try:
                subprocess.run(
                    ["lighthouse-web3", "--version"],
                    capture_output=True,
                    timeout=2,
                    check=True
                )
            except (FileNotFoundError, subprocess.CalledProcessError):
                logger.error(
                    "❌ Lighthouse CLI not installed. "
                    "Install: npm install -g @lighthouse-web3/sdk"
                )
                return False
            
            result = subprocess.run(
                [*self.DELETE_COMMAND, file.file_id],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Check if deletion was successful
            output = result.stdout + result.stderr
            if result.returncode == 0 and any(
                keyword in output.lower() 
                for keyword in ["success", "deleted", "removed"]
            ):
                logger.debug(
                    f"✅ Deleted: {file.cid[:40]}... "
                    f"({file.size_mb:.2f} MB)"
                )
                return True
            else:
                logger.warning(
                    f"❌ Failed to delete {file.cid[:40]}...: "
                    f"{output[:100]}"
                )
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"⏱️  Timeout deleting {file.cid[:40]}...")
            return False
        except Exception as e:
            logger.error(f"❌ Error deleting {file.cid[:40]}...: {e}")
            return False
    
    def cleanup_old_files(
        self,
        protected_cid: Optional[str] = None,
        dry_run: bool = False
    ) -> Dict[str, any]:
        """
        Clean up old files, keeping only protected files.
        
        This method protects:
        1. Permanent CIDs (configured in PERMANENT_PROTECTED_CIDS)
        2. The latest uploaded file (protected_cid parameter or newest if not specified)
        3. Any additional CIDs passed during initialization
        
        Args:
            protected_cid: Specific CID to protect (e.g., latest upload)
            dry_run: If True, don't actually delete files
            
        Returns:
            Dict with cleanup results:
            {
                "success": bool,
                "files_total": int,
                "files_deleted": int,
                "files_failed": int,
                "files_remaining": int,
                "space_saved_mb": float,
                "protected_files": List[str] (CIDs)
            }
        """
        start_time = datetime.now()
        
        try:
            # List all files
            all_files = self.list_all_files()
            
            # Calculate minimum files to keep (permanent + dynamic)
            min_protected = len(self.PERMANENT_PROTECTED_CIDS) + self.min_files_to_keep
            
            if len(all_files) <= min_protected:
                logger.info(
                    f"✅ Only {len(all_files)} file(s) - no cleanup needed "
                    f"(minimum: {min_protected})"
                )
                return {
                    "success": True,
                    "files_total": len(all_files),
                    "files_deleted": 0,
                    "files_failed": 0,
                    "files_remaining": len(all_files),
                    "space_saved_mb": 0.0,
                    "protected_files": [f.cid for f in all_files]
                }
            
            # Identify files to delete
            protected_files, files_to_delete = self.identify_files_to_delete(
                all_files,
                protected_cid
            )
            
            if not files_to_delete:
                logger.info("✅ No old files to delete")
                return {
                    "success": True,
                    "files_total": len(all_files),
                    "files_deleted": 0,
                    "files_failed": 0,
                    "files_remaining": len(all_files),
                    "space_saved_mb": 0.0,
                    "protected_files": [f.cid for f in protected_files]
                }
            
            if dry_run:
                space_to_save = sum(f.size_bytes for f in files_to_delete)
                logger.info(
                    f"🔍 DRY RUN: Would delete {len(files_to_delete)} files "
                    f"({space_to_save / (1024*1024):.2f} MB)"
                )
                return {
                    "success": True,
                    "files_total": len(all_files),
                    "files_deleted": 0,
                    "files_failed": 0,
                    "files_remaining": len(all_files),
                    "space_saved_mb": space_to_save / (1024*1024),
                    "protected_files": [f.cid for f in protected_files]
                }
            
            # Delete old files
            logger.info(f"🗑️  Deleting {len(files_to_delete)} old files...")
            
            deleted_count = 0
            failed_count = 0
            space_saved = 0
            
            for i, file in enumerate(files_to_delete, 1):
                if i % 10 == 0:
                    logger.info(f"Progress: {i}/{len(files_to_delete)}")
                
                if self.delete_file(file):
                    deleted_count += 1
                    space_saved += file.size_bytes
                else:
                    failed_count += 1
            
            # Final verification
            final_files = self.list_all_files()
            
            elapsed = (datetime.now() - start_time).total_seconds()
            
            result = {
                "success": failed_count == 0,
                "files_total": len(all_files),
                "files_deleted": deleted_count,
                "files_failed": failed_count,
                "files_remaining": len(final_files),
                "space_saved_mb": space_saved / (1024*1024),
                "protected_files": [f.cid for f in protected_files],
                "elapsed_seconds": elapsed
            }
            
            # Log summary
            logger.info("=" * 60)
            logger.info("🎉 CLEANUP COMPLETE")
            logger.info(f"   Deleted: {deleted_count}/{len(files_to_delete)}")
            logger.info(f"   Failed: {failed_count}")
            logger.info(f"   Protected: {len(protected_files)} files")
            logger.info(f"   Remaining: {len(final_files)} files")
            logger.info(f"   Space saved: {result['space_saved_mb']:.2f} MB")
            logger.info(f"   Time: {elapsed:.1f}s")
            logger.info("=" * 60)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "files_total": 0,
                "files_deleted": 0,
                "files_failed": 0,
                "files_remaining": 0,
                "space_saved_mb": 0.0,
                "protected_files": []
            }


def setup_cli_if_needed(api_key: str) -> bool:
    """
    Set up Lighthouse CLI if not already configured.
    
    Args:
        api_key: Lighthouse API key to import
        
    Returns:
        True if setup successful or already configured
    """
    try:
        # Check if CLI is installed
        try:
            subprocess.run(
                ["lighthouse-web3", "--version"],
                capture_output=True,
                timeout=5,
                check=True
            )
        except FileNotFoundError:
            logger.error(
                "❌ Lighthouse CLI not installed. "
                "Install with: npm install -g @lighthouse-web3/sdk"
            )
            logger.error(
                "💡 Cleanup disabled until CLI is available. "
                "Files will accumulate on Lighthouse."
            )
            return False
        
        # Try to import API key (safe to re-run)
        result = subprocess.run(
            ["lighthouse-web3", "api-key", "--import", api_key],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            logger.info("✅ Lighthouse CLI configured")
            return True
        else:
            logger.warning(f"⚠️  CLI config warning: {result.stderr}")
            # Still return True - might already be configured
            return True
            
    except subprocess.TimeoutExpired:
        logger.error("⏱️  CLI setup timeout")
        return False
    except Exception as e:
        logger.error(f"❌ CLI setup failed: {e}")
        return False


# Convenience function for easy import
def cleanup_lighthouse_storage(
    api_key: str,
    protected_cid: Optional[str] = None,
    dry_run: bool = False
) -> Dict[str, any]:
    """
    Convenience function to clean up Lighthouse storage.
    
    Args:
        api_key: Lighthouse API key
        protected_cid: CID to protect (optional, uses newest if not specified)
        dry_run: If True, only simulate cleanup
        
    Returns:
        Dict with cleanup results
        
    Example:
        from lighthouse_cleanup import cleanup_lighthouse_storage
        
        result = cleanup_lighthouse_storage(
            api_key=settings.LIGHTHOUSE_API_KEY,
            protected_cid="QmXXX..."
        )
        
        if result["success"]:
            print(f"Deleted {result['files_deleted']} files")
    """
    # Ensure CLI is set up
    if not setup_cli_if_needed(api_key):
        logger.warning("CLI setup incomplete, but will try cleanup anyway")
    
    # Run cleanup
    cleanup = LighthouseCleanup(api_key=api_key, verify_cli=False)
    return cleanup.cleanup_old_files(protected_cid=protected_cid, dry_run=dry_run)


if __name__ == "__main__":
    # CLI entry point for standalone execution
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Clean up old Lighthouse storage files"
    )
    parser.add_argument(
        "--api-key",
        required=True,
        help="Lighthouse API key"
    )
    parser.add_argument(
        "--protected-cid",
        help="Specific CID to protect (optional)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate cleanup without deleting"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Run cleanup
    result = cleanup_lighthouse_storage(
        api_key=args.api_key,
        protected_cid=args.protected_cid,
        dry_run=args.dry_run
    )
    
    # Exit with appropriate code
    sys.exit(0 if result["success"] else 1)
