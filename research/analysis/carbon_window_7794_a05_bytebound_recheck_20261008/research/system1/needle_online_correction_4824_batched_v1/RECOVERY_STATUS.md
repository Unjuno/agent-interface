# Recovery status — Issue #4824 batched construction package

This directory preserves the exact 40-file package recovered from remote branch
`research/needle-online-correction-4824-batched-20260927` at source tip
`0b384d2fd5ca20b1eccc41f394d26b11a6af42b4`. The package is retained as an
archive of an incomplete construction diagnostic, not as a validated result.

## Verified

- The 28 ordered encoded parts reconstruct to 2,299,063 bytes with SHA-256
  `9feb483c29c71191d519eb1be3842de44ead6e4df6c751defabd5fa40795af97`.
- `FREEZE.json` records `formal_invocations: 0` and
  `STOP_AUDIT_INCOMPLETE_NO_FORMAL_DECISION`.
- The runner present at the branch tip hashes to
  `829193b58a3e3a1f6fdc7961d84c7f668a4375fc24b34847b653883ce03f98f1`, not
  the frozen `A2064F69...` digest. The root auditor hashes to
  `a09751f3fb4a0f41241e9af95dde437d33f1976386c067403c4f2550a1d8f58c`, not
  the frozen auditor digest `D4F12239...`; frozen source files
  `source/runner.py` and `source/audit.py` are absent.
- The retained runner's treatment is a single batch-8 update, not the four
  batch-2 updates described by the package README. Treatment-to-source binding
  is therefore unresolved.
- The retained audit status says model logits were not independently
  regenerated, optimizer updates were not replayed, and base tensors are
  missing.

## Disposition and boundary

`STOP_PROVENANCE_TREATMENT_MISMATCH` / `STOP_AUDIT_INCOMPLETE`. This recovery
only preserves the bytes and makes the provenance gap discoverable. Matching
the raw transport hash is not source or scientific validation. No runner,
trainer, auditor, construction seed, or formal experiment was executed during
recovery; do not infer acquisition, retention, or model quality, and do not
rerun the consumed construction seeds. Any future experiment requires a fresh
allocation, complete frozen source binding, retained model/optimizer tensors,
and independent model-output and update replay.

The original source head remains recoverable via immutable archive tag
`archive/recovered/needle-online-correction-4824-batched-original-20260927`.
Issue #6321 is a separate preflight/successor and is not changed or superseded
by this archive.
