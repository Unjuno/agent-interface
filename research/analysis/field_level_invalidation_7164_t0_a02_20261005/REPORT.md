# #7164 field-level invalidation T0 A02 result

## Result

The frozen A02 candidate and independent auditor produced `PASS_METHOD_SCOPED` over 18 outputs: six synthetic cases under three update policies. The dependency-aware reducer matched fresh current-input derivation in all six cases. Whole-record invalidation also matched in all six. Direct-field-only refresh matched in one and retained stale derived values in five, including stale screen position and recovery anchor after a layout change and stale `enabled` after switching from edit to preview mode.

The recomputation comparison favored dependency-aware refresh on each fully supported update: for the transitive layout case it recomputed two current derived fields versus five for whole-record refresh; for the mode switch it recomputed one versus five. These are deterministic counts of current derived outputs, not runtime or product-cost measurements.

All five auditor mutation controls were rejected: a corrupted derived anchor, a false current claim without source support, the wrong dynamic enabled branch, acceptance of an older epoch, and acceptance of the previous object generation. The independent-field mismatches are reported as expected negative-control counterexamples; A01 documents the auditor gate bug that A02 corrected.

## Reproduction and integrity

The source, fixture, protocol, run recipe, construction receipt, and image digest were frozen in `FREEZE.json` before the formal invocations. The candidate ran once, followed by the auditor once, in the pinned `linux/arm64` Python image using OrbStack with networking disabled and pulling disabled. Both outputs are retained under `formal_02/`; their SHA-256 values are recorded in `formal_02/SHA256SUMS`. The container inventory was empty after execution.

Host construction checks passed before freeze: `construction_tests.py`, Python byte-compilation, JSON parsing, and `git diff --check`. These checks are separate from the container result.

## Limits

This is a finite synthetic reducer test against an authored support graph. It does not establish that a live GUI observer captures every dependency, that field-level memory is safe or useful in a product, or any improvement in latency, repair cost, stale-use rate, model quality, or task effect. Promotion requires repeated live tasks and those user-impact measures.
