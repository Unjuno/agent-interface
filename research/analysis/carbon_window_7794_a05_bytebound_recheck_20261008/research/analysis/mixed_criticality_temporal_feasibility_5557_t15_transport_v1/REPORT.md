# T15-03 result — scoped temporal service-contract feasibility

## Decision

`PASS_TEMPORAL_SERVICE_CONTRACT_SCOPED` for the frozen finite 4-tick model. The result supports only the preregistered claim that a same-tick HI deadline plus observer obligation can make a horizon-total-feasible trace temporally infeasible, while explicit contract scheduling retains the planner minimum on the specified feasible traces.

## Executed allocation and provenance

- Issue: [#5557](https://github.com/Unjuno/agent-interface/issues/5557); allocation `ISSUE-5557-TEMPORAL-SERVICE-T15-20261001-03`.
- Preregistration: comments [#5919418128](https://github.com/Unjuno/agent-interface/issues/5557#issuecomment-5919418128) and [#5919428655](https://github.com/Unjuno/agent-interface/issues/5557#issuecomment-5919428655). Pre-execution local transport-only canary: [#5919438677](https://github.com/Unjuno/agent-interface/issues/5557#issuecomment-5919438677).
- GitHub Actions run: [36774993099](https://github.com/Unjuno/agent-interface/actions/runs/36774993099), job `110090546447`, PR-head commit `3b623b2c4999b891a4c1c09a6492a09d69a66c1e`.
- Container image: `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f` (linux/amd64 manifest `sha256:44ff437bba879d4941b710a369a8f19266aea34b29002807f0c487fabc9eec9b`); runtime Python 3.12.14 on Linux x86_64.
- Exact-head bounded raw transport completed in 0.823 seconds for the six frozen files. Preregistered manifest SHA-256 `d8edd0f4ebae245077da36ff8774fa08dc5ec5e58a2030e48e018916325c5983`; all six individual source hashes matched before execution.
- Workflow SHA-256: `264217ccfe01d9cd6aef56991c65693cdd9c803837e5294b0381bfcebf31548f`.
- Candidate invocations: 1. Independent raw-only auditor invocations: 1. Construction test command: 1 (6/6 passed). No retries.
- Actions artifact `issue-5557-t15-03-36774993099`, artifact ID `11124836811`, ZIP SHA-256 `17c33654b44bbf60441fdb547b0b5c2f6e84698103ba583059e2b9547226c803`.

## Executed commands and retained outputs

Inside the pinned container, after the bounded fetch and SHA verification:

```text
python -B -m unittest -v test_audit.py
python -B experiment.py --output results/formal-03/raw.jsonl
python -B audit.py results/formal-03/raw.jsonl --output results/formal-03/AUDIT.json
```

The exact artifact bytes are retained in `results/formal-03/`:

- `raw.jsonl` — 32 rows; SHA-256 `8142cfe432f2c9be460db7eebb94efab91b18c5cfb6a79ead71305b926ce2f77`.
- `AUDIT.json` — SHA-256 `1d15db37d28ab200bd7be6f9e7d6f95b70ad35eb0463c795a2c557d185a0922f`.
- `environment.json` — SHA-256 `b11f259a42be320e9494ff06f12e9b1816978339666f71421f8731725accc905`.

The formal auditor independently reconstructed all 32 unique cases with zero errors and rejected all three preregistered mutations: false SAT on a temporal conflict, omitted required observation, and silent LO-planner minimum drop. Its output is `PASS_TEMPORAL_SERVICE_CONTRACT_SCOPED`.

As a separate post-retrieval integrity check (not a rerun of the frozen candidate or formal auditor), `python3 -B results/formal-03/verify_retained.py` independently checked row IDs, aggregate-demand arithmetic, per-tick HI/observer service, planner minimum on SAT schedules, explicit no-dispatch UNSAT results, decision counts, and the retained auditor JSON. It passed. The formal one-shot counts above remain unchanged.

## Findings

- Capacity 2: 1 trace is SAT (no HI arrivals); 15 are explicit UNSAT because at least one tick needs 2 HI units plus 1 observer unit against capacity 2.
- Of the four exactly-one-HI traces at capacity 2, the horizon-total comparator calls all four feasible (`7 <= 8`), while the per-tick contract correctly returns UNSAT (`3 > 2` at the HI tick). This is the preregistered aggregate-vs-temporal witness.
- Capacity 3: 15 traces with zero through three HI arrivals are SAT while preserving at least one LO-planner unit; the all-four-HI trace is explicit UNSAT because the planner minimum cannot be met.
- Across all 32 cases: 16 SAT and 16 UNSAT. Every UNSAT contract result has an empty dispatch.

## Limits

This is a deterministic, hand-authored, single-resource, four-tick feasibility model. It does not validate real arrivals, execution-time distributions, clock behavior, semantic value/freshness of observations, a production scheduler, broad real-time schedulability, task effects, or product benefit. No runtime or performance claim follows. T15-01 and T15-02 remain separately preserved infrastructure STOP allocations and were not changed or retried.
