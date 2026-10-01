# #5766 T0 allocation 01 — retained failure

Allocation `ORACLE-CHECK-5766-T0-20261001-01` tested a finite synthetic bracketed oracle-check protocol in pinned Python 3.13 Docker. The candidate exited 0 and emitted four scenario rows; the independent auditor exited 0 but reported `FAIL_T0_CONTRACT` with two base errors. This is a failed method construction, not a qualified PASS.

The important candidate defect is observable in the raw table: under `semantic_drift_unchanged_scorer`, the unchanged scorer returns `PASS` for `positive` where the independently derived current-semantic reference is `FAIL`, and `FAIL` for `wrong_target` where that reference is `PASS`; yet candidate disposition says `ELIGIBLE_FOR_FURTHER_TASK_AUDIT`. It compared scores to frozen labels instead of using the bracket discrepancy to hold the interval. Therefore it demonstrates a constructed semantic mismatch, but failed to implement the proposed decision gate.

The auditor also reported `deck_hash_mismatch`: its validator reads `freeze.deck_sha256`, but FREEZE records the same value as `deck_canonical_sha256`. This is an auditor implementation defect. Because the base audit failed, its four `rejected: true` mutation rows are not accepted as valid mutation coverage; they were rejected in the presence of base errors.

Other observed candidate dispositions: nominal = `ELIGIBLE_FOR_FURTHER_TASK_AUDIT`; equivalent version/schema control = `ELIGIBLE_FOR_FURTHER_TASK_AUDIT`; out-of-coverage = `UNKNOWN_COVERAGE`. These are fixture outputs and not qualified evidence because the base audit failed.

No retries or edits were made to this allocation's frozen source, raw candidate, or first audit. Candidate invocation: 1; auditor invocation: 1. Preserve `FAIL_T0_CONTRACT`; no H_PASS or real scorer/app drift claim. No GUI, model, user data, live task, or GPU was involved.

## Reproduction

See `FREEZE.json`, `PREREGISTRATION.md`, `RUN_MANIFEST.json`, exact command captures, `candidate.py`, `audit.py`, `deck.json`, `raw.json`, `audit.json`, stdout/stderr, exit codes, and `SHA256SUMS`. The pinned image ran with `--network none`, read-only root, source read-only, and a dedicated writable output mount. The auditor reads the frozen deck and raw candidate output only.

## Scope limits

Synthetic finite profiles only; scorer/app semantic rules and references are constructed. This does not establish real application scorer drift, user-visible task correctness, metrological traceability, or efficacy for #12/#57/#59.
