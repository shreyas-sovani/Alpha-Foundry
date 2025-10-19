# Autoscout Instance Configuration

## Deployment Checklist

- [ ] **Deploy Autoscout early**: Launch your Autoscout explorer instance as soon as possible
- [ ] **Fill `instance.json`**: Update this file with `explorer_base`, `api_base`, and `chain_id` from your deployed Autoscout instance
- [ ] **Embed explorer links**: The `explorer_base` will be embedded in dataset links, worker output, and the hosted agent UI

## Why Early Deployment Matters

Autoscout provides the user-facing explorer for transaction inspection. The worker will generate explorer links in the format `${AUTOSCOUT_BASE}/tx/${tx_hash}`, so having this URL finalized early ensures consistency across all components.

## Reference

- [Autoscout Explorer Launchpad](https://docs.blockscout.com/using-blockscout/autoscout)
