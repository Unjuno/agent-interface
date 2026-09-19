# MAP01 release telemetry v2 construction

Status: **OFFLINE PASS — MAP01 LIVE INTEGRATION NOT YET AUTHORIZED.**

Task: `O3-G3-RELEASE-BATCH-TELEMETRY-001`  
Base: `73b1b685737e6cc258b5eeab39b8111668d6971f`

## Blocking correction to v1

The retained v1 candidate is useful but not safe to integrate into MAP01. For each explicit key-up, v1 performs `up -> d.sync -> input_state -> return`. A multi-key historical hold releases keys sequentially, so v1 inserts a synchronous owner-state round trip between key releases. For `Down+space` this can extend the later key's hold merely because telemetry is enabled.

Therefore the v1 Xvfb result remains valid only for its single-key primitive. It does not authorize MAP01 integration.

## v2 construction

`input_transition_owner_v2.py` wraps unchanged `input_owner_v10` and makes explicit `up` / `button_up` return only a cheap receipt containing caller timestamps around the original synchronous v10 call. It performs no post-release state query and no telemetry publication.

`doom_retained_input_backend_v2.py` collects those receipts in the step thread. While `self.held` is non-empty it does nothing else. Only after the final key has been released does it:

1. call `input_state` once;
2. evaluate backend ownership, intent-token, owner-empty, and interruption consistency;
3. publish one `input_release_batch_v2` aggregate event containing all per-key receipts.

Any interruption or ownership mismatch makes `owner_transition_verified=false`; it is not relabelled as a normal direct release.

## Deterministic offline tests

`python3 -m py_compile` passed for all new Python files.

- `test_input_transition_owner_v2.py`: **4/4 PASS**
- `test_doom_retained_input_backend_v2.py`: **6/6 PASS**

The critical two-key regression proves exact owner-call order:

```text
up(a) -> up(d) -> input_state
```

There is no owner-state sample and no event publication between the two up calls. A single-key release still produces exactly one post-batch sample/publication. Owner-not-empty, stale backend ownership, and any lease interruption all fail closed.

## Xvfb two-key development experiment

The first launch attempt ended before any trial because Python Xlib looked for a missing `/opt/xvfb/.Xauthority`. This is an infrastructure setup failure, not a scientific result. The same probe was rerun with Xvfb `-ac` and an explicit empty XAUTHORITY.

Conditions:

- Python 3.13.5
- Linux 6.18.44 x86_64
- Intel Xeon Platinum 8370C @ 2.80 GHz
- process affinity: 5 logical CPUs (`0..4`)
- Xvfb: 800x600x24, local UNIX socket
- batch: 500 trials
- each trial: press `a+d`, verify both physically down, release `a`, release `d`, then perform the first owner-state sample and verify both physically up

Results:

| Metric | Result |
|---|---:|
| both keys physically down | 500 / 500 |
| both keys physically up after batch | 500 / 500 |
| exact `up, up, input_state` ordering | 500 / 500 |
| per-release caller bracket median | 161.258 µs |
| per-release bracket p99 | 2.855298 ms |
| local gap between release 1 return and release 2 start, median | 0.429 µs |
| local gap p99 | 0.746 µs |
| two-release batch window median | 350.306 µs |
| two-release batch window p99 | 3.539280 ms |
| post-final-release `input_state` delay median | 53.903 µs |
| post-final-release delay p99 | 1.273676 ms |

The 128.924 µs maximum between-release local gap is an observed scheduler/outlier event; the p99 is 0.746 µs. No X11 query or telemetry emit occurs in that interval. The post-batch state sample can delay downstream feedback, but it occurs after the last release and therefore does not extend the commanded hold.

These are development Xvfb timings, not MAP01 latency and not hard real-time guarantees.

## H / T / D / C / U

**H — falsifiable hypothesis.** Release telemetry can preserve historical multi-key release ordering by deferring all state sampling/publication until after the final key-up.

**T — minimum test.** Unit-test two-key ordering and fail-closed ownership/interruption cases; then run 500 two-key Xvfb trials requiring physical down before release, exact `up, up, input_state` ordering, and physical up after the batch.

**D — decision.** **PASS** for offline v2 construction and the two-key Xvfb primitive. **UNCERTAIN** for MAP01 runtime integration because no VizDoom episode was run under this lease. Formal/live authority remains NONE.

**C — break modes.** Scheduler load may widen caller brackets; backend/owner state may diverge; asynchronous expiry/focus/cancel may supersede explicit cleanup; a post-batch sample can delay the next observation even though it no longer extends the hold; Xvfb timing may differ materially from VizDoom/WSL load.

**U — uncertainty.** Residual release uncertainty is the caller bracket around each v10 call; physical occupancy is not observed continuously. The Xvfb distribution is descriptive for this container only. MAP01 capture/model workload effects remain unmeasured.

## Next gate

Do not compare recovery policies yet. The next permissible experiment is one newly versioned, provenance-complete MAP01 telemetry validation selecting v2, with a new allocation ID and no retry. PASS must require complete batched release coverage for normal holds, terminal empty input, unchanged independent task scoring semantics, and no duplicate/missing batch events.
