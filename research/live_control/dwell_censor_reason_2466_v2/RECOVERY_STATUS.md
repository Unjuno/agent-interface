# Issue #2466 recovery / archival status

This directory and the adjacent `dwell_censor_reason_2466_v1/` directory preserve the exact source and records from remote branch `research/dwell-censor-reason-2466-20260923` at frozen head `1e3f001e5074d0eec77cdc4d4715d10e76bf5c7a`. This is an archival recovery, not a new experiment and not a result promotion.

## Immutable allocation boundaries

- Allocation-01 remains `STOP_EXTERNAL_EXECUTION_TIMEOUT / HOLD_INCOMPLETE_DENOMINATOR`: 25 of 48 complete cases, no aggregate `ROWS.json`, no `END.json`, no Xvfb terminal receipt, and no outer return-code receipt. Its biased prefix contributes zero rows to allocation-02. The branch's `STOP_ALLOCATION_01.json` and `PREFIX_AUDIT_ALLOCATION_01.json` are retained unchanged; the prefix record does not repair the missing raw evidence.
- Allocation-02 is frozen at **0/4 batches, 0/48 formal rows**. Its prospective clock-origin and immutable batching changes are preserved in v2. No formal batch, GUI/Xvfb case, or formal audit was run during this recovery.
- The Issue remains open. Neither allocation establishes a validated production dwell bound or policy.

## Local verification in this recovery

The original 17 files from the remote branch are copied byte-for-byte; all 17 local Git blob IDs matched the frozen remote head. On host CPython 3.14.5/macOS, the two committed contract suites passed 6/6 each. All six allocation JSON files parsed, and the repository workspace-index and Git-tree suites passed 21/21 with the committed-tree workspace-index check reporting 152 directories. The v2 freeze specifies Linux/CPython 3.13.5/Xvfb, and the committed environment record says Docker and Podman CLIs are unavailable. These host/source checks are supplemental only, not the frozen environment gate or formal evidence.

Only the committed `test_contract.py` unit suites may be run as source checks. Do not invoke `run.py`, `run_batch.py`, aggregate formal output, create replacement raw rows, or pool allocation-01's prefix. A future formal allocation requires following the existing Issue and frozen gates; this archive grants no execution authority.

## Integration scope

This archive makes the exact source, freeze and STOP records discoverable on `main`. It does not claim allocation-01 or allocation-02 PASS, complete the missing allocation-01 denominator, authorize/resume allocation-02, or promote a timeout policy. Only after merge and exact readback of all 17 original Git blobs from `main`, with no PR or active-worker dependency, is the old remote branch redundant and eligible for deletion; the Issue and both allocation records remain open/retained regardless.
