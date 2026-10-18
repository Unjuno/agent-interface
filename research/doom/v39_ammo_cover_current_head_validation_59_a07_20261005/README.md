# Issue #59 A07 — current paired-cover integration regression set

## H / T / D / C / U

**H.** The combined V39 paired-ammo guard, strict pair identity/time checks, full-observation fallback, planner-interruption/cancellation handoff, and existing action-validity/source-refresh contracts remain compatible after the latest branch integration.

**T.** Freeze the current PR head and rerun five local suites: paired cover monitor, V39 controller, V39 nested wait, source refresh, and immediate action validity. Compile changed Python files and check the diff.

**D.** PASS only if every test in all five suites passes, compilation succeeds, and `git diff --check` is clean.

**C.** These tests exercise synthetic observations and stubs. They do not establish producer timing, physical release, useful feedback, recovery, or game progress.

**U.** No game, model, GUI, OS input, or formal live allocation was invoked. #59 remains gated on explicit live-lane assignment and matched task-effect evidence.
