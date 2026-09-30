# Recovery provenance for the partial-order replay HOLD

On 2026-09-30, the twelve package files from [PR #4892](https://github.com/Unjuno/agent-interface/pull/4892), head `62da1558f84c0a8d061fb2b26076f16c1e67f33f` on `research/replay-partial-order-1748-4889-v1`, were reviewed for exact-byte retention. Recovery intake used main `bc1ca7f316d86ecaee5f24b3f961b69f8be32eae`. This integration preserves all twelve original Git objects. Its analysis-index entry is added to the current index rather than copying the old branch's shared README.

Static readback matches all twelve Git blobs. Published `runner.py` SHA-256 is `6e80cebcea36c76427fad6797a302a2672e965bca280abd4166a3d13872f275c`; `audit.py` is `cec0ecb574821887093f3ce5c1583fe35dd5a9096eec38124b8749119086b117`, both matching the retained report.

Concatenating the two original archive parts in manifest order produces the declared 104,640-byte ZIP, SHA-256 `a127e04d2fcce672f3ce5cc6f20d2af0e1f85b34ac16116e9e5a518e7c358f6b`. Its sole member is the relative file `RAW.jsonl`; CRC passes. That member is 3,241,590 bytes, SHA-256 `a25bc4a9e6cf845fb5b446b1d2d5071bd26909679efcc535372fdf77b58b4eb8`, and parses as 11,111 JSON rows. These are static publication checks, not a replay of candidate semantics or the historical auditor.

The overall disposition remains **`HOLD_AUDIT_CONTROL_HARNESS`**. The retained `AUDIT.json` reports `FAIL_RAW_AUDIT` with no semantic errors, and `CONTROLS.json` reports `FAIL_CONTROLS`: seven of eight controls rejected, while the linearizations mutation was a no-op. Neither those records nor the candidate's historical scoped PASS label are changed. Merged [#4914](https://github.com/Unjuno/agent-interface/pull/4914) is a separate two-event construction probe, not a repair or re-audit of this allocation.

No original runner, auditor, simulation, corruption control, container, GUI, or model was executed during recovery. Hash and CRC agreement do not independently attest historical execution or establish the finite replay theorem. No production trace ordering, action authority, performance, storage saving, task benefit, or Issue #4889 completion is claimed. Preserve the first result and failed control; do not rerun the consumed allocation to fill publication or audit gaps.

