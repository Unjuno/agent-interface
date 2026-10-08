# Cleanup composition validation

H: The exact composition of PR #7584 and PR #7598 preserves bounded finish-send/escalation/scorer/planner/reader cleanup and skips the finish-dependent child wait when finish delivery fails.

T: Run both PR-specific cleanup suites, portability/stage diagnostics, and the adjacent V39 wait-loop and source-refresh suites against the frozen conflict-resolved tree in one cached, network-disabled WSLc container.

D: PASS only if all cases pass and the POSIX pipe-pressure and failed-send wait tests execute (not platform-skipped); compile all exercised Python files and retain a clean diff check. Any test failure or skipped POSIX case is HOLD/FAIL for that property.

C: Synthetic/unit and owned-child pipe behavior only; a green suite cannot establish complete input release, task effect, survival, or live-controller efficacy.

U: Container limits are requested, not assumed to be enforced. No game, model, GUI, OS input, or formal #59 allocation is included.
