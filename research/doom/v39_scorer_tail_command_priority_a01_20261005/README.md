# Issue #59 A01 — scorer tail command readiness under callback overrun

This package reproduces a liveness defect in the source-pinned `MainThreadScorerStdin.sample_tail` adapter from PR #7692. The documented contract says a ready command censors the tail immediately. The loop only polls readiness while waiting for the next scheduled sample. If synchronous scorer work runs longer than the sample period, the next iteration sees a due sample and invokes the scorer without polling the command pipe.

The deterministic construction uses a 10 ms period and 100 ms deadline. A 1 ms fast control returns `command_ready` after one readiness poll. With 25 ms synchronous fake scorer calls, both a command ready at entry and one becoming ready during the first call receive zero readiness polls; each tail runs four samples until its deadline. `RESULT.json` records `FAIL_READY_COMMAND_STARVATION_ON_SAMPLE_OVERRUN`; the independent audit reconstructs the exact output and passes 7/7 checks. Four unit tests include three result-corruption controls.

## Scope and limitation

This is a synthetic source-boundary construction, not an operating-system pipe timing trial, game/controller run, keyboard action, formal safety assessment, or live allocation. It did not consume command bytes. The archived dependency snapshots support import/context only; the reproduction invokes the pinned adapter with fake loop, clock, scorer, and stream objects. Exact source hashes and the reported source head are in `FREEZE.json`. The local `gh` client was unauthenticated at packaging time, so the PR head was not refreshed during this turn.

## H/T/D/C/U

- **H:** In the frozen adapter revision, a ready command can be delayed behind repeated synchronous scorer calls when each call overruns the sample period. The measured quantity here is readiness polls and tail termination, not wall-clock latency.
- **T:** Run one fast control and two deterministic 25 ms-over-10 ms cases under a 100 ms deadline, with the command ready at entry or becoming ready in the first scorer callback. Stop after this finite three-case construction.
- **D:** FAIL if either overrun case performs scorer work to the deadline without observing readiness; PASS only if each ready command returns `command_ready` before another scorer call. The fast control must show the readiness path is functional.
- **C:** The synchronous callback is a fake deterministic duration and may not capture all OS scheduling or real scorer behavior. A command can become ready just after a readiness poll; polling cannot preempt an already running synchronous callback.
- **U:** No measured real adapter latency, actual stdin readiness, thread scheduling, command handling, input release, model, game effect, benefit, safety, or live-resource behavior. Remote head freshness was not queried this turn.

## Reproduction

From this directory, run `python candidate.py`, `python audit.py`, then `python -m unittest -v test_audit.py`. The candidate refuses to overwrite an existing `RESULT.json`; retain the first output as the raw result.

