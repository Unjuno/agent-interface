# Local paused-Xvfb standard-caller trial — R01

**SCHEDULE_ENDPOINTS_PASS_ORACLE_EXACT_ONCE_FAIL.** The frozen integration test ran once and passed (1 test, 0 skips, inner and host exit 0). A separate raw audit reconstructs 20 declared endpoint checks, but finds three old-window KeyPress/effect-handler events where the existing oracle's task text claims “one initial a effect.” The old property is assigned `[1]` every time, masking the repeated handlers. Preserve both the original test result and this stricter task-oracle counterexample; this is not an unqualified task-success result.

## Frozen scope and execution

- Base main: `2b6f7aaa1d16813d7e21b2b5c97e2771ac2d408c`; source freeze `8c696acd3`; conditions freeze `8a77e797c` before the attempt marker.
- Native Ubuntu WSL2/Python 3.12.3 on the user-selected PC, not WSLc or Docker. One newly owned authenticated Xvfb `:88`, TCP disabled, 1024×768×24. Input is confined to this synthetic X domain; no Windows desktop input is requested.
- Two inherited logical CPUs, nice +10, one test job, BLAS/OMP thread count 1; test timeout 210 s with finite termination/kill cleanup. See [conditions](conditions.json), [preflight](environment-preflight.json), [all dependency versions](pip-freeze.txt), [216 source hashes](SOURCES.json), [launcher](run_trial.py) and [host receipt](host-launch.json).
- This is a separately frozen native-WSL successor. The earlier unexecuted WSLc `LIVE_NEXT_RUN.md` remains unchanged; no WSLc allocation was consumed or retried.
- Prestarted cancel supervisor enabled, acknowledgement hold 0, process-method trace enabled, one requested 1000 ms Xvfb pause. The launcher retained the integration test's outer scratch at its original path, leaving other temporary-directory semantics unchanged. The `raw/` tree preserves 46 original files including public requests/reports, native PNGs and application/owner receipts.

## Reconstructed endpoints

| Endpoint | This one sample |
|---|---:|
| Actual cancel tool invocation to return | 254.183630 ms (declared bound 300 ms) |
| STOP-request to CONT-request receipt interval | 1000.444147 ms |
| CONT receipt to independent all-up readback | 155.809827 ms |
| Fresh input invocation to independent effect readback | 89.901451 ms |
| Fresh app effect commit to independent readback | 14.073487 ms |

The caller returned while the private server was stopped. The terminal cancellation recorded exact owner retirement, supervisor XRes disconnection observation and release readback. A separate parent X client sampled all-up afterward and at the 8.5 s horizon. A distinct fresh target changed `[0]` to `[3]`, stayed `[3]` at the horizon, and had one captured fresh-window KeyPress. The old delayed `b` was not observed. The old cancellation/terminal/after-fresh receipts all retain `cleanup_status=UNKNOWN`, `release_confirmed=false`, `task_success=null`, late-request possibility and no replay. These observations do not prove that every old server queue was empty.

Each interval above is elapsed monotonic nanoseconds divided by 1,000,000 to obtain milliseconds; the endpoints are recorded under explicit `*_monotonic_ns`/`timing_ns` names in [result.json](result.json). The STOP receipt begins before sending STOP, so its interval is not an exact duration of the kernel's stopped state. No model call, matched control arm, broad reliability or hard real-time guarantee was measured.

## Task-oracle counterexample

The old window has KeyPress timestamps 42,350,865,579; 43,385,434,374; and 43,425,756,473 ns in `synthetic_application_effect.app_key_events`. All three have corresponding `effect_committed_ns`; the latter two occur after the recorded CONT request. The final old property remains `[1]`, and the existing scorer returns `pass` because it compares values rather than handler count. This disproves the literal “one initial” event/effect-handler reading of that scorer's task definition. It does not show three non-idempotent external task outcomes. Key auto-repeat is a plausible explanation, not established by this trace alone.

The new [offline auditor](audit.py) does not import runtime or its scorer. It recomputes timings, property transition, keymap states, separate targets, event count, safety fences and cleanup from retained raw. Its [output](audit.json) deliberately records the exact-once failure separately from the 20 passing endpoint checks. It was written after execution; it is not an additional live observer or another formal trial.

Next: repair the fixture/oracle with explicit non-idempotent effect-count evidence and a pure regression for repeated press handling. Then freeze a new experiment if native behavior must be measured. Do not relabel this old result or rerun R01. Successful key release and a stable idempotent property are insufficient to prove exactly-once task effect.

## Cleanup and remaining limits

The final test cleanup observed all three keys up; no cleanup errors were reported. The owned pidfd CONT/TERM/reap returned Xvfb exit 0. A separate [readback](cleanup-recheck.json) found Xvfb PID 388, test PID 392, old test-session members, lock and pathname socket absent. The private auth cookie was removed and is not published. `xvfb.txt` retains pathname-listener/keymap warnings; actual authenticated readiness and X clients succeeded.

This sample exercises the repaired pidfd helper with the current standard caller, independent X readback, fresh synthetic task and explicit effect timing under one pause. It does not solve physical input, MAP01, native Windows containment, general target-fencing/recovery authority, model/provider integration, matched efficiency, repeated reliability or exactly-once effects. The full goal remains active.
