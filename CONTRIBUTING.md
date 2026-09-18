# Contributing

Agent Interface is research-first. Contributions do not need to start as code.

The most useful contribution is often a simpler explanation of **what work or information the current interface is wasting**, plus an idea for removing that waste without removing information the agent actually needs.

## Three ways to contribute

### 1. Idea

Use the [Idea issue form](https://github.com/Unjuno/agent-interface/issues/new?template=idea.yml) for an architectural or algorithmic suggestion.

A good idea can be short. Explain:

- what is currently wasteful, inaccurate, fragile, or unnecessarily complex;
- what should change;
- why the change should improve token/image efficiency, correctness, latency, reliability, generality, or simplicity;
- any obvious tradeoff or failure mode you already see.

You do **not** need benchmark results or an implementation before opening an idea.

### 2. Research proposal

Use the [Research proposal form](https://github.com/Unjuno/agent-interface/issues/new?template=research-proposal.yml) once an idea is specific enough to test.

Every promoted experiment should state:

- **H — Hypothesis:** a falsifiable claim with metric and environment.
- **T — Test:** dataset/tasks, environment, sample size, changed variable, and stopping rule.
- **D — Decision:** explicit PASS / FAIL / UNCERTAIN condition.
- **C — Competing explanation:** how the apparent win could be misleading.
- **U — Uncertainty:** dominant error sources and scope limits.

### 3. Research harness bug

Use the bug form for reproducible defects in the benchmark harnesses, reports, or runtime experiments. Bugs are important, but Issues are intentionally not limited to bugs.

## First-principles review questions

Before promoting a design change, ask:

1. **What information is actually required for the next correct decision?**
2. **What computation, observation, serialization, or model call carries no new useful information?**
3. **Can that work be eliminated rather than merely compressed?**
4. **What is the cheapest local mechanism that can preserve the same correctness?**
5. **What uncertainty remains, and when must the system escalate back to a stronger observation or planner?**
6. **Does the idea generalize beyond one application or one benchmark fixture?**

The project prefers mechanisms that remove unnecessary boundaries while preserving an explicit fallback.

## Benchmark rules

1. Correctness is a hard gate.
2. Tune on development/screen runs; freeze parameters before fresh/hidden runs.
3. Compare candidate and baseline under the same task/environment schedule.
4. Separate local wall time, serialization bytes, observed pixels, model calls, and actual tokens.
5. Do not rename proxy bytes as tokens.
6. Do not call simulator latency model-in-loop latency.
7. Keep failed/rejected ideas in the research record when they constrain future design.
8. Prefer paired comparisons and multiple fresh replicates for noisy GUI timings.
9. Prefer eliminating unnecessary observation/work before applying lossy compression.
10. A fast path must retain a safe fallback when its assumptions are no longer valid.

## Repository placement

Keep new material in the narrowest existing namespace that matches its role. Do not create new root-level categories when an existing area already fits.

| Material | Preferred location |
|---|---|
| Public/current documentation | `docs/` |
| Experimental evidence | `research/` |
| Scoped quantitative/formal measurement | `research/measurement/` |
| Cross-component/domain composition | `research/integration/` |
| Coordination-semantics experiments | `research/coordination/` |
| Promoted runnable semantics/code | `runtime/` |
| Packaging/release-readiness work | `release/` |
| Public presentation assets | `site/` |

Retained evidence paths may be referenced by Issues, PRs, reports, hashes, and audits. Prefer adding an index/README over renaming or moving completed evidence solely for cosmetic cleanup.

## Adding a research track

Create the experiment under the narrowest applicable research namespace (for example `research/measurement/<name>/` or `research/integration/<name>/`). Use a direct `research/<name>/` directory only when no existing category fits. A typical experiment directory contains:

```text
REPORT.md
<benchmark>.py
summary.csv
```

A good `REPORT.md` includes environment details, exact success counts, p50/p95/p99 where meaningful, negative results, and a short error check.

## Safety

Real GUI harnesses can type, click, drag, save files, and close windows. Run them only in an isolated X session/container with disposable application state.
