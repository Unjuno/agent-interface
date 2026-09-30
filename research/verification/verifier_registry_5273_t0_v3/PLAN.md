# Issue #5273 T0 v3 successor

## Changes from retained predecessors

V1 and v2 remain unchanged. V3 addresses the second review: it preflights *all* checks in each IR as one plan rather than a selected check, validates exact assignment-to-check coverage, preserves per-check plus aggregate status, independently validates the frozen IR fixture shape, and rejects unknown raw/decision fields and non-bijective rows.

## H/T/D/C/U

- **H:** A versioned authority-neutral registry can classify every check in a valid #5268 IR plan before dispatch, returning a conservative aggregate plan status without hiding incompatible or unavailable members.
- **T:** Eleven frozen cases, including ten one-check edge cases and one two-check dependency-bearing IR with a compatible member plus an unavailable member. Exercise unsupported primitive, input/output role, stale version, unknown verifier, missing resource, cold budget, side-effect refusal, deadline, full assignment coverage and aggregate status. Compare to a literal independent raw auditor.
- **D:** Exact raw and decision schemas, exact case/check bijection, independent IR validation, source/input/allocation/base binding, per-row/aggregate outcomes, zero dispatch and `authority=none` must all pass. Mutations to duplicate/missing/extra IDs, output fields and metadata must fail.
- **C:** Declared capabilities/costs can be stale or false; a fixed synthetic fixture does not establish operational correctness or distributional behavior.
- **U:** Host preflight only. No backend calls, verifier truth, measured latency, scheduler benefit, runtime integration or authority. Numeric #5268 deadlines are interpreted as milliseconds only by the explicit synthetic fixture convention.

Do not reuse a prior allocation or promote this result to container formal evidence. #5268/#5269 source remains untouched.
