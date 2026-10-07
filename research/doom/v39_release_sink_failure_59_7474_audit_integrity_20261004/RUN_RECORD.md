# Evidence-audit integrity run record

- H: the predecessor audit can accept fabricated summary fields when the attempt trace is missing or inconsistent.
- T: load the predecessor's saved raw JSON, pin its canonical JSON SHA-256 and source Git blob, derive sink call counts, acceptance counts, and retry suppression from attempts, and apply corruption controls.
- D: the unmodified predecessor raw must pass; a missing trace, sink-call mismatch, summary drift, or duplicate case must fail.
- C: unchanged predecessor raw with exactly success, fail-before-accept, and accept-then-raise cases.
- U: this validates saved-artifact internal consistency only. It does not rerun the exact source helper, prove sink behavior, or establish executor-thread/physical-input outcomes.
- Runtime: Ubuntu WSL2, Python 3.12, ext4 isolated worktree; no container, WSLc, game, model, or input was used because only a small JSON audit was required.
- Tests: five unit tests pass; standalone audit passes; py_compile and git diff --check pass.
- Result: the saved predecessor raw passes all trace/summary checks. Each corruption control is rejected. Canonical content pin: 5bb5bdbbe5434eb23441e6e5ae3b32f9380d7cd4ddbc72e37a2e4ebb2f280cc3; predecessor raw source Git blob recorded in the raw: 7f308a0dd863af534f764f657d603b4921ba1c6a.
- Relationship: additive successor package; no predecessor PR file or evidence was modified.
