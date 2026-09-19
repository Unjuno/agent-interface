# MAP01 measurement integration v2

Status: **CONSTRUCTION PASS — LIVE MAP01 VALIDATION FROZEN, NOT EXECUTED IN THIS CONTAINER.**

Base commit: `7356970b15406c74bd2b404327f39c2e6b546022` (which has parent `ceda6ab...` and therefore includes release telemetry v3).

This is the next integration gate after the retained release-telemetry v3, progress-clock work, and the synthetic telemetry-session integration at `7356970b...`. The synthetic session validates scheduling/persistence with a fake game; this construction targets the unchanged real v12 runtime boundary without claiming a ViZDoom execution. It composes already-retained primitives around immutable `session_map01_v12.py`; it does not introduce a recovery policy, change cover semantics, make a model call, or relabel old allocations.

## Architecture

`session_map01_v13.py` keeps v12 as the controller/runtime implementation and changes only measurement plumbing:

- `doom_retained_input_backend_v3.Backend` replaces the ordinary typed backend, preserving v3's non-staggering per-key direct release evidence;
- `MainThreadScorerStdin` adapts the retained readiness/timing primitives from `main_thread_scorer_polling_v1.py` to v12's existing `for line in sys.stdin` control loop;
- `independent_progress_clock_v2` receives scorer-only kill/death/terminal samples and terminal-locks each scorer epoch;
- scorer samples/events are written only to `scorer-samples.jsonl`, `scorer-events.jsonl`, and `scorer-summary.json`; they are never sent through v12 `emit` and therefore cannot grant controller authority;
- `DoomGame` remains owned by the session main thread. The controller executor still performs X11 input on its established owner/worker path, but every scorer API call is synchronous on the thread that constructed/owns the game object.

The wrapper records hashes for itself, the adapter, v3 release sources, progress clock v2, and main-thread polling in the runtime `sources.json`; v12 already records its established dependency closure.

## Coherent independent scorer sampling

ViZDoom advances asynchronously, so multiple engine reads are not assumed atomic. Each candidate scorer sample brackets the state reads with `get_episode_time()` before and after. It is admitted only when both episode tics match. Up to three bounded attempts are allowed; failure to obtain one-tic coherence aborts rather than fabricating an event timestamp. The sample's monotonic `sample_ns` is taken after the coherent state is known.

This does not prove that kill count is a dense navigation-progress oracle. It only makes the sparse independent events internally better defined.

## Fail-closed retained audit

`audit_map01_measurement_integration_v1.py` requires all of the following before live integration can PASS:

1. `events.jsonl` and `delivered.jsonl` are identical and contain **zero** independent-scorer schemas;
2. every file named in runtime `sources.json` exists at the audited commit and has the recorded SHA-256;
3. the retained direct-input analyzer reports `measurement_ready=true`;
4. every completed hold has one v3 release transition per admitted key, matching intent/key/id/step, complete batch positions, `ordinary_release_candidate=true`, empty post-batch owner state, and `owner_transition_verified=true`;
5. every terminal reports verified empty key/button state;
6. at least four scorer samples are retained, using only the v2 scorer field set and a monotonic clock;
7. scorer events, if any, are v2 controller-invisible events bound to retained sample timestamps;
8. the retained scheduler reports zero missed sample periods in this minimal telemetry validation.

Zero positive scorer events is explicitly valid. Kill/exit events are sparse; absence of one is not evidence that the hold had no useful task effect.

## Container verification

Integration-specific `py_compile` passes. **16/16 tests pass**. They cover real Linux pipe wakeup, scorer-file isolation, v2 progress-event composition and terminal locking, same-main-thread fake-DoomGame ownership, one-tic coherence retry/failure, runtime provenance merge, v3 batch shape, direct analyzer readiness, source hashes, zero-positive acceptance, controller leak rejection, unverified transition rejection, and missed-period rejection.

A development scorer-persistence benchmark ran 15 repetitions × 1,000 samples on Python 3.13.5 / Linux 6.18.44 with process affinity `0..4`. Median was **22.242 us/sample**, range **21.103–26.832 us/sample**. This benchmark uses an API-compatible local progress-clock copy and JSONL sink only; it excludes ViZDoom API calls, X11, capture, controller workload and model latency. It is not a live cadence guarantee.

## Environment block

The current disposable container cannot execute the formal MAP01 validation: `import vizdoom` raises `ModuleNotFoundError`; no local ViZDoom/Freedoom artifact is present; and `pip install vizdoom==1.3.0` fails at DNS resolution. No synthetic result is substituted for the missing episode.

The frozen next allocation is `map01-measurement-integration-live-02`: seed `990613`, skill 1, 60-second episode budget, zero model calls, one `a+d` 250 ms normal hold, 120 ms scorer-only post-hold window, then finish and audit. It is **one run, no retry**. PASS permits zero positive events but requires direct release measurement readiness, zero source/hash/leak/release failures, and zero missed scorer periods.

## H / T / D / C / U

**H — falsifiable hypothesis.** Retained release v3, progress clock v2 and main-thread polling can be composed around v12 without controller-policy changes, scorer leakage, concurrent DoomGame calls, or loss of direct normal-release observability.

**T — minimum test.** Compile and run the 16 integration regressions; verify same-thread and one-tic scorer sampling; freeze all integration hashes and the no-model/no-retry probe. The live part remains one fresh MAP01 run under the frozen preregistration.

**D — disposition.** **PASS construction. UNCERTAIN live integration.** Recovery-vs-coast efficacy remains blocked until allocation `map01-measurement-integration-live-02` passes.

**C — competing explanations / break modes.** Real ViZDoom reads may exceed the 35 Hz budget; asynchronous game progress may defeat three-attempt coherence; WSL/capture load may create missed scorer periods; v3 may expose a real stale-release path in MAP01; final scorer state may disagree with v12's established score at an episode boundary. The first such result must be retained rather than retried away.

**U — uncertainty.** The unresolved uncertainty is now concentrated in the real MAP01 process: scorer cadence/jitter, coherent API-read availability, release-transition completeness under capture load, and actual scorer/controller isolation. Xvfb and synthetic benchmarks do not reduce those uncertainties enough to authorize an efficacy comparison.

## Cross-domain relevance

- **Control systems:** actuator occupancy is separated from evaluator progress, avoiding nominal-duration substitution.
- **Measurement science:** privileged outcome instrumentation is isolated from the system under control and fails closed on incoherent sampling.
- **HCI / embodied agents:** later latency studies can distinguish retained physical control, no-control gaps, positive outcome arrival and harmful outcome arrival without exposing evaluator-only state to the policy.
