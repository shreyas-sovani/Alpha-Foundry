"""Main worker loop for DEX arbitrage data ingestion."""
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv

from settings import Settings
from blockscout_client import BlockscoutMCPClient
from transform import normalize_swap_event, compute_price_delta
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


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def fetch_and_process_logs(
    client: BlockscoutMCPClient,
    from_block: int,
    to_block: int,
    dex_addresses: List[str]
) -> List[Dict[str, Any]]:
    """
    Fetch logs for configured DEX addresses and transform to normalized rows.
    
    Args:
        client: Blockscout MCP client
        from_block: Starting block
        to_block: Ending block
        dex_addresses: List of DEX pool addresses
    
    Returns:
        List of normalized swap events
    """
    logger.info(f"Fetching logs from block {from_block} to {to_block}")
    
    all_normalized_events = []
    
    for address in dex_addresses:
        # TODO: Call client.get_transaction_logs with proper parameters
        # logs_response = client.get_transaction_logs(
        #     address=address,
        #     from_block=from_block,
        #     to_block=to_block
        # )
        
        # TODO: Transform each log using normalize_swap_event
        # for log in logs_response.get("items", []):
        #     normalized = normalize_swap_event(log, abi_cache={})
        #     all_normalized_events.append(normalized)
        
        logger.warning(f"TODO: Implement log fetching for address {address}")
    
    return all_normalized_events


def append_jsonl(file_path: Path, rows: List[Dict[str, Any]]) -> None:
    """Append rows to JSONL file."""
    with open(file_path, "a") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")


def update_metadata(metadata_path: Path, row_count: int) -> None:
    """Update metadata.json with latest stats."""
    metadata = {
        "last_updated": datetime.utcnow().isoformat() + "Z",
        "rows": row_count,
        "latest_cid": None,  # TODO: Integrate with Lighthouse/1MB DataCoin
    }
    
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)


def main():
    """Main worker loop."""
    logger.info("Starting DEX arbitrage data worker")
    
    # Print redacted configuration
    settings.print_redacted()
    
    # Ensure output directory exists
    data_out_dir = Path(settings.DATA_OUT_DIR)
    data_out_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize client
    client = BlockscoutMCPClient(
        mcp_base_url=settings.BLOCKSCOUT_MCP_BASE,
        chain_id=settings.CHAIN_ID
    )
    
    # Load last processed block
    state = read_state(settings.LAST_BLOCK_STATE_PATH)
    last_block = state.get("last_block", 0)
    
    dex_addresses = [settings.DEX_POOL_A, settings.DEX_POOL_B]
    jsonl_path = data_out_dir / "dexarb_latest.jsonl"
    metadata_path = data_out_dir / "metadata.json"
    
    logger.info(f"Starting from block {last_block}")
    
    try:
        while True:
            try:
                # Get latest block
                # TODO: Uncomment when get_latest_block is implemented
                # latest_block = client.get_latest_block()
                latest_block = last_block + 10  # Placeholder
                
                if latest_block <= last_block:
                    logger.info(f"No new blocks. Sleeping {settings.WORKER_POLL_SECONDS}s")
                    time.sleep(settings.WORKER_POLL_SECONDS)
                    continue
                
                # Process window
                from_block = last_block + 1
                to_block = latest_block
                
                logger.info(f"Processing blocks {from_block} to {to_block}")
                
                # Fetch and transform logs
                normalized_rows = fetch_and_process_logs(
                    client=client,
                    from_block=from_block,
                    to_block=to_block,
                    dex_addresses=dex_addresses
                )
                
                if normalized_rows:
                    # Append to JSONL
                    append_jsonl(jsonl_path, normalized_rows)
                    logger.info(f"Appended {len(normalized_rows)} rows to {jsonl_path}")
                    
                    # TODO: Implement rotation by max_lines or max_minutes
                
                # Count total rows
                total_rows = 0
                if jsonl_path.exists():
                    with open(jsonl_path, "r") as f:
                        total_rows = sum(1 for _ in f)
                
                # Update metadata
                update_metadata(metadata_path, total_rows)
                
                # Persist checkpoint
                write_state(settings.LAST_BLOCK_STATE_PATH, {"last_block": to_block})
                last_block = to_block
                
                logger.info(f"Checkpoint saved at block {last_block}")
                
            except Exception as e:
                logger.error(f"Error in worker loop: {e}", exc_info=True)
                logger.info(f"Retrying in {settings.WORKER_POLL_SECONDS}s")
            
            time.sleep(settings.WORKER_POLL_SECONDS)
    
    finally:
        client.close()
        logger.info("Worker stopped")


if __name__ == "__main__":
    main()
