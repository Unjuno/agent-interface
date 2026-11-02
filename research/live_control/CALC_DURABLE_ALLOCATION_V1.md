# Calc durable caller allocation v1

This offline seam composes the existing `run_g10_in_caller` / adaptive v3 caller with an allocation-local evidence writer. It addresses the missing publication edge in Issue #57: the caller's returned receipt and usage accounting must survive independently of in-memory state.

## Record order

1. Create an exclusive allocation directory and persist frozen conditions, source SHA-256, source-code hashes, and explicit source-observation IDs.
2. Fsync each v3 caller journal event as it arrives. The model attempt ledger retains failed and successful call IDs, usage and cost coverage, requested model/effort, image counts, and wait time. A cost for a failed call is retained when the provider adapter reports it; missing cost remains unavailable. Model output text is not copied into `result.json`.
3. Hash and bind the selected interface, source digest, and observation IDs. Persist the compiled execution receipt before the outer `verify_effect` callback runs.
4. Normalize and persist the outer effect receipt, then persist the terminal caller result and all-attempt ledger. An apparent `TASK_SUCCEEDED` is rejected by finalization unless both execution and successful effect receipts were persisted.

`events.jsonl` is sequence-numbered and hash-linked. A torn line or bad link is an audit error and is never silently truncated or repaired. `audit_allocation()` checks the event chain, receipt/effect file digests and bindings, terminal result, and attempt usage totals. An allocation with no terminal result remains `UNKNOWN`; interruption does not create an inferred success result.

## Offline verification

Run from the repository root:

```
python -m unittest research.live_control.test_calc_durable_allocation_v1 -v
```

The composed test replaces only the low-level G10 native adapter. It verifies success ordering, two-call token and cost accounting, a deferred provider timeout with retained usage/cost, receipt-write failure before outer verification, interruption, and torn-log rejection. It does not call Calc, WSLc, a model provider, or a live GUI.

## Limits before live comparison

The allocation writer provides local fsync and hashes, not independent custody, signed identity, directory-entry durability on every filesystem, or crash-proof supervision. Source hashes and observation IDs are explicit caller-provided bindings. The effect verifier remains caller-supplied and is not proven independent by this wrapper. Raw receipts and observations may contain sensitive information and must stay in the approved private allocation store. The code is a research seam, not a live result.

Before a new run, pin the exact caller/scorer source hashes, allocation and private storage, model/settings, target/observation bindings, cold/warm/invalidation/repair arms, complete attempt budget, timeout/recovery boundaries, and independently scored saved-file and neutral-input evidence. Preserve every failed or unknown attempt in the same ledger. Do not replay the consumed G10 allocation.
