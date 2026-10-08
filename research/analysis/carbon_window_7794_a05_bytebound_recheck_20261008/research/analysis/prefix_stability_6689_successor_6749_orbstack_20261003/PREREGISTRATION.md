# #6749 — corrected prefix-stability successor T0

## Lineage

This is a new allocation for Issue #6749, successor to the immutable #6689 artifacts in PRs #6704 and #6706. The predecessor outcomes remain respectively `FAIL_AUDIT / STOP_CLASSIFICATION_COUNT_CONTRACT` and adjudicated `FAIL_METHOD` for lost mandatory obligations. Nothing from either output is rewritten or silently pooled.

## H / T / D / C / U

- **H:** The corrected finite classifier and an independently implemented raw-only oracle will recognize a current-generation decisive mandatory failure as stable while still listing all outstanding obligations, including another mandatory check not yet received. Disposition counts will contain only disposition labels; derived early-finalization metrics will be stored separately.
- **T:** 32 authored worlds (two binary mandatory results × two generation states × four optional-source paths), 2,112 legal source-order-preserving interleavings, and all 4,064 distinct prefixes. Optional paths include clear→complete, clear→later-conflict→complete, conflict→complete, and timeout without completion. Exactly one candidate and one independent auditor invocation, in separate offline OrbStack containers. Five predeclared mutations test dropped mandatory obligation, mixed aggregate metric, forged completion, stale→current relabel, and timeout→complete relabel. No model, GPU, GUI, task/user data, package installation, network, retries, or tuning.
- **D:** `PASS_METHOD_SCOPED` only when all 4,064 prefix rows and legal continuation outcomes are independently reconstructed; a stable FAIL with an unseen mandatory result still lists that obligation; STABLE_PASS requires both mandatory PASS, CURRENT generation, and explicit optional COMPLETE; disposition and derived metric count spaces are disjoint; all five mutations are rejected; authority and consumer side-effects remain zero. Any violated condition is FAIL; incomplete semantics is HOLD.
- **C:** Wait-for-all or #6509's claim-scoped partial verdict may be simpler; a corrected certificate may add no runtime value. The finite model may still omit real late correction behavior.
- **U:** This is an authored logical model, not evidence about live verifiers, GUI freshness, runtime safety, application effects, user benefit, or latency.

## Construction amendment before freeze

The first construction pass revealed that the initial optional-source paths could not deliver a conflict after an already observed CLEAR, so the planned positive-finality test was insufficient. Before any formal candidate/auditor container ran, the fixture was amended with `CLEAR → CONFLICT → COMPLETE`, bringing the frozen space to 32 worlds. Host construction tests pass 5/5. One host-only candidate construction smoke produced 2,112 traces and 4,064 prefixes to validate fixture size; its temporary output was not retained as formal evidence and does not count as either formal invocation. This amendment is recorded on Issue #6749 before the formal run.

## Frozen inputs and output boundary

See `FREEZE.json` for base commit, image digest, engine, exact source hashes, formal invocation ceilings, and initially absent output paths. Candidate and auditor run once in separate containers. Candidate raw is mounted read-only to the auditor; output directories are separate. Do not retry either formal invocation.
