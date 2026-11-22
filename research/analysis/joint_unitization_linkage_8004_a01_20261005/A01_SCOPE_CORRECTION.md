# A01 post-run scope correction

This correction is additive. `fixture.json`, `candidate.py`, the first
`run_candidate.json`, `run_audit.json`, and their original test results are
preserved unchanged.

## Finding

Review after the A01 run found two oracle-boundary defects:

1. Candidate code reads `truth.channel_b_identity` and compares it directly to
   the linkage alternatives. The `L1_oracle_candidate` therefore carries the
   answer the linkage procedure is meant to infer. A01 does not independently
   evaluate record linkage.
2. Candidate code reads `missing_channel_control.truth_present` and
   `detected_by` directly and emits a Boolean. It does not build a per-channel
   detection ledger or count a latent-opportunity denominator. The tests that
   remove a row mutate the four-assignment Cartesian-product denominator, not
   the population denominator. A01 does not demonstrate all-channel-missing
   retention in an ascertainment estimator.

The independent audit has separate implementation code, but it reads the same
oracle-bearing fixture and validates only the toy's four booleans. It cannot
repair candidate input leakage. The original `ok: true` means only that these
four deterministic rows match the authored fixture.

## Corrected disposition

Reclassify A01 as `LOGIC_TOY_ONLY`. Preserve the first result, but do not cite it
as `PASS_CONSTRUCTION_ONLY`, `PASS_METHOD_SCOPED`, evidence of independent
linkage, or denominator preservation. The one-factor/joint truth table remains a
logical illustration only. Issue #8004 T0 remains `HOLD`.

## Required successor design

For a valid next rung, candidate-visible raw channel traces and admissible
segmentations/link candidates must be physically separated from a sealed
oracle file. The candidate must not import/read truth IDs, oracle match labels,
or all-channel-missing status. The auditor alone joins inferred records against
the oracle and recomputes latent-opportunity denominators, capture histories,
false/missed links, split/merge errors, censoring, and any sensitivity envelope.
Mutations must include oracle leakage, deleted opportunities, false/missed
links, split-as-independent counting, and an incorrect `UNIDENTIFIED` outcome.
