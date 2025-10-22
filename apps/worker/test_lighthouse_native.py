#!/usr/bin/env python3
"""
Test script for Lighthouse Native Encryption module.

This script tests the integration without actually uploading files.
It verifies:
1. Module imports correctly
2. Wallet address derivation works
3. Auth message signing works
4. Node.js subprocess infrastructure is available
"""

import sys
import os
import tempfile
from pathlib import Path

# Add worker directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all required modules can be imported."""
    print("=" * 60)
    print("TEST 1: Module Imports")
    print("=" * 60)
    
    try:
        from lighthouse_native_encryption import LighthouseNativeEncryption
        print("✓ lighthouse_native_encryption imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import lighthouse_native_encryption: {e}")
        return False
    
    try:
        from eth_account import Account
        print("✓ eth_account imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import eth_account: {e}")
        print("  Run: pip install eth-account")
        return False
    
    try:
        import requests
        print("✓ requests imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import requests: {e}")
        return False
    
    return True

def test_wallet_derivation():
    """Test wallet address derivation from private key."""
    print("\n" + "=" * 60)
    print("TEST 2: Wallet Address Derivation")
    print("=" * 60)
    
    # Use a test private key (DO NOT use in production)
    test_private_key = "0x0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    
    try:
        from lighthouse_native_encryption import LighthouseNativeEncryption
        
        lighthouse = LighthouseNativeEncryption(
            api_key="test_api_key",
            private_key=test_private_key
        )
        
        print(f"✓ Wallet address derived: {lighthouse.wallet_address}")
        
        # Verify format
        if lighthouse.wallet_address.startswith("0x") and len(lighthouse.wallet_address) == 42:
            print("✓ Wallet address format valid (0x + 40 hex chars)")
            return True
        else:
            print("✗ Wallet address format invalid")
            return False
            
    except Exception as e:
        print(f"✗ Wallet derivation failed: {e}")
        return False

def test_nodejs_availability():
    """Test that Node.js and required packages are available."""
    print("\n" + "=" * 60)
    print("TEST 3: Node.js & Dependencies")
    print("=" * 60)
    
    import subprocess
    
    # Check Node.js
    try:
        result = subprocess.run(
            ["node", "-v"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            print(f"✓ Node.js available: {result.stdout.strip()}")
        else:
            print("✗ Node.js not found")
            return False
    except Exception as e:
        print(f"✗ Node.js check failed: {e}")
        return False
    
    # Check if @lighthouse-web3/sdk is installed
    try:
        # Create a test script that tries to require the SDK
        test_script = """
const lighthouse = require('@lighthouse-web3/sdk');
console.log('SDK Version:', lighthouse ? 'installed' : 'not found');
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(test_script)
            script_path = f.name
        
        try:
            result = subprocess.run(
                ["node", script_path],
                capture_output=True,
                text=True,
                timeout=5,
                cwd=os.path.dirname(__file__)  # Run in worker directory where node_modules is
            )
            
            if result.returncode == 0 and "installed" in result.stdout:
                print(f"✓ @lighthouse-web3/sdk installed")
                return True
            else:
                print(f"✗ @lighthouse-web3/sdk not found")
                print(f"  Error: {result.stderr}")
                print(f"  Tip: Run 'npm install' in apps/worker directory")
                return False
        finally:
            Path(script_path).unlink(missing_ok=True)
            
    except Exception as e:
        print(f"✗ SDK check failed: {e}")
        return False

def test_auth_signing():
    """Test auth message signing (without actual API call)."""
    print("\n" + "=" * 60)
    print("TEST 4: Auth Message Signing")
    print("=" * 60)
    
    test_private_key = "0x0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    
    try:
        from eth_account import Account
        from eth_account.messages import encode_defunct
        
        account = Account.from_key(test_private_key)
        test_message = "Test message for signing"
        
        message_hash = encode_defunct(text=test_message)
        signed = account.sign_message(message_hash)
        
        signature_hex = signed.signature.hex()
        if not signature_hex.startswith("0x"):
            signature_hex = "0x" + signature_hex
        
        print(f"✓ Message signed successfully")
        print(f"  Signature: {signature_hex[:20]}...{signature_hex[-20:]}")
        
        if signature_hex.startswith("0x") and len(signature_hex) == 132:
            print("✓ Signature format valid (0x + 130 hex chars)")
            return True
        else:
            print("✗ Signature format invalid")
            return False
            
    except Exception as e:
        print(f"✗ Auth signing failed: {e}")
        return False

def main():
    """Run all tests."""
    print("\n" + "╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "LIGHTHOUSE NATIVE ENCRYPTION TESTS" + " " * 14 + "║")
    print("╚" + "=" * 58 + "╝\n")
    
    results = []
    
    # Run tests
    results.append(("Module Imports", test_imports()))
    results.append(("Wallet Derivation", test_wallet_derivation()))
    results.append(("Node.js & Dependencies", test_nodejs_availability()))
    results.append(("Auth Message Signing", test_auth_signing()))
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name}")
    
    print("=" * 60)
    print(f"Total: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("\n🎉 All tests passed! Ready for integration.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Fix issues before proceeding.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
