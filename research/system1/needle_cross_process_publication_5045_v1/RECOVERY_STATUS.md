# Recovery status — Issue #5045 allocation v1

This additive archive preserves the exact files from remote branch
`research/needle-cross-process-publication-5045-v1-20260928` at
`bcb59e62e13226a517a82fd5838d7b4dcf180a48`. The original freeze, source,
construction receipts, and STOP receipts are unchanged.

## Original dispositions — do not rerun or reinterpret

- `STOP_PREFLIGHT.json`: the frozen `formal.py` reads top-level
  `freeze["input_sha256"]`, but `FREEZE.json` stores the digest at
  `freeze.input.sha256`. The resulting `KeyError` precedes output creation and
  every Docker invocation. Formal runner/auditor/container counts are all zero;
  no hypothesis observation occurred.
- `STOP_RESOURCE_OWNERSHIP.json`: the shared Docker CPU lane had no explicit
  release and two running containers had unconfirmed owners. No container was
  modified. Formal runner/auditor/container counts are all zero and no output
  was created.
- Construction receipts remain distinct: `STAGE0_FINAL.json` records 7/7 tests
  and 12/12 synthetic audit controls; `STAGE0_CONSTRUCTION_FINAL.json` records
  7/7 tests and 9/9 synthetic controls. These are construction-only, not
  cross-process publication evidence.

## Successor boundary and branch retention

Issue #5066 / merged PR #5078 tested a separate frozen v2 allocation and path.
Its scoped PASS does not revise allocation v1's two STOPs. Issue #5045 remains
open and instructs preservation of prior branches and evidence; therefore its
source branch remains in place despite this main read-back. No allocation,
formal runner, auditor, or Docker experiment was executed during recovery.

All 13 original blobs were verified byte-identical. Consequently, their
existing CRLF/extra-blank-EOF whitespace is preserved; `git diff --check`
reports those source-file lines, so no whitespace rewrite is claimed. The new
recovery note itself is whitespace-clean.
