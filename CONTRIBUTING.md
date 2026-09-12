# Contributing experiments

Agent Interface is currently research-first. Contributions are most useful when they falsify a specific design claim rather than only add features.

## Required experiment record

Every promoted experiment should state:

- **H — Hypothesis:** a falsifiable claim with metric and environment.
- **T — Test:** dataset/tasks, environment, sample size, changed variable, and stopping rule.
- **D — Decision:** explicit PASS / FAIL / UNCERTAIN condition.
- **C — Competing explanation:** how the apparent win could be misleading.
- **U — Uncertainty:** dominant error sources and scope limits.

## Benchmark rules

1. Correctness is a hard gate.
2. Tune on development/screen runs; freeze parameters before fresh/hidden runs.
3. Compare candidate and baseline under the same task/environment schedule.
4. Separate local wall time, serialization bytes, observed pixels, model calls, and actual tokens.
5. Do not rename proxy bytes as tokens.
6. Do not call simulator latency model-in-loop latency.
7. Keep failed/rejected ideas in the research record when they constrain future design.
8. Prefer paired comparisons and multiple fresh replicates for noisy GUI timings.

## Adding a research track

Create a directory under `research/` containing:

```text
REPORT.md
<benchmark>.py
summary.csv
```

A good `REPORT.md` includes environment details, exact success counts, p50/p95/p99 where meaningful, negative results, and a short error check.

## Safety

Real GUI harnesses can type, click, drag, save files, and close windows. Run them only in an isolated X session/container with disposable application state.
