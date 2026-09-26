# Canonical allocation status — Issue #4174

This additive correction does not delete, overwrite, rerun, or relabel either retained allocation.

## Canonical ownership

The 144-row allocation on `research/typed-negative-outcome-4174-20260923-v1` published its source/gate freeze in Issue #4174 comment **5787860065** with formal rows 0/144.

The later 80-row allocation on `research/typed-negative-outcome-39-20260923` published its own freeze in comment **5787870105** and was later merged by PR #4182.

Under the repository collision rule, the earlier frozen 144-row allocation is the canonical #4174 allocation. The later 80-row PASS remains retained evidence but is:

`NONCANONICAL_PARALLEL_ALLOCATION_RETAINED`

It must not be used as the Issue-level #4174 disposition.

## Canonical disposition

The canonical first formal invocation completed 144/144 rows with runner exit 0 and no rerun/replacement/tuning. Its frozen audit exited 1 because only 10/12 declared corruption controls rejected. The execution container was subsequently reinitialized and the original RAW/AUDIT bytes became unavailable; they are not recreated.

Canonical disposition:

`HOLD_EVIDENCE_INCOMPLETE_AFTER_CONTAINER_RESET`

Recorded first-outcome RAW SHA-256:
`0e6b99fe110d2958cbc960b6660d928c121ee6129dd01bada05a46d7e40cff69`.

The canonical source/corpus/status records are retained byte-identically under `canonical_144_hold/`. Root 80-row files remain unchanged for provenance.

Parent #39 remains open. Future work must use a genuinely fresh allocation and must not pool either consumed run.
