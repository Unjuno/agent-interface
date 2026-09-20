# Issue #3660 — independent reconstruction of #3652 transition evidence

## H/T/D/C/U

- **H:** A raw-only auditor can independently derive the mixed-app transition outcomes from event payloads, operation receipts, identities and cleanup. Missing observations must produce HOLD rather than trusting runner-supplied `checks`.
- **T:** Freeze the #3656 PR head and formal raw SHA. Audit the retained raw read-only; require the exact event protocol, contiguous sequence and hashes; derive the five transition conditions; then run mutation tests for event reordering/extra events, count mismatch, identity changes, missing receipts, cleanup and bool/int confusion. No GUI, model, network, formal allocation or raw modification. WSL-only in this environment; the pinned container is unavailable.
- **D:** `PASS_AUDIT_RECONSTRUCTION_SCOPED` only if all five outcomes are independently derivable and all mutations are rejected. `HOLD_AUDIT_EVIDENCE_INCOMPLETE` where raw receipts do not support an independent reconstruction. `FAIL_AUDIT_RAW_INTEGRITY` for contradictory/tampered structure or claims.
- **C:** Exact frozen #3652 raw, claim set and boundaries. Only the independent auditor and tests are new. The prior runner decision and audit remain unchanged.
- **U:** This does not establish GUI correctness beyond the retained evidence, independent task effect, model benefit, integrated runtime, or container behavior.

## Provenance and current boundary

The formal result is from PR #3656 head `13ac542d1a99f8ec27f5baa7fb8f0aa5c337da23`; raw SHA-256 is pinned in `audit.py`. PR #3656 subsequently added a posthoc readback at head `6c937af70f6861a7c83a3b17d5bb20588fb461e9`. This reconstruction does not use runner booleans to decide and additionally requires the exact ordered protocol and raw receipts for each operation and observation.

The current raw supports three transition checks. It does not include an explicit receipt that Chromium's old XID was absent before replacement, an `input_emitted` marker for the geometry operation, or an observed active-window value after returning to Calc. The independent disposition is therefore expected to be `HOLD_AUDIT_EVIDENCE_INCOMPLETE`, even though the original runner reports 5/5 and its scoped transition result is preserved unchanged.

Run from the repository root:

```bash
python3 -m unittest research.integration.issue_3656_transition_reconstruction_v1.test_audit -v
python3 -m research.integration.issue_3656_transition_reconstruction_v1.audit research/integration/issue_2499_readiness_successor_3652_v1/evidence/formal-01/result.json
```

## Independent rerun

On 2026-09-21, the WSL unit suite passed 14/14 tests; `compileall` passed. The pinned formal raw canonical-LF SHA-256 remained `f0df0248ff5e754a91e93271d9784f08d06ae1e8ff349b5f82f0fd015eb42883`. Result: `HOLD_AUDIT_EVIDENCE_INCOMPLETE`, with focus drift, geometry/refusal and modal/recovery derivable; return-to-Calc and window replacement held for missing receipts. Error list was empty. Mutation controls include a synthetic positive control, which is not formal evidence.

Docker Desktop was not usable for this rerun: `com.docker.service` reported `Stopped` / `Manual`, and `docker info` could not connect to either configured named-pipe endpoint (`docker_engine` or `dockerDesktopLinuxEngine`). No container was started; WSL was used only for raw evidence parsing and unit tests. Thus the container portion is explicitly unrun, not passed.
