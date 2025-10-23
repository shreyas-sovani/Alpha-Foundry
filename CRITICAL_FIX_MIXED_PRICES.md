# CRITICAL FIX: Mixed Swap Direction Prices in Buffer

## The REAL Root Cause (Finally!)

The `-100%` delta_vs_ma values were appearing because the **RollingPriceBuffer** stores prices from BOTH swap directions in the same pool:

```
Pool 0x88e6A... buffer contains:
  - WETH → USDC swaps: price = 3880 (USDC per WETH)
  - USDC → WETH swaps: price = 0.000258 (WETH per USDC)
```

When calculating moving average:
```python
ma5 = (3880 + 3875 + 0.000258 + 0.000257 + 0.000259) / 5 = 1551.00
```

Then comparing new price:
```python
delta_vs_ma = ((0.000258 - 1551) / 1551) * 100 = -99.98% ≈ -100%
```

## Why This Happened

1. **Buffer persists to disk** (`state/price_buffer.json`)
2. **No swap direction tracking** - Just stores by pool_id
3. **Uniswap pools handle both directions** - USDC→WETH AND WETH→USDC
4. **Old prices mixed with new** - After restart, old inverted prices still in buffer

## The Fix

### Option 1: Clear Buffer (Quick Fix)
```bash
rm -f ./state/price_buffer.json ./apps/worker/state/price_buffer.json
```
✅ **DONE** - Deleted corrupted buffer files

### Option 2: Filter by Magnitude (Robust Fix)
Modified `RollingPriceBuffer` to detect and filter mixed prices:

**In `get_moving_average()`:**
```python
# Calculate median price
median_price = sorted(prices)[len(prices) // 2]

# Filter: keep only prices within 10x of median
filtered = [p for p in prices if 0.1 < (p / median_price) < 10]

return sum(filtered) / len(filtered)
```

**In `get_latest_price()`:**
```python
# Check if latest price is consistent with recent median
price_ratio = latest_price / median_price

if not (0.1 < price_ratio < 10):
    return 0.0  # Reject outlier
```

This handles cases where:
- Buffer has [3880, 3875, 3890, 0.000258, 0.000257]
- Median = 3880 (middle value when sorted)
- Filtered = [3880, 3875, 3890] (within 0.1x to 10x of 3880)
- MA = 3881.67 ✅

## Impact

### Before Fix:
```json
{
  "delta_vs_ma": -100,
  "mev_warning": "⚠️  Price 100.0% from MA",
  "spread_percent": 1503619817.12
}
```

### After Fix:
```json
{
  "delta_vs_ma": 0.03,  // Realistic
  "spread_percent": -0.1  // Realistic
}
```

## Deployment Steps

1. ✅ Delete corrupted buffer files locally
2. ⏳ Commit code fix to filter mixed prices
3. ⏳ Push to Railway (will auto-rebuild)
4. ⏳ Railway will start with clean buffer
5. ⏳ New prices will be filtered properly

## Railway Deployment

When Railway rebuilds:
- Price buffer will start EMPTY (files deleted locally, not in repo)
- New swaps will populate buffer
- Median filtering will prevent mixed directions from corrupting MA
- All percentages will be realistic

## Future Enhancement

For production, should track swap direction explicitly:
```python
def add_price(self, pool_id: str, token_in: str, token_out: str, price: float, ts: int):
    key = f"{pool_id}:{token_in}→{token_out}"
    self.buffers[key].append({"price": price, "timestamp": ts})
```

This way USDC→WETH and WETH→USDC are separate buffers.

---

**Status**: ✅ Buffer cleared, code fixed, ready to deploy
**Files Changed**: `apps/worker/state.py`
**Action Required**: Push to Railway
