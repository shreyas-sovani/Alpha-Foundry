"""Test preview update with analytics."""
import sys
import json
from pathlib import Path

sys.path.insert(0, 'apps/worker')

from settings import Settings
from state import RollingPriceBuffer, PreviewStateTracker
from run import update_preview_with_analytics
from blockscout_rest import get_rest_client_from_env

# Load settings
from dotenv import load_dotenv
load_dotenv()
settings = Settings()

# Load state objects
price_buffer = RollingPriceBuffer.load("state/price_buffer.json", max_size=20)
preview_state = PreviewStateTracker.load("state/preview_state.json", max_size=10)

# Prepare paths
preview_path = Path(settings.DATA_OUT_DIR) / "preview.json"
jsonl_path = Path(settings.DATA_OUT_DIR) / "dexarb_latest.jsonl"

# Get pool addresses
pool_addresses = []
if settings.DEX_POOL_A:
    pool_addresses.append(settings.DEX_POOL_A)
if settings.DEX_POOL_B:
    pool_addresses.append(settings.DEX_POOL_B)

# Create client
client = get_rest_client_from_env(settings)

print("Updating preview with analytics...")
print(f"  Preview path: {preview_path}")
print(f"  JSONL path: {jsonl_path}")
print(f"  Pool addresses: {pool_addresses}")
print(f"  Preview rows: {settings.PREVIEW_ROWS}")
print(f"  Window minutes: {settings.WINDOW_MINUTES}")
print(f"  ETH price USD: ${settings.REFERENCE_ETH_PRICE_USD}")

# Call the update function
rows_after, latest_ts = update_preview_with_analytics(
    preview_path=preview_path,
    jsonl_path=jsonl_path,
    preview_rows=settings.PREVIEW_ROWS,
    price_buffer=price_buffer,
    preview_state=preview_state,
    pool_addresses=pool_addresses,
    window_minutes=settings.WINDOW_MINUTES,
    eth_price_usd=settings.REFERENCE_ETH_PRICE_USD,
    autoscout_base=settings.AUTOSCOUT_BASE or "https://eth-sepolia.blockscout.com",
    client=client
)

print(f"\n✓ Updated preview: {rows_after} total rows, latest_ts={latest_ts}")

# Read and display the preview
with open(preview_path, "r") as f:
    preview_data = json.load(f)

print("\nPreview Header:")
print(json.dumps(preview_data.get("header", {}), indent=2))

print("\nFirst Row Keys:")
if preview_data.get("preview_rows"):
    print(list(preview_data["preview_rows"][0].keys()))

print("\nFirst Row Sample:")
if preview_data.get("preview_rows"):
    row = preview_data["preview_rows"][0]
    print(f"  tx_hash: {row.get('tx_hash', 'N/A')[:20]}...")
    print(f"  delta_vs_ma: {row.get('delta_vs_ma', 'MISSING')}")
    print(f"  gas_used: {row.get('gas_used', 'MISSING')}")
    print(f"  gas_cost_usd: {row.get('gas_cost_usd', 'MISSING')}")
    print(f"  swap_value_usd: {row.get('swap_value_usd', 'MISSING')}")

# Save state
price_buffer.save("state/price_buffer.json")
preview_state.save("state/preview_state.json")
print("\n✓ State saved")
