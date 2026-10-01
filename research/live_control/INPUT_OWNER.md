# Independent input expiry under blocked capture and logging

The cooperative lease had a concrete failure mode: a worker blocked after
key-down could not release input at expiry. `input_owner.py` now owns XTEST
input on a dedicated thread with its own X11 connection. `session_v5.py` is a
development backend using that owner and the frozen revision 4 observation path.
It is exercised by the paired probe, not yet wired as an interactive CLI or into
the DOOM controller.

The owner checks expiry before dequeuing requests and waits at most 2 ms between
checks, shortening the wait to the deadline. It also observes cancellation.
Key-down is checked again on the owner; expired or cancelled leases cannot
restart input. Key-up cleanup remains possible. Lease identity prevents old
cleanup from releasing a newer intent's held key. Executor v3 still admits only
one active program; this is not general concurrent input arbitration.

The owner performs no image processing, user callback, file write or stdout
write. Its release records stay in memory until the experiment ends. This keeps
the injected logging/capture stall outside the input path, but does not protect
against an X server stall, process stop, GIL-holding extension, scheduler
starvation or blocked X11 call. There is no hard real-time deadline guarantee.
Connection health, command timeouts and process-level supervision remain open.

## Retained experiments

`stalls-01` retains four episodes demonstrating the cooperative failure before
implementation. `stalls-02` compares both backends in eight fresh private-Xvfb
XTerm episodes: two seeds × two faults × two arms. Arm order reverses for the
second seed. A deadline is set 200 ms ahead; the program requests a 1,000 ms
Control hold followed by text. The fault sleeps for 500 ms either in the
post-injection admission logger or before a snapshot. This is a development
comparison with intentional sleeping faults, not a model performance benchmark.

A separate X11 connection samples actual key state, waiting 2 ms between
queries. Sample timestamps are taken after query responses. The last-down and
first-up samples are preserved; their spacing includes query/scheduler time,
so neither is an exact OS transition timestamp or rigorous real-time bound.

| Fault | Cooperative: first sampled up after expiry | Independent owner: first sampled up after expiry |
|---|---|---|
| Logging, two seeds | 301.860 / 303.334 ms | 1.920 / 2.328 ms |
| Capture, two seeds | 371.899 / 363.230 ms | 1.727 / 1.203 ms |

In all four candidate episodes, the owner independently queried and verified
release 0.453–0.706 ms after expiry. However, executor terminal verification
still arrived 301.205–356.882 ms after expiry because the worker was blocked.
**Input release and terminal notification are separate measurements.** The
backend's `held` set is worker bookkeeping, not a live authoritative view after
the owner's asynchronous release.

All twelve archived episodes expired, stopped their tail, and eventually
verified release. Six captured frames reconstruct exactly from their packets
and match PNG pixels. Logger-fault cases expire before their first snapshot.
No saved-task correctness outcome was measured in these fault probes: they test
input authority and cleanup, not successful task completion.

Eight tests passed: the five earlier lease/input-boundary tests and three new
real-X11 checks for expiry without worker progress, cancellation without worker
polling, and rejection of stale cleanup while a new intent holds the same key.
The inherited Xvfb startup code emits socket ResourceWarnings during tests, and
the new connection emits an Xauthority diagnostic in the probe. These did not
fail the runs; connection/startup cleanup still deserves separate maintenance.
The experiment helpers also leave private temporary directories after closing
their processes. They are research harnesses, not a long-running service.

## Reproduce and audit

Run in the documented Ubuntu/WSL environment from this directory, choosing a
fresh output path:

```sh
python3 -m unittest test_lease test_input_boundary test_input_owner -v
python3 probe_stalls_v2.py --out ../../results-local/stalls-new
python3 audit_stalls.py results/stalls-01
python3 audit_stalls.py results/stalls-02
```

Each cohort hashes its directly measured sources before running. Additional
inherited-source provenance was recorded at publication and verified byte for
byte against the prior published commit; it is explicitly labelled retrospective.
Measured source files and negative evidence are retained unchanged.

Next: integrate explicit owner lifecycle and failure reporting into an
interactive runtime, verify ordinary task completion and self-use, then combine
this with focus/window validity. Actual planner latency and tokens remain
unmeasured here; this result improves input expiry during local worker stalls.
