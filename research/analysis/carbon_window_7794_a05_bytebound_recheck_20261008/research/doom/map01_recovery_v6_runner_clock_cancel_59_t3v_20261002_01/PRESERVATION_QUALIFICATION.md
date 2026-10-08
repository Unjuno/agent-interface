# Historical preservation qualification

This note accompanies preservation of PR #6266 at original head `41d5d5093d7125347c8eb919e8f45cfd86d4da12`. All 18 original package files, the recorded candidate/auditor sub-results and overall `HOLD_D_CLOCK_RETURN_BOUND_AMBIGUOUS` disposition are retained unchanged.

## Timestamp-unit discrepancy

The original REPORT, README, PR body and prior intake comment describe case A release as 55.791 ms after clock return and 36.166 ms after cancel request, and infer a 5.791 ms miss under the stricter 50 ms interpretation. The committed `results/candidate_raw.json` instead records:

- `clock_return_ns`: 285971112097750
- `cancel_requested.requested_ns`: 285971112117375
- `release_ns`: 285971112153541

Direct subtraction of these nanosecond-labeled fields gives 55,791 ns = 0.055791 ms from clock return, and 36,166 ns = 0.036166 ms from cancel request. The published millisecond figures are therefore inconsistent with the retained raw fields by a factor of 1,000. The claimed 5.791 ms miss is not established by these fields.

This is a static arithmetic qualification, not a rerun, replacement audit, or new scientific disposition. The historical HOLD and original prose remain visible. The ambiguous prose threshold origin, original implementation, invocation history and scope must not be silently rewritten or promoted to a new PASS.

## Scope

The preserved record is host-only fake-session/fake-backend evidence. It has no cancel-first runner arm and does not establish a measured benefit from changing the real runner to cancel-first, natural transport latency, live MAP01 behavior, task effect, production readiness or completion of Issue #59. The predecessor #6252 / PR #6254 STOP remains distinct. No experiment, construction, candidate, auditor, Docker/GPU recovery or optional test suite was run for this preservation review.
