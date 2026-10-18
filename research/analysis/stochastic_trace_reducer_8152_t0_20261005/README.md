# Issue #8152 T0 — stochastic authority-preserving trace reduction

This is a finite, synthetic CPU experiment for the unverified successor idea in [Issue #8152](https://github.com/Unjuno/agent-interface/issues/8152). It does not replay a repository failure or exercise a GUI.

## Frozen question

Compare single-run screening (A), conservative fixed-64 statistical screening (B), and an 8-to-64 sequential screen (C) on twelve seeded instances across four preregistered strata. Every candidate must retain reset, lease, and release ancestry; target success is an exact fingerprint, not exit code 17. Final traces are checked on paired held-out seeds disjoint from all baseline and search seeds. The report uses conservative simultaneous one-sided exact Clopper–Pearson bounds for final-minus-original target recurrence, with family-wise alpha 0.05 and a 0.20 non-inferiority margin. The independent auditor reconstructs every raw oracle response and recalculates baseline and candidate gates.

## Reproduction and one-shot boundary

Run construction checks before freeze:

```sh
python3 -B -m unittest discover -s research/analysis/stochastic_trace_reducer_8152_t0_20261005 -p 'test_*.py' -v
python3 research/analysis/stochastic_trace_reducer_8152_t0_20261005/prepare.py
```

Then execute exactly once, only on the frozen base commit and pinned image:

```sh
python3 research/analysis/stochastic_trace_reducer_8152_t0_20261005/run_formal.py
```

The runner uses `/Users/taka/.orbstack/bin/docker`, `--pull=never`, `--network=none`, a read-only root, bounded CPU/memory/pids, and only a results-directory output mount. Candidate and auditor are separate container invocations. The candidate is mounted only its own source, simulator, and frozen spec; sealed generator truth is not mounted. Any formal output, including a failure, forbids another invocation under this freeze. Preserve `results/` and make any correction as an additive successor.

`FREEZE.json` binds source and input hashes. `results/RUN.json` records invocation counts, exit codes and hashes; raw output and logs are retained verbatim. A passing result is only `METHOD_PASS_SCOPED` for this authored finite model; it is not evidence of live GUI reliability, causal minimality, safety, or deployment suitability.
