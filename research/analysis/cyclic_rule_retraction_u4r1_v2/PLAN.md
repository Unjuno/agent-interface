# Execution plan — Issue #4449

## Fixed universe

Roots: E0 and E1. Claims: A and B. Rules:

| ID | Head | Positive body |
|---|---|---|
| r0 | A | E0 |
| r1 | A | B |
| r2 | A | E1, B |
| r3 | B | E1 |
| r4 | B | A |
| r5 | B | E0, A |

For all 64 active-rule masks, produce a NO_CHANGE row and one row per active
single-rule deletion. Expected denominator is `64 + 6*32 = 256`.

## Algorithms

- `FULL_REBUILD`: compute the least fixed point from roots after deletion.
- `clear_and_rederive`: find the deleted head's transitive surviving
  support-to-head cone, clear it from the old grounded state, retain old
  grounded claims outside the cone, and rederive to a fixed point only inside
  the cone.
- `LOCAL_SUPPORT`: start with the old grounded state and repeatedly remove
  claims with no currently satisfied rule; this intentionally exposes
  self-supporting positive cycles.
- `BLIND_INVALIDATE`: clear the affected cone but do not rederive; this
  intentionally exposes loss of alternate support.
- Independent auditor oracle: intersect all rule-closed interpretations over
  `{A,B}`; do not import the study implementation.

The formal invocation emits one JSONL row per condition, source and input
hashes, a process receipt, and summary counters. Audit is a separate process.
Ten deterministic copied-evidence mutations are required to be rejected.

Construction is an excluded 10-condition discriminating subset (masks 1, 11,
and 19, including alternative support and an externally grounded positive
cycle), run before freeze. Formal
invocation budget is one; no retry, replacement, row exclusion, or post-result
tuning.
