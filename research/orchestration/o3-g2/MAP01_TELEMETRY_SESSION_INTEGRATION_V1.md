# MAP01 telemetry session integration v1

Status: **PASS synthetic session integration; live ViZDoom/MAP01 integration remains UNPROVEN.**

Task: `O3-G2-MAP01-TELEMETRY-SESSION-001`

Immutable base: `a0abe6cf31bd68a416c02fa417baab3704533bfc`

## Purpose

The preceding retained work established two pieces separately: a terminal-locked independent progress clock and a same-thread readiness polling primitive. This experiment composes them with the `session_map01_v12.py` command-routing contract without granting the scorer a controller callback or input authority.

The candidate has three boundaries:

1. `Map01IndependentScorer` reads outcome state only on its construction/owner thread, timestamps the completed getter set, converts it through `independent_progress_clock_v2`, and writes scorer-only JSONL files.
2. `make_v12_command_handler` preserves the existing `submit`, `cancel`, `clock`, `save_fixture`, and `finish` routing shape; rejected commands remain nonterminal.
3. `run_telemetry_control_loop` composes that handler with `MainThreadScorerPolling`, so command dispatch and game-state sampling share one caller thread and missed periods remain explicit.

There is intentionally no scorer-to-controller callback.

## Experimental procedure

Construction was done in a disposable Linux container. The container has Python 3.13.5, Xlib/Pillow and Xvfb, but **does not have the `vizdoom` package**. Therefore the work was split at that hard boundary rather than substituting a fake live claim.

Before formal measurement:

- `py_compile`: PASS;
- deterministic integration regressions: **10/10 PASS**;
- one pre-freeze test incorrectly assumed that a scorer-event file must exist when zero events occur. That was a test error, not a runtime result; the test was corrected before source hashes and the formal benchmark were frozen.

The frozen preregistration pins the three candidate sources plus repository dependency blob SHAs for `session_map01_v12.py`, `main_thread_scorer_polling_v1.py`, and `independent_progress_clock_v2.py`. The formal benchmark was then run **once**, with zero retry.

## Formal container benchmark

Conditions:

| Condition | Value |
|---|---|
| Python | CPython 3.13.5 |
| Kernel | Linux 6.18.44 x86_64 |
| CPU | AMD EPYC 9V74 80-Core Processor |
| CPU affinity | 0-4 |
| CPU clock | not pinned / unavailable |
| Repetitions | 12 × 1.0 s |
| Scorer cadence | 35 Hz |
| Command cadence | 50 Hz |
| Concurrency | owner polling/scorer thread + synthetic command writer |
| Scorer persistence | JSONL samples/events + JSON summary |
| Game object | deterministic fake DoomGame-shaped getters |
| Model / GUI / X11 input | none |

Observed totals:

- scorer samples: **420**;
- commands handled: **600**;
- scorer events: **12**;
- missed sample periods: **0**;
- scorer/controller leakage incidents: **0**;
- owner-thread violations: **0**.

Timing:

| Metric | Median | p95 | p99 | Max |
|---|---:|---:|---:|---:|
| scheduled sample → sample start | 100.344 us | 132.375 us | 192.910 us | 658.250 us |
| sample callback | 16.985 us | 24.235 us | 47.400 us | 185.585 us |
| command write → handler | 102.469 us | 163.467 us | 323.213 us | 937.761 us |

The preregistered responsiveness bound was one 35 Hz period (28.571 ms) for p99 sample lateness and p99 command dispatch. Both passed. All 12 runs stopped on exactly one `finish`, persisted one sample receipt per reported sample, and kept every fake game getter on the polling owner thread.

These values are **not** ViZDoom getter latency, gameplay control latency, X11 timing, model latency, or a human-tempo claim.

## H / T / D / C / U

### H — falsifiable hypothesis

A v12-compatible command loop can add 35 Hz independent scorer sampling and persistence on the same owner thread without changing command routing, leaking privileged scorer state, fabricating catch-up observations, or missing periods under a 50 Hz synthetic command load.

### T — minimum test

Ten deterministic construction tests cover v12 routing, rejection behavior, fixture gating, owner-thread enforcement, scorer isolation, kill/exit event generation, timeout/non-exit behavior, terminal epoch locking, and buffered-command stop behavior. The exact source hashes are then frozen and one 12-second aggregate formal benchmark is run with no retry.

### D — decision

**PASS for synthetic session integration. LIVE MAP01/ViZDoom = UNPROVEN.**

All preregistered synthetic checks passed. This task therefore retains the integration candidate, but it does **not** authorize a recovery-policy experiment or a recovery-vs-coast efficacy allocation.

### C — ways the result can break

- Real `DoomGame.get_game_variable` or episode-state getters may block or have different same-thread behavior.
- Real capture/X11/controller work may delay the cooperative scorer cadence.
- JSONL persistence may interact differently with WSL/filesystem pressure.
- The actual `session_map01_v12` setup/finish/save-fixture paths are not executed in this container.
- Sparse kills/exits may miss meaningful navigation progress even with perfect polling.

### U — uncertainty

Dominant uncertainty is the missing real ViZDoom session. No combined uncertainty or coverage factor is justified from the synthetic benchmark. The timing distribution only characterizes this container and fake getter workload.

## Parallel-main note

After the formal source freeze and one-shot benchmark, another agent advanced `main` with release-telemetry v3 at `ceda6ab15beca499918abd42ca78e86df317cd57`. That result was **not** silently rebased into this experiment. The immutable base and measured bytes above remain unchanged. The next real-session integration must explicitly compose against the then-current release-telemetry contract rather than assuming this branch already contains it.

## Next gate

Create a separately versioned real MAP01 session integration in a repo-backed container that actually has ViZDoom/X11. Freeze exact source hashes, then run **one no-retry telemetry-only validation** that proves:

- all `DoomGame` getters stay on the owner main thread;
- existing controller command/release semantics are unchanged;
- scorer samples/events are written only to scorer-owned files;
- missed periods and getter durations are retained;
- no scorer state enters `events.jsonl` or `delivered.jsonl`;
- terminal score agrees with the independently sampled terminal scorer state.

A failure at that gate must be retained. Only after it passes should recovery-vs-coast policy efficacy be allocated.
