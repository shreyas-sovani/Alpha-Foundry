"""
Lighthouse Native Encryption with ERC20 Token-Gating

This module implements Lighthouse's native encryption system with automated
ERC20 token-gating for access control. It replaces the custom AES-256-GCM
encryption with Lighthouse's Kavach encryption SDK, enabling proper token-gated
decryption in the frontend.

Key Features:
- uploadEncrypted() via Node.js subprocess
- applyAccessCondition() with ERC20 balance checks
- Proper auth message signing with eth-account
- Seamless integration with existing worker pipeline

Usage:
    lighthouse = LighthouseNativeEncryption(
        api_key="your_api_key",
        private_key="0x..."
    )
    
    result = lighthouse.encrypt_and_upload_with_gating(
        file_path="data.jsonl",
        tag="dexarb_ethereum",
        datacoin_address="0x8d302FfB73134235EBaD1B9Cd9C202d14f906FeC",
        chain="Sepolia",
        min_balance_dadc=1.0
    )
"""

import json
import subprocess
import tempfile
import requests
from pathlib import Path
from typing import Dict, Any, Optional
from eth_account import Account
from eth_account.messages import encode_defunct


class LighthouseNativeEncryption:
    """
    Lighthouse native encryption with ERC20 token-gating.
    
    Provides methods to:
    1. Upload files with Lighthouse's native Kavach encryption
    2. Apply ERC20 token-gating access control conditions
    3. Complete end-to-end encrypted upload with gating
    
    Attributes:
        api_key: Lighthouse API key
        private_key: Ethereum private key for signing
        wallet_address: Derived Ethereum address
    """
    
    def __init__(self, api_key: str, private_key: str):
        """
        Initialize Lighthouse native encryption handler.
        
        Args:
            api_key: Lighthouse API key (e.g., "7e711ba4.5db09f1a785145159ab740254e63f070")
            private_key: Ethereum private key with 0x prefix
        
        Raises:
            ValueError: If private_key is invalid format
        """
        self.api_key = api_key
        self.private_key = private_key
        
        # Derive wallet address from private key
        try:
            self.account = Account.from_key(private_key)
            self.wallet_address = self.account.address
        except Exception as e:
            raise ValueError(f"Invalid private key: {e}")
        
        # API endpoints
        self.lighthouse_api = "https://api.lighthouse.storage"
        self.lighthouse_node = "https://upload.lighthouse.storage"
        self.lighthouse_encryption = "https://encryption.lighthouse.storage"
    
    def _get_signed_message(self) -> str:
        """
        Get authentication message from Lighthouse and sign it.
        
        This implements the Lighthouse auth flow:
        1. Request message from API with wallet address
        2. Sign message with private key
        3. Return signed message for API authentication
        
        Returns:
            Signed message as hex string (0x...)
        
        Raises:
            requests.HTTPError: If API request fails
            Exception: If signing fails
        """
        # Step 1: Get message to sign from Lighthouse
        response = requests.get(
            f"{self.lighthouse_api}/api/auth/get_message",
            params={"publicKey": self.wallet_address},
            timeout=30
        )
        response.raise_for_status()
        message = response.json()
        
        # Step 2: Sign message with private key
        message_hash = encode_defunct(text=message)
        signed = self.account.sign_message(message_hash)
        
        # Return signature with 0x prefix
        signature_hex = signed.signature.hex()
        if not signature_hex.startswith("0x"):
            signature_hex = "0x" + signature_hex
        return signature_hex
    
    def upload_encrypted(self, file_path: str, tag: str = "") -> Dict[str, Any]:
        """
        Upload file with Lighthouse native encryption.
        
        Uses Node.js @lighthouse-web3/sdk via subprocess to call uploadEncrypted().
        This properly encrypts the file with Kavach SDK and stores encryption key
        shards on Lighthouse nodes, enabling token-gated decryption.
        
        Args:
            file_path: Absolute path to file to upload
            tag: Optional tag for the upload (not used in native encryption)
        
        Returns:
            {
                "cid": "QmXXX...",
                "name": "file.jsonl",
                "size": "12345"
            }
        
        Raises:
            Exception: If upload fails or Node.js subprocess errors
        """
        # Create temporary Node.js script for uploadEncrypted
        script_content = """
const lighthouse = require('@lighthouse-web3/sdk');

async function uploadEncrypted() {
    const filePath = process.argv[2];
    const apiKey = process.argv[3];
    const publicKey = process.argv[4];
    const signedMessage = process.argv[5];
    
    try {
        const response = await lighthouse.uploadEncrypted(
            filePath,
            apiKey,
            publicKey,
            signedMessage
        );
        
        if (!response || !response.data || response.data.length === 0) {
            throw new Error('Upload returned no data');
        }
        
        console.log(JSON.stringify(response.data[0]));
        process.exit(0);
    } catch (error) {
        console.error(JSON.stringify({
            error: error.message || 'Unknown error',
            stack: error.stack
        }));
        process.exit(1);
    }
}

uploadEncrypted();
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(script_content)
            script_path = f.name
        
        try:
            # Get signed authentication message
            print(f"[Lighthouse] Getting signed auth message...")
            signed_message = self._get_signed_message()
            
            # Convert to absolute path - Lighthouse SDK requires absolute paths
            abs_file_path = str(Path(file_path).resolve())
            
            # Run Node.js script with uploadEncrypted
            # Use current directory as working directory so node can find node_modules
            print(f"[Lighthouse] Uploading {abs_file_path} with native encryption...")
            result = subprocess.run(
                [
                    'node',
                    script_path,
                    abs_file_path,
                    self.api_key,
                    self.wallet_address,
                    signed_message
                ],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes timeout
                # Don't set cwd - use global NODE_PATH instead
            )
            
            if result.returncode != 0:
                error_msg = result.stderr or result.stdout
                raise Exception(f"Upload failed: {error_msg}")
            
            # Parse upload result
            try:
                upload_result = json.loads(result.stdout)
            except json.JSONDecodeError as e:
                raise Exception(f"Failed to parse upload result: {result.stdout}")
            
            if 'error' in upload_result:
                raise Exception(f"Upload error: {upload_result['error']}")
            
            # Return standardized format
            return {
                "cid": upload_result["Hash"],
                "name": upload_result["Name"],
                "size": upload_result["Size"]
            }
            
        finally:
            # Cleanup temp script
            Path(script_path).unlink(missing_ok=True)
    
    def apply_access_control(
        self,
        cid: str,
        contract_address: str,
        chain: str,
        min_balance_wei: int
    ) -> Dict[str, Any]:
        """
        Apply ERC20 token-gating to uploaded CID.
        
        Creates an access control condition that checks if the user's wallet
        has at least min_balance_wei tokens of the specified ERC20 contract.
        
        Args:
            cid: Lighthouse CID to gate (e.g., "QmXXX...")
            contract_address: ERC20 token contract (e.g., DataCoin: "0x8d302FfB...")
            chain: Chain name (MUST match Lighthouse chain names, e.g., "Sepolia")
            min_balance_wei: Minimum balance in wei (1 DADC = 1e18 wei)
        
        Returns:
            {
                "status": "Success",
                "cid": "QmXXX..."
            }
        
        Raises:
            Exception: If access control application fails
        """
        # Create temporary Node.js script for applyAccessCondition
        script_content = """
const lighthouse = require('@lighthouse-web3/sdk');

async function applyAccessControl() {
    const publicKey = process.argv[2];
    const cid = process.argv[3];
    const signedMessage = process.argv[4];
    const conditions = JSON.parse(process.argv[5]);
    const aggregator = process.argv[6];
    
    try {
        const response = await lighthouse.applyAccessCondition(
            publicKey,
            cid,
            signedMessage,
            conditions,
            aggregator
        );
        
        if (!response || !response.data) {
            throw new Error('Access control returned no data');
        }
        
        console.log(JSON.stringify(response.data));
        process.exit(0);
    } catch (error) {
        console.error(JSON.stringify({
            error: error.message || 'Unknown error',
            stack: error.stack
        }));
        process.exit(1);
    }
}

applyAccessControl();
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(script_content)
            script_path = f.name
        
        try:
            # Get signed authentication message
            print(f"[Lighthouse] Getting signed auth message for access control...")
            signed_message = self._get_signed_message()
            
            # Build access control conditions
            # See: https://github.com/lighthouse-web3/lighthouse-package/tree/main/src/Lighthouse/tests/encryption.test.ts#L127-L145
            conditions = [{
                "id": 1,
                "chain": chain,  # MUST match Lighthouse chain names exactly
                "method": "balanceOf",
                "standardContractType": "ERC20",
                "contractAddress": contract_address,
                "returnValueTest": {
                    "comparator": ">=",
                    "value": str(min_balance_wei)
                },
                "parameters": [":userAddress"]
            }]
            
            aggregator = "([1])"
            
            # Run Node.js script with applyAccessCondition
            print(f"[Lighthouse] Applying ERC20 access control to {cid}...")
            result = subprocess.run(
                [
                    'node',
                    script_path,
                    self.wallet_address,
                    cid,
                    signed_message,
                    json.dumps(conditions),
                    aggregator
                ],
                capture_output=True,
                text=True,
                timeout=60,  # 1 minute timeout
                # Don't set cwd - use global NODE_PATH instead
            )
            
            if result.returncode != 0:
                error_msg = result.stderr or result.stdout
                raise Exception(f"Access control failed: {error_msg}")
            
            # Parse access control result
            try:
                access_result = json.loads(result.stdout)
            except json.JSONDecodeError as e:
                raise Exception(f"Failed to parse access control result: {result.stdout}")
            
            if 'error' in access_result:
                raise Exception(f"Access control error: {access_result['error']}")
            
            return access_result
            
        finally:
            # Cleanup temp script
            Path(script_path).unlink(missing_ok=True)
    
    def encrypt_and_upload_with_gating(
        self,
        file_path: str,
        tag: str,
        datacoin_address: str,
        chain: str = "Sepolia",
        min_balance_dadc: float = 1.0
    ) -> Dict[str, Any]:
        """
        Complete flow: Upload with Lighthouse native encryption + Apply ERC20 token-gating.
        
        This is the main method to use for encrypted uploads with token-gating.
        It orchestrates:
        1. Upload file with native encryption (uploadEncrypted)
        2. Apply ERC20 access control condition (applyAccessCondition)
        3. Return complete result with CID and access control info
        
        Args:
            file_path: Path to file to upload (absolute path recommended)
            tag: Upload tag (e.g., "dexarb_ethereum")
            datacoin_address: DataCoin ERC20 contract address
            chain: Blockchain name (default: "Sepolia")
            min_balance_dadc: Minimum token balance in DADC (not wei)
        
        Returns:
            {
                "cid": "QmXXX...",
                "name": "file.jsonl",
                "size": "12345",
                "encryption": "Lighthouse Native",
                "access_control": {
                    "status": "Success",
                    "contract": "0x8d302FfB73134235EBaD1B9Cd9C202d14f906FeC",
                    "chain": "Sepolia",
                    "min_balance": "1.0 DADC"
                }
            }
        
        Raises:
            Exception: If upload or access control fails
        """
        # Step 1: Upload with native encryption
        print(f"[Lighthouse Native] Step 1/2: Uploading {file_path} with native encryption...")
        upload_result = self.upload_encrypted(file_path, tag)
        cid = upload_result["cid"]
        print(f"[Lighthouse Native] ✓ Uploaded: {cid}")
        
        # Step 2: Apply ERC20 token-gating
        print(f"[Lighthouse Native] Step 2/2: Applying ERC20 token-gating...")
        min_balance_wei = int(min_balance_dadc * 1e18)  # Convert DADC to wei
        
        access_result = self.apply_access_control(
            cid=cid,
            contract_address=datacoin_address,
            chain=chain,
            min_balance_wei=min_balance_wei
        )
        print(f"[Lighthouse Native] ✓ Access control applied: {access_result['status']}")
        
        # Return complete result
        return {
            "cid": cid,
            "name": upload_result["name"],
            "size": upload_result["size"],
            "encryption": "Lighthouse Native",
            "access_control": {
                "status": access_result["status"],
                "contract": datacoin_address,
                "chain": chain,
                "min_balance": f"{min_balance_dadc} DADC"
            }
        }


# Example usage
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 4:
        print("Usage: python lighthouse_native_encryption.py <file_path> <api_key> <private_key>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    api_key = sys.argv[2]
    private_key = sys.argv[3]
    
    # Initialize
    lighthouse = LighthouseNativeEncryption(api_key, private_key)
    
    # Upload with token-gating
    result = lighthouse.encrypt_and_upload_with_gating(
        file_path=file_path,
        tag="test_upload",
        datacoin_address="0x8d302FfB73134235EBaD1B9Cd9C202d14f906FeC",
        chain="Sepolia",
        min_balance_dadc=1.0
    )
    
    print("\n=== Upload Result ===")
    print(json.dumps(result, indent=2))
