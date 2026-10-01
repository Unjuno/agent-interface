# Checkpoint commit-receipt boundary v1 — allocation 02 execution envelope

Issue #4111. Predecessor allocation `checkpoint-ack-outcome-20260922-01` remains immutable `STOP_EXTERNAL_EXECUTION_TIMEOUT`: 9 complete rows, one partial case directory, no terminal END/STOP/outer-exit receipt. It is not resumed or pooled.

## Scientific invariants

H/T/D/C/U, three policies, ten scenarios, three repetitions, exact order, expected decision counts, unsafe-control counts, candidate gates, checkpoint/receipt semantics and raw auditor are unchanged from `PLAN.md` / `FREEZE.json`.

## Only deltas

- fresh allocation ID: `checkpoint-ack-outcome-20260922-02`;
- fresh case directories and update IDs;
- execution is prospectively split into 15 immutable contiguous batches of six global indices each: [0,6), [6,12), …, [84,90);
- one invocation per batch, strictly ascending;
- batch N+1 runs only after batch N has END exit0 and an external returncode0 receipt;
- any missing/nonzero/incomplete batch stops the entire allocation; no retry, replacement or pooling;
- after all 15 batches, `finalize_v2.py` performs a read-only/copy aggregation into a fresh 90-case directory; it executes no worker/recovery case;
- the unchanged independent `audit.py` and `controls.py` run only after complete aggregation.

No scientific threshold, case, expected result or source used by the candidate/auditor is changed to accommodate the previous timeout.
