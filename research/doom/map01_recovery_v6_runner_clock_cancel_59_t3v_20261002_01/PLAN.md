# T3V plan — shared-clock v6 runner boundary

Issue: #6261 (successor to #6252 / PR #6254; under #59)

## H / T / D / C / U

**H.** With exact main v6 `_run_arm`, Executor-v10 and Lease using one injected monotonic clock, (A) a delayed planner return before Lease expiry permits matched cooperative cancel and verified release; (B) Lease expiry during a longer planner-clock delay releases before the clock returns and the runner's later cancel is unmatched. The planner end equals the exact delayed-clock return value. Normal backend return after observing cancel is Executor terminal `completed`; deadline expiration is `expired`.

**T.** Fresh allocation `MAP01-V6-RUNNER-CLOCK-CANCEL-59-T3V-20261002-01`, base `4cf0a3dfde1219671b671bf0a9079a11dcb2e159`, additive path `research/doom/map01_recovery_v6_runner_clock_cancel_59_t3v_20261002_01/`. Execute the exact current-main v6 runner, Executor-v10 and Lease through a fake session/backend. The only seam is injecting the same `perf_counter_ns` function into the exact Lease constructor. Host CPython only: no shared container assignment, game, GUI, model/provider, GPU, network, physical input or live application. One 30 ms construction case; if it passes, one candidate invocation containing A=(600 ms timer, 400 ms clock delay, 2000 ms Lease) and B=(600, 1600, 1500 ms), then one independent raw-only audit only after candidate exit 0. Zero retries. Candidate and construction rows, stdout/stderr, and all failed predicates must be durable before exit.

**D.** PASS only when source/package hashes match; construction has exact clock binding, matched/observed cancel, terminal `completed`, and verified release; A has planner-end equal to delayed clock return, matched/observed cancel, `completed`, release 350–2000 ms after timer expiry and within 50 ms after return/cancel; B has `expired`, release within 50 ms of planner-start + 1500 ms and before clock return, then unmatched/unobserved late cancel; independent raw-only audit has zero errors. Any failure is retained, not rerun.

**C.** Fake session/backend boundary, not real RPC, process scheduling, X11 or game behavior. Shared injected clock aligns runner, Lease and receipt timestamps but does not measure natural transport latency.

**U.** No live MAP01, useful task effect, threat response, physical occupancy, safety/efficacy, human tempo, production or #59-completion claim.

## Why this is a new successor

The #6252 T3U allocation remains STOP and unchanged: its only construction invocation exited 1 because the harness required `cancelled` although exact Executor-v10 records a cooperative backend return as `completed`; the failed row was not retained. T3V uses a fresh allocation/base and fixes both defects prospectively (status follows exact Executor semantics; every failure row is persisted). No T3U candidate scenario ran, and this package does not edit that historical evidence.

## Exact timing cases

Both cases use a real monotonic clock (`time.perf_counter_ns`) through the same callable injected into Lease; the runner's delayed `runtime_clock` returns one captured value. The fake backend waits on exact Lease cancellation/deadline semantics. Case A expires its 600 ms planner timer, blocks in the runner's third clock call for 400 ms, then requests cancellation while the 2000 ms Lease remains live. Case B's 1500 ms Lease expires during the 1600 ms blocked clock call; after return, the runner should observe that the fallback already released and issue an unmatched cancellation.

## Reproduction and evidence

`python3 -m unittest discover -s research/doom/map01_recovery_v6_runner_clock_cancel_59_t3v_20261002_01 -p 'test_*.py' -v`

`python3 research/doom/map01_recovery_v6_runner_clock_cancel_59_t3v_20261002_01/run_t3v.py --construction`

If and only if construction passes: `python3 research/doom/map01_recovery_v6_runner_clock_cancel_59_t3v_20261002_01/run_t3v.py`, followed by `python3 research/doom/map01_recovery_v6_runner_clock_cancel_59_t3v_20261002_01/audit_t3v.py` only when the candidate exits 0. The execution freeze and package SHA manifest are committed before either invocation. Raw results, stdout/stderr, audit, report and hashes remain in this path.
