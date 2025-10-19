# Hosted Agent (Chat Brain)

## Overview

The chat brain runs as a **Hosted Agent on Agentverse** implementing the **ASI:One Agent Chat Protocol**.

## Architecture Principles

- **Stateless**: The agent does not maintain persistent state between conversations
- **Read-only**: Reads preview/metadata from the worker's output directory
- **Lightweight**: Heavy queries and data processing happen in the worker, not here
- **Chat-focused**: Optimized for conversational interaction via ASI:One protocol

## Key Responsibilities

1. Respond to user queries about DEX arbitrage opportunities
2. Read and parse `apps/worker/out/metadata.json` for dataset stats
3. Read and preview `apps/worker/out/dexarb_latest.jsonl` for recent events
4. Provide Autoscout explorer links for detailed transaction inspection
5. Suggest arbitrage opportunities based on normalized price deltas

## References

- [Agentverse Documentation](https://docs.agentverse.ai/documentation/getting-started/overview)
- [ASI:One Agent Chat Protocol](https://docs.asi1.ai/documentation/tutorials/agent-chat-protocol)
- [Blockscout MCP Server](https://docs.blockscout.com/devs/mcp-server)

## Deployment

Follow the Agentverse hosted agent deployment guide. Ensure the agent has read access to the worker output directory or configure a lightweight API endpoint for metadata retrieval.

## Environment Variables

The agent will need:
- `WORKER_DATA_PATH`: Path to `apps/worker/out/` or API endpoint
- `AUTOSCOUT_BASE`: Base URL for explorer links
- `CHAIN_ID`: Chain identifier for context

## Data Access

The hosted agent should read from the worker's output directory:

### preview.json
Updated every cycle with the latest N rows (default: 5). Format:
```json
{
  "preview_rows": [
    {
      "timestamp": 1729353600,
      "tx_hash": "0x...",
      "log_index": 0,
      "token_in": "0x...",
      "token_out": "0x...",
      "amount_in": "1000000",
      "amount_out": "2000000",
      "pool_id": "0x...",
      "normalized_price": 2.0,
      "delta_vs_other_pool": null,
      "explorer_link": "https://..."
    }
  ],
  "total_rows": 23,
  "last_updated": "2025-10-19T12:34:56Z"
}
```

### metadata.json
Overall dataset statistics. Format:
```json
{
  "schema_version": "1.0",
  "last_updated": "2025-10-19T12:34:56Z",
  "rows": 23,
  "latest_cid": null,
  "format": "jsonl",
  "fields": ["timestamp", "tx_hash", "log_index", ...]
}
```

### dexarb_latest.jsonl
Full dataset in JSONL format (one JSON object per line). The agent can:
- Parse last N lines for recent activity
- Count total lines for dataset size
- Filter by timestamp for time-based queries

## TODO

- Implement agent logic using ASI:One protocol
- Add message handlers for arbitrage queries
- Read preview.json for quick responses
- Parse metadata.json for dataset stats
- Stream JSONL for full dataset access if needed
