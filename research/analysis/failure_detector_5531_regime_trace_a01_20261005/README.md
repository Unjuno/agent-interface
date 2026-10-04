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

## A01 result — 2026-10-04 UTC

The one frozen candidate invocation exited 0 after 600 seconds. It retained
6,000 heartbeat rows, 600 progress rows, and 595 independent host-counter
samples. The frozen raw-only auditor ran once and returned
`PASS_TRACE_CAPTURE_SCOPED` with no structural or timing errors. Median
observer heartbeat interval was 100.002 ms (maximum 104.705 ms); median child
interval was 99.999 ms.

**Current disposition: `HOLD_INVALID_UNAUDITABLE_HOST_REGIME_LABELS`.** A later
review found that `GetSystemTimes` includes idle time in the kernel counter,
while the collector adds idle, kernel, and user deltas before deriving busy
percent. This double-counts idle, so the recorded 595 `elevated` labels and
5,991 elevated intervals are historical outputs of an invalid formula; they
cannot establish actual host regimes. The collector retained no raw counter
deltas, so the labels cannot be reconstructed or corrected from A01. The
heartbeat/raw event streams were retained, but the regime-comparison result is
invalid and remains HOLD. See the additive
[`review-correction-02/RECHECK.json`](results/review-correction-02/RECHECK.json).

The original audit's `PASS_TRACE_CAPTURE_SCOPED` remains preserved as a
historical structural/timing result; it did not independently derive the
Windows busy-percent arithmetic. This trace is not detector calibration, a
fixed/global/regime-conditioned comparison, or a performance result. Earlier
#5531 outcomes remain unchanged.

`results/a01/OUTPUT_SHA256SUMS.txt` is the collector's pre-audit manifest. The
post-audit seals were initially committed with newline-normalized JSON/text
files, so the recorded hashes did not match several committed blobs. The
evidence files have been re-staged under byte-preservation attributes and the
additive review recheck verifies both local and committed bytes. The candidate
stdout-tail and stderr files remain as captured; the exact worker stream is
`worker-stdout.jsonl`.

### Handoff

Do not rerun A01 or retune its threshold after seeing the data. Any later trace
requires a new, prospectively reviewed allocation that retains raw idle,
kernel, and user counter deltas and derives busy percent without double-counting
idle. Per-regime held-out sample-size review is required before any detector
comparison. This trace alone does not authorize suspicion-policy or runtime
changes.
