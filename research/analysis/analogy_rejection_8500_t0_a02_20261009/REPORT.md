# Issue #8500 T0 A02 result

**Disposition: `PASS_METHOD_SCOPED`.** Candidate and independent raw-only auditor each ran once with zero retries under allocation `ANALOGY-REJECTION-8500-T0-A02-20261009`. The pre-run freeze is `83c2fbe1983fc3acdca0f2b5dedd3d3461e9d78c`; its main/source anchor is `a6343bb76e4dc0a4afa32a29c8a485a617faeff8`. Construction tests passed 4/4 before formal execution. Runtime: macOS host CPython 3.14.5, standard library only; the finite deterministic fixture did not require a container.

## Observed result

The candidate emitted 72 rows across six base schedules and six changed-envelope schedules. The independent auditor reconstructed all 72 rows, reported zero errors, and rejected all five frozen mutations. On unchanged-envelope invalid candidates, proposals were 6/6 for no-memory, 6/6 for prose memory, and 0/6 for structured memory. On the 12 valid candidates across unchanged and changed envelopes, all three conditions proposed 12/12; structured memory also proposed all six changed-envelope controls.

The candidate raw SHA-256 is `c1a343c9713daa9581b0b6902c601c96aedfc82f4b0cef161e42dc3ef7fb6517`; the audit SHA-256 is `e435f2013f802fc80091af573e75c6c0d887712996831404855ddf0054e3bf6a`. Complete outputs, invocation receipts, stdout/stderr, and their hashes are in `raw/first-outcome/` and `SHA256SUMS.json`.

The two memory conditions use the same exact family-key retrieval, record, lookup count, fresh checks, exposure, review slot, and 64-word context. Under this authored scorer, only structured memory makes the retained boundary question consumable. This result therefore establishes only that the fixture's deterministic rule exhibits the preregistered contrast under equalized checks and budgets.

## Limits

The cards, mappings, memory notes, truth, and scorer are hand-authored. No human participants, language model, real research task, open-literature search, deployed memory system, or product runtime was exercised. The result does not establish agent reasoning, idea quality, generalization, scientific validity, creativity, or product benefit. A02 addresses A01's verifier-access confound but remains a synthetic method result.

The A01 record and raw files remain unchanged. The initial A02 construction assertion failure and its pre-freeze correction are retained in `CONSTRUCTION_REPAIR.md`; formal execution began only after the correction was frozen and preregistered.
