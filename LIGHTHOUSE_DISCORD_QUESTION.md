# Lighthouse Discord Support Question

## Subject: `node.lighthouse.storage:443` Upload Endpoint Unreachable - Connection Timeout

---

### Issue Summary

The Lighthouse Python SDK upload endpoint (`node.lighthouse.storage:443`) has been unreachable for the past several hours, causing all uploads to time out globally. This appears to be an infrastructure issue on Lighthouse's side.

### Environment
- **SDK**: `lighthouseweb3==0.1.5` (official Python SDK)
- **Deployment**: Railway.app (production)
- **Issue Started**: ~October 21, 2025, 12:00 UTC
- **Status**: Still ongoing as of 12:50 UTC

### Technical Details

**Error Message:**
```python
HTTPSConnectionPool(host='node.lighthouse.storage', port=443): 
Max retries exceeded with url: /api/v0/add 
(Caused by ConnectTimeoutError(<urllib3.connection.HTTPSConnection object>, 
'Connection to node.lighthouse.storage timed out. (connect timeout=15)'))
```

**Connection Test (from multiple locations):**
```bash
$ curl -v --max-time 10 https://node.lighthouse.storage/api/v0/add
* Host node.lighthouse.storage:443 was resolved.
* IPv4: 13.235.128.180
*   Trying 13.235.128.180:443...
* Connection timed out after 10002 milliseconds
curl: (28) Connection timed out after 10002 milliseconds
```

**DNS Resolution:** ✅ Working - Resolves to `13.235.128.180`  
**TCP Connection:** ❌ Failing - Port 443 not responding  
**Alternative API:** ✅ `api.lighthouse.storage` (43.205.243.175) is reachable

### Code Context

**Our Implementation:**
```python
from lighthouseweb3 import Lighthouse

# Initialize client
lighthouse = Lighthouse(token=api_key)

# Upload attempt (times out after 15 seconds)
result = lighthouse.upload(source=str(file_path), tag="dexarb_data")
```

**SDK Configuration (from GitHub):**
The Python SDK is hardcoded to use:
```python
# src/lighthouseweb3/functions/config.py
lighthouse_node = "https://node.lighthouse.storage"
```

### What We've Verified

✅ **Our API key is valid** - tested with `api.lighthouse.storage` endpoints  
✅ **Encryption working** - 77KB encrypted files generated successfully  
✅ **Network connectivity** - Railway deployment can reach other endpoints  
✅ **Timeout configuration** - Set to 15s connect, 180s read  
✅ **Local testing** - Same timeout from multiple ISPs and locations  

❌ **Upload node unreachable** - `node.lighthouse.storage:443` not accepting connections

### Questions

1. **Is there a known outage** with `node.lighthouse.storage`?
2. **Is there an alternative upload endpoint** we can use temporarily?
3. **ETA for resolution** if this is a known issue?
4. **Should we use a different endpoint** like `api.lighthouse.storage` for uploads?
5. **Is there a status page** we should monitor for infrastructure updates?

### Workaround Attempted

We tried to implement a direct upload to `api.lighthouse.storage/api/v0/add` but received a 404, suggesting the upload endpoint may have a different path or the node endpoint is required.

### Impact

Our decentralized data pipeline is currently unable to upload encrypted arbitrage data to IPFS/Filecoin. The worker continues processing data locally, but uploads are failing.

### Request

Please advise on:
- Current status of the upload node infrastructure
- Alternative endpoints or temporary workarounds
- Expected timeline for resolution

Thank you for your assistance! 🙏

---

**Additional Context:**
- Production deployment: Railway.app
- Use case: Real-time DEX arbitrage data storage
- Files: 70-100KB JSON files, uploaded every 15 seconds
- Hackathon deadline: Need working solution ASAP

**Logs Available:** Can provide full Railway deployment logs if helpful.
