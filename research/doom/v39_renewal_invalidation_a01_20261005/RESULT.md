# Result — V39 invalidated renewal submit (A01)

**Decision:** the observed failure is real in the pinned source path; the narrow candidate resolves admission before choosing cancellation. Keep the result synthetic and draft.

## TDD evidence

- RED against baseline 1403c822609395f9ab21e0cdbb36b7b4c8ee044d: invalidation followed by a rejected renewal reached cancel_invalidated_cover(); the FIFO then raised NoTerminalForRejectedSubmit: baseline waited for terminal of rejected renewal. Process exit was 1 (expected RED).
- GREEN against the candidate reconstructed from the pinned baseline: the production renewal invalidation branch passed rejected and accepted controls, 2/2. The checked-in source-extraction harness produced the same PASS.
- Rejected control: one planner interruption; no cancellation write; no renewal ID added; previous verified terminal retained.
- Accepted control: one planner interruption; renewal ID added; cancellation sent for that exact ID; cancelled terminal required with verified empty release.
- Read-only source auditor passed 8/8 checks: correct renewal resolver wiring; rejection is distinguished; planner is interrupted; old terminal is not replaced on rejection; dependent answer is discarded before action admission.
- Auditor construction failure preserved: an initial check compared AST unparse output to a quote-style-specific string and failed (not a production-code failure). The auditor was corrected to inspect AST nodes and then passed 8/8. See audit_initial_check_fail.stdout.txt and audit.stdout.txt.
- Syntax compilation passed for the controller and regression module. No full controller import/suite was run.

## Limits and next gate

No WSLc run, live game/model/input, or latest-main composition was executed. The local disk filled during dependency materialization; WSLc list did not return within 30 seconds. Treat this as construction evidence, not integrated runtime readiness. Re-run the candidate test and auditor in WSLc after capacity recovery, then run focused suites on a refreshed main composition.
