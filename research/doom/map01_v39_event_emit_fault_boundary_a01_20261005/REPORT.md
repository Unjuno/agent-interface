# MAP01 V39 event sink fault boundary A01窶鄭04

## Result

A04 passes the preregistered source-bound sink contract: the literal `emit(row)` from main writes sequentially to `events.jsonl`, then `delivered.jsonl`, then stdout. Injected exceptions confirmed that a failure between the two file appends leaves an event row only in the first destination; an attempted retry completes the second destination but duplicates the first. A stdout failure happens after both appends; retry duplicates both. The no-fault baseline writes one row to each sink. Exact counts and stable logical IDs are in `results/A04_RAW.json` and its independently checked result.

The current ExecutorV12/V13 source records a release publication attempt before calling the external sink. The release-specific wrapper stores the exception as `delivery_unknown`, which prevents automatic retry. That is at-most-once attempt behavior at this boundary; it does not recover a missing sink copy. This source review does not instantiate the executor.

## Preserved first outcomes

- A01: `STOP_EMIT_AST_SHAPE` (expected AST count 6; actual 2 direct statements), zero injections.
- A02: `STOP_EMIT_AST_SHAPE` (expected 5; actual 2), zero injections.
- A03: candidate exit 0; audit exit 1. Its open-fault wrapper was not descriptor-bound and caused `FileNotFoundError('a')`; retained as harness FAIL, not product evidence.
- A04: candidate and separately run raw-only auditor exit 0; `PASS_SCOPED_SOURCE_BOUND_EVENT_SINK_FAULT_CONTRACT`.

Each disposition has separate freeze/STOP/raw/log/exit records. No failed run was retried or relabeled.

## Method and scope

Current main: `6a2826d391b77496b69752609a6f07b6971b4b6f`. Exact Git blobs and SHA-256 source pins are in `FREEZE.json` and `results/A04_FREEZE_SUPPLEMENT.json`. The candidate AST-extracts only the nested `emit` function from the exact pinned `research/doom/session_map01_v12.py` blob and applies Python exceptions to private temporary file destinations. The independent auditor reads saved raw only. Candidate and auditor ran once in separate network-disabled WSLc 3.0.1.0 containers using cached Python 3.12-slim image `sha256:414a398990af718f018ff9c23cea0e7489b7986eb54f2b1d7cc874c99ebc7364`, one CPU and 512 MiB requested. Logs preserve the WSLc warning that swap limit capability is unavailable; CPU enforcement was not independently measured.

This tests Python-call fault boundaries only, not process termination, fsync/device failures, filesystem crash durability, transactionality, production executor integration, real X11/OS input, GUI/game, application effect, useful feedback, bounded recovery or Issue #59 completion. No GPU was used or allocated.
