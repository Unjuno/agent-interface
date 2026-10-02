# Archival qualification: terminal ROI diagnostic STOP

Reviewed 2026-10-02 for preservation only. Original PR #5728 head:
`98b46cdaaa4b666112e3cfe735267ccd4c4a88e5`.

## Disposition and evidence boundary

Preserve `STOP_PROTOCOL_DEVIATION_RAW_UNAVAILABLE` / `NOT_EVALUATED`.
The historical candidate was invoked once and exited 0, but its resource gate did not fail closed and complete raw stdout was not durably retained. Independent auditor invocations and retries were zero. No raw-output SHA, accepted parity, break-even, or speed claim can be recovered from the partial display. Do not reconstruct or rerun the consumed allocation.

`FREEZE.json`'s `FROZEN_NOT_RUN` state is the immutable preregistration snapshot. `STOP.json` and `RESULT.md` record the later terminal disposition; preserving both does not make the preregistration state the final outcome.

The separate `gate_correction/` files are historical construction-only remediation. Their reported 8/8 fixture pass and idle inventory snapshot have not been rerun in this review. They neither repair the missing raw record nor grant an allocation.

## Static preservation checks

- All nine original files were retrieved by immutable head, decoded without newline normalization, and reconstructed their published Git blob IDs.
- The benchmark and auditor SHA-256 values match FREEZE and STOP. The preregistration Git blob matches FREEZE.
- Both PowerShell file hashes and Git blobs match GATE_CORRECTION.md.
- JSON parsing and Python AST parsing succeeded. No archived source, test, auditor, benchmark, or GPU gate was executed.
- `ORIGINAL_SHA256SUMS` binds all nine original files, including the historical correction. This qualification and that new manifest are additive.
- At main `f4fcea6a67f1d8695626447d97ae697fa454a04e`, this exact package root was absent. The current-main three-dot comparison contained only these nine additive files, with no shared source/default/workflow edits.
- The existing exact-head replay-gate check succeeded. That deterministic repository check is not an experiment audit or performance validation.

## Ownership and separation

The owner explicitly released this allocation in [#5085 comment 5923984051](https://github.com/Unjuno/agent-interface/issues/5085#issuecomment-5923984051). The preservation/correction follow-up is [PR comment 5924044869](https://github.com/Unjuno/agent-interface/pull/5728#issuecomment-5924044869). These are historical ownership records, not a present resource claim or proof of current host availability.

Later ROI allocations remain separate; their data cannot fill this allocation's missing raw output. Preserve #5118 unchanged. Merging this package archives a truthful STOP only: it creates no scientific PASS/FAIL, reopens no allocation, and closes no scientific owner issue.
