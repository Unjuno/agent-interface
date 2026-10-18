# Rescue readback — scorer endpoint readback type A03

This package rescues the evidence-only portion of closed, unmerged PR #7698 from exact head `614348df05ae603526a6a74a8feec17f039e7927`. It preserves the original `README.md` and `SHA256SUMS.txt` byte-for-byte and includes the exact source and test snapshots under `source/`. No test, auditor, game, model, GUI, or formal allocation was rerun.

## Current-main relationship at rescue

- The corrected `checkpoint_candidate.py` SHA-256 is `37387861339edf94401068cb08b2ca48e922ddc16d8d373c8b3e504816549c96`; the blob at `research/doom/scorer_endpoint_composition_59_a01_20261005/checkpoint_candidate.py` on main is identical. The implementation fix already arrived through merged PR #7685.
- The PR #7698 `test_candidate.py` snapshot SHA-256 is `a4516ce54656e50c97f5610aacee5ef9cad0ee82e7bdde09776d83217016f8ff`. Current main's test file has a later combined float/Boolean regression with different bytes (`test_post_read_tic_requires_exact_integer_type`); it still asserts `UNKNOWN` and withholds score values for both `11.0` and `True`.
- Consequently, the original `SHA256SUMS.txt` is retained as historical provenance. Its test-path entry describes the closed PR's original canonical path/content, while the exact bytes are now archived at `source/test_candidate.py`. Do not use the historical manifest as a claim that current main's test file is byte-identical.

## Scope

The result is stub-only endpoint-contract evidence. It does not show that real ViZDoom returned a malformed tic, and it establishes no live scorer behavior, game task effect, control input, recovery, or product acceptance. The preserved output is a historical TDD/regression record, not a new result.
