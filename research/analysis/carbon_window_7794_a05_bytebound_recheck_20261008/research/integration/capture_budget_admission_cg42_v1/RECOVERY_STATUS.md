# Recovery status: source verified; formal disposition HOLD

This additive snapshot preserves all six files from remote branch
`research/capture-budget-admission-4316-20260924-cg42`, head
`c50297f95f65965062c05afe8979f8df7f2b0ca8`. It does not rerun the consumed
allocation or relabel its first outcome.

## Source recovery and local check

The two source-capsule chunks restore 14 manifest-bound files. Restoration
verified archive SHA-256
`dfa17d31257f30e4f078972e4c6fcbe3b9f540db989868672b5c57fb817643df`; all 14
member SHA-256 values match `SOURCE_MANIFEST.json`. The pure policy suite
passes 7/7 on the available host. This is source/contract validation only; it
does not reproduce the frozen GUI/native experiment.

## Formal-evidence and control boundary

The branch contains only `EVIDENCE.00.b64` (18,001 bytes including newline).
Strict base64 decoding yields a 13,500-byte XZ prefix with no terminal marker;
it cannot restore the formal result package. There is no complete formal raw,
audit output, or controls output in this branch. Issue #4325 records the
scientific allocation as `HOLD_CONTROL_COPY_INCOMPLETE`: the original frozen
corruption wrapper completed 0/12 mutations after failing at its baseline.
The original failure must remain unchanged; a planned posthoc wrapper repair
is not present here and was not rerun in this recovery.

Therefore the reported local observations and unchanged raw audit remain
historical Issue records, not a reproducible overall PASS. No GUI/native actor,
formal case, auditor, or control was run here, and no missing bytes were
reconstructed.

Disposition: `HOLD_CONTROL_COPY_INCOMPLETE_AND_RAW_PREFIX_ONLY`. Preserve the
original control failure and first audit as reported; a complete result
delivery needs the exact remaining evidence, original control outputs, and
any separately labelled repair diagnostic for independent review.
