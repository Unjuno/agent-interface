# Issue #59 T0b — capture-availability endpoint differential

Disposition: `STOP_ORACLE_CANDIDATE_BOUNDARY_DISAGREEMENT`. This is an additive, construction-only check against the already-consumed finite T0. It does not rerun or alter the formal candidate, auditor, fixture, or raw output.

## H / T / D / C / U

- **H:** The continuation candidate and independent oracle should make the same conservative decision at closed capture-interval endpoints.
- **T:** Transcribe the two predicates from frozen T0 source at main `c4d2d4b1ccf4512ec79af75bd8eaecfcada39947`; evaluate five deterministic intervals around `available_at_ns), including an upper endpoint equal to availability and a point interval at availability.
- **D:** Candidate: `lo <= available < hi` yields `YIELD_CAPTURE_ORDER_UNKNOWN`; oracle: `lo <= available <= hi` yields the same. Executed Python 3.12.10 check: 2/5 disagreements (both exact-boundary cases). Retain STOP; no side was silently fixed.
- **C:** Existing fixture covers a strictly straddling interval, but not endpoint contact. The source contract does not specify whether the upper endpoint is inclusive; conservative YIELD avoids depending on an undocumented tie order.
- **U:** Source-level deterministic check only. No runtime controller, model, GUI, input, real capture clock, gameplay, safety, or MAP01 claim.

## Execution

`python -B boundary_check.py` exited 1 as preregistered for any disagreement and printed 5 cases / 2 mismatches. The nonzero exit is the retained result, not an infrastructure failure. `RESULT.json` records the cases and limits. The original allocation remains candidate=1, auditor=1, retries=0; this construction check invoked neither formal command.

This observation invalidates neither the original finite raw record nor broader runtime behavior. It identifies a boundary contract discrepancy requiring owner review before any decision about correcting either predicate.