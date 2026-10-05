# Issue #59 A06 — paired-ammo invalidation to verified-release handoff

## H / T / D / C / U

**H.** When paired health/ammo monitoring invalidates a fire cover during a running planner turn, the controller must interrupt the planner, cancel the active cover, and refuse to proceed unless the terminal reports verified empty keys and buttons.

**T.** Add regressions for the existing nested wait's invalidation precedence and the controller's cancellation helper, including nonempty and unverified release receipts. Rerun the paired-cover, V39 controller, V39 wait, source-refresh, and immediate action-validity suites.

**D.** Pass only if all five focused suites pass, both changed test files compile, and `git diff --check` passes. This tests the controller handoff contract with synthetic rows and stubs.

**C.** These tests do not drive an actual session process, prove race-free cancellation, or verify physical key release. They confirm only that the code rejects incomplete release receipts and propagates a monitor invalidation through the existing wait/cancel helpers.

**U.** No game, model, GUI, OS input, live allocation, or task-effect measurement was run. End-to-end useful feedback and matched bounded recovery remain unverified.

An initial negative-case test harness passed a plain `object()` where the cancellation helper requires a planner implementing `interrupt`; those three harness errors occurred before release validation. The fixture was corrected to implement the documented interface and the final suite was run once; no controller code changed during that correction.
