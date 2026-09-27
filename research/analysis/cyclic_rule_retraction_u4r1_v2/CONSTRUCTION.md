# Construction rung — Issue #4449

The construction subset ran in OrbStack before the formal freeze. It contains
10 rows from active-rule masks 1, 11, and 19 and covers no-change, alternative
support, and an externally grounded positive cycle.

- Image ID: `sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e`
- Runtime: Linux/arm64, CPython 3.12.14, network disabled, read-only source/root,
  1 CPU, 256 MiB memory/swap, 32 PIDs, all capabilities dropped.
- `construction01/rows.jsonl` SHA-256:
  `d6f4ebbd6cdc29309dc0b98ecc5622b00b9d3b7f90f97937bac0f6b08ffbee97`
- The first audit output is retained as `construction01/audit.json`: its
  semantic audit had zero errors, but only 9/10 copied-evidence controls
  rejected. Control 6 targeted an already-empty cone in the first no-change
  row, so it was ineffective.
- Without changing the construction raw, the auditor was corrected to mutate
  the nonempty cone at row index 3. A separate audit output,
  `construction-audit02.json`, reports `PASS_CONSTRUCTION`, zero errors, and
  10/10 rejected controls.

This is excluded construction evidence, not the 256-condition formal result.
The initial ineffective control remains visible and is not overwritten.
