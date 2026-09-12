# Cooperative intent expiry, development revisions 3/4

An execution duration ends a step; it does not by itself limit the authority of
the remaining program. `executor_v3.py` adds an independent absolute
`valid_until_ns` deadline in the runtime's `perf_counter_ns` clock domain.
Admission rejects an expired deadline and one more than 30 seconds ahead.
Receipt does not restart its validity. Callers can derive validity from a
timestamped observation; unrelated remote clocks must not be substituted.

The lease wraps cancellation checks/waits. Expiry during a program produces
`expired`, discards the tail and verifies key release. The backend also checks
expiry before each new key-down. Key-up cleanup is permitted after expiry.
This is cooperative enforcement, not a hard real-time watchdog. Python
scheduling, X11, file/PNG and stdout blocking can delay checks or release.

## Development comparisons

Two paired XTerm cohorts are retained:

- `lease-development-01`, seeds 900101/900102: first implementation.
- `lease-development-02`, seeds 900301/900302: new backend revision after finding
  and removing logging between the validity check and the input API call.

Each arm runs a 400 ms held key followed by task-token input. The client records
a comparison deadline 200 ms ahead in the same WSL monotonic clock domain.
Duration-only ignores that deadline. The candidate enforces it. Arm order is
reversed for the second seed. Source snapshots/hashes are saved before each
cohort. These are small functional comparisons, not a preregistered efficacy
or model-speed benchmark.

In the latest cohort, both duration-only episodes started the tail after the
comparison deadline. Both leased episodes expired inside the hold, stopped
the tail and verified release 0.929/0.940 ms after the deadline. Neither logged
a post-deadline key-down admission. Both then completed the task after a fresh
submission; independent saved-output checks passed for all four episodes.
The candidate required **two accepted programs**, versus one for duration-only.
This demonstrates bounded authority with an extra decision boundary, not faster
completion. Release times are local observations, not guarantees.

`input_admission` records the checked time immediately before the input API;
revision 4 also records acknowledgement after X11 sync. Neither timestamp proves
an atomic deadline at the actual OS input-injection instant. Baseline does not
have per-key admission records, so its corresponding count is unavailable;
the baseline comparison uses observed tail-step start timestamps.

## Self-use and a discovered flaw

In `lease-assistant-01`, the assistant inspected the initial XTerm screen,
submitted an already expired five-second observation-derived intent, then a
new thirty-second intent. The first request was rejected without acceptance;
the second typed/saved `t900201`, independently verified. This used revision 3.

Review then identified a real ordering flaw: revision 3 emitted admission logs
between its check and XTEST. `test_input_boundary.py` injects a 200 ms logger
stall with a 100 ms deadline and a mocked input API, demonstrating late injection
in archived revision 3. Revision 4 moves logging after injection. The same test
confirms that this stall no longer delays that input call beyond the deadline.
It does **not** prove timely release under stalled logging; a blocked worker can
still hold keys too long. Old evidence/source remains unchanged.

Five tests cover absolute expiry, stale admission, interrupted hold/tail, and
the two logging-order cases. Fresh real GUI probes validate revision 4 in
ordinary conditions. Injected slow capture, transport disconnection, scheduler
stalls, focus changes and partial text expiry still need broader evaluation.
Remote planner generation/dispatch timestamps and actual token usage are not
measured by this experiment. No semantic-version mechanism was added.

## Run

Use `session_v4.py` with the earlier interactive session arguments and include
`valid_until_ns` with each submission. Deadline values must come from the live
runtime clock domain; the observation `capture_ns` can anchor a bounded intent.
Do not copy a historical absolute number from archived evidence.

```sh
python3 -m unittest test_lease test_input_boundary -v
python3 probe_lease_v2.py --out ../../results-local/lease-new
```

The [independent input-owner follow-up](INPUT_OWNER.md) now measures the blocked
observation/logging failure and compares a dedicated input thread against this
cooperative backend. It also distinguishes early key release from delayed
terminal notification. Focus/window validity and task-level integration remain
separate work.
