# Main-thread scorer polling boundary v1

## Scope

Task: `O3-G2-SCORER-POLLING-BOUNDARY-001`

Immutable base: `64b286722adaf4daae8936cc373d44c559bd86da`

This is a source-closure and synthetic scheduling construction only. It does not
modify `session_map01_v12.py`, the controller/runtime, existing preregistrations
or retained results. It makes no model call, GUI action, X11 input, or formal
MAP01 allocation.

The preceding independent-progress-clock result established a scorer-only event
vocabulary but deliberately left ViZDoom integration unproved. This task asks
which scheduling boundary can sample those outcomes without introducing an
unvalidated background thread on the active `DoomGame` object.

## Source closure

At the base commit, `session_map01_v12.py` owns one ViZDoom `DoomGame` in its
main thread. After setup it blocks on `for line in sys.stdin:`. The independent
`post_control_score` reads `KILLCOUNT` and `DEATHCOUNT` only after a `finish`
command, so it cannot timestamp the first independent useful effect during a
planner wait.

Upstream ViZDoom documentation exposes `get_game_variable`. At upstream commit
`9bbf2f25c8ab8b59709d27a1640f89e61f6205d5`,
`DoomGame::getGameVariable` checks `isRunning()` and directly delegates to
`doomController->getGameVariable(variable)`. The inspected API documentation
and source do not state a same-object multithread-safety guarantee, and a
repository search for `mutex`, `lock_guard`, or `shared_mutex` returned no
matches in the search scope.

This does **not** prove ViZDoom is thread-unsafe. It means a background scorer
thread is not justified by retained evidence. The lower-risk candidate is to
keep scorer sampling and command dispatch on the `DoomGame`-owning main thread.

## Candidate boundary

`main_thread_scorer_polling_v1.py` is a pure-Python scheduling primitive. It
replaces a blocking line-reader *conceptually* with readiness-driven fd input and
periodic sampling:

```text
DoomGame-owning main thread
    |
    +-- fd readiness -> command_handler(line)
    |
    +-- periodic deadline -> sample_fn() -> scorer_sink(receipt)
```

Both callbacks run synchronously on the `run()` caller thread. The module has no
controller emitter. A future session adapter would have to bind `scorer_sink` to
an independent scorer-only stream, never `events.jsonl` / `delivered.jsonl`.

A late loop does not emit synthetic catch-up samples. If multiple sample periods
pass, it emits one current sample and records how many periods were missed. This
preserves epistemic honesty: missing cadence remains missing evidence.

The input side also fails closed on unterminated EOF, invalid UTF-8, and excessive
buffer growth.

## Container validation

The exact candidate bytes were compiled and executed in the container.

- `py_compile`: PASS
- unit regressions: **12/12 PASS**

The tests cover:

- periodic sampling without commands;
- scorer and command callbacks executing on one owner thread;
- privileged scorer payload not entering the command callback;
- long sample and long command paths recording missed periods without catch-up;
- multiple and split commands;
- clean EOF versus partial-command EOF;
- bounded command buffering;
- invalid sample rates;
- a real `os.pipe` command path.

The container has no `vizdoom` package, so no game call is represented by these
tests.

## Synthetic scheduling benchmark

Measurement conditions:

| Condition | Value |
|---|---|
| Python | CPython 3.13.5 |
| Kernel | Linux 6.18.44 x86_64 |
| CPU | Intel Xeon Platinum 8370C @ 2.80 GHz, reported model |
| CPU affinity | CPUs 0-4 |
| Clock pinning | unavailable / not pinned |
| Main work | one polling/scorer thread |
| Synthetic producer | one command-writer thread |
| Command transport | `os.pipe` + `select.select` |
| Scorer cadence | 35 Hz |
| Synthetic command cadence | 50 Hz |
| Repetitions | 12 x 1.0 s |

The sample callback only returns its thread ID. It does not approximate the cost
of `get_game_variable` or scorer persistence.

Observed totals:

- scorer samples: **420**;
- handled synthetic commands: **588**;
- missed scorer periods: **0**.

Timing:

| Metric | Median | p95 | p99 | Maximum |
|---|---:|---:|---:|---:|
| scheduled sample -> sample start | 159.234 us | 294.167 us | 1332.817 us | 2559.266 us |
| sample callback duration | 4.801 us | 5.755 us | n/a | 51.643 us |
| command write -> handler | 137.564 us | 290.068 us | 944.342 us | 1709.187 us |

These values characterize this synthetic Linux pipe/select construction only.
They are not MAP01 timing, ViZDoom getter latency, X11 timing, model latency, or
a hard real-time guarantee.

## H / T / D / C / U

### H — falsifiable hypothesis

A readiness-driven main-thread loop can preserve single-thread game-object access
while providing bounded scorer sampling and responsive command dispatch, without
making scorer payloads controller-visible.

### T — minimum test

First deterministic regressions exercise ownership, isolation, cadence and
failure behavior. Then a finite synthetic Linux pipe benchmark runs concurrent
35 Hz scorer scheduling and 50 Hz command arrival. No live game allocation is
used.

### D — decision

**PASS for the synthetic scheduling primitive; MAP01 integration remains
UNPROVEN.**

PASS requires one callback thread, explicit missed-period accounting, scorer
sink isolation, responsive real-pipe dispatch, and no hidden catch-up samples.
All construction tests passed and the synthetic benchmark missed zero periods.

This does not authorize editing or running the existing MAP01 session. A
versioned session integration must still prove that replacing blocking stdin does
not alter command semantics and that scorer persistence never reaches the
controller channel.

### C — competing explanations / ways this can fail

- A real ViZDoom getter may block or be far slower than the trivial sample callback.
- A long session command handler may delay scorer deadlines.
- Linux `select` behavior and scheduler jitter may differ under WSL/X11/game load.
- Replacing the blocking stdin loop may accidentally change EOF/error/command
  ordering semantics.
- A future adapter may leak privileged scorer state by reusing the controller
  `emit` function.
- Sparse kill/exit events still undercount useful navigation progress even if
  sampled perfectly.

### U — uncertainty

Unresolved uncertainty includes actual ViZDoom getter cost, single-thread API
behavior under asynchronous spectator game time, MAP01 scheduler/capture load,
scorer file I/O, command-loop semantic equivalence, and controller/scorer stream
isolation. No combined uncertainty or coverage factor is justified from the
synthetic benchmark.

## Next gate

The next candidate, if no parallel task already owns it, should be a **versioned
MAP01 telemetry-only session integration**, not a recovery-policy experiment.
It must:

1. preserve all current controller command schemas and authority semantics;
2. keep all `DoomGame` getter calls on the owning main thread;
3. write independent scorer samples/events to a separate scorer-only file;
4. never deliver those samples through controller `emit`;
5. retain explicit sample start/finish timestamps and missed-period counts;
6. compile/test before allocation and freeze source hashes;
7. run one no-retry telemetry validation before any recovery-vs-coast efficacy
   comparison.

A negative integration result is a valid retained outcome.

## Related disciplines

- **Real-time systems:** this is a cooperative event-loop scheduling problem, not
  merely a logging feature.
- **Measurement science:** missed periods are censored evidence and must not be
  reconstructed as fake samples.
- **Concurrency/software architecture:** avoiding unproven shared-object
  multithreading is a correctness choice; ownership stays single-threaded.

Machine-readable result:
`results/main-thread-scorer-polling-v1.json`.
