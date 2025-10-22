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
    USE_ORJSON = False

import json  # Always import json as fallback

from dotenv import load_dotenv

from settings import Settings
from blockscout_rest import BlockscoutRESTClient, get_rest_client_from_env
from transform import normalize_tx, normalize_log_to_swap, compute_price_delta
from state import read_state, write_state, DedupeTracker, RollingPriceBuffer, PreviewStateTracker
from http_server import ReadOnlyHTTPServer
from chainlink_price import fetch_eth_price_from_chainlink, infer_eth_price_from_swaps


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

# Lighthouse Storage integration
try:
    from lighthouse_sdk_integration import LighthouseSDK
    LIGHTHOUSE_AVAILABLE = True
except ImportError as e:
    LIGHTHOUSE_AVAILABLE = False
    logger.warning(f"Lighthouse SDK not available - file upload disabled: {e}")

# Global HTTP server instance for cleanup
http_server: Optional[ReadOnlyHTTPServer] = None


def compute_gas_context(log: Dict[str, Any], client) -> Dict[str, Any]:
    """
    Extract gas context from transaction receipt.
    
    Returns dict with gas_used, effective_gas_price_gwei, gas_cost_eth.
    """
    gas_context = {
        "gas_used": 0,
        "effective_gas_price_gwei": 0.0,
        "gas_cost_eth": 0.0
    }
    
    # In a full implementation, we would fetch the transaction receipt
    # For now, return placeholder values
    # TODO: Implement via client.get_transaction_receipt(tx_hash)
    
    return gas_context


def estimate_usd_value(
    token_in_symbol: str,
    token_out_symbol: str,
    amount_in_normalized: str,
    amount_out_normalized: str,
    eth_price_usd: float
) -> Dict[str, Any]:
    """
    Estimate USD value of swap using stablecoin detection or ETH reference price.
    
    Returns dict with swap_value_usd and value_method (e.g., "USDC", "WETH_est", etc.)
    """
    stablecoins = {"USDC", "USDCE", "USDT", "DAI"}
    
    # Check if token_in is a stablecoin
    if token_in_symbol in stablecoins:
        try:
            value = float(amount_in_normalized)
            return {"swap_value_usd": value, "value_method": token_in_symbol}
        except:
            pass
    
    # Check if token_out is a stablecoin
    if token_out_symbol in stablecoins:
        try:
            value = float(amount_out_normalized)
            return {"swap_value_usd": value, "value_method": token_out_symbol}
        except:
            pass
    
    # Check for WETH and estimate using reference price
    if token_in_symbol in {"WETH", "ETH"}:
        try:
            eth_amount = float(amount_in_normalized)
            value = eth_amount * eth_price_usd
            return {"swap_value_usd": value, "value_method": "WETH_est"}
        except:
            pass
    
    if token_out_symbol in {"WETH", "ETH"}:
        try:
            eth_amount = float(amount_out_normalized)
            value = eth_amount * eth_price_usd
            return {"swap_value_usd": value, "value_method": "WETH_est"}
        except:
            pass
    
    return {"swap_value_usd": 0.0, "value_method": "unknown"}


def enrich_row_with_analytics(
    row: Dict[str, Any],
    price_buffer: RollingPriceBuffer,
    preview_state: PreviewStateTracker,
    eth_price_usd: float,
    client,
    enable_emoji: bool = True
) -> Dict[str, Any]:
    """
    Enrich a swap row with comprehensive analytics and visual markers.
    
    Adds:
    - delta_vs_ma: Price delta vs 5-swap moving average
    - gas_used, effective_gas_price_gwei, gas_cost_eth, gas_cost_usd
    - swap_value_usd, value_method
    - price_impact_vs_buffer: % deviation from rolling median
    - mev_warning: Flag for abnormal price deviations (>2 stddev)
    - is_new: Visual marker for first-time appearance
    - emoji_marker: Visual indicator (🔥 NEW, ⭐ LARGE, ⚡ FAST, etc.)
    """
    enriched = row.copy()
    
    # Compute delta vs moving average
    pool_id = row.get("pool_id", "")
    normalized_price = row.get("normalized_price")
    tx_hash = row.get("tx_hash", "")
    
    if normalized_price and pool_id:
        ma5 = price_buffer.get_moving_average(pool_id, window=5)
        if ma5 > 0:
            delta_vs_ma = ((normalized_price - ma5) / ma5) * 100.0
            enriched["delta_vs_ma"] = round(delta_vs_ma, 2)
            
            # MEV warning: flag swaps >2 stddev from average
            if abs(delta_vs_ma) > 10.0:  # Simplified: >10% deviation
                enriched["mev_warning"] = f"⚠️  Price {abs(delta_vs_ma):.1f}% from MA"
        else:
            enriched["delta_vs_ma"] = 0.0
    else:
        enriched["delta_vs_ma"] = 0.0
    
    # Gas context (placeholder for now)
    gas_context = compute_gas_context(row, client)
    enriched.update(gas_context)
    
    # Gas cost in USD
    enriched["gas_cost_usd"] = round(gas_context["gas_cost_eth"] * eth_price_usd, 2)
    
    # USD value estimate
    usd_estimate = estimate_usd_value(
        row.get("token_in_symbol", ""),
        row.get("token_out_symbol", ""),
        row.get("amount_in_normalized", "0"),
        row.get("amount_out_normalized", "0"),
        eth_price_usd
    )
    enriched.update(usd_estimate)
    
    # NEW marker detection
    is_new = preview_state.is_new(tx_hash)
    enriched["is_new"] = is_new
    
    # Emoji marker logic (visual enhancement)
    if enable_emoji:
        swap_value = usd_estimate.get("swap_value_usd", 0)
        
        if is_new:
            enriched["emoji_marker"] = "🔥"  # NEW swap
        elif swap_value > 10000:
            enriched["emoji_marker"] = "💎"  # WHALE trade
        elif swap_value > 1000:
            enriched["emoji_marker"] = "⭐"  # LARGE trade
        elif abs(enriched.get("delta_vs_ma", 0)) > 5:
            enriched["emoji_marker"] = "⚡"  # VOLATILE price
        else:
            enriched["emoji_marker"] = "•"  # Normal
    
    return enriched


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
                
                # Transform each log (BEFORE early-stop check so we process the current page)
                logger.debug(f"Processing {len(logs)} logs from page {page_count}")
                for idx, log in enumerate(logs):
                    tx_hash = log.get("transaction_hash") or log.get("transactionHash") or ""
                    log_index = log.get("log_index") or log.get("logIndex") or 0
                    
                    logger.debug(f"  Processing log {idx+1}/{len(logs)}: {tx_hash[:10]}:{log_index}")
                    
                    # Check for duplicate
                    if dedupe.is_duplicate(tx_hash, log_index):
                        logger.debug(f"  Skipping duplicate: {tx_hash}:{log_index}")
                        continue
                    
                    block_num = log.get("block_number") or log.get("blockNumber") or 0
                    
                    try:
                        logger.debug(f"  Calling normalize_log_to_swap for {tx_hash[:10]}")
                        row = await normalize_log_to_swap(log, autoscout_base, pool_tokens, client, block_num)
                        if row:
                            logger.info(f"  ✓ Normalized log {tx_hash[:10]} to swap row")
                            all_rows.append(row)
                            dedupe.mark_seen(tx_hash, log_index)
                        else:
                            logger.debug(f"  normalize_log_to_swap returned None for {tx_hash[:10]}")
                    except Exception as e:
                        logger.error(f"  Error normalizing log {tx_hash}:{log_index}: {e}", exc_info=True)
                        continue
                
                # NOW check early-stop AFTER processing the current page
                if log_timestamps:
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
    DEPRECATED: Use apply_rolling_window_pruning() instead for atomic rolling window.
    
    Rotate JSONL file if it exceeds max_rows by renaming with timestamp.
    This creates archive files but doesn't implement a rolling window.
    
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


def apply_rolling_window_pruning(
    file_path: Path,
    window_size: int,
    dedupe_tracker: Optional[DedupeTracker] = None
) -> dict:
    """
    Apply rolling window pruning to keep only the latest N rows in JSONL file.
    
    This function:
    1. Reads all rows from the file
    2. Keeps only the latest window_size rows (sorted by timestamp desc)
    3. Atomically writes back via temp file + os.replace
    4. Optionally prunes dedupe tracker to match the window
    5. Returns stats about the pruning operation
    
    Args:
        file_path: Path to the JSONL file
        window_size: Maximum number of rows to keep
        dedupe_tracker: Optional dedupe tracker to prune in sync
        
    Returns:
        Dict with keys: total_before, total_after, rows_dropped, oldest_ts, newest_ts, oldest_block, newest_block
    """
    if not file_path.exists():
        return {
            "total_before": 0,
            "total_after": 0,
            "rows_dropped": 0,
            "oldest_ts": None,
            "newest_ts": None,
            "oldest_block": None,
            "newest_block": None
        }
    
    # Read all rows
    rows = []
    with open(file_path, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    if USE_ORJSON:
                        rows.append(orjson.loads(line))
                    else:
                        rows.append(json.loads(line))
                except Exception as e:
                    logger.warning(f"Skipping malformed JSONL row: {e}")
    
    total_before = len(rows)
    
    # If within window, no pruning needed
    if total_before <= window_size:
        return {
            "total_before": total_before,
            "total_after": total_before,
            "rows_dropped": 0,
            "oldest_ts": min((r.get("timestamp", 0) for r in rows), default=None) if rows else None,
            "newest_ts": max((r.get("timestamp", 0) for r in rows), default=None) if rows else None,
            "oldest_block": min((r.get("block_number", 0) for r in rows), default=None) if rows else None,
            "newest_block": max((r.get("block_number", 0) for r in rows), default=None) if rows else None
        }
    
    # Sort by timestamp descending (newest first), then by block_number as tiebreaker
    rows.sort(key=lambda r: (r.get("timestamp", 0), r.get("block_number", 0)), reverse=True)
    
    # Keep only the latest window_size rows
    kept_rows = rows[:window_size]
    dropped_rows = rows[window_size:]
    
    # Extract stats
    oldest_ts = min((r.get("timestamp", 0) for r in kept_rows), default=None) if kept_rows else None
    newest_ts = max((r.get("timestamp", 0) for r in kept_rows), default=None) if kept_rows else None
    oldest_block = min((r.get("block_number", 0) for r in kept_rows), default=None) if kept_rows else None
    newest_block = max((r.get("block_number", 0) for r in kept_rows), default=None) if kept_rows else None
    
    # Atomic write via temp file
    temp_path = file_path.with_suffix(".jsonl.tmp")
    try:
        with open(temp_path, "w") as f:
            for row in kept_rows:
                if USE_ORJSON:
                    f.write(orjson.dumps(row).decode("utf-8") + "\n")
                else:
                    f.write(json.dumps(row) + "\n")
            f.flush()
            os.fsync(f.fileno())
        
        # Atomic replace
        temp_path.replace(file_path)
        logger.info(f"Rolling prune: dropped {len(dropped_rows)} old swaps, latest rows now: {len(kept_rows)}")
        
    except Exception as e:
        logger.error(f"Failed to apply rolling window pruning: {e}")
        if temp_path.exists():
            temp_path.unlink()
        raise
    
    # Prune dedupe tracker if provided
    if dedupe_tracker and dropped_rows:
        # Remove entries for dropped rows
        dropped_keys = {
            f"{r.get('tx_hash', '')}:{r.get('log_index', 0)}"
            for r in dropped_rows
        }
        dedupe_tracker.prune(dropped_keys)
        logger.debug(f"Pruned {len(dropped_keys)} entries from dedupe tracker")
    
    return {
        "total_before": total_before,
        "total_after": len(kept_rows),
        "rows_dropped": len(dropped_rows),
        "oldest_ts": oldest_ts,
        "newest_ts": newest_ts,
        "oldest_block": oldest_block,
        "newest_block": newest_block
    }


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
    
    # Compute freshness and preserve existing lighthouse fields
    freshness_minutes = 0
    existing_cid = None
    existing_lighthouse_fields = {}
    
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
                
                # Preserve Lighthouse fields from previous update
                existing_cid = existing.get("latest_cid")
                if existing.get("lighthouse_gateway"):
                    existing_lighthouse_fields["lighthouse_gateway"] = existing["lighthouse_gateway"]
                if existing.get("lighthouse_updated"):
                    existing_lighthouse_fields["lighthouse_updated"] = existing["lighthouse_updated"]
                if existing.get("encryption"):
                    existing_lighthouse_fields["encryption"] = existing["encryption"]
                if existing.get("last_lighthouse_upload"):
                    existing_lighthouse_fields["last_lighthouse_upload"] = existing["last_lighthouse_upload"]
        except Exception as e:
            logger.debug(f"Could not read existing metadata: {e}")
    
    metadata = {
        "schema_version": schema_version,
        "last_updated": last_updated_iso,
        "rows": row_count,
        "freshness_minutes": freshness_minutes,
        "latest_cid": existing_cid,  # Preserve existing CID instead of resetting to None
        "format": "jsonl",
        "fields": fields
    }
    
    # Add back preserved Lighthouse fields
    metadata.update(existing_lighthouse_fields)
    
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


async def upload_to_lighthouse_and_cleanup(
    jsonl_path: Path,
    metadata_path: Path,
    settings: Settings,
    last_upload_time: Optional[float] = None
) -> tuple[Optional[str], float]:
    """
    Upload the latest JSONL file to Lighthouse periodically (not every cycle).
    
    Args:
        last_upload_time: Unix timestamp of last upload (None = force upload)
    
    Returns:
        Tuple of (new_cid, current_time) - CID is None if skipped/failed
    """
    current_time = time.time()
    
    # Skip if upload disabled or API key not set
    if not settings.LIGHTHOUSE_ENABLE_UPLOAD:
        logger.debug("Lighthouse upload disabled (LIGHTHOUSE_ENABLE_UPLOAD=False)")
        return None, current_time
    
    if not settings.LIGHTHOUSE_API_KEY:
        logger.warning("Lighthouse upload enabled but LIGHTHOUSE_API_KEY not set")
        return None, current_time
    
    if not LIGHTHOUSE_AVAILABLE:
        logger.warning("Lighthouse SDK not available - cannot upload")
        return None, current_time
    
    # Check if enough time has passed since last upload
    if last_upload_time is not None:
        time_since_last = current_time - last_upload_time
        if time_since_last < settings.LIGHTHOUSE_UPLOAD_INTERVAL:
            logger.debug(f"Skipping upload - {time_since_last:.0f}s since last upload (interval: {settings.LIGHTHOUSE_UPLOAD_INTERVAL}s)")
            return None, last_upload_time  # Return old time since we didn't upload
    
    try:
        # Initialize Lighthouse SDK with timeout
        lighthouse = LighthouseSDK(
            api_key=settings.LIGHTHOUSE_API_KEY,
            upload_timeout=settings.LIGHTHOUSE_UPLOAD_TIMEOUT
        )
        
        # Get old CID from metadata to delete later
        old_cid = None
        if metadata_path.exists():
            try:
                with open(metadata_path, "r") as f:
                    metadata = json.load(f)
                    old_cid = metadata.get("latest_cid")
            except Exception as e:
                logger.debug(f"Could not read old CID from metadata: {e}")
        
        # Upload new file (encrypted) - run in executor since it's blocking
        logger.info(f"📤 Uploading {jsonl_path.name} to Lighthouse (timeout: {settings.LIGHTHOUSE_UPLOAD_TIMEOUT}s)...")
        upload_start = time.time()
        
        # Run blocking upload in thread pool executor with timeout
        loop = asyncio.get_event_loop()
        try:
            result = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: lighthouse.encrypt_and_upload(
                        input_path=jsonl_path,
                        tag=f"dexarb_{settings.NETWORK_LABEL}",
                        keep_encrypted=False  # Don't keep .enc file
                    )
                ),
                timeout=settings.LIGHTHOUSE_UPLOAD_TIMEOUT
            )
        except asyncio.TimeoutError:
            upload_duration = time.time() - upload_start
            logger.error(f"❌ Lighthouse upload timed out after {upload_duration:.1f}s")
            logger.error(f"   Tip: Increase LIGHTHOUSE_UPLOAD_TIMEOUT or disable with LIGHTHOUSE_ENABLE_UPLOAD=false")
            return None, current_time
        except Exception as e:
            upload_duration = time.time() - upload_start
            logger.error(f"❌ Lighthouse upload failed after {upload_duration:.1f}s: {e}")
            return None, current_time
        
        upload_duration = time.time() - upload_start
        
        # Extract CID from nested result
        upload_data = result.get("upload", {})
        new_cid = upload_data.get("cid")
        
        if new_cid:
            logger.info(f"✅ Lighthouse upload successful in {upload_duration:.2f}s")
            logger.info(f"   CID: {new_cid}")
            logger.info(f"   View: https://files.lighthouse.storage/viewFile/{new_cid}")
            
            # Update metadata with rich details (CID, encryption stats, gateway URL)
            # CRITICAL: Always update metadata, create if missing
            try:
                # Try to read existing metadata
                metadata = {}
                if metadata_path.exists():
                    try:
                        with open(metadata_path, "r") as f:
                            # Use standard json to avoid orjson compatibility issues
                            metadata = json.load(f)
                        logger.debug(f"Read existing metadata: {len(metadata)} fields")
                    except Exception as read_error:
                        logger.warning(f"Could not read metadata, will recreate: {read_error}")
                        metadata = {}
                else:
                    logger.warning(f"Metadata file doesn't exist yet, creating with CID")
                
                # Add Lighthouse fields with full details
                metadata["latest_cid"] = new_cid
                metadata["lighthouse_gateway"] = f"https://gateway.lighthouse.storage/ipfs/{new_cid}"
                metadata["lighthouse_updated"] = datetime.utcnow().isoformat() + "Z"
                
                # Add encryption stats if available
                encryption_data = result.get("encryption", {})
                if encryption_data:
                    metadata["encryption"] = {
                        "enabled": True,
                        "algorithm": "AES-256-GCM",
                        "encrypted_file": f"{jsonl_path.name}.enc",
                        "encrypted_size": encryption_data.get("encrypted_size", 0),
                        "original_size": encryption_data.get("original_size", 0),
                        "sha256_encrypted": encryption_data.get("sha256_encrypted", "")[:20] + "...",
                        "sha256_original": encryption_data.get("sha256_original", "")[:20] + "...",
                        "status": "Encrypted and uploaded successfully"
                    }
                
                metadata["last_lighthouse_upload"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
                
                # Atomic write with fsync
                temp_path = metadata_path.with_suffix(".json.tmp")
                with open(temp_path, "w") as f:
                    # Always use standard json for metadata (more compatible)
                    json.dump(metadata, f, indent=2)
                    f.flush()
                    os.fsync(f.fileno())
                temp_path.replace(metadata_path)
                logger.info(f"✓ Metadata updated with CID: {new_cid}")
                logger.info(f"  Gateway: {metadata['lighthouse_gateway']}")
            except Exception as e:
                logger.error(f"❌ Failed to update metadata with CID: {e}")
                import traceback
                logger.error(traceback.format_exc())
            
            # Auto-cleanup: Delete old files, keep only latest
            try:
                from lighthouse_cleanup import cleanup_lighthouse_storage
                
                logger.info("🧹 Running automatic cleanup...")
                cleanup_result = cleanup_lighthouse_storage(
                    api_key=settings.LIGHTHOUSE_API_KEY,
                    protected_cid=new_cid,
                    dry_run=False
                )
                
                if cleanup_result["success"]:
                    if cleanup_result["files_deleted"] > 0:
                        logger.info(
                            f"✅ Cleanup: Deleted {cleanup_result['files_deleted']} old files "
                            f"({cleanup_result['space_saved_mb']:.2f} MB saved)"
                        )
                    else:
                        logger.debug("✅ Cleanup: No old files to delete")
                else:
                    logger.warning(f"⚠️  Cleanup failed: {cleanup_result.get('error', 'Unknown')}")
            except ImportError:
                logger.warning("⚠️  Cleanup module not available - old files not deleted")
            except Exception as e:
                logger.error(f"❌ Cleanup error: {e}")
            
            return new_cid, current_time
        else:
            logger.error("Lighthouse upload failed - no CID returned")
            return None, current_time
            
    except Exception as e:
        logger.error(f"Lighthouse upload error: {e}", exc_info=True)
        return None, current_time


def update_preview_with_analytics(
    preview_path: Path,
    jsonl_path: Path,
    preview_rows: int,
    price_buffer: RollingPriceBuffer,
    preview_state: PreviewStateTracker,
    pool_addresses: List[str],
    window_minutes: int,
    eth_price_usd: float,
    autoscout_base: str,
    client,
    enable_emoji: bool = True,
    enable_spread_alerts: bool = True
) -> tuple[int, int]:
    """
    Update preview.json with latest N rows and DYNAMIC header metrics + ARB ALERTS.
    
    Implements:
    - Sort by timestamp desc (newest first)
    - Bias selection toward new tx_hashes
    - Header with updated_ago_seconds, activity_swaps_per_min, spread_percent
    - Enriched rows with delta_vs_ma, gas context, USD estimates, visual markers
    - Cross-pool arbitrage opportunity detection
    - Trend indicators (price rising/falling)
    
    Returns:
        Tuple of (total_rows, latest_timestamp)
    """
    now_utc = datetime.utcnow()
    now_ts = int(time.time())
    
    if not jsonl_path.exists():
        preview = {
            "header": {
                "updated_ago_seconds": 0,
                "window_minutes": window_minutes,
                "activity_swaps_per_min": 0.0,
                "pool_ids": pool_addresses,
                "spread_percent": None,
                "spread_reason": "no data",
                "status_emoji": "⏸️",
                "alert": None
            },
            "preview_rows": [],
            "total_rows": 0,
            "last_updated": now_utc.isoformat() + "Z"
        }
        latest_ts = 0
    else:
        # Read all rows from JSONL
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
        
        # Sort by timestamp desc (newest first)
        rows.sort(key=lambda r: r.get("timestamp", 0), reverse=True)
        
        # Bias selection: prefer new tx_hashes
        new_rows = [r for r in rows if preview_state.is_new(r.get("tx_hash", ""))]
        
        # Select at least K=2 new rows if available, otherwise newest rows
        min_new = 2
        if len(new_rows) >= min_new:
            selected = new_rows[:preview_rows]
        else:
            # Mix new and newest
            selected = new_rows + [r for r in rows if r not in new_rows]
            selected = selected[:preview_rows]
        
        # Enrich selected rows with analytics
        enriched_rows = []
        for row in selected:
            enriched = enrich_row_with_analytics(
                row, price_buffer, preview_state, eth_price_usd, client, enable_emoji
            )
            enriched_rows.append(enriched)
        
        # Compute delta_vs_prev_row for sequential price changes
        for i in range(len(enriched_rows) - 1):
            current_price = enriched_rows[i].get("normalized_price")
            prev_price = enriched_rows[i + 1].get("normalized_price")
            
            if current_price and prev_price and prev_price > 0:
                delta_pct = ((current_price - prev_price) / prev_price) * 100.0
                enriched_rows[i]["delta_vs_prev_row"] = round(delta_pct, 3)
        
        # Update preview state tracker
        preview_tx_hashes = [r.get("tx_hash", "") for r in enriched_rows]
        preview_state.update(preview_tx_hashes)
        
        # Get latest timestamp
        latest_ts = max((row.get("timestamp", 0) for row in enriched_rows), default=0)
        
        # Compute header metrics
        updated_ago_seconds = now_ts - latest_ts if latest_ts > 0 else 0
        
        # Activity: swaps per minute over window
        cutoff_ts = now_ts - (window_minutes * 60)
        recent_swaps = [r for r in rows if r.get("timestamp", 0) >= cutoff_ts]
        
        if recent_swaps and len(recent_swaps) > 1:
            time_span = max(r.get("timestamp", 0) for r in recent_swaps) - min(r.get("timestamp", 0) for r in recent_swaps)
            if time_span > 0:
                activity_swaps_per_min = (len(recent_swaps) / time_span) * 60.0
            else:
                activity_swaps_per_min = 0.0
        else:
            activity_swaps_per_min = 0.0
        
        # Spread: compute price difference between pools + ARB ALERT
        spread_percent = None
        spread_reason = None
        arb_alert = None
        
        if len(pool_addresses) == 2 and enable_spread_alerts:
            price_a = price_buffer.get_latest_price(pool_addresses[0], max_age_seconds=600)
            price_b = price_buffer.get_latest_price(pool_addresses[1], max_age_seconds=600)
            
            if price_a > 0 and price_b > 0:
                spread_percent = ((price_a - price_b) / price_b) * 100.0
                spread_percent = round(spread_percent, 2)
                
                # ARB OPPORTUNITY ALERT (>0.5% spread is tradeable)
                if abs(spread_percent) > 0.5:
                    direction = "PoolA→PoolB" if spread_percent > 0 else "PoolB→PoolA"
                    arb_alert = f"🎯 ARB OPPORTUNITY: {direction} +{abs(spread_percent):.2f}%"
            elif price_a == 0 and price_b == 0:
                spread_reason = "no recent prices for either pool"
            elif price_a == 0:
                spread_reason = "no recent price for pool A"
            elif price_b == 0:
                spread_reason = "no recent price for pool B"
        else:
            spread_reason = "requires exactly 2 pools"
        
        # Status emoji based on activity
        if activity_swaps_per_min > 1.0:
            status_emoji = "🚀"  # High activity
        elif activity_swaps_per_min > 0.1:
            status_emoji = "✅"  # Active
        elif updated_ago_seconds < 60:
            status_emoji = "🟢"  # Recent update
        elif updated_ago_seconds < 300:
            status_emoji = "🟡"  # Slightly stale
        else:
            status_emoji = "🔴"  # Stale
        
        # Price trend (simple: compare first and last row prices)
        price_trend = None
        if len(enriched_rows) >= 2:
            first_price = enriched_rows[0].get("normalized_price")
            last_price = enriched_rows[-1].get("normalized_price")
            if first_price and last_price and last_price > 0:
                trend_pct = ((first_price - last_price) / last_price) * 100.0
                if abs(trend_pct) > 1.0:
                    price_trend = f"{'📈' if trend_pct > 0 else '📉'} {trend_pct:+.2f}%"
        
        # Build header with RICH metrics
        header = {
            "updated_ago_seconds": updated_ago_seconds,
            "window_minutes": window_minutes,
            "activity_swaps_per_min": round(activity_swaps_per_min, 2),
            "pool_ids": pool_addresses,
            "spread_percent": spread_percent,
            "status_emoji": status_emoji,
            "activity_ring": f"{len(recent_swaps)} swaps/{window_minutes}min | Updated {updated_ago_seconds}s ago"
        }
        
        if spread_reason:
            header["spread_reason"] = spread_reason
        if arb_alert:
            header["alert"] = arb_alert
        if price_trend:
            header["price_trend"] = price_trend
        
        preview = {
            "header": header,
            "preview_rows": enriched_rows,
            "total_rows": len(rows),
            "last_updated": now_utc.isoformat() + "Z"
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


async def run_cycle(
    client: BlockscoutRESTClient,
    settings: Settings,
    state: Dict[str, Any],
    dedupe: DedupeTracker,
    price_buffer: RollingPriceBuffer,
    preview_state: PreviewStateTracker,
    last_upload_time: Optional[float] = None
) -> tuple[Dict[str, Any], float]:
    """
    Run one ingestion cycle with logs-first path, pool resolution, and early-stop guards.
    
    Args:
        last_upload_time: Unix timestamp of last Lighthouse upload
    
    Returns:
        Tuple of (updated_state, new_last_upload_time)
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
        return state, last_upload_time
    
    # Fetch ETH/USD price from Chainlink or infer from recent swaps
    eth_price_info = await fetch_eth_price_from_chainlink(
        chain_id=settings.CHAIN_ID,
        client=client,
        fallback_price=settings.REFERENCE_ETH_PRICE_USD
    )
    eth_price_usd = eth_price_info["price"]
    
    # If using fallback, try to infer from recent swaps
    if eth_price_info["source"].startswith("fallback") and jsonl_path.exists():
        try:
            with open(jsonl_path, "r") as f:
                recent_lines = f.readlines()[-50:]  # Last 50 swaps
                if USE_ORJSON:
                    recent_swaps = [orjson.loads(line) for line in recent_lines]
                else:
                    recent_swaps = [json.loads(line) for line in recent_lines]
                inferred_price = infer_eth_price_from_swaps(recent_swaps)
                
                if inferred_price:
                    eth_price_usd = inferred_price
                    logger.info(f"ETH price: ${eth_price_usd:.2f} (source: inferred_from_swaps)")
                else:
                    logger.warning(f"ETH price: ${eth_price_usd:.2f} (source: {eth_price_info['source']}) - {eth_price_info.get('warning', 'No warning')}")
        except Exception as e:
            logger.warning(f"Could not infer ETH price from swaps: {e}")
            logger.warning(f"ETH price: ${eth_price_usd:.2f} (source: {eth_price_info['source']})")
    else:
        # Log price source
        if eth_price_info.get("warning"):
            logger.warning(f"ETH price: ${eth_price_usd:.2f} (source: {eth_price_info['source']}) - {eth_price_info['warning']}")
        else:
            logger.info(f"ETH price: ${eth_price_usd:.2f} (source: {eth_price_info['source']})")
    
    if eth_price_info["feed_address"]:
        logger.debug(f"Chainlink feed address: {eth_price_info['feed_address']}")
    
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
    
    # Update rolling price buffer with new rows
    for row in rows:
        normalized_price = row.get("normalized_price")
        pool_id = row.get("pool_id", "")
        timestamp = row.get("timestamp", 0)
        
        if normalized_price and pool_id and timestamp:
            price_buffer.add_price(pool_id, normalized_price, timestamp)
    
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
    
    # Apply rolling window pruning if needed
    prune_stats = apply_rolling_window_pruning(
        file_path=jsonl_path,
        window_size=settings.ROLLING_WINDOW_SIZE,
        dedupe_tracker=dedupe
    )
    
    # Prune price buffer to match rolling window
    if prune_stats["oldest_ts"]:
        price_buffer.prune_by_timestamp(prune_stats["oldest_ts"])
    
    # Update metadata
    total_rows = prune_stats["total_after"]
    update_metadata(metadata_path, total_rows, schema_version=settings.SCHEMA_VERSION)
    logger.info(f"✓ Updated metadata: {total_rows} rows")
    
    # Upload to Lighthouse (if enabled and interval passed)
    lighthouse_cid, last_upload_time = await upload_to_lighthouse_and_cleanup(
        jsonl_path=jsonl_path,
        metadata_path=metadata_path,
        settings=settings,
        last_upload_time=last_upload_time
    )
    if lighthouse_cid:
        logger.info(f"✓ Lighthouse CID: {lighthouse_cid}")
    
    # Update preview with analytics
    rows_after, preview_latest_ts = update_preview_with_analytics(
        preview_path=preview_path,
        jsonl_path=jsonl_path,
        preview_rows=settings.PREVIEW_ROWS,
        price_buffer=price_buffer,
        preview_state=preview_state,
        pool_addresses=pool_addresses,
        window_minutes=settings.WINDOW_MINUTES,
        eth_price_usd=eth_price_usd,  # Use live/inferred price instead of static
        autoscout_base=settings.AUTOSCOUT_BASE or "https://eth-sepolia.blockscout.com",
        client=client,
        enable_emoji=settings.ENABLE_EMOJI_MARKERS,
        enable_spread_alerts=settings.ENABLE_SPREAD_ALERTS
    )
    logger.info(f"✓ Updated preview: {preview_path} (latest_ts={preview_latest_ts})")
    
    # Read preview to get header for summary
    preview_header = {}
    sample_row = {}
    if preview_path.exists():
        try:
            with open(preview_path, "r") as f:
                preview_data = json.load(f) if not USE_ORJSON else orjson.loads(f.read())
                preview_header = preview_data.get("header", {})
                preview_rows_list = preview_data.get("preview_rows", [])
                if preview_rows_list:
                    sample_row = preview_rows_list[0]
        except Exception as e:
            logger.warning(f"Could not read preview header: {e}")
    
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
    
    # Print cycle summary with VALIDATION
    print("")
    print("=" * 80)
    print("🔄 CYCLE SUMMARY - HACKATHON DEMO OPTIMIZED")
    print("=" * 80)
    print(f"  Network: {settings.NETWORK_LABEL or 'Unknown'} (Chain {settings.CHAIN_ID})")
    print(f"  Strategy: {settings.WINDOW_STRATEGY.upper()}")
    print(f"  Data path: {'🎯 LOGS-FIRST (optimal)' if used_logs_path else '⚠️  TRANSACTION-BASED (fallback)'}")
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
    
    # Print rolling window stats
    if prune_stats["rows_dropped"] > 0:
        print(f"  Rolling window: dropped {prune_stats['rows_dropped']} old swaps")
        print(f"    - Window size: {prune_stats['total_after']}/{settings.ROLLING_WINDOW_SIZE} rows")
        print(f"    - Oldest: block {prune_stats['oldest_block']} (ts {prune_stats['oldest_ts']})")
        print(f"    - Newest: block {prune_stats['newest_block']} (ts {prune_stats['newest_ts']})")
    else:
        print(f"  Rolling window: {prune_stats['total_after']}/{settings.ROLLING_WINDOW_SIZE} rows (no pruning needed)")
    
    print(f"  New state:")
    print(f"    - last_seen_ts: {new_last_seen_ts}")
    print(f"    - last_seen_block: {new_last_seen_block}")
    print("")
    
    # VALIDATION CHECKS
    validation_status = "PASS"
    validation_warnings = []
    
    # Check 1: Were new rows produced?
    if rows_after - rows_before < settings.MIN_SWAPS_PER_CYCLE:
        validation_warnings.append(f"⚠️  Insufficient activity: only {rows_after - rows_before} new swaps (min: {settings.MIN_SWAPS_PER_CYCLE})")
        validation_status = "WARN"
    
    # Check 2: Is data fresh?
    if preview_latest_ts > 0:
        staleness = now_ts - preview_latest_ts
        if staleness > settings.STALE_THRESHOLD_SECONDS:
            validation_warnings.append(f"⚠️  Stale data: latest swap is {staleness}s old (threshold: {settings.STALE_THRESHOLD_SECONDS}s)")
            validation_status = "WARN"
    
    # Check 3: Did preview change?
    if rows_after > 0 and preview_latest_ts == state.get("last_preview_ts", 0):
        validation_warnings.append(f"⚠️  Preview unchanged between cycles - possible data stagnation")
        validation_status = "WARN"
    
    print("📊 PREVIEW HEADER:")
    print(f"  {preview_header.get('status_emoji', '•')} {preview_header.get('activity_ring', 'N/A')}")
    print(f"  Activity: {preview_header.get('activity_swaps_per_min', 0):.2f} swaps/min")
    print(f"  Spread: {preview_header.get('spread_percent', 'N/A')}%")
    if preview_header.get('alert'):
        print(f"  {preview_header.get('alert')}")
    if preview_header.get('price_trend'):
        print(f"  Trend: {preview_header.get('price_trend')}")
    if preview_header.get('spread_reason'):
        print(f"  Spread note: {preview_header.get('spread_reason')}")
    print("")
    
    if sample_row:
        print("💎 SAMPLE ENRICHED ROW:")
        print(f"  {sample_row.get('emoji_marker', '•')} tx_hash: {sample_row.get('tx_hash', 'N/A')[:16]}...")
        print(f"  timestamp: {sample_row.get('timestamp', 'N/A')} ({datetime.fromtimestamp(sample_row.get('timestamp', 0)).isoformat() if sample_row.get('timestamp') else 'N/A'})")
        print(f"  {sample_row.get('token_in_symbol', '?')} → {sample_row.get('token_out_symbol', '?')}")
        print(f"  Amount: {sample_row.get('amount_in_normalized', '0')[:10]} → {sample_row.get('amount_out_normalized', '0')[:10]}")
        print(f"  Normalized price: {sample_row.get('normalized_price', 'N/A')}")
        print(f"  Delta vs MA: {sample_row.get('delta_vs_ma', 'N/A')}%")
        if sample_row.get('delta_vs_prev_row') is not None:
            print(f"  Delta vs prev: {sample_row.get('delta_vs_prev_row', 'N/A')}%")
        print(f"  Swap value: ${sample_row.get('swap_value_usd', 0):.2f} ({sample_row.get('value_method', 'unknown')})")
        print(f"  Gas: {sample_row.get('gas_used', 0)} @ {sample_row.get('effective_gas_price_gwei', 0)} gwei = ${sample_row.get('gas_cost_usd', 0):.2f}")
        if sample_row.get('mev_warning'):
            print(f"  {sample_row.get('mev_warning')}")
        print(f"  New: {'🔥 YES' if sample_row.get('is_new') else 'No'}")
        print(f"  Explorer: {sample_row.get('explorer_link', 'N/A')[:70]}...")
    print("")
    
    # Print validation results
    if validation_status == "PASS":
        print("✅ VALIDATION: PASS - Dynamic and Useful Data")
    else:
        print(f"⚠️  VALIDATION: {validation_status}")
        for warning in validation_warnings:
            print(f"    {warning}")
        
        # Suggest alternatives if pools are quiet
        if rows_after - rows_before == 0:
            print("")
            print("💡 SUGGESTED ACTIONS:")
            print("  1. Switch to Ethereum Mainnet with active pools:")
            print("     - Uniswap V2 Router: 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D")
            print("     - Uniswap V3 Router: 0xE592427A0AEce92De3Edee1F18E0157C05861564")
            print("  2. Use active pairs like ETH/USDC or ETH/USDT")
            print("  3. Reduce WINDOW_MINUTES to 1-2 for faster catchup")
            print("  4. Check Etherscan to confirm pool has recent swaps")
    
    print(f"\n  📁 Files:")
    print(f"    - JSONL: {jsonl_path}")
    print(f"    - Metadata: {metadata_path}")
    print(f"    - Preview: {preview_path}")
    print("=" * 80)
    print("")
    
    # Update state with preview timestamp for staleness detection
    new_state["last_preview_ts"] = preview_latest_ts
    
    return new_state, last_upload_time


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
    
    # Load price buffer for moving averages
    price_buffer_path = Path(settings.LAST_BLOCK_STATE_PATH).parent / "price_buffer.json"
    price_buffer = RollingPriceBuffer.load(str(price_buffer_path), max_size=20)
    
    # Load preview state tracker
    preview_state_path = Path(settings.LAST_BLOCK_STATE_PATH).parent / "preview_state.json"
    preview_state = PreviewStateTracker.load(str(preview_state_path), max_size=10)
    
    # Track last upload time to avoid uploading every cycle
    last_upload_time = None
    
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
                    state, last_upload_time = loop.run_until_complete(run_cycle(
                        client, settings, state, dedupe, price_buffer, preview_state, last_upload_time
                    ))
                    # Close client to prepare for next event loop
                    loop.run_until_complete(client.close())
                finally:
                    loop.close()
                
                # Persist state, dedupe, price buffer, and preview state
                write_state(settings.LAST_BLOCK_STATE_PATH, state)
                logger.info(f"✓ State saved to {settings.LAST_BLOCK_STATE_PATH}")
                
                dedupe.save(str(dedupe_path))
                logger.debug(f"✓ Dedupe saved to {dedupe_path}")
                
                price_buffer.save(str(price_buffer_path))
                logger.debug(f"✓ Price buffer saved to {price_buffer_path}")
                
                preview_state.save(str(preview_state_path))
                logger.debug(f"✓ Preview state saved to {preview_state_path}")
                
            except KeyboardInterrupt:
                raise
            except Exception as e:
                logger.error(f"Error in worker cycle: {e}", exc_info=True)
            
            logger.info(f"Sleeping {settings.WORKER_POLL_SECONDS}s until next cycle...")
            time.sleep(settings.WORKER_POLL_SECONDS)
    
    except KeyboardInterrupt:
        logger.info("Received interrupt, shutting down...")
    finally:
        # Save state one last time
        dedupe.save(str(dedupe_path))
        price_buffer.save(str(price_buffer_path))
        preview_state.save(str(preview_state_path))
        
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
