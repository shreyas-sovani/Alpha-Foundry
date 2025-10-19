# DEX Arbitrage Data Platform

## System Overview

This monorepo implements a multi-component system for monitoring and monetizing DEX arbitrage opportunities on EVM chains. The **Worker** (apps/worker) continuously ingests swap events from configured DEX pools via the **Blockscout MCP Server** ([docs](https://docs.blockscout.com/devs/mcp-server)), normalizes price deltas, and outputs JSONL datasets. The **Hosted Agent** (apps/hosted-agent) runs on **Agentverse** ([docs](https://docs.agentverse.ai/documentation/getting-started/overview)) implementing the **ASI:One Agent Chat Protocol** ([docs](https://docs.asi1.ai/documentation/tutorials/agent-chat-protocol)) to provide stateless, conversational access to arbitrage insights. **Autoscout** ([docs](https://docs.blockscout.com/using-blockscout/autoscout)) serves as the user-facing block explorer, with links embedded throughout the dataset for transaction inspection. Future monetization will leverage **Lighthouse** and **1MB DataCoin** ([docs](https://docs.lighthouse.storage/lighthouse-1)) to package and sell curated arbitrage datasets.

## Architecture

```
┌─────────────────┐
│  Hosted Agent   │  Chat interface (Agentverse + ASI:One)
│  (stateless)    │  Reads metadata, provides insights
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│     Worker      │  Ingestion loop (MCP → Transform → JSONL)
│  (stateful)     │  Monitors DEX pools, persists checkpoints
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Blockscout MCP │  Chain data access layer
│     Server      │  Logs, transactions, contract reads
└─────────────────┘
         │
         ▼
┌─────────────────┐
│   Autoscout     │  Block explorer UI
│   (explorer)    │  Transaction inspection
└─────────────────┘
```

## Quick Start

1. Copy `.env.example` to `.env` and configure all required variables
2. Run `bash scripts/dev_bootstrap.sh` to set up the Python environment
3. Deploy your Autoscout instance and fill `infra/autoscout/instance.json`
4. Run `bash scripts/run_worker.sh` to start the ingestion worker
5. Deploy the hosted agent to Agentverse (see `apps/hosted-agent/README.md`)

## Directory Structure

- `apps/worker/` - Data ingestion worker (Python)
- `apps/hosted-agent/` - Chat agent for Agentverse (future implementation)
- `infra/autoscout/` - Autoscout instance configuration
- `scripts/` - Development and runtime scripts
- `state/` - Worker checkpoint state (gitignored)

## References

- [Blockscout MCP Server](https://docs.blockscout.com/devs/mcp-server)
- [Autoscout Explorer](https://docs.blockscout.com/using-blockscout/autoscout)
- [Blockscout Documentation](https://docs.blockscout.com)
- [Agentverse Overview](https://docs.agentverse.ai/documentation/getting-started/overview)
- [ASI:One Agent Chat Protocol](https://docs.asi1.ai/documentation/tutorials/agent-chat-protocol)
- [Lighthouse Storage](https://docs.lighthouse.storage/lighthouse-1)
- [1MB DataCoin](https://docs.lighthouse.storage/lighthouse-1/how-to/create-a-datacoin)
