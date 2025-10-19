"""Main worker loop for DEX arbitrage data ingestion."""
import asyncio
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

try:
    import orjson
    USE_ORJSON = True
except ImportError:
    import json
    USE_ORJSON = False

from dotenv import load_dotenv

from settings import Settings
from blockscout_client import MCPClient, get_mcp_client_from_env, MCPError
from transform import normalize_tx, compute_price_delta
from state import read_state, write_state


# Load environment variables
load_dotenv()

# Initialize settings
settings = Settings()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


async def fetch_and_process_transactions(
    client: MCPClient,
    pool_addresses: List[str],
    age_from: int,
    age_to: int,
    autoscout_base: str
) -> List[Dict[str, Any]]:
    """
    Fetch transactions for pool addresses and transform to normalized rows.
    
    Args:
        client: MCP client
        pool_addresses: List of pool/router addresses
        age_from: Start timestamp (UNIX seconds)
        age_to: End timestamp (UNIX seconds)
        autoscout_base: Autoscout explorer base URL
    
    Returns:
        List of normalized swap rows
    """
    all_rows = []
    
    # DEX swap method signatures to filter
    swap_methods = [
        "swapExactTokensForTokens",
        "swapTokensForExactTokens",
        "swapExactETHForTokens",
        "swapETHForExactTokens",
        "swapExactTokensForETH",
        "swapTokensForExactETH",
    ]
    
    for address in pool_addresses:
        logger.info(f"Fetching transactions for {address[:10]}...")
        
        cursor = None
        tx_count = 0
        
        while True:
            try:
                # Fetch page of transactions
                # Note: methods parameter may not be supported by all MCP servers
                transactions, next_cursor = await client.get_transactions_by_address(
                    address=address,
                    age_from=age_from,
                    age_to=age_to,
                    methods=None,  # Filter client-side if not supported
                    cursor=cursor
                )
                
                tx_count += len(transactions)
                
                # Transform each transaction
                for tx in transactions:
                    rows = normalize_tx(tx, autoscout_base)
                    all_rows.extend(rows)
                
                logger.debug(f"  Processed {len(transactions)} tx, produced {len(all_rows)} rows so far")
                
                # Check for more pages
                if not next_cursor:
                    break
                
                cursor = next_cursor
            
            except MCPError as e:
                logger.error(f"MCP error fetching transactions: {e}")
                break
            except Exception as e:
                logger.error(f"Unexpected error: {e}", exc_info=True)
                break
        
        logger.info(f"  ✓ Fetched {tx_count} transactions for {address[:10]}...")
    
    return all_rows


def append_jsonl(file_path: Path, rows: List[Dict[str, Any]]) -> None:
    """Append rows to JSONL file."""
    with open(file_path, "a") as f:
        for row in rows:
            if USE_ORJSON:
                f.write(orjson.dumps(row).decode("utf-8") + "\n")
            else:
                f.write(json.dumps(row) + "\n")


def count_jsonl_rows(file_path: Path) -> int:
    """Count rows in JSONL file."""
    if not file_path.exists():
        return 0
    
    with open(file_path, "r") as f:
        return sum(1 for _ in f)


def rotate_jsonl_if_needed(file_path: Path, max_rows: int) -> bool:
    """
    Rotate JSONL file if it exceeds max_rows.
    
    Returns:
        True if rotated, False otherwise
    """
    row_count = count_jsonl_rows(file_path)
    
    if row_count >= max_rows:
        # Rotate by renaming with timestamp
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        archive_path = file_path.with_name(f"{file_path.stem}_{timestamp}.jsonl")
        file_path.rename(archive_path)
        logger.info(f"Rotated {file_path.name} → {archive_path.name} ({row_count} rows)")
        return True
    
    return False


def update_metadata(metadata_path: Path, row_count: int) -> None:
    """Update metadata.json with latest stats."""
    metadata = {
        "last_updated": datetime.utcnow().isoformat() + "Z",
        "rows": row_count,
        "latest_cid": None,  # TODO: Integrate with Lighthouse/1MB DataCoin
    }
    
    with open(metadata_path, "w") as f:
        if USE_ORJSON:
            f.write(orjson.dumps(metadata, option=orjson.OPT_INDENT_2).decode("utf-8"))
        else:
            json.dump(metadata, f, indent=2)


async def run_cycle(client: MCPClient, settings: Settings, state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run one ingestion cycle.
    
    Returns:
        Updated state dict
    """
    data_out_dir = Path(settings.DATA_OUT_DIR)
    jsonl_path = data_out_dir / "dexarb_latest.jsonl"
    metadata_path = data_out_dir / "metadata.json"
    
    # Get latest block
    try:
        latest = await client.get_latest_block()
        latest_block = latest["number"]
        latest_timestamp = latest["timestamp"]
        logger.info(f"Latest block: {latest_block} (timestamp: {latest_timestamp})")
    except MCPError as e:
        logger.error(f"Failed to get latest block: {e}")
        logger.warning("Skipping this cycle")
        return state
    
    # Determine time window (age-based for MCP API)
    # age_to = now, age_from = now - WINDOW_MINUTES
    now = int(time.time())
    age_to = now
    age_from = now - (settings.WINDOW_MINUTES * 60)
    
    # Check if we should use last_seen_timestamp instead
    last_seen_timestamp = state.get("last_seen_timestamp")
    if last_seen_timestamp:
        age_from = last_seen_timestamp
    
    logger.info(f"Time window: {age_from} to {age_to} ({settings.WINDOW_MINUTES} min window)")
    
    # Collect pool addresses
    pool_addresses = []
    if settings.DEX_POOL_A:
        pool_addresses.append(settings.DEX_POOL_A)
    if settings.DEX_POOL_B:
        pool_addresses.append(settings.DEX_POOL_B)
    
    logger.info(f"Monitoring {len(pool_addresses)} pool(s): {[p[:10]+'...' for p in pool_addresses]}")
    
    # Fetch and transform transactions
    rows = await fetch_and_process_transactions(
        client=client,
        pool_addresses=pool_addresses,
        age_from=age_from,
        age_to=age_to,
        autoscout_base=settings.AUTOSCOUT_BASE
    )
    
    logger.info(f"✓ Produced {len(rows)} normalized rows")
    
    # Append to JSONL
    if rows:
        append_jsonl(jsonl_path, rows)
        logger.info(f"✓ Appended to {jsonl_path}")
    
    # Check if rotation is needed
    rotated = rotate_jsonl_if_needed(jsonl_path, settings.MAX_ROWS_PER_ROTATION)
    
    # Update metadata
    total_rows = count_jsonl_rows(jsonl_path)
    update_metadata(metadata_path, total_rows)
    logger.info(f"✓ Updated metadata: {total_rows} rows")
    
    # Update state
    new_state = {
        "last_seen_timestamp": age_to,
        "last_block": latest_block,
        "last_updated": datetime.utcnow().isoformat() + "Z"
    }
    
    # Print cycle summary
    print("")
    print("=" * 60)
    print("CYCLE SUMMARY")
    print("=" * 60)
    print(f"  Fetched transactions: {len(rows)} tx processed")
    print(f"  Produced rows: {len(rows)}")
    print(f"  Total rows in file: {total_rows}")
    print(f"  Rotated: {'Yes' if rotated else 'No'}")
    print(f"  New last_seen_timestamp: {age_to}")
    print(f"  New last_block: {latest_block}")
    print(f"  JSONL path: {jsonl_path}")
    print(f"  Metadata path: {metadata_path}")
    print("=" * 60)
    print("")
    
    return new_state


def main():
    """Main worker loop."""
    logger.info("=" * 60)
    logger.info("DEX Arbitrage Data Worker Starting")
    logger.info("=" * 60)
    
    # Validate configuration
    settings.validate_required_fields()
    
    # Print redacted configuration
    settings.print_redacted()
    
    # Ensure output directory exists
    data_out_dir = Path(settings.DATA_OUT_DIR)
    data_out_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {data_out_dir.absolute()}")
    
    # Initialize MCP client
    try:
        client = get_mcp_client_from_env(settings)
        logger.info("✓ MCP client initialized")
        
        # Print discovered tools
        if client.available_tools:
            logger.info(f"✓ MCP tools available: {', '.join(client.available_tools)}")
    except Exception as e:
        logger.error(f"Failed to initialize MCP client: {e}")
        logger.error("Please check BLOCKSCOUT_MCP_BASE and network connectivity.")
        logger.error("Reference: https://docs.blockscout.com/devs/mcp-server")
        return
    
    # Load state
    state = read_state(settings.LAST_BLOCK_STATE_PATH)
    logger.info(f"Loaded state: {state}")
    
    # Print dry-run summary
    print("")
    print("=" * 60)
    print("DRY-RUN SUMMARY")
    print("=" * 60)
    print(f"  Pools to monitor:")
    if settings.DEX_POOL_A:
        print(f"    - DEX_POOL_A: {settings.DEX_POOL_A}")
    if settings.DEX_POOL_B:
        print(f"    - DEX_POOL_B: {settings.DEX_POOL_B}")
    print(f"  Window strategy: Age-based (last {settings.WINDOW_MINUTES} minutes)")
    print(f"  JSONL output: {data_out_dir / 'dexarb_latest.jsonl'}")
    print(f"  Metadata output: {data_out_dir / 'metadata.json'}")
    print(f"  Max rows per file: {settings.MAX_ROWS_PER_ROTATION}")
    print(f"  Poll interval: {settings.WORKER_POLL_SECONDS}s")
    print("=" * 60)
    print("")
    
    # Main loop
    try:
        while True:
            try:
                # Run async cycle
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    state = loop.run_until_complete(run_cycle(client, settings, state))
                finally:
                    loop.close()
                
                # Persist state
                write_state(settings.LAST_BLOCK_STATE_PATH, state)
                logger.info(f"✓ State saved to {settings.LAST_BLOCK_STATE_PATH}")
                
            except KeyboardInterrupt:
                raise
            except Exception as e:
                logger.error(f"Error in worker cycle: {e}", exc_info=True)
            
            logger.info(f"Sleeping {settings.WORKER_POLL_SECONDS}s until next cycle...")
            time.sleep(settings.WORKER_POLL_SECONDS)
    
    except KeyboardInterrupt:
        logger.info("Received interrupt, shutting down...")
    finally:
        # Close client
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(client.close())
        finally:
            loop.close()
        logger.info("Worker stopped")


if __name__ == "__main__":
    main()
