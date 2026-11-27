# Result — V39 invalidated renewal submit (A01)

**Decision:** the pinned renewal path reproduces the rejected-submit cleanup bug; the candidate resolves admission before choosing cancellation. Synthetic gates pass; integration remains HOLD.

## TDD and behavioral evidence

- **RED:** Baseline PR #7904 head 1403c822609395f9ab21e0cdbb36b7b4c8ee044d received invalidation followed by a stale-sequence renewal rejection. Its renewal branch called cancel_invalidated_cover and waited for a terminal that cannot follow the rejected submit. Harness exited 1 with NoTerminalForRejectedSubmit.
- **GREEN:** Candidate test extracted the actual renewal branch and helper functions. Rejected and accepted controls passed 2/2. Rejection caused one planner interruption, no cancel write, no renewal ID, and retained the old verified terminal. Acceptance registered the ID, cancelled that ID, and required cancelled terminal plus empty verified release.
- **Independent audit:** 8/8 control-flow checks passed. An initial auditor assertion failed because it matched AST unparse quote formatting; it was corrected to inspect AST nodes. The assertion failure and corrected pass output are both retained.
- **WSLc focused suites:** agent-interface/native-suite-wslc-a08:20261004, Python 3.12.14. 43/43 passed normally and 43/43 passed under -O. Suites: V39 controller, V39 wait/admission, source refresh, action validity admission, and observable signal guard v2.
- **WSLc source harness:** 2/2 branch controls; read-only audit: 8/8.
- **Syntax:** candidate controller and controller test compile. No full controller import suite beyond the listed tests is claimed.

## Retained setup failures and warning

The first suite attempt used the image's default fixed runner entrypoint; the next two import attempts exposed omitted HUD v2 then v1 source files from the sparse checkout. All outputs are retained; the missing exact tracked dependencies were added and the same focused suite then passed. Each WSLc run emitted the cgroup/swap warning; see FREEZE.md. No claim of memory/swap enforcement is made.

## Limits / next gate

No game, model, GUI, OS input, live allocation, full repository suite, or refreshed-main composition ran. This PR is a stacked draft against #7904; after its parent is integrated/refreshed, rerun the focused gates against current main before considering readiness. No input authority or product success is claimed.
