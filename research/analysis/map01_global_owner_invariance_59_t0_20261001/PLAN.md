# Frozen plan — Issue #59 global-owner event/head invariance T0

## H / T / D / C / U

- **H:** The path-global allocation owner can be bypassed when the workflow-run request filters by current event, irrespective of whether the hidden prior owner's head SHA is equal or different.
- **T0:** From frozen commit `ad123c3875d81ebdc8bdfbdb59340005d705a60d`, compose the actual live-04 API query scope with the actual `select_global_owner` helper over 8 synthetic cells (current event × prior event × prior SHA), plus first-run and truncated-view controls. No network/API/Actions call.
- **D:** `FAIL_EVENT_FILTER_ESCAPES_PATH_GLOBAL_OWNER` if all four cross-event prior-owner cases are admitted by the event-filtered rows while complete history denies; same-event cases deny; first run admits; truncated view fails closed. Any disagreement with this rule is retained as failure, not repaired in place.
- **C:** This does not model workflow concurrency/scheduling or whether overlapping real Actions runs occur.
- **U:** No live API reachability, allocation, Docker/game/model/GPU/GUI/input, release telemetry, or MAP01 efficacy.

## One-shot protocol

1. Validate construction tests, Python compilation, frozen source/query identities, and absent outputs.
2. Freeze hashes in `FREEZE.json` before candidate execution.
3. Execute `candidate.py` exactly once; preserve `candidate.raw.json`.
4. Freeze its raw hash and auditor hash in `AUDIT_FREEZE.json`; execute `independent_audit.py` exactly once.
5. Never overwrite a run artifact. Any rerun requires a separately named successor experiment.

Docker Desktop's engine was unavailable. This finite source-composition fixture is deterministic and host-only; no container was started.
