# Issue #57 current-main Calc cancellation-boundary recheck

Date: 2026-11-21  
Frozen code HEAD: `9a23c57284b18a7e35f35f299f5c15e94d91ad85` (`origin/main`, after PR #10368)  
Platform: Windows, CPython 3.11.9  
Scope: focused synthetic Calc/Fake-X composition and diagnostic-only test changes. No production runtime behavior or acceptance thresholds were changed.

## Revised finding

The initial runs appeared to fail at the 3-second Save boundary and terminal-cancel wait. The retained call report and point-resolution trace now show the earlier cause: the compiled Calc action terminates before dispatch because `calc_entry` is rejected as `STALE` with reason `expired_or_nonfresh_observation`. The test receipt reports `runtime_failed` with `ValueError: Calc entry must use the reviewed stable menu keyboard anchor`.

The retained mint receipt sets `capture_freshness_ms` to 1500. The alias is resolved against observation sequence 1 after it is no longer fresh. The test's Save boundary is therefore never reached: both latest fail-fast boundary snapshots contain `save_state_files=0`, no Save states, and `owner_io_entered=false`. There is no `calc-fake-state.json`, and no input or task effect occurred. These runs are not cancellation/recovery trials and do not establish whether the cancel path succeeds or fails.

This supersedes the preliminary scheduling-sensitivity interpretation below. Earlier timing observations remain historical and instrumentation-perturbed; they do not explain these fail-fast reproductions.

## Commands and evidence

Environment: `PYTHONPATH=runtime/cli_v1;runtime/provider`.

| Run | Outcome | Retained evidence |
|---|---|---|
| Focused normal discovery | PASS 2/2, 12.738 s | `focused-normal.log` |
| Focused optimized discovery | FAIL 1/2, 15.361 s | `focused-optimized.log` |
| Fail-fast focused normal | FAIL at stale-anchor rejection, 6.509 s | `failfast-normal.log`, `artifacts-failfast-normal/` |
| Fail-fast focused `-O` | FAIL at stale-anchor rejection, 8.263 s | `failfast-optimized.log`, `artifacts-failfast-optimized/` |
| Point-resolution normal | FAIL; explicit `STALE/expired_or_nonfresh_observation` | `resolution-normal.log`, `artifacts-resolution-normal/` |
| Close-receipt normal | Expected test failure preserved; close verified | `close-receipt-normal.log`, `artifacts-close-receipt-normal/` |
| Close-receipt `-O` | Expected test failure preserved; close verified | `close-receipt-optimized.log`, `artifacts-close-receipt-optimized/` |

The fail-fast test change polls the retained call report and surfaces its terminal error instead of waiting for Save and then a cancellation receipt after the action has already failed. Its `finally` path closes the owner/server on the failure path. It changes diagnostics/cleanup only; it does not make a stale observation fresh or relax the guard.

Both retained close receipts report `status=closed`, `verified=true`, `owner_process.retired=true`, and exit code 0. `release_confirmed=false` is retained as such; because no input was dispatched, these receipts do not claim an input release. The fail-fast snapshots also preserve `effect_status=unknown`, `task_success=null`, and `replay_allowed=false`.

Earlier full-discovery diagnostic runs remain in this directory. They include different composition failures and scheduling observations and are not pooled as successful cancellation results. The latest focused fail-fast results isolate a pre-dispatch stale-alias rejection.

## Reproduction and interpretation

1. The standard composed caller mints a reviewed `calc_entry` alias from observation sequence 1.
2. The action reaches alias resolution after the alias freshness window.
3. Admission rejects it as stale before owner I/O or any input transition.
4. The public call fails with UNKNOWN effect and no replay permission; test cleanup retires the owner.

The next useful experiment is a bounded caller-side reacquisition/review path after provider delay, with exact same target/process identity and unchanged visual/anchor semantics required. It must demonstrate a fresh observation followed by renewed explicit review/admission; it must not retry the old stale alias or loosen freshness. A controlled positive and negative pair should establish whether reacquisition works and whether changed identity/surface still rejects. Until then, the standard caller composition gate remains open.

## Limits

This is local fake-backed integration evidence only. It does not exercise a live GUI, model/provider call, real user input, input-release recovery, task effect, MAP01, WSLc, matched efficiency, or public-runtime readiness. No timeout or pass criterion was weakened. Issue #57 remains open.

## Historical preliminary observations (superseded diagnosis)

The earlier focused run showed no Save within 3 seconds under `-O`, and a one-off instrumented normal run recorded Save 1.078 s after pending return, owner-I/O entry 110 ms later, cancel response 625 ms later, and terminal observation 906 ms later. Instrumentation perturbs timing; the optimized trace failed to retain later phase events. These observations motivated failure-boundary capture, but they are not evidence that the current fail-fast failure is a cancellation scheduling defect.

## Cancellation-test integrity and one retained recovery failure

The standard accounting test manually awaited an inner `unittest.TestCase` method without capturing its assertion result. The wrapper now catches and re-raises inner exceptions as an outer test failure. This is a test-integrity correction only. `wrapper-honest-normal.log` and `wrapper-honest-optimized.log` both report 1/1 OK after this correction, but their temporary runtime data is not fully paired: the inner raw runtime retains multiple Fake-X runs, while the single cancellation receipt selected by the capture is not reliably associated with that wrapper invocation. Do not use these two logs as paired proof of the runtime cleanup outcome.

The directly retained optimized run `artifacts-reordered-optimized/` is a single-run record. Its point-resolution log records `calc_entry` as `STALE/expired_or_nonfresh_observation`; the composed Calc call still reaches a Save-request Fake-X state, then cancellation exceeds its retirement grace. The cancellation receipt says owner process retired with exit code `-15`, `cleanup_status=UNKNOWN`, `release_confirmed=false`, `task_success=null`, `replay_allowed=false`; its independent Fake-X readback reports empty `keys_down` and `buttons_down` with `verified=true`. The subsequent `interface_close` receipt reports `cleanup_failed/verified=false`, still with release unconfirmed. This single run is sufficient to show the runtime refuses to assert release after the bounded cancellation horizon, even though a separate Fake-X observer found no held inputs. It is a recovery failure, not a release pass.

The earlier `freshness-5000-*` and `artifacts-freshness-5000-*` runs are exploratory and excluded: an initial edit hit the wrong source site, and the captures do not establish matched effective conditions. Preserve them as raw history without aggregating their outcomes.

## Corrected paired wrapper run (2026-11-21)

The actual cancellation test minted two aliases and then performed symbolic Calc preparation before dispatch. That setup consumed the observation freshness budget. The test now prepares the symbolic task first, then observes and mints with the already-supported maximum `freshness_ms=5000` immediately before the compiled request. Production freshness rules were not changed. The test wrapper also rethrows the inner test exception, uses an invocation-specific run directory, and closes/retains diagnostics if stale rejection occurs before a pending call ID is created.

At the same frozen source HEAD, the corrected public accounting test passes 1/1 normally in 5.807 s and under `-O` in 5.949 s. Exact commands and invocation IDs are recorded in `conditions.json`; each run's boundary snapshot, owner raw runtime, point resolutions, cancellation receipt, final Fake-X state, and interface-close receipt are under its matching `artifacts-cleanup-fixed-{normal,optimized}/cancel-accounting-*/` directory.

Both runs reach the Save boundary and block owner I/O before cancellation. Both cancellation receipts have the same result: owner retired with exit code `-15`, `cleanup_status=UNKNOWN`, `release_confirmed=false`, `task_success=null`, and `replay_allowed=false`. Both independent Fake-X readbacks report verified empty key/button state. Both `interface_close` receipts are `cleanup_failed` and `verified=false`. The paired test passes because its contract expects UNKNOWN and replay denial; the cancellation/release reliability gate remains NOT PASSED. An empty independent Fake-X readback does not establish the runtime's custody-bound release receipt.

The corrected optimized run proves the test reaches cancellation, but it still does not prove input-release recovery or a task effect. The preceding exact run-id optimized stale failure is retained separately: it shows `calc_entry` rejected as nonfresh before input, then owner close verified. The intervening 114.8 s optimized failure occurred while the same test still minted before preparation and also ended pre-dispatch stale; it is not combined with the corrected pair.

## Supervisor custody contract audit and focused regression (2026-11-21)

Source audit of `x11_cancel_worker` confirms it requires the retired owner identity and matching session, child PID, X resource base, and binding revision before any release attempt. It records disconnect, release requests, sync, and physical readback. The function explicitly treats this as a stage receipt: current X11 evidence cannot establish queue drainage or owner-exclusive physical state, so the worker always retains `cleanup_status=UNKNOWN`, `release_confirmed=false`, `task_success=null`, and `replay_allowed=false`, even when readback is empty. The paired integration failure therefore reflects the current conservative product contract, not merely a missing result-field promotion. Do not promote this receipt based only on owner retirement or an empty readback.

Focused regression command on the frozen source (Windows CPython 3.11.9): `python -m unittest -v runtime.guarded_x11_v1.test_cancel_supervisor runtime.guarded_x11_v1.test_owned_supervisor_capability runtime.guarded_x11_v1.test_xres_client_fence`; same command under `python -O`. Both pass 41/41 discovered tests with 7 platform skips (normal 3.985 s; optimized 3.366 s). Logs are `supervisor-contract-{normal,optimized}.log`. The tests cover stale/mismatched generation refusal, unrelated resource-base reuse refusal, finite deadline behavior, verified stage readback while retaining UNKNOWN, and exactly scoped UP release.
## Current decision and next experiment

The bounded recovery/release gate remains unmet. The harness now retains invocation-linked point resolution, runtime, Save-boundary state, final Fake-X state, cancel receipt, and close receipt. The normal/-O pair reaches cancellation from the Save boundary, then retires the owner after the grace horizon; custody remains `UNKNOWN`, `release_confirmed=false`, and close is `cleanup_failed`. Empty independent readback is not proof of release, and UNKNOWN tasks are not replayed.

The supervisor source audit confirms that X11 presently cannot promote this stage receipt: XRes retirement and generation checks, scoped UP requests, sync, and physical readback still do not prove queue drainage or owner-exclusive physical state. The 41-test cancel/supervisor/XRes regression passes in normal and `-O` modes while preserving this boundary. A product change must first supply the missing bounded, generation-bound evidence and a negative control that has an empty but unbound readback; until then UNKNOWN is the correct safe result.

Next, test late-operation exclusion independently using the retained cancellation identity and a finite post-retirement horizon, with an old-generation delayed operation and a new-generation positive control. Then adjudicate task effect independently. Keep recovery/release NOT PASSED unless a product-supported identity-bound receipt proves the physical release conditions; do not weaken the current guard to make the test green.
GitHub Issue #57 evidence comment: https://github.com/Unjuno/agent-interface/issues/57#issuecomment-7055903208
