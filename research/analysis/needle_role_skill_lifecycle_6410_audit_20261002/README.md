# Issue #6410 raw-only audit successor

This additive allocation independently adjudicates the immutable 30,000-row WSLc candidate output already retained by #6410. It does not rerun the candidate, model, fit, optimizer, or timing workload, and it does not change the original STOP or its failed auditor artifacts.

The source/reference discrepancy previously recorded as a provenance STOP was reproduced as a checkout-byte issue: the frozen scorer digest is `d8a729…`; the original WSLc Windows checkout with `core.autocrlf=true` hashes to that exact value (1,052 bytes), while the corresponding LF Git blob/worktree hashes differently. The frozen T0 checkout also matches the original FREEZE, candidate, auditor, construction-test, validator, raw, and both input digests. The auditor reads and hashes these original bytes; it never imports the scorer or the failed auditor.

`FREEZE.json` binds this audit to Issue #6410, latest main at freeze, source/input identities, exact one-run WSLc settings, mutation controls, and decision gates. `RUN_COMMANDS.md` documents the sole formal invocation. The candidate run remains consumed under T0; candidate=0, audit=1, retries=0 for this separately frozen audit-only allocation.

## Allocation 02 disposition

The sole WSLc invocation exited before adjudication because the read-only repository `research/` directory was mounted at `/evidence`, while the command addressed its contents with an extra `research/` prefix. It raised `FileNotFoundError` for the original T0 freeze; no audit report was written and no prediction reconstruction began. The host also emitted: `Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.` Per the frozen no-retry rule this allocation is STOP, not a scientific result. See `STOP.json`; a corrected invocation requires a separately reviewed successor allocation.

No PASS/FAIL/HOLD conclusion is asserted until the frozen WSLc auditor invocation finishes and its output is preserved. See #6410 and its evidence-preservation PR #6426 for lineage.
