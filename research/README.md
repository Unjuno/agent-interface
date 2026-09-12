# Research

This directory is the experimental workspace and evidence record. Directories are research steps, not product versions.

## Tracks

- [`real_apps_v1/`](real_apps_v1/) — input-delivery semantics and fixed-wait vs sparse/reactive control.
- [`real_apps_v2/`](real_apps_v2/) — semantic-method lifetime vs optimized-route lifetime.
- [`real_apps_v3/`](real_apps_v3/) — Guarded Hierarchical Deoptimization, binding repair, and pre-execution guards.
- [`observation_gating/`](observation_gating/) — active track: eliminate model-visible observations that carry no new task-relevant information.

## Environment

Research-only Python dependencies live here:

```bash
python -m pip install -r research/requirements.txt
```

Some harnesses inject real GUI input. Use an isolated X session/container with disposable application state.

## Evidence policy

Start from [`../RESEARCH.md`](../RESEARCH.md) for the evidence ledger, claims taxonomy, promoted results, rejected ideas, and promotion policy.

A research directory should keep the benchmark, raw summary, environment, and negative results close enough that a performance claim can be traced back to its experiment.
