# Issue #5372 T1: safety-aware backpressure under endogenous demand

This is an authored deterministic queue-model experiment, not a production runtime benchmark. It tests whether faster local action can increase stale verification work under fixed offered loads and a completion-triggered closed-loop source, and whether delayed-telemetry backpressure reduces that effect while preserving the mandatory safety lane. It does not compare independent FIFO/deadline queues or a priority-only normal-work policy, so it is a scoped T1 rather than a complete evaluation of every policy in Issue #5372.

## Frozen matrix and gates

The 16 cells are four source schedules (`fixed-low`, `fixed-near`, `fixed-high`, `closed-loop`), two local action durations (2 ticks BASE, 1 tick FAST), and two admission policies (FIFO, pressure-aware backpressure). FIFO is the normal-work baseline; a separate mandatory safety lane receives strict priority in both policies. The three fixed schedules offer 12 at stride 4, 24 at stride 2, or 36 at `floor(i*4/3)` ticks. Closed loop starts one request and emits the next when the current local action completes, through horizon 48 or a 36-task cap. The verifier has one shared server; six safety events enter every 8 ticks before horizon, use strict priority and 1-tick service; normal verification takes 2 ticks. Evidence is fresh at age <=4. The pressure policy defers when the 2-tick delayed pending count is >=2; the audit requires its normal pending peak to remain <=4 (threshold + telemetry delay). Retry budget is one.

Primary outcomes are verified task count by horizon 48, stale attempts/retries/UNKNOWN, per-class disposition, bounded pending work, and all safety obligations serviced with maximum release-to-completion latency <=3. Drain runs through tick 160 so final dispositions are observed. The inversion gate compares BASE/FIFO to FAST/FIFO in fixed near/high load and requires a finite higher FAST p95 verified latency or strictly fewer FAST horizon completions. Backpressure must improve that same metric in the matching FAST cell and reduce stale attempts; it must not lower horizon throughput in any FAST near/high/closed cell. The p95 denominator contains only tasks verified by horizon and is survivor-selected, so p95 alone is not sufficient evidence. This is a model result only; it says nothing about a live verifier deployment.

## Local validation

```sh
python3 -m unittest discover -s research/analysis/safety_backpressure_5372_t1_v1 -p 'test*.py' -v
python3 -m py_compile research/analysis/safety_backpressure_5372_t1_v1/*.py
python3 research/analysis/safety_backpressure_5372_t1_v1/simulate.py | python3 research/analysis/safety_backpressure_5372_t1_v1/audit.py /dev/stdin
```

The independent auditor does not import the simulator. Container execution and a second isolated audit are required before any formal finding is claimed.
