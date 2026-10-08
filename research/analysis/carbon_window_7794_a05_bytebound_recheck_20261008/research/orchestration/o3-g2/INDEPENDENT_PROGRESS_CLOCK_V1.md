# Independent progress clock v1

## Scope

Task: `O3-G2-INDEPENDENT-PROGRESS-CLOCK-001`

Immutable base: `f678afa8eb7b1db1da7cfd9a15ff65d4c146d74d`

This is a scorer-contract construction and container test only. It does **not**
modify the MAP01 controller/session, runtime authority, model prompt, existing
retained results, preregistrations, or the separately leased G2 release-edge
telemetry lane. It makes no model call, GUI action or OS-input allocation.

## Why this task exists

The retained v38/v39 evidence and the held-input source-closure work now separate
accepted program lifetime from bounded delivered input. The remaining P0 timing
gap is different: the current `session_map01_v12.py` only emits its independent
`post_control_score` when the controller sends `finish`. At that point it reads
ViZDoom `KILLCOUNT`/`DEATHCOUNT` and computes terminal MAP exit. That terminal
score cannot timestamp the first independently useful effect during a planner
wait.

This task defines the smallest event vocabulary needed before integrating a
progress clock. It intentionally does not solve sampling/thread/process safety.

## Contract

`ProgressClock` consumes samples from an **independent scorer**. V1 samples have
only:

- monotonic scorer timestamp;
- kill count;
- death count;
- episode-finished state;
- player-dead state;
- scorer-computed MAP-exit state.

The first sample establishes the episode baseline and emits no event. Later
samples may emit append-only events:

| Event | Polarity | Counts as useful? |
|---|---|---|
| `KILL_COUNT_INCREASE` | positive | yes |
| `MAP_EXIT` | positive | yes |
| `DEATH_COUNT_INCREASE` | negative | no |
| `PLAYER_DEAD` | negative | no |
| `EPISODE_FINISHED_NO_EXIT` | negative | no |

Every event records `controller_visible=false`. The supplied persistence helper
only appends JSONL to a scorer-owned file. There is no controller-delivery
adapter in this task.

V1 deliberately excludes health, ammo, viewport pixel changes and frame hashes
from the sample schema. Those signals may be useful diagnostics, but a health or
pixel change is not automatically useful task progress.

## Fail-closed rules

The contract rejects rather than repairs or guesses when:

- scorer time moves backwards;
- state mutates at an identical timestamp;
- kill/death counters regress without a new scorer epoch;
- `episode_finished` or `map_exit` regresses;
- MAP exit is asserted without episode completion or while the player is dead.

An exact duplicate sample at the same timestamp is idempotent and emits nothing.

## Container verification

Executed against the exact files retained by this task before GitHub publication:

- `python3 -m py_compile`: PASS for module, tests and benchmark;
- `python3 -m unittest -v test_independent_progress_clock_v1.py`: **14/14 PASS**.

The tests cover positive kill/exit events, death/non-exit negatives, first-sample
baseline behavior, exact duplicate idempotence, timestamp/counter regression,
invalid exit states, append-only JSONL and the explicit exclusion of health,
ammo and pixel fields.

### Compute microbenchmark

This benchmark measures only the pure Python scorer state machine. It does not
measure ViZDoom polling, runtime scheduling, filesystem persistence, controller
isolation, model latency or gameplay performance.

Environment:

- CPU: Intel Xeon Platinum 8370C @ 2.80 GHz (reported model; process clock not pinned/verified);
- process affinity: CPUs 0-4;
- Python: CPython 3.13.5;
- kernel: Linux 6.18.44 x86_64;
- concurrency: one Python process / one thread;
- batch: one `ProgressSample` per `ingest` call.

Workload: 100,000 samples per repetition, 3 warmups, 15 measured repetitions.
Sparse deterministic counter changes emitted six events per repetition.

Result:

- median: **193.274 ms / 100,000 samples**;
- range: **183.642–219.828 ms**;
- descriptive median throughput: **517,401 samples/s**.

No runtime latency claim follows from this number.

## H / T / D / C / U

### H — falsifiable hypothesis

A small scorer-only state machine can make independent useful/harmful outcome
events timestampable and auditable without exposing privileged engine state to
the controller or weakening authority semantics.

### T — minimum test

Pure-Python synthetic sequences cover baseline, positive, negative, duplicate,
regression and impossible-state cases. A compute-only benchmark checks that the
state machine itself is not an obvious high-cadence bottleneck. No live sample is
allocated.

### D — disposition

**PASS for the event contract; INTEGRATION UNPROVEN.**

PASS means the standalone state machine is deterministic, fail-closed on invalid
ordering, explicitly polarizes outcomes, does not treat health/ammo/pixels as
useful, and has no controller-delivery path. It does not authorize a live run.

Actual scorer integration remains a separate gate because the current session
owns one ViZDoom game object and concurrent/safe polling has not been established.

### C — competing explanations / ways this can fail

- A kill can be incidental rather than necessary for navigation progress.
- Many genuinely useful navigation actions can produce no kill or exit event,
  leaving useful-control continuity undercounted.
- Polling ViZDoom concurrently from another thread may be unsafe or perturb the
  session.
- Polling only at controller observation boundaries would no longer be an
  independent high-cadence progress clock.
- A scorer stream could accidentally leak privileged state to the controller if
  integration reuses the controller `emit` channel.

### U — uncertainty

Unresolved uncertainty includes scorer cadence/jitter, ViZDoom API thread/process
safety, cross-clock alignment, file-persistence overhead, controller isolation,
and a general navigation-progress oracle. No synthetic benchmark reduces these
integration uncertainties.

## Next gate

Do not connect this module directly to `session_map01_v12.py` yet.

First source-review the safest scorer integration boundary. The preferred design
must satisfy all of the following:

1. privileged scorer state is written to a separate scorer-only stream and never
   included in controller-visible `events.jsonl` / `delivered.jsonl`;
2. scorer timestamps share or have an explicitly mapped monotonic clock with
   runtime/release telemetry;
3. sampling does not call a non-thread-safe ViZDoom object concurrently;
4. controller decisions cannot observe or condition on scorer events;
5. independent kill/exit timing is useful but explicitly sparse; absence of an
   event must not be interpreted as no useful control.

Only after that isolation/safety gate should a versioned session integration be
leased. A later matched recovery experiment must retain both positive and
negative scorer events, including a result with zero positive events.

## Retained result

Machine-readable construction and benchmark:
`results/independent-progress-clock-v1.json`.

Source hashes and all measured repetitions are preserved there. Negative and
incomplete findings are retained: this task does **not** establish navigation
progress coverage or ViZDoom integration safety.
