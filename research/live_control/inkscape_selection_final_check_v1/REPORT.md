# Ordinary Inkscape final selection check — scoped candidate result

Task `INKSCAPE-SELECTION-FINAL-CHECK-20260916-371`; Issue #371. Publication base `0dd239b7db10831a4e8ac078d3a32d4be6370e3d`.

Decision: **PASS_SELECTION_FINAL_CHECK_SCOPED**. In this standalone Inkscape 1.4/Xvfb/XTEST fixture, a final four-sided selection-handle check immediately before the Right effect rejected all five already-switched-to-B cases and admitted all fifteen cases where A was the current selection, including return to the same living A and unrelated pointer movement. This is not atomicity: a selection change after the final check remains outside the tested guarantee.

## Frozen design

Construction was excluded. It observed four A-side dark-handle counts 176/176/176/176 when A was selected and 0/0/0/0 around A after selecting B. Before any measured outcome, the predicate was frozen to RGB channels <60 and >=100 dark pixels on each of four strips around A. The 20-case schedule was frozen with seed `37120260916`; five cases each of stable, switch-to-B, A-B-A, and unrelated-pointer trajectories.

Frozen scientific source SHA-256: `run_case.py` f80f01e2be7c590c8e64d06f00d12007d8a7bbd3db1a0907ee2d237445f00a80; `audit.py` 113207c2d3ed249ed966f327961615e2eee82c01726e66e81f447c1d18798a7e; `prereg.json` 27bb7437d063186724f2a65fdf34db40afa24ca3f5383a85ad515973becc56f4. Original single-call supervisor `run_block.py` was 2f1098cf5cba37badbb87087701d207ab3ba8ea4438161c7b3761243da9400c1. After external tool timeout in allocation a1, allocation a2 used supervision-only `run_chunk.py` abb1fb069fbc5bdb40ff0d0840becd26021689f064606bdb5e405d55edfd2a24; case source/predicate/schedule/audit were unchanged.

## Outcome

| trajectory | n | final check | Right admitted | persisted A dx | persisted B dx |
|---|---:|---:|---:|---:|---:|
| stable A | 5 | 5/5 PASS | 5/5 | +2 all | 0 all |
| A -> B | 5 | 0/5 PASS (5/5 refusal) | 0/5 | 0 all | 0 all |
| A -> B -> same living A | 5 | 5/5 PASS | 5/5 | +2 all | 0 all |
| unrelated pointer move | 5 | 5/5 PASS | 5/5 | +2 all | 0 all |

All 20 cases preserved X focus across the trajectory/check boundary. Pre-effect, post-effect/refusal and final physical state had no held keys or mouse buttons in 20/20. The independent auditor re-read the saved SVGs, re-counted final selection handles from PNGs, verified image hashes, schedule, event ordering, geometry and physical-release evidence, and returned `PASS_SELECTION_FINAL_CHECK_AUDIT`, errors 0.

The final-check-capture to admit/refuse bookkeeping interval was descriptive only: medians stable 1.194 ms, switch-to-B 1.417 ms, A-B-A 1.041 ms, unrelated-pointer 0.988 ms. These are not a task-speed or atomicity claim.

## Retained interruption

Allocation `selection-final-check-20260916-a1` is retained incomplete. Four cases completed; case 04 started but produced no result before the container tool killed the supervising command; later cases did not start. Those rows are not pooled with a2. a2 starts from a fresh root and executes all 20 cases once under the same frozen scientific bytes/schedule using only chunked supervision.

## H / T / D / C / U

H: one final selection-specific observation can reject a selection change that has already happened while preserving harmless changes and same-object return.

T: 20 serial first outcomes in unmodified installed Inkscape 1.4, Xvfb 1100x800x24, ordinary XTEST keyboard/pointer input, exact saved-SVG scoring; no model/game call.

D: PASS_SELECTION_FINAL_CHECK_SCOPED; zero B false-admits, zero valid-A false-stops, zero wrong-object effects, release/focus/audit gates all pass.

C: the selection state can change after this last observation and before the application consumes Right. Screenshot paint state can also lag application semantic state under other timings; this block deliberately tested only already-completed selection trajectories.

U: authored trajectories, one host/application/version/layout/action, standalone harness rather than latest full caller/Executor, no natural race rate, no general semantic identity, no calibrated worst-case timing.

## Next single question

Insert exactly one selection change **after** the frozen final check but before the same Right input. Keep the predicate, fixture, action and scorer unchanged. If Right can again move B, the current check is only a precondition observation and the next architectural question becomes effect-owner/application-side conditional commit rather than more screenshot polling.
