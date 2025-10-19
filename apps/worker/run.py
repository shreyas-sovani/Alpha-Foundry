"""Main worker loop for DEX arbitrage data ingestion."""
import asyncio
import logging
import os
import signal
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    import orjson
    USE_ORJSON = True
except ImportError:
    import json
    USE_ORJSON = False

from dotenv import load_dotenv

from settings import Settings
from blockscout_rest import BlockscoutRESTClient, get_rest_client_from_env
from transform import normalize_tx, normalize_log_to_swap, compute_price_delta
from state import read_state, write_state, DedupeTracker
from http_server import ReadOnlyHTTPServer


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

# Global HTTP server instance for cleanup
http_server: Optional[ReadOnlyHTTPServer] = None


async def fetch_and_process_logs(
    client: BlockscoutRESTClient,
    pool_addresses: List[str],
    from_block: int,
    to_block: int,
    autoscout_base: str,
    dedupe: DedupeTracker,
    pool_tokens: Dict[str, Any],
    watermark_ts: int = 0,
    watermark_block: int = 0,
    early_stop_mode: str = "timestamp",
    max_pages: int = 10
) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Fetch logs (events) for pool addresses - LOGS-FIRST PATH with early-stop guards.
    
    Args:
        client: REST client
        pool_addresses: List of pool/router addresses
        from_block: Starting block (may be ignored by REST API)
        to_block: Ending block (may be ignored by REST API)
        autoscout_base: Autoscout explorer base URL
        dedupe: Deduplication tracker
        pool_tokens: Cache of pool_address -> (token0, token1)
        watermark_ts: Stop pagination when logs older than this timestamp
        watermark_block: Stop pagination when logs older than this block
        early_stop_mode: "block" or "timestamp"
        max_pages: Maximum pages to fetch per cycle
    
    Returns:
        Tuple of (normalized swap rows, stats dict)
    """
    all_rows = []
    stats = {
        "total_logs_fetched": 0,
        "pages_fetched": 0,
        "early_stop_triggered": False,
        "early_stop_reason": None,
        "max_block_seen": 0,
        "max_ts_seen": 0,
    }
    
    for address in pool_addresses:
        logger.info(f"Fetching logs for {address[:10]}... (watermark_ts={watermark_ts}, watermark_block={watermark_block})")
        
        cursor = None
        page_count = 0
        
        while page_count < max_pages:
            try:
                # Fetch page of logs
                logs, next_cursor = await client.get_logs(
                    address=address,
                    from_block=from_block,
                    to_block=to_block,
                    topics=None,  # Get all topics, filter by signature in transform
                    cursor=cursor
                )
                
                page_count += 1
                stats["pages_fetched"] += 1
                stats["total_logs_fetched"] += len(logs)
                
                if not logs:
                    logger.info(f"  Page {page_count}: No logs returned")
                    break
                
                logger.info(f"  Page {page_count}: Fetched {len(logs)} logs")
                
                # Compute timestamps for logs using block_ts cache
                log_timestamps = []
                log_blocks = []
                for log in logs:
                    block_num = log.get("block_number") or log.get("blockNumber") or 0
                    log_blocks.append(block_num)
                    
                    # Get timestamp from cache
                    block_info = await client.get_block_info(block_num)
                    log_ts = block_info.get("timestamp", 0)
                    log_timestamps.append(log_ts)
                
                # Check early-stop condition at page level
                if log_blocks:
                    max_block_in_page = max(log_blocks)
                    min_block_in_page = min(log_blocks)
                    stats["max_block_seen"] = max(stats["max_block_seen"], max_block_in_page)
                
                if log_timestamps:
                    max_ts_in_page = max(log_timestamps)
                    min_ts_in_page = min(log_timestamps)
                    stats["max_ts_seen"] = max(stats["max_ts_seen"], max_ts_in_page)
                    
                    if early_stop_mode == "timestamp" and watermark_ts > 0:
                        if min_ts_in_page <= watermark_ts:
                            stats["early_stop_triggered"] = True
                            stats["early_stop_reason"] = f"timestamp watermark reached (min_ts={min_ts_in_page} <= {watermark_ts})"
                            logger.info(f"  Early-stop: {stats['early_stop_reason']}")
                            break
                    
                    if early_stop_mode == "block" and watermark_block > 0:
                        if min_block_in_page <= watermark_block:
                            stats["early_stop_triggered"] = True
                            stats["early_stop_reason"] = f"block watermark reached (min_block={min_block_in_page} <= {watermark_block})"
                            logger.info(f"  Early-stop: {stats['early_stop_reason']}")
                            break
                
                # Transform each log
                for idx, log in enumerate(logs):
                    tx_hash = log.get("transaction_hash") or log.get("transactionHash") or ""
                    log_index = log.get("log_index") or log.get("logIndex") or 0
                    
                    # Check for duplicate
                    if dedupe.is_duplicate(tx_hash, log_index):
                        logger.debug(f"Skipping duplicate: {tx_hash}:{log_index}")
                        continue
                    
                    block_num = log.get("block_number") or log.get("blockNumber") or 0
                    
                    try:
                        row = await normalize_log_to_swap(log, autoscout_base, pool_tokens, client, block_num)
                        if row:
                            all_rows.append(row)
                            dedupe.mark_seen(tx_hash, log_index)
                    except Exception as e:
                        logger.error(f"  Error normalizing log {tx_hash}:{log_index}: {e}", exc_info=True)
                        continue
                
                # Check for more pages
                if not next_cursor:
                    logger.info(f"  No more pages for {address[:10]}...")
                    break
                
                cursor = next_cursor
            
            except Exception as e:
                logger.error(f"Error fetching logs: {e}", exc_info=True)
                break
        
        if page_count >= max_pages:
            logger.warning(f"  Reached max pages ({max_pages}) for {address[:10]}..., will continue next cycle")
        
        logger.info(f"  ✓ Fetched {stats['total_logs_fetched']} logs across {page_count} pages for {address[:10]}...")
    
    return all_rows, stats


async def fetch_and_process_transactions(
    client: BlockscoutRESTClient,
    pool_addresses: List[str],
    age_from: int,
    age_to: int,
    autoscout_base: str,
    dedupe: DedupeTracker
) -> List[Dict[str, Any]]:
    """
    Fetch transactions for pool addresses - FALLBACK PATH.
    
    Args:
        client: MCP client
        pool_addresses: List of pool/router addresses
        age_from: Start timestamp (UNIX seconds)
        age_to: End timestamp (UNIX seconds)
        autoscout_base: Autoscout explorer base URL
        dedupe: Deduplication tracker
    
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
                    tx_hash = tx.get("hash") or tx.get("transaction_hash") or ""
                    
                    # Use log_index=0 for tx-based deduplication
                    if dedupe.is_duplicate(tx_hash, 0):
                        logger.debug(f"Skipping duplicate tx: {tx_hash}")
                        continue
                    
                    rows = normalize_tx(tx, autoscout_base)
                    all_rows.extend(rows)
                    
                    if rows:
                        dedupe.mark_seen(tx_hash, 0)
                
                logger.debug(f"  Processed {len(transactions)} tx, produced {len(all_rows)} rows so far")
                
                # Check for more pages
                if not next_cursor:
                    break
                
                cursor = next_cursor
            
            except Exception as e:
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


def update_metadata(metadata_path: Path, row_count: int, schema_version: str = "1.0") -> None:
    """Update metadata.json with latest stats, schema version, and freshness."""
    
    # Schema 1.1 fields include enriched token metadata
    if schema_version == "1.1":
        fields = [
            "timestamp", "block_number", "tx_hash", "log_index",
            "token_in", "token_in_symbol", "token_out", "token_out_symbol",
            "amount_in", "amount_out", "amount_in_normalized", "amount_out_normalized",
            "decimals_in", "decimals_out", "pool_id", "normalized_price",
            "delta_vs_other_pool", "explorer_link"
        ]
    else:
        fields = [
            "timestamp", "tx_hash", "log_index", "token_in", "token_out",
            "amount_in", "amount_out", "pool_id", "normalized_price",
            "delta_vs_other_pool", "explorer_link"
        ]
    
    now_utc = datetime.utcnow()
    last_updated_iso = now_utc.isoformat() + "Z"
    
    # Compute freshness: read existing metadata if available
    freshness_minutes = 0
    if metadata_path.exists():
        try:
            with open(metadata_path, "r") as f:
                existing = json.load(f)
                prev_updated = existing.get("last_updated", "")
                if prev_updated:
                    # Parse ISO timestamp
                    prev_dt = datetime.fromisoformat(prev_updated.replace("Z", "+00:00"))
                    prev_dt_naive = prev_dt.replace(tzinfo=None)
                    delta = now_utc - prev_dt_naive
                    freshness_minutes = int(delta.total_seconds() / 60)
        except Exception as e:
            logger.debug(f"Could not compute freshness: {e}")
    
    metadata = {
        "schema_version": schema_version,
        "last_updated": last_updated_iso,
        "rows": row_count,
        "freshness_minutes": freshness_minutes,
        "latest_cid": None,
        "format": "jsonl",
        "fields": fields
    }
    
    # Atomic write with temp file + rename + fsync
    temp_path = metadata_path.with_suffix(".json.tmp")
    try:
        with open(temp_path, "w") as f:
            if USE_ORJSON:
                f.write(orjson.dumps(metadata, option=orjson.OPT_INDENT_2).decode("utf-8"))
            else:
                json.dump(metadata, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        
        # Atomic rename
        temp_path.replace(metadata_path)
        logger.debug(f"Metadata written atomically to {metadata_path}")
    except Exception as e:
        logger.error(f"Failed to write metadata: {e}")
        if temp_path.exists():
            temp_path.unlink()
        raise


def update_preview(preview_path: Path, jsonl_path: Path, preview_rows: int = 5) -> tuple[int, int]:
    """
    Update preview.json with latest N rows for Hosted Agent.
    
    Returns:
        Tuple of (total_rows, latest_timestamp)
    """
    if not jsonl_path.exists():
        preview = {
            "preview_rows": [],
            "total_rows": 0,
            "last_updated": datetime.utcnow().isoformat() + "Z"
        }
        latest_ts = 0
    else:
        # Read last N rows efficiently (read from end if file is large)
        rows = []
        with open(jsonl_path, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        if USE_ORJSON:
                            rows.append(orjson.loads(line))
                        else:
                            rows.append(json.loads(line))
                    except:
                        pass
        
        # Take last N rows (most recent)
        preview_rows_data = rows[-preview_rows:] if len(rows) > preview_rows else rows
        
        # Get latest timestamp
        latest_ts = max((row.get("timestamp", 0) for row in preview_rows_data), default=0)
        
        preview = {
            "preview_rows": preview_rows_data,
            "total_rows": len(rows),
            "last_updated": datetime.utcnow().isoformat() + "Z"
        }
    
    # Atomic write with temp file + rename + fsync
    temp_path = preview_path.with_suffix(".json.tmp")
    try:
        with open(temp_path, "w") as f:
            if USE_ORJSON:
                f.write(orjson.dumps(preview, option=orjson.OPT_INDENT_2).decode("utf-8"))
            else:
                json.dump(preview, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        
        # Atomic rename
        temp_path.replace(preview_path)
        logger.debug(f"Preview written atomically to {preview_path}")
    except Exception as e:
        logger.error(f"Failed to write preview: {e}")
        if temp_path.exists():
            temp_path.unlink()
        raise
    
    return len(rows) if jsonl_path.exists() else 0, latest_ts


async def run_cycle(client: BlockscoutRESTClient, settings: Settings, state: Dict[str, Any], dedupe: DedupeTracker) -> Dict[str, Any]:
    """
    Run one ingestion cycle with logs-first path, pool resolution, and early-stop guards.
    
    Returns:
        Updated state dict
    """
    from transform import extract_pool_tokens
    
    data_out_dir = Path(settings.DATA_OUT_DIR)
    jsonl_path = data_out_dir / "dexarb_latest.jsonl"
    metadata_path = data_out_dir / "metadata.json"
    preview_path = data_out_dir / settings.PREVIEW_PATH.split("/")[-1]
    
    # Count rows before cycle
    rows_before = count_jsonl_rows(jsonl_path)
    
    # Get latest block
    try:
        latest = await client.get_latest_block()
        latest_block = latest["number"]
        latest_timestamp = latest["timestamp"]
        logger.info(f"Latest block: {latest_block} (timestamp: {latest_timestamp})")
    except Exception as e:
        logger.error(f"Failed to get latest block: {e}")
        logger.warning("Skipping this cycle")
        return state
    
    # Determine windowing strategy and watermark
    early_stop_mode = settings.EARLY_STOP_MODE or settings.WINDOW_STRATEGY
    now_ts = int(time.time())
    
    if settings.WINDOW_STRATEGY == "timestamp":
        # Timestamp-based windowing
        last_seen_ts = state.get("last_seen_ts", 0)
        if last_seen_ts == 0:
            # First run: use WINDOW_MINUTES from now
            watermark_ts = now_ts - (settings.WINDOW_MINUTES * 60)
        else:
            # Subsequent runs: use max of last_seen_ts and recent window
            watermark_ts = max(last_seen_ts, now_ts - (settings.WINDOW_MINUTES * 60))
        
        watermark_block = 0
        from_block = 0  # REST API may ignore this
        to_block = latest_block
        
        logger.info(f"Window strategy: TIMESTAMP")
        logger.info(f"  Watermark timestamp: {watermark_ts} ({datetime.fromtimestamp(watermark_ts).isoformat()})")
        logger.info(f"  Window: last {settings.WINDOW_MINUTES} minutes")
    else:
        # Block-based windowing
        last_seen_block = state.get("last_seen_block", 0)
        if last_seen_block == 0:
            # First run: use BLOCK_LOOKBACK from latest
            watermark_block = max(0, latest_block - settings.BLOCK_LOOKBACK)
        else:
            # Subsequent runs: use max of last_seen_block and recent window
            watermark_block = max(last_seen_block, latest_block - settings.BLOCK_LOOKBACK)
        
        watermark_ts = 0
        from_block = watermark_block
        to_block = latest_block
        
        logger.info(f"Window strategy: BLOCK")
        logger.info(f"  Watermark block: {watermark_block}")
        logger.info(f"  Window: last {settings.BLOCK_LOOKBACK} blocks")
    
    # Pool resolution: Use POOL_A/B if set, else resolve from TOKEN0/TOKEN1
    pool_addresses = []
    if settings.DEX_POOL_A:
        pool_addresses.append(settings.DEX_POOL_A)
    if settings.DEX_POOL_B:
        pool_addresses.append(settings.DEX_POOL_B)
    
    # If no pools but have tokens, resolve pool from factory (simplified for V2)
    # NOTE: Full implementation would query factory.getPair(token0, token1)
    if not pool_addresses and settings.TOKEN0 and settings.TOKEN1:
        logger.info(f"No pools configured, TOKEN0/TOKEN1 resolution not yet implemented")
        logger.info(f"  TOKEN0: {settings.TOKEN0}")
        logger.info(f"  TOKEN1: {settings.TOKEN1}")
    
    logger.info(f"Monitoring {len(pool_addresses)} pool(s): {[p[:10]+'...' for p in pool_addresses]}")
    
    # Initialize pool tokens cache
    pool_tokens = state.get("pool_tokens", {})
    
    # Manual pool token configuration (workaround until eth_call is implemented)
    # For Uniswap V2 pair 0x9Ae18109692b43e95Ae6BE5350A5Acc5211FE9a1 on Sepolia:
    # This is a WETH/UNI pair based on the Swap events we've seen
    if "0x9Ae18109692b43e95Ae6BE5350A5Acc5211FE9a1" not in pool_tokens:
        # Placeholder tokens - these should be resolved from the pool contract
        # For now, using generic addresses as placeholders
        pool_tokens["0x9Ae18109692b43e95Ae6BE5350A5Acc5211FE9a1"] = (
            "0x7b79995e5f793A07Bc00c21412e50Ecae098E7f9",  # WETH on Sepolia (token0)
            "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984"   # UNI on Sepolia (token1)
        )
        logger.info(f"Using manual pool token configuration for 0x9Ae18109...")
    
    # Try logs-first path if available
    rows = []
    stats = {}
    used_logs_path = False
    
    if client.has_tool("get_logs"):
        logger.info("Using LOGS-FIRST path (get_logs available)")
        try:
            rows, stats = await fetch_and_process_logs(
                client=client,
                pool_addresses=pool_addresses,
                from_block=from_block,
                to_block=to_block,
                autoscout_base=settings.AUTOSCOUT_BASE or "https://eth-sepolia.blockscout.com",
                dedupe=dedupe,
                pool_tokens=pool_tokens,
                watermark_ts=watermark_ts,
                watermark_block=watermark_block,
                early_stop_mode=early_stop_mode,
                max_pages=settings.MAX_PAGES_PER_CYCLE
            )
            used_logs_path = True
        except NotImplementedError:
            logger.warning("Logs tool not available, falling back to transactions")
    
    # Fallback to transaction-based path
    if not used_logs_path:
        logger.info("Using TRANSACTION-BASED fallback path")
        # Determine time window (age-based for MCP API)
        age_to = now_ts
        age_from = watermark_ts if watermark_ts > 0 else now_ts - (settings.WINDOW_MINUTES * 60)
        
        logger.info(f"Time window: {age_from} to {age_to} ({settings.WINDOW_MINUTES} min window)")
        
        rows = await fetch_and_process_transactions(
            client=client,
            pool_addresses=pool_addresses,
            age_from=age_from,
            age_to=age_to,
            autoscout_base=settings.AUTOSCOUT_BASE,
            dedupe=dedupe
        )
        stats = {"total_logs_fetched": len(rows), "pages_fetched": 1}
    
    logger.info(f"✓ Produced {len(rows)} normalized rows (deduped)")
    
    # Compute cross-pool price deltas if both pools have data
    if len(pool_addresses) == 2:
        pool_a_rows = [r for r in rows if r.get("pool_id") == pool_addresses[0]]
        pool_b_rows = [r for r in rows if r.get("pool_id") == pool_addresses[1]]
        
        if pool_a_rows and pool_b_rows:
            logger.info(f"Computing cross-pool deltas: {len(pool_a_rows)} vs {len(pool_b_rows)} swaps")
            
            # Simple approach: Match by timestamp within tolerance (e.g., same block)
            # In production, use time-weighted matching or block windows
            for row_a in pool_a_rows:
                for row_b in pool_b_rows:
                    # Match if within same block or close timestamp
                    block_match = row_a.get("block_number") == row_b.get("block_number")
                    time_match = abs(row_a.get("timestamp", 0) - row_b.get("timestamp", 0)) < 60
                    
                    if block_match or time_match:
                        price_a = row_a.get("normalized_price")
                        price_b = row_b.get("normalized_price")
                        
                        if price_a and price_b:
                            delta = compute_price_delta(price_a, price_b)
                            row_a["delta_vs_other_pool"] = delta
                            row_b["delta_vs_other_pool"] = -delta  # Inverse for pool B
    
    # Append to JSONL with fsync
    if rows:
        with open(jsonl_path, "a") as f:
            for row in rows:
                if USE_ORJSON:
                    f.write(orjson.dumps(row).decode("utf-8") + "\n")
                else:
                    f.write(json.dumps(row) + "\n")
            f.flush()
            os.fsync(f.fileno())
        logger.info(f"✓ Appended {len(rows)} rows to {jsonl_path}")
    
    # Check if rotation is needed
    rotated = rotate_jsonl_if_needed(jsonl_path, settings.MAX_ROWS_PER_ROTATION)
    
    # Update metadata
    total_rows = count_jsonl_rows(jsonl_path)
    update_metadata(metadata_path, total_rows, schema_version=settings.SCHEMA_VERSION)
    logger.info(f"✓ Updated metadata: {total_rows} rows")
    
    # Update preview for Hosted Agent and get latest timestamp
    rows_after, preview_latest_ts = update_preview(preview_path, jsonl_path, settings.PREVIEW_ROWS)
    logger.info(f"✓ Updated preview: {preview_path} (latest_ts={preview_latest_ts})")
    
    # Update state with new watermarks
    new_last_seen_ts = max(
        state.get("last_seen_ts", 0),
        stats.get("max_ts_seen", 0),
        preview_latest_ts,
        now_ts
    )
    new_last_seen_block = max(
        state.get("last_seen_block", 0),
        stats.get("max_block_seen", 0),
        to_block
    )
    
    new_state = {
        "last_seen_ts": new_last_seen_ts,
        "last_seen_block": new_last_seen_block,
        "last_published_ts": now_ts,
        "last_updated": datetime.utcnow().isoformat() + "Z",
        "used_logs_path": used_logs_path,
        "pool_tokens": pool_tokens  # Persist pool token cache
    }
    
    # Print cycle summary
    print("")
    print("=" * 60)
    print("CYCLE SUMMARY")
    print("=" * 60)
    print(f"  Strategy: {settings.WINDOW_STRATEGY.upper()}")
    print(f"  Data path: {'LOGS-FIRST' if used_logs_path else 'TRANSACTION-BASED'}")
    if settings.WINDOW_STRATEGY == "timestamp":
        print(f"  Watermark (timestamp): {watermark_ts} ({datetime.fromtimestamp(watermark_ts).isoformat()})")
    else:
        print(f"  Watermark (block): {watermark_block}")
    print(f"  Block range: {from_block} to {to_block}")
    print(f"  Logs fetched: {stats.get('total_logs_fetched', 0)} across {stats.get('pages_fetched', 0)} pages")
    print(f"  Produced rows: {len(rows)}")
    print(f"  Rows: {rows_before} -> {rows_after} (delta: +{rows_after - rows_before})")
    print(f"  Preview latest timestamp: {preview_latest_ts} ({datetime.fromtimestamp(preview_latest_ts).isoformat() if preview_latest_ts > 0 else 'N/A'})")
    print(f"  Early-stop triggered: {stats.get('early_stop_triggered', False)}")
    if stats.get("early_stop_reason"):
        print(f"  Early-stop reason: {stats['early_stop_reason']}")
    print(f"  Dedupe cache size: {len(dedupe.seen)}")
    print(f"  Rotated: {'Yes' if rotated else 'No'}")
    print(f"  New state:")
    print(f"    - last_seen_ts: {new_last_seen_ts}")
    print(f"    - last_seen_block: {new_last_seen_block}")
    print(f"  Files:")
    print(f"    - JSONL: {jsonl_path}")
    print(f"    - Metadata: {metadata_path}")
    print(f"    - Preview: {preview_path}")
    print("=" * 60)
    print("")
    
    return new_state


def main():
    """Main worker loop with HTTP server."""
    global http_server
    
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
    
    # Start HTTP server in background thread
    http_server = ReadOnlyHTTPServer(
        host=settings.WORKER_HTTP_HOST,
        port=settings.WORKER_HTTP_PORT,
        preview_path=settings.PREVIEW_PATH,
        metadata_path=settings.METADATA_PATH
    )
    
    def run_http_server():
        """Run HTTP server in its own event loop."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(http_server.start())
            # Keep the server running
            loop.run_forever()
        except Exception as e:
            logger.error(f"HTTP server error: {e}")
        finally:
            loop.close()
    
    # Start HTTP server in background thread
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()
    
    # Give server time to start
    time.sleep(1)
    
    logger.info("=" * 60)
    logger.info("HTTP ENDPOINTS:")
    logger.info(f"  • http://{settings.WORKER_HTTP_HOST}:{settings.WORKER_HTTP_PORT}/preview")
    logger.info(f"  • http://{settings.WORKER_HTTP_HOST}:{settings.WORKER_HTTP_PORT}/metadata")
    logger.info(f"  • http://{settings.WORKER_HTTP_HOST}:{settings.WORKER_HTTP_PORT}/health")
    logger.info("=" * 60)
    logger.info("")
    logger.info("Test with:")
    logger.info(f"  curl -s http://localhost:{settings.WORKER_HTTP_PORT}/preview | head")
    logger.info(f"  curl -s http://localhost:{settings.WORKER_HTTP_PORT}/metadata | jq")
    logger.info("=" * 60)
    
    # Initialize MCP client
    try:
        client = get_rest_client_from_env(settings)
        logger.info("✓ MCP client created")
        
        # Initialize session in async context
        if settings.MCP_INIT_ON_START:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(client.init_session())
            finally:
                loop.close()
        
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
    
    # Load dedupe tracker
    dedupe_path = Path(settings.LAST_BLOCK_STATE_PATH).parent / "dedupe.json"
    dedupe = DedupeTracker.load(str(dedupe_path))
    
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
    print(f"  Data path: LOGS-FIRST (if available), else TRANSACTION-BASED")
    print(f"  Window strategy: Block-based or age-based (adaptive)")
    print(f"  JSONL output: {data_out_dir / 'dexarb_latest.jsonl'}")
    print(f"  Metadata output: {data_out_dir / 'metadata.json'}")
    print(f"  Preview output: {data_out_dir / 'preview.json'}")
    print(f"  Max rows per file: {settings.MAX_ROWS_PER_ROTATION}")
    print(f"  Deduplication: Enabled (cache size: {len(dedupe.seen)})")
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
                    state = loop.run_until_complete(run_cycle(client, settings, state, dedupe))
                    # Close client to prepare for next event loop
                    loop.run_until_complete(client.close())
                finally:
                    loop.close()
                
                # Persist state and dedupe
                write_state(settings.LAST_BLOCK_STATE_PATH, state)
                logger.info(f"✓ State saved to {settings.LAST_BLOCK_STATE_PATH}")
                
                dedupe.save(str(dedupe_path))
                logger.debug(f"✓ Dedupe saved to {dedupe_path}")
                
            except KeyboardInterrupt:
                raise
            except Exception as e:
                logger.error(f"Error in worker cycle: {e}", exc_info=True)
            
            logger.info(f"Sleeping {settings.WORKER_POLL_SECONDS}s until next cycle...")
            time.sleep(settings.WORKER_POLL_SECONDS)
    
    except KeyboardInterrupt:
        logger.info("Received interrupt, shutting down...")
    finally:
        # Save dedupe one last time
        dedupe.save(str(dedupe_path))
        
        # Close client
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(client.close())
            
            # Stop HTTP server
            if http_server:
                loop.run_until_complete(http_server.stop())
        finally:
            loop.close()
        logger.info("Worker stopped")


if __name__ == "__main__":
    main()
