# MAP01 held-input raw receipt replay T1

Allocation: `MAP01-HELD-INPUT-RAW-RECEIPT-59-T1-20261002-01`  
Issue: [#6198](https://github.com/Unjuno/agent-interface/issues/6198)  
Branch: `research/6175-held-input-raw-receipt-t1-20261002`  
Current-main freeze: `3d33fe482ad55e99943f2c7b40e92c685c3bf92a`  
Historical analyzer and trace freeze: `69a1bf509eb432e5e3c0c294d05ad7671d86adb6`

## H / T / D / C / U

**H — hypothesis.** Re-running the exact pinned analyzer once for each retained v38/v39 event log and independently reconstructing the rows from raw events will reproduce every candidate row and published aggregate, or expose a discrepancy. The missing original temporary receipts can thereby be replaced with newly retained replay receipts, but the replay is not new data and does not revise the historical interval claim.

**T — test.** Host CPU only; no model, network, GUI, game, task effect, or user data. Inputs and analyzer are the exact Git objects identified in `FREEZE.json`. Run the analyzer exactly once on each event log, then invoke the separately authored `audit_raw.py` exactly once. It reconstructs timing bounds from raw JSONL and compares every field and aggregate against the two new candidate JSON files. Three auditor mutation controls remove a row, alter a timestamp, or alter a summary count. Retries/substitutions: zero.

**D — decision.** `PASS_RAW_RECEIPT_REPRODUCED` only if source and input objects are exact, 11 v38 completed rows and 27 v39 completed plus one verified interruption are reconstructed, every row/summary/limitation matches, the three mutation controls are rejected, all outputs and hashes verify, and no retry occurs. Any discrepancy is retained as FAIL/HOLD without rerunning.

**C — counterfactual.** This is the same historical trace and deterministic method as #6175, not a new observation. It tests receipt reproducibility/provenance only; the previous published table was a transcription rather than original candidate/auditor output.

**U — uncertainty and scope.** Exact physical key-up and continuous keymap occupancy remain unidentifiable. This does not measure task-useful feedback, causal v38/v39 differences, control safety, game success, latency benefit, or human tempo. The bound relies on the retained session-v4/session-v5 source-order contract. The one interrupted v39 row reports owner-release verification, not reversal of any external effect.
