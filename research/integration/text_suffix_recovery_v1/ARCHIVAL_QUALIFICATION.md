# Freeze-only archive qualification — Issue #4040

This directory preserves the exact public preformal `FREEZE.json` from remote branch `research/text-suffix-recovery-20260922` at head `eb07a1b701641253b6b348c91923230b757f142a`. The archived freeze's Git blob is `3c7792a670b5c27905e2ffe85349198c05200fe0`; it is copied unchanged.

## H/T/D/C/U

- **H:** retain the allocation identity and source/plan hashes so agents do not mistake the consumed 48-case allocation for unrun work.
- **T:** compared the exact remote ref and tree against current `main`; the branch-only delta is this one freeze file. Issue #4040 reports a 48-case scoped PASS, but the frozen source, both raw batches, audit/process receipts, and predecessor 27-case corpus are absent from the branch and could not be recovered from the identified Actions runs or bounded repository/workspace searches. No formal case was rerun.
- **D:** `HOLD_SOURCE_AND_RAW_UNAVAILABLE`. This is metadata preservation only. The Issue-reported result is not independently reproduced, promoted, or merged as a verified scientific result.
- **C:** retaining a hash commitment is useful for provenance and duplicate-allocation prevention, but a freeze and Issue prose cannot substitute for executable sources or raw observations.
- **U:** no repository-restorable source/raw corpus, independent audit, or result reconstruction is available. Issue #4040 remains open for exact-byte recovery.

The original branch tip/history is retained separately under `archive/recovered/text-suffix-recovery-4040-20260922`. Recover missing bytes only through a fresh linked branch; do not rerun the consumed allocation or alter its reported outcome.
