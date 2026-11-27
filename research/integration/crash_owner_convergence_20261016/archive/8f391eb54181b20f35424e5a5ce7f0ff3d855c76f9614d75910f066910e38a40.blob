# V39 Action Validity to Executor Acceptance Xvfb A01

## Scope

This experiment tests the current V2 action-validity stage that the prior active-invalidation candidate stopped before. It checks an unchanged current sample that reaches actual Xvfb keydown after action validity and a synthetic hard health drop that must be rejected before any input.

## Pre-registration (H/T/D/C/U)

- **H:** A completed structured planner answer reaches current V2 action validity. Current health/ammo can advance to first Executor acceptance; health outside the authored envelope must not.
- **T:** Two arms from retained seq2→seq3 values and shared observation epochs, with timestamps rebased to the current monotonic clock. Source health/ammo 97/48; current control 97/48; invalid arm health 80/48, hard minimum 89. The original pointer binding names a different window, so typed source/current bindings are explicitly rebound to each focused Xvfb test window and geometry [0,0,320,200]. Current-main V39 admission functions and InputOwner V4/V12 are AST/imported from the frozen source. Actual Xvfb keydown occurs only after V2 returns fresh executor readiness. One candidate invocation total.
- **D:** PASS_METHOD_SCOPED requires control freshness→VALID_CURRENT→accepted first input→verified keyup, and invalid-arm action rejection before any input; both owner threads terminate and Xvfb exits 0. Any deviation is STOP.
- **C:** The health drop, window binding, planner answer, and accepted-executor protocol event are synthetic. Xvfb and the owner are real, but no production executor process/game/physical keyboard is present.
- **U:** No semantic threat detection, live task feedback, production executor crash behavior, recovery, physical input, or live MAP01 allocation. WSL2 is used because Docker is unavailable; no network namespace or hard resource cap is configured.

Exact source/input hashes and environment are in FREEZE.json.

## A01 execution and result

One invocation used WSL2 Ubuntu 24.04.3, CPython 3.12.3, python-xlib 0.33-2, Xvfb 2:21.1.12-1ubuntu1.8, display :134. The test rebased typed capture times to the local monotonic clock and explicitly rebound both typed observations to each focused Xvfb window; raw images and health/ammo values were retained.

The single unchanged-health arm reached READY_FOR_ACTION_VALIDITY, V2 returned VALID_CURRENT and READY_FOR_FRESH_EXECUTOR_ADMISSION, and bind_first_plan_acceptance recorded INPUT_ADMITTED. Xvfb independently observed a real owner keydown and subsequent V4/V12 verified keyup.

**Formal A01 status: STOP.** The recorded X KeyPress timestamp precedes the fake Executor accepted_ns, so the harness produced input before the acceptance event it meant to represent. The final assertion also incorrectly required the key to remain down after the explicit verified keyup. The low-health arm was never executed. These are test-harness/order defects; do not interpret this as proof of correctly ordered Executor admission, do not change the STOP, and do not rerun A01.

The raw-only audit confirms the frozen source/input hashes, records the valid-arm transitions and key lifecycle, and flags the acceptance-order mismatch. Raw SHA-256: f0552dcc7062c4cef52f9e4200b631e1540baa5ee710622cb753098fa2abbe84. Audit SHA-256: cd01964192bb5e668dde450d2f7acc4b5211384077c69c24d23725ae2afce479. Audit result is PASS_RAW_CONSISTENCY; formal experiment status remains STOP.

## Next integration

Replace the fake acceptance with current-main Executor V3 itself. It emits accepted before starting its worker thread; connect its event stream to the current V39 controller helper and InputOwner V4/V12 under Xvfb. Verify accepted-before-KeyPress, real executor cancellation, terminal release receipt, and stale planner-answer rejection. Then exercise executor failure/release-failure before seeking live task feedback under the separate Issue #59 allocation.
