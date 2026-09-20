# Issue #3188 — source-bound MAP01 entry-gate execution

This additive record closes the missing exact-source/local-container execution rung with a bounded outcome. It does **not** claim live MAP01 recovery or task safety.

## H/T/D/C/U

- **H:** Exact main-source entry-gate execution yields the declared 32-vector readiness output; an independent auditor can reconstruct every row and control.
- **T:** Formal-01 was frozen but stopped before container creation because Docker rejected the image-ID reference. Formal-02 used the same exact candidate bytes and gates under a new allocation ID, resolving the already-pinned image by its verified local tag. One network-disabled OrbStack container ran the frozen `run.py`; a fresh read-only-input container ran the preregistered independent audit. No game, model, GUI, X11, or task input was started.
- **D:** Candidate execution: `RAW vectors=32 controls=5`. Candidate audit: `PASS_AUDIT rows=37 vectors=32 authorize=1 current=HOLD controls=5/5`. The pre-frozen independent auditor v1 returned `FAIL_AUDIT` due two defects in its own oracle (bit enumeration order and summary row accounting), retained unchanged. A separately versioned post-outcome independent auditor v2 then recomputed the exact same raw SHA, returned zero errors, and rejected five corruption challenges. **Formal allocation disposition: `HOLD_FROZEN_AUDITOR_DEFECT`**, because the independent auditor frozen before formal did not pass; the post-outcome corrected auditor is corroborating evidence and does not launder the formal gate to PASS.
- **C:** Finite readiness classifier only. No MAP01 game session, recovery, model/provider, GUI/X11, OS input, or authority grant. The single `AUTHORIZE` truth-table row is not a live authority grant.
- **U:** Does not establish live recovery efficacy, runtime/input safety, CI equivalence, model quality, or production readiness. The corrected audit checks this finite raw/schema and source binding, not arbitrary auditor soundness.

## Frozen and executed identities

- Source base: `f79ef46d478911170d73b71bddcbe58fd698dc84`.
- Preregistration commit: `b6c0d351a83c5fe21c9a47d6b6d1e9e5a6aeafac`; formal-02 successor prereg + formal-01 STOP retained at `5f5386b3644d8a98888a6a30db5d25dc3b4f1909`.
- Candidate source is main's `research/analysis/map01_matched_recovery_entry_gate_3008_v2/run.py`, SHA-256 `e104bf12925ef7878e7972c768cb19ecfdfe699303667bebf0ee6a0276f05822`; candidate audit SHA-256 `72a5f6dcffff0e9d3a5e2daa58937bb4ab440ca789d824f183f168abc57e458d`.
- Formal allocation `issue3188-source-bound-entry-gate-formal-02`; image `python:3.12-slim`, immutable ID `sha256:2f17fc044b579bab302c2e8053d4a686e2cb9a83de48e70534b94cd8ebbe06a9`, Linux/arm64; OrbStack Docker Engine 29.4.0 (daemon reports `linux/aarch64`).
- Raw SHA-256: `8460a9ca79611929cbd6d2f6930067a06c6f177e7da3287ad07d1b7f483cb324`.
- Frozen independent audit v1 SHA-256 `ffae71aa3546b552915f894fac14d29c9e5d4c7007058941b881e7233e3083d2`; outcome SHA-256 `7d8370ff59e866794b2b1426f17c918325692df422c0ab72b719a8a9c205f02e`.
- Supplemental independent audit v2 SHA-256 and outcome are in `SHA256SUMS` and `results/independent-03/`.

See `RUNLOG.md` for exact commands, separate allocations, mounts, and outcome chronology. `SHA256SUMS` covers every retained source, preregistration, raw output, audit, and log. Formal-01 STOP and the independent-audit-v1 failure are first outcomes and remain unchanged.
