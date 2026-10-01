# Durable incarnation-install receipt v1 — retained first outcome

Task: `COORD-DURABLE-INCARNATION-INSTALL-20260917-024`

Disposition: **`HARNESS_FAIL_RESTART_WRITE_COUNTER_EXPECTATION`**

The frozen formal runner was invoked once and produced `FAIL_DURABLE_INCARNATION_INSTALL_RECEIPT_SCOPED`. This result is retained without rerun.

## Observed mechanism outcomes

- mutable-only install rollback revived old I1/A/seq1 and applied it to g5;
- durable receipt candidate detected mutable rollback as `INSTALL_STATE_ROLLBACK`, with zero replay transition writes;
- restart reconstruction recovered I2, classified old I1 as `STALE_ISSUER_INCARNATION`, and applied fresh I2/seq1 exactly once;
- same install ID with changed install content returned `INSTALL_RECEIPT_CONFLICT`.

## Why the formal decision failed

The frozen gate `restart_fresh_i2_applies_once` required the restarted ledger's local `transition_writes == 4`. The restart constructor intentionally creates a fresh in-memory ledger and does not copy the predecessor's transition-write counter; after one fresh I2 apply the correct local counter is `1`. The retained state shows generation g5 and exactly one history entry for fresh I2/seq1, but the gate therefore evaluates false.

This is a scoring/harness counter expectation defect, not permission to rewrite the first result. The exact source/result/log bytes are retained. A successor must use a fresh task ID and change only the restart write-count gate to the local post-restart meaning (`1`), leaving mechanism cases unchanged.

## Container checks

- `py_compile`: PASS
- unit tests: 8/8 PASS
- formal runner invocations: 1
- formal reruns: 0
- verifier: FAIL because it correctly requires the frozen PASS decision
- post-result source hash recheck: 4/4 PASS

## Boundary

Deterministic single-process container fixture only. Install producer remains trusted; no cryptographic authentication claim.
