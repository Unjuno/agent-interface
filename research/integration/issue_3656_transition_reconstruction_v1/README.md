# Issue #3660 — independent transition evidence reconstruction

Audit-only successor for #3656 / #3652. It reads an exact retained copy of formal-01 `result.json`, does not alter its predecessor, and performs no GUI/input/model/network operation.

## H/T/D/C/U

- **H:** A raw-only auditor can derive the five transition outcomes and reject protocol, count, identity, receipt, and cleanup mutations. Missing observations must produce typed HOLD, never be inferred from the runner's boolean checks.
- **T:** Freeze PR #3656 head `6c937af70f6861a7c83a3b17d5bb20588fb461e9`, raw SHA-256 `f0df0248ff5e754a91e93271d9784f08d06ae1e8ff349b5f82f0fd015eb42883`, and preregistration SHA-256 `787f159f2c5ff7e2e017ef6e4d08ca1b843923d4e8c831b7659907a77ea18ffe`. Recompute event hashes/order, exact event set, role observations, transition payloads, input count, cleanup, and scope from raw only. CLI raw bytes are SHA-bound to the immutable PR file; mutation tests are local and synthetic. The raw is read-only.
- **D:** `PASS_AUDIT_RECONSTRUCTION_SCOPED` requires all gates plus both missing observation receipts. `HOLD_AUDIT_EVIDENCE_INCOMPLETE` when a required claim depends on a missing receipt. Mutated event shape/count/identity/cleanup returns `FAIL_AUDIT_MUTATION_ACCEPTED` (despite the historical decision name, this is a rejection signal). Runner check booleans are compared only after recomputation, never trusted.
- **C:** Same immutable #3652 formal-01 raw and preregistration; only this independent read-only audit is new. The source/raw copies must match their frozen identifiers.
- **U:** No new GUI run, task effect, model performance, integration, or Docker behavior claim.

## Result

The independent recomputation derives all five transition predicates as true, but disposition is `HOLD_AUDIT_EVIDENCE_INCOMPLETE`: raw lacks an explicit Chromium old-window-absence receipt, an independently observed active-window value on Calc return, and an event-level third input-operation receipt (only two events carry `input_emitted: true`, although the top-level integer count is 3). `fresh_validation: true` is a runner-produced assertion, not an observation receipt. This does not reverse #3652's retained historical runner/audit result; it narrows what the raw alone can substantiate.

Container infrastructure: `STOP_CONTAINER_UNAVAILABLE`. Docker Desktop's `com.docker.service` is stopped (`Manual`); `desktop-linux` could not connect, and service start was denied. The audit was run in local Windows Python and independently in WSL Ubuntu (not a container). The 13-test mutation suite passes in both. WSL additionally streams the exact frozen Git object through the CLI; byte SHA-256 is verified as `f0df0248…` and raw disposition is `HOLD_AUDIT_EVIDENCE_INCOMPLETE` with three missing receipts. No GUI/formal allocation was attempted.

## Reproduction

```bash
# Run from the repository root in WSL/Linux.
python3 -m unittest discover -s research/integration/issue_3656_transition_reconstruction_v1 -p 'test_*.py' -v
git fetch origin research/issue-3652-calc-launch-successor-v1
git show FETCH_HEAD:research/integration/issue_2499_readiness_successor_3652_v1/evidence/formal-01/result.json | python3 research/integration/issue_3656_transition_reconstruction_v1/audit_transition.py -
```

The committed `evidence/formal-01/result.json` is a JSON-semantic reserialization for review/test convenience (`ef4b6677…`), not byte-identical raw. The CLI refuses to treat a missing or mismatched byte digest as a provenance-qualified audit; use the Git-object streaming command above for the frozen raw.
