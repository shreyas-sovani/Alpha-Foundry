# Quick Reference: Protected Lighthouse Files

## 🛡️ Permanently Protected CIDs

These files will **NEVER** be deleted:

```
bafybeih5j5recyxiwscbtjl7o5rmv22rijmeq552iovrguas45s4766yw4
bafkreie73wguaf7yucgzcudbkivtgtxzvyv2efjg24s76j67lu7cbt7vcy
```

## 📍 Configuration Location

File: `/apps/worker/lighthouse_cleanup.py`

```python
PERMANENT_PROTECTED_CIDS = {
    "bafybeih5j5recyxiwscbtjl7o5rmv22rijmeq552iovrguas45s4766yw4",
    "bafkreie73wguaf7yucgzcudbkivtgtxzvyv2efjg24s76j67lu7cbt7vcy"
}
```

## ✅ Verification

Run this command to verify protection is active:

```bash
python3 scripts/verify_lighthouse_protection.py
```

Expected output:
```
✅ ALL TESTS PASSED

The following CIDs are permanently protected:
  🛡️  bafkreie73wguaf7yucgzcudbkivtgtxzvyv2efjg24s76j67lu7cbt7vcy
  🛡️  bafybeih5j5recyxiwscbtjl7o5rmv22rijmeq552iovrguas45s4766yw4

These files will NEVER be deleted during cleanup cycles.
```

## 🔧 How to Add More Protected CIDs

1. Edit `/apps/worker/lighthouse_cleanup.py`
2. Add new CID to the set:

```python
PERMANENT_PROTECTED_CIDS = {
    "bafybeih5j5recyxiwscbtjl7o5rmv22rijmeq552iovrguas45s4766yw4",
    "bafkreie73wguaf7yucgzcudbkivtgtxzvyv2efjg24s76j67lu7cbt7vcy",
    "your_new_cid_here"  # Add new CIDs here
}
```

3. Run verification: `python3 scripts/verify_lighthouse_protection.py`

## 📖 Full Documentation

- Detailed guide: `/LIGHTHOUSE_PROTECTION_CONFIG.md`
- Implementation summary: `/IMPLEMENTATION_SUMMARY_LIGHTHOUSE_PROTECTION.md`

## 🚀 Status

- ✅ Implementation complete
- ✅ All tests passed
- ✅ No syntax errors
- ✅ Production ready
