# #5531 regime-labelled local heartbeat trace — A01

## Purpose and scope

This is a prospective **trace-capture feasibility allocation**, prompted by the
read-only eligibility HOLD in the latest #5531 refinement. The retained N01
rows are isolated checkpoint/read outcomes, not a cadence of independently
timed heartbeats, and have no external host-regime labels. This A01 records a
new, bounded 10-minute heartbeat stream from one child process plus independent
Windows aggregate-CPU samples. It does not replay, repair, or reinterpret N01 or
any earlier #5531 allocation.

This is not the fixed-timeout / global-phi / regime-conditioned comparison and
does not qualify a failure detector. The worker is a controlled local
stand-in, not an Agent Interface verifier or provider. It remains healthy for
the capture; there are no crash, restart, network partition, invalid-response,
GUI, model, user-data, or authority events. The continuous CPU series and the
frozen 50% split are exploratory host-regime labels. A single healthy trace
cannot support accuracy, completeness, calibration, matched-delay, useful
progress, or production claims.

## H / T / D / C / U

- **H:** A separate observer can retain incarnation-bound monotonic heartbeat
  arrival intervals and independently sampled host CPU regime labels from a
  low-resource local process, yielding a candidate trace for later eligibility
  review without injecting stress or effects.
- **T:** One 600-second Windows host capture. A child emits a heartbeat every
  100ms and a separate progress counter every tenth heartbeat. A parent records
  receipt time on the shared monotonic clock and samples aggregate processor
  utilization once per second with `GetSystemTimes`. Each event is bound to the
  allocation ID, child PID, random per-run nonce, and sequence. Host regime is
  `ordinary` below 50% busy and `elevated` at/above 50%; retain the numeric value
  and raw samples. No forced load, induced delay, retries, external calls, or
  GUI/input operations.
- **D:** `TRACE_CAPTURED_SCOPED` only if the one candidate exits normally, all
  heartbeats have contiguous sequence/PID/nonce identity and monotonic worker
  and observer clocks, and host samples span the run with finite `[0,100]`
  values. The trace is a candidate for later eligibility review only. If either
  host regime lacks 100 heartbeat intervals in each chronological half, the
  regime-comparison eligibility result is `HOLD_INSUFFICIENT_REGIME_COVERAGE`.
  Any identity gap, observer-clock regression, malformed record, or runner
  failure is preserved as `FAIL_CAPTURE`/`STOP_INFRASTRUCTURE`; no retry.
- **C:** A fixed 50% aggregate-CPU threshold is only a host-load proxy; it does
  not identify the worker's causal delay regime. Host-wide CPU pressure may be
  unrelated to the child, and the observer shares that host.
- **U:** One process, one host and 10 minutes cannot establish regime-specific
  detector quality, tail probability, threshold calibration, failure
  completeness, restart safety, provider behavior, or operational value. Any
  later comparator needs a separately frozen sample-size/materiality analysis,
  fresh owner/resource checks, and adequate per-regime held-out data.

## Frozen execution

- Allocation: `FAILURE-DETECTOR-5531-REGIME-TRACE-A01-20261005-01`
- Source intake: current `main` at freeze commit recorded in `FREEZE.json`.
- Candidate: `python -B collect.py --duration-seconds 600 --period-ms 100`
- Auditor: after the single candidate exits, `python -B audit.py`
- Output path: `results/a01/`; the collector refuses to overwrite an existing
  output directory.
- Resource: one sleeping child, one low-rate observer, one Windows aggregate
  counter thread; no container, GPU, model, memory stress, GUI, network, or
  external effect. Host-only capture is intentional because the measurement is
  Windows host scheduling and `GetSystemTimes`; this is not a WSLc/container
  result.
- Do not rerun this allocation or tune the threshold after seeing its data.

