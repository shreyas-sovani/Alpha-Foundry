#!/usr/bin/env python3
"""
Verification script for Lighthouse file protection.

Tests that the permanent CIDs are properly configured and protected.
"""

import sys
from pathlib import Path

# Add worker directory to path
worker_dir = Path(__file__).parent.parent / "apps" / "worker"
sys.path.insert(0, str(worker_dir))

from lighthouse_cleanup import LighthouseCleanup

def test_permanent_cids():
    """Test that permanent CIDs are properly configured."""
    
    print("=" * 70)
    print("LIGHTHOUSE PROTECTION VERIFICATION")
    print("=" * 70)
    print()
    
    # Expected permanent CIDs
    expected_cids = {
        "bafybeih5j5recyxiwscbtjl7o5rmv22rijmeq552iovrguas45s4766yw4",
        "bafkreie73wguaf7yucgzcudbkivtgtxzvyv2efjg24s76j67lu7cbt7vcy"
    }
    
    print("✓ Expected Permanent CIDs:")
    for cid in expected_cids:
        print(f"  - {cid}")
    print()
    
    # Check class configuration
    print("✓ Checking LighthouseCleanup configuration...")
    configured_cids = LighthouseCleanup.PERMANENT_PROTECTED_CIDS
    
    print(f"  Found {len(configured_cids)} permanent CIDs in configuration")
    print()
    
    # Verify all expected CIDs are present
    missing = expected_cids - configured_cids
    extra = configured_cids - expected_cids
    
    if not missing and not extra:
        print("✅ SUCCESS: All permanent CIDs are correctly configured!")
        print()
        print("Protected CIDs:")
        for cid in configured_cids:
            print(f"  🛡️  {cid}")
        print()
        return True
    
    # Report issues
    if missing:
        print("❌ ERROR: Missing CIDs from configuration:")
        for cid in missing:
            print(f"  ✗ {cid}")
        print()
    
    if extra:
        print("⚠️  WARNING: Extra CIDs in configuration (not expected):")
        for cid in extra:
            print(f"  + {cid}")
        print()
    
    return False


def test_initialization():
    """Test cleanup initialization with additional CIDs."""
    
    print("=" * 70)
    print("TESTING INITIALIZATION")
    print("=" * 70)
    print()
    
    try:
        # Test with no additional CIDs
        print("Test 1: Initialize with permanent CIDs only...")
        cleanup1 = LighthouseCleanup(
            api_key="test_key",
            verify_cli=False  # Skip CLI verification for testing
        )
        
        permanent_count = len(LighthouseCleanup.PERMANENT_PROTECTED_CIDS)
        if len(cleanup1.protected_cids) == permanent_count:
            print(f"  ✅ Correctly initialized with {permanent_count} permanent CIDs")
        else:
            print(f"  ❌ Expected {permanent_count} CIDs, got {len(cleanup1.protected_cids)}")
            return False
        print()
        
        # Test with additional CIDs
        print("Test 2: Initialize with additional CIDs...")
        additional = ["QmTest1", "QmTest2"]
        cleanup2 = LighthouseCleanup(
            api_key="test_key",
            verify_cli=False,
            additional_protected_cids=additional
        )
        
        expected_total = permanent_count + len(additional)
        if len(cleanup2.protected_cids) == expected_total:
            print(f"  ✅ Correctly initialized with {expected_total} total CIDs")
            print(f"     ({permanent_count} permanent + {len(additional)} additional)")
        else:
            print(f"  ❌ Expected {expected_total} CIDs, got {len(cleanup2.protected_cids)}")
            return False
        print()
        
        print("✅ All initialization tests passed!")
        print()
        return True
        
    except Exception as e:
        print(f"❌ Initialization test failed: {e}")
        return False


def main():
    """Run all verification tests."""
    
    print()
    print("🔍 LIGHTHOUSE FILE PROTECTION VERIFICATION")
    print()
    
    # Run tests
    test1 = test_permanent_cids()
    test2 = test_initialization()
    
    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()
    
    if test1 and test2:
        print("✅ ALL TESTS PASSED")
        print()
        print("The following CIDs are permanently protected:")
        for cid in LighthouseCleanup.PERMANENT_PROTECTED_CIDS:
            print(f"  🛡️  {cid}")
        print()
        print("These files will NEVER be deleted during cleanup cycles.")
        print()
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        print()
        print("Please review the errors above and fix the configuration.")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
