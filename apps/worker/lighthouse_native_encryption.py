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
        response_data = response.json()
        
        # Extract message from response - API returns {"message": "..."}
        message_text = response_data.get("message") if isinstance(response_data, dict) else response_data
        
        # Step 2: Sign message with private key
        message_hash = encode_defunct(text=message_text)
        signed = self.account.sign_message(message_hash)
        
        # Return signature with 0x prefix
        signature_hex = signed.signature.hex()
        if not signature_hex.startswith("0x"):
            signature_hex = "0x" + signature_hex
        return signature_hex
    
    def upload_encrypted(self, file_path: str, tag: str = "") -> Dict[str, Any]:
        """
        Upload file with Lighthouse native encryption.
        
        CRITICAL FIX: The SDK's uploadEncrypted() is BROKEN internally.
        SOLUTION: Use textUploadEncrypted() method for text content encryption.
        
        This reads the file as text, encrypts it with Kavach SDK, and uploads
        to Lighthouse with distributed key shards for token-gated access.
        
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
        # COMPREHENSIVE DEBUGGING: All tips from user's debugging guide
        # Testing: file size, encoding, SDK version, Node crypto, parameters, etc.
        script_content = """
const lighthouse = require('@lighthouse-web3/sdk');
const fs = require('fs');
const path = require('path');

async function uploadWithEncryption() {
    const filePath = process.argv[2];
    const apiKey = process.argv[3];
    const publicKey = process.argv[4];
    const signedMessage = process.argv[5];
    
    try {
        console.error(`\\n========== COMPREHENSIVE LIGHTHOUSE DEBUGGING ==========`);
        
        // ===== DEBUG TIP #1: File validation (size, encoding) =====
        console.error(`\\n[TIP #1] FILE VALIDATION:`);
        if (!fs.existsSync(filePath)) {
            throw new Error(`File does not exist: ${filePath}`);
        }
        
        const stats = fs.statSync(filePath);
        console.error(`  ✓ File exists: ${filePath}`);
        console.error(`  ✓ File size: ${stats.size} bytes (${(stats.size/1024).toFixed(2)} KB)`);
        
        // Check if file is too large (>10MB as mentioned in tips)
        if (stats.size > 10 * 1024 * 1024) {
            throw new Error(`File too large: ${stats.size} bytes (max 10MB for encryption)`);
        }
        
        // Read and validate UTF-8 content
        let fileContent;
        try {
            fileContent = fs.readFileSync(filePath, 'utf8');
            console.error(`  ✓ File encoding: UTF-8 valid`);
            console.error(`  ✓ Content length: ${fileContent.length} characters`);
            console.error(`  ✓ First 100 chars: ${fileContent.substring(0, 100).replace(/\\n/g, '\\\\n')}`);
            
            // Check for null bytes or invalid UTF-8
            if (fileContent.includes('\\0')) {
                throw new Error(`File contains null bytes (invalid for text upload)`);
            }
        } catch (encError) {
            throw new Error(`File encoding error: ${encError.message}. Try: iconv -f utf-8 -t utf-8 -c ${filePath} -o ${filePath}`);
        }
        
        // ===== DEBUG TIP #2: SDK version check =====
        console.error(`\\n[TIP #2] SDK VERSION CHECK:`);
        const packageJson = require('@lighthouse-web3/sdk/package.json');
        console.error(`  ✓ SDK version: ${packageJson.version}`);
        console.error(`  ✓ SDK name: ${packageJson.name}`);
        
        // Warn if old version (0.2.8-0.3.0 had known bugs)
        const version = packageJson.version;
        if (version.startsWith('0.2.') || version.startsWith('0.3.')) {
            console.error(`  ⚠️  WARNING: SDK version ${version} has known encryption bugs. Recommend 0.4.0+`);
        }
        
        // ===== DEBUG TIP #3: Node environment check =====
        console.error(`\\n[TIP #3] NODE ENVIRONMENT:`);
        console.error(`  ✓ Node version: ${process.version}`);
        console.error(`  ✓ Platform: ${process.platform}`);
        
        // Check crypto availability (required for encryption)
        const crypto = require('crypto');
        console.error(`  ✓ Node crypto available: ${typeof crypto.createHash === 'function'}`);
        
        if (parseInt(process.version.slice(1)) < 18) {
            console.error(`  ⚠️  WARNING: Node ${process.version} < 18. Encryption may fail!`);
        }
        
        // ===== DEBUG TIP #4: Parameter validation =====
        console.error(`\\n[TIP #4] PARAMETER VALIDATION:`);
        console.error(`  ✓ apiKey format: ${apiKey ? apiKey.substring(0, 10) + '...' : '❌ MISSING'}`);
        console.error(`  ✓ apiKey length: ${apiKey ? apiKey.length : 0} chars`);
        console.error(`  ✓ publicKey (wallet): ${publicKey}`);
        console.error(`  ✓ publicKey has 0x: ${publicKey.startsWith('0x')}`);
        console.error(`  ✓ publicKey length: ${publicKey.length} (should be 42)`);
        console.error(`  ✓ signedMessage format: ${signedMessage ? signedMessage.substring(0, 20) + '...' : '❌ MISSING'}`);
        console.error(`  ✓ signedMessage length: ${signedMessage ? signedMessage.length : 0} (should be 132)`);
        
        if (!apiKey || apiKey.length < 10) {
            throw new Error(`Invalid API key: too short or missing`);
        }
        
        if (!publicKey.startsWith('0x') || publicKey.length !== 42) {
            throw new Error(`Invalid publicKey format: ${publicKey} (need 0x prefix + 40 hex chars)`);
        }
        
        if (!signedMessage || signedMessage.length !== 132) {
            throw new Error(`Invalid signedMessage: length ${signedMessage ? signedMessage.length : 0} (expected 132)`);
        }
        
        // ===== DEBUG TIP #5: SDK method availability =====
        console.error(`\\n[TIP #5] SDK METHOD CHECK:`);
        console.error(`  ✓ lighthouse object: ${typeof lighthouse}`);
        console.error(`  ✓ textUploadEncrypted: ${typeof lighthouse.textUploadEncrypted}`);
        console.error(`  ✓ uploadEncrypted: ${typeof lighthouse.uploadEncrypted}`);
        console.error(`  ✓ upload (non-encrypted): ${typeof lighthouse.upload}`);
        
        if (typeof lighthouse.textUploadEncrypted !== 'function') {
            throw new Error(`textUploadEncrypted not available in SDK ${version}`);
        }
        
        // ===== DEBUG TIP #6: Test smaller file first (if > 100KB) =====
        console.error(`\\n[TIP #6] FILE SIZE STRATEGY:`);
        if (stats.size > 100 * 1024) {
            console.error(`  ℹ️  File is ${(stats.size/1024).toFixed(2)} KB. Testing with full content.`);
            console.error(`  ℹ️  If this fails, try: head -n 50 ${filePath} > test.jsonl`);
        } else {
            console.error(`  ✓ File size OK: ${(stats.size/1024).toFixed(2)} KB (< 100KB)`);
        }
        
        // ===== TEST: TRY NON-ENCRYPTED UPLOAD FIRST =====
        console.error(`\\n[TEST] Attempting non-encrypted upload first to verify connectivity...`);
        
        const lighthouse = require('@lighthouse-web3/sdk');
        
        try {
            const testUpload = await lighthouse.uploadText(
                'Test upload to verify connectivity',
                apiKey,
                'test-file.txt'
            );
            console.error(`  ✓ NON-ENCRYPTED upload SUCCESS`);
            console.error(`  → CID: ${testUpload.data.Hash}`);
            console.error(`  → This proves: API key works, network works, Lighthouse is reachable`);
        } catch (testError) {
            console.error(`  ❌ NON-ENCRYPTED upload FAILED`);
            console.error(`  → This means basic connectivity issue, not encryption`);
            console.error(`  → Error: ${testError.message}`);
            throw new Error(`Basic upload failed: ${testError.message}`);
        }
        
        // ===== NOW TRY ENCRYPTED UPLOAD =====
        console.error(`\\n[UPLOAD] Now trying ENCRYPTED upload...`);
        console.error(`  → text: ${fileContent.length} chars`);
        console.error(`  → apiKey: ${apiKey.substring(0, 10)}...`);
        console.error(`  → publicKey: ${publicKey}`);
        console.error(`  → signedMessage: ${signedMessage.substring(0, 20)}...`);
        
        let response;
        const startTime = Date.now();
        
        try {
            response = await lighthouse.textUploadEncrypted(
                fileContent,
                apiKey,
                publicKey,
                signedMessage
            );
            const elapsed = Date.now() - startTime;
            console.error(`\\n[SUCCESS] textUploadEncrypted() completed in ${elapsed}ms ✓`);
        } catch (sdkError) {
            const elapsed = Date.now() - startTime;
            console.error(`\\n[ERROR] textUploadEncrypted() failed after ${elapsed}ms`);
            console.error(`  ❌ Error type: ${sdkError.constructor.name}`);
            console.error(`  ❌ Error message: ${sdkError.message}`);
            console.error(`  ❌ Error stack:\\n${sdkError.stack}`);
            
            if (sdkError.response) {
                console.error(`  ❌ HTTP response: ${JSON.stringify(sdkError.response.data || sdkError.response)}`);
            }
            if (sdkError.code) {
                console.error(`  ❌ Error code: ${sdkError.code}`);
            }
            
            // Specific guidance based on error
            if (sdkError.message.includes('saveShards')) {
                console.error(`\\n  💡 HINT: saveShards() failed - likely authentication issue`);
                console.error(`     Check: publicKey and signedMessage are correct`);
                console.error(`     Try: Regenerate signed message`);
            } else if (sdkError.message.includes('encryptFile')) {
                console.error(`\\n  💡 HINT: encryptFile() failed - likely file content issue`);
                console.error(`     Try: iconv -f utf-8 -t utf-8 -c ${filePath}`);
            }
            
            throw sdkError;
        }
        
        // ===== RESPONSE VALIDATION =====
        console.error(`\\n[VALIDATION] Checking response structure...`);
        console.error(`  ✓ Response type: ${typeof response}`);
        
        if (!response) {
            throw new Error(`Response is null/undefined`);
        }
        
        if (!response.data) {
            throw new Error(`Response.data missing: ${JSON.stringify(response)}`);
        }
        console.error(`  ✓ response.data exists`);
        
        if (!response.data.Hash && !response.data[0]?.Hash) {
            throw new Error(`No CID in response: ${JSON.stringify(response.data)}`);
        }
        
        const cid = response.data.Hash || response.data[0].Hash;
        const name = response.data.Name || response.data[0]?.Name || path.basename(filePath);
        const size = response.data.Size || response.data[0]?.Size || stats.size.toString();
        
        console.error(`  ✓ CID: ${cid}`);
        console.error(`  ✓ Name: ${name}`);
        console.error(`  ✓ Size: ${size}`);
        
        console.error(`\\n========== UPLOAD SUCCESSFUL ==========\\n`);
        
        // Return result
        console.log(JSON.stringify({
            cid: cid,
            name: name,
            size: size
        }));
        process.exit(0);
        
    } catch (error) {
        console.error(`\\n========== UPLOAD FAILED ==========`);
        console.error(`❌ Fatal error: ${error.message}`);
        console.error(`❌ Stack:\\n${error.stack}`);
        
        console.error(JSON.stringify({
            error: error.message || 'Unknown error',
            stack: error.stack,
            details: error.response ? JSON.stringify(error.response.data) : null
        }));
        process.exit(1);
    }
}

uploadWithEncryption();
"""
        
        # Write script to temp file and execute
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(script_content)
            script_path = f.name
        
        try:
            # CRITICAL: Get signed message BEFORE uploading
            # This authenticates with Lighthouse and enables uploadEncrypted()
            print(f"[Lighthouse] Getting signed auth message for uploadEncrypted()...")
            signed_message = self._get_signed_message()
            
            # Convert to absolute path - Lighthouse SDK requires absolute paths
            abs_file_path = str(Path(file_path).resolve())
            
            # Run Node.js script with uploadEncrypted() and authentication
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
            
            # Debug: ALWAYS print ALL stderr to see comprehensive debugging
            if result.stderr:
                print(f"[Lighthouse Debug Output]:")
                print(result.stderr)
                print(f"[End Debug Output]")
            
            if result.returncode != 0:
                # Try to extract JSON error from stderr
                try:
                    stderr_lines = result.stderr.strip().split('\n')
                    error_json = json.loads(stderr_lines[-1])
                    raise Exception(f"Lighthouse SDK error: {error_json.get('error', 'Unknown error')}")
                except (json.JSONDecodeError, IndexError):
                    error_msg = result.stderr or result.stdout
                    raise Exception(f"Upload failed: {error_msg}")
            
            # Parse upload result (regular upload returns {cid, name, size})
            try:
                upload_result = json.loads(result.stdout)
            except json.JSONDecodeError as e:
                raise Exception(f"Failed to parse upload result: {result.stdout}")
            
            if 'error' in upload_result:
                raise Exception(f"Upload error: {upload_result['error']}")
            
            # Return standardized format
            return {
                "cid": upload_result["cid"],
                "name": upload_result["name"],
                "size": upload_result["size"]
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
        # Use Lighthouse SDK for access control
        script_content = """
const lighthouse = require('@lighthouse-web3/sdk');

async function applyAccessControl() {
    const publicKey = process.argv[2];
    const cid = process.argv[3];
    const signedMessage = process.argv[4];
    const conditions = JSON.parse(process.argv[5]);
    const aggregator = process.argv[6];
    
    try {
        console.error(`DEBUG: Applying access control`);
        console.error(`DEBUG: CID=${cid}`);
        console.error(`DEBUG: publicKey=${publicKey}`);
        console.error(`DEBUG: Conditions: ${JSON.stringify(conditions, null, 2)}`);
        console.error(`DEBUG: Aggregator: ${aggregator}`);
        
        // Use Lighthouse SDK
        const response = await lighthouse.applyAccessCondition(
            publicKey,
            cid,
            signedMessage,
            conditions
        );
        
        console.error(`DEBUG: SDK response: ${JSON.stringify(response)}`);
        
        if (response && response.data) {
            console.log(JSON.stringify(response.data));
        } else {
            console.log(JSON.stringify({status: 'success', cid: cid}));
        }
        process.exit(0);
    } catch (error) {
        console.error(JSON.stringify({
            error: error.message || 'Unknown error',
            stack: error.stack,
            details: error.response ? error.response.data : null
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
