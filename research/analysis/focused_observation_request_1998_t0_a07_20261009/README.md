# A07 focused-observation contract boundary fixture

Allocation `LABEL-CONTROL-AMBIGUITY-1998-T0-A07-20261009` tests the finite semantics in Issue #1998 that the retained #1935 v1 fixture did not encode: full-frame exactness, distractor-only changes, focus loss, ambiguous region candidates, replaced identity, and the no-action-authority boundary. The previous package is immutable and is an input to this package's provenance only.

This is a deterministic standard-library fixture. It contains two 8×8 frames differing only outside a declared 2×2 target region, plus eleven request states for each frame. It makes no live GUI, OS-focus, model, task-effect, latency, or product claim.

Formal candidate and independent raw-only audit are each invoked once after the host/source freeze. The immutable decision and actual outputs are in `REPORT.md` and `results/`.
