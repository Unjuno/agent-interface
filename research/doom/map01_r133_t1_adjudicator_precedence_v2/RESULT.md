# Result — Issue #5658 identity-precedence v2

**Disposition: `PASS_CONSTRUCTION_ONLY`** for the frozen finite synthetic contract. This is not a live MAP01 result or approval of #59's T1 allocation.

## Executed evidence

- Freeze commit: `6663353f3999666f275a00dd01439b5eb79d7e9b`; base `main` commit: `a44541541546290c4d2d5e6e6913ef07bc1f01f8`.
- Construction: `python3 -m unittest -v test_construction.py` — 4/4 passed, including an exhaustive 729-vector comparison against a separately implemented oracle and the identity-precedence controls.
- Candidate: `python3 formal_candidate.py` — one invocation, exit 0; emitted all 729 rows and four identity controls.
- Independent audit: `python3 audit.py results/formal-01/RAW.json results/formal-01/AUDIT.json` — one invocation, exit 0; 729/729 rows matched, four identity cases matched, zero errors.
- Mutation controls: 4/4 rejected (deleted row, wrong decision, row reordering, and precedence-output corruption).
- Formal raw SHA-256: `d3e4c82d97b540e4b980513adbbc8743dfb470fd021003e830d69ef1b52f6bd7`.

Malformed `model_contract_sha256` that also differs across sessions is rejected as `identity_format:model_contract_sha256`, before cross-session comparison can report a mismatch. Missing-field precedence is also exercised before equality. The declared scope is only this synthetic precedence and directional-rule implementation.

## Provenance limitation

At initial intake, the predecessor package was unavailable in the public tree and its cited local commit was not present in this checkout. A later live readback found it published in PR #5660 at `research/doom/map01_r133_recovery_coast_t1_v1/decision_rule_construction_v1/`. The predecessor audit's exact failure is retained: its `identity_hash_malformed` control expected `identity_format:model_contract_sha256`, while the frozen adjudicator returned `identity_mismatch:model_contract_sha256` first.

Review of #5660 also shows this v2 package implements a narrower sign classifier, not the predecessor's full six-session `adjudicate()` path or its twelve frozen control cases. It does **not** satisfy #5658's full successor acceptance criteria and must not be treated as closing that Issue. Its `PASS_CONSTRUCTION_ONLY` remains valid only for the smaller contract declared in this package. The predecessor PR #5660 and raw failure remain unchanged. A direct full-adjudicator successor needs a distinct freeze/path and its own one-shot candidate/auditor sequence.

## Environment and limits

CPython 3.14.5, macOS 26.6 arm64, standard library only. No Docker, GUI, X11, ViZDoom, model, physical input, network experiment, GPU, or shared allocation. Candidate and auditor execution commands and outputs are retained alongside `RAW.json`, `AUDIT.json`, and `MUTATIONS.json`. No retries occurred.
