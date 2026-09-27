# #4146 exact-max candidate-set cueing — first formal outcome

Decision: **PASS_AMBIGUITY_PRESERVING_CUE_SET_SCOPED**.

Formal allocation: `uncertainty-candidate-set-1933-20260922-formal-01`.
Formal invocations1 / reruns0 / replacements0 / tuning0.

## H

When an observation-side detector assigns exactly equal maximal evidence scores to multiple regions, deterministic top-1 tie-breaking manufactures exclusivity that is not present in the detector evidence. Returning the complete exact-max candidate set should preserve the fixture-authored true changed region without changing unique-max controls. Candidate membership remains an inspection hint and grants no action authority.

## T

Standard-library CPython 3.13.5 in the supplied Linux x86_64 execution container. Docker CLI was unavailable, so this is not Docker/OrbStack image-attested replication. No GUI, model/provider, network experiment, user data or task input.

The frozen corpus contains 48 independent deterministic rows over four 32-byte regions:

- 12 UNIQUE_TRUE controls;
- 24 TWO_WAY_TIE rows;
- 12 THREE_WAY_TIE rows.

The detector receives only exact before/after bytes and computes integer L1 region deltas. `TOP1_HARD` selects the lowest region id among exact maxima. `EXACT_MAX_SET` returns every exact maximum and sets `exclusive=false` for ties. Fixture truth is retained only for independent scoring.

The exact source/gate freeze was committed to GitHub before formal execution at branch head `bf0a70552777b0327f6c5c7c619a972e9e50e468`; all 10 remote source blobs matched locally computed Git blob IDs. Freeze SHA-256: `db94fce5c496c3e326327d93626c5bfa71a235aa71616fd7deda5fdef3dcee15`.

## D / first outcome

All frozen scientific gates pass:

- rows: 48/48;
- exact-max candidate matches independent reconstruction: 48/48;
- UNIQUE_TRUE singleton containing truth: 12/12;
- tie truth included with exact cardinality: 36/36;
- candidate true-region omissions: 0;
- candidate non-max inclusions: 0;
- `TOP1_HARD` true-region omissions on ties: exactly 21/36;
- action-authority flags true: 0;
- formal runner exit: 0;
- independent raw-only auditor errors: 0;
- evidence corruption controls rejected: 9/9;
- audit exit: 0.

Raw SHA-256: `681e55c107034609c0f85fa9a12bd9450af4725233a7db2e416b7142e438040d`.
Result SHA-256: `cec3a3d3f4fa3a516ae6648d067c430fa2276a2365b7fa2df25e52c104730291`.
Audit SHA-256: `12d7e7262181127b9f2d3382e4e74eebffc849e7d1feceb6be6481165ef93c23`.

The deliberately lossy top-1 comparator is not alleged to be current production behavior. Its role is to expose the exact information lost when a tie is collapsed.

## C

The exact ties, region boundaries and semantic changed-region labels are fixture-authored. The result is a finite representation/integrity result, not an estimate of natural ambiguity frequency or detector quality. Multiple highlighted candidates may increase planner inspection cost. Hash equality binds retained bytes, not semantic authenticity.

The independent auditor is a separately implemented raw-byte reconstruction run in a separate process by the same assistant; it is not independent human review.

## U / integration boundary

Not measured: near-tie thresholds, probabilistic confidence calibration, real GUI region proposal, actual multimodal-model attention or automation bias, image/token cost, latency, task correctness, cross-platform behavior or production integration.

Concrete conclusion for #1933: **an exact detector tie should not be serialized as an exclusive single cue unless a separately justified tie-break contract exists.** Preserving all exact maxima is sufficient for this frozen finite contract and remains authority-neutral. A separate live/model-facing successor is required before claiming user-visible benefit.
