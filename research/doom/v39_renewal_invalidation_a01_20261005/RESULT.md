# Result — V39 invalidated renewal submit (A01)

**Decision:** the observed failure is real in the pinned source path; the narrow candidate resolves admission before choosing cancellation. Keep the result synthetic and draft.

## TDD evidence

- RED against baseline `1403c822609395f9ab21e0cdbb36b7b4c8ee044d`: invalidation followed by a rejected renewal reached `cancel_invalidated_cover()`; the FIFO then raised `NoTerminalForRejectedSubmit: baseline waited for terminal of rejected renewal`. Process exit was 1 (expected RED).
- GREEN against the candidate built from the pinned baseline: the production renewal invalidation branch passed rejected and accepted controls, 2/2.
- Rejected control: one planner interruption; no cancellation write; no renewal ID added; previous verified terminal retained.
- Accepted control: one planner interruption; renewal ID added; cancellation sent for that exact ID; cancelled terminal required with verified empty release.
- Candidate source audit: the invalidation decision is recorded as `policy_dependency_invalidated` and continues before action admission. The dependent model answer is discarded.

## Limits and next gate

No full imported unittest suite, WSLc run, live game/model/input, or latest-main composition was executed. The local disk filled during dependency materialization; WSLc list also failed to return. Treat this as construction evidence, not integrated runtime readiness. Re-run `candidate_test.py` and `audit.py` in WSLc after capacity recovery, then run the project's focused suites on a refreshed main composition.
