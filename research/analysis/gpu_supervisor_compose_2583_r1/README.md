# GPU supervisor composition evidence (Issue #4972)

This directory is an additive evidence bundle. It does not modify runtime code, predecessor #2583, or the current #57 formal allocation.

## H / T / D / C / U

**H** — A small local CUDA supervisor can provide only a binary CONTINUE/YIELD hint while a separate final gate owns freshness, ambiguity, and authority admission.

**T** — Run deterministic typed traces in the pinned Docker image `pytorch/pytorch:2.5.1-cuda12.1-cudnn9-runtime`, with CPU oracle comparison, GPU-resident versus CPU-to-GPU input contrasts, mutation controls, and zero authority/input/task-success grants. Preserve source, environment and hashes.

**D** — Scoped evidence passes when labels agree with the oracle, stale or ambiguous rows always yield, mutation controls cannot bypass the gate, and all authority/input/task-success counts remain zero. This does not pass an integrated product evaluation.

**C** — GPU/CPU floating-point values can differ while discrete labels agree; transfer overhead can erase local inference savings; synthetic feature traces do not represent real application observations; a local hint can conflict with another continuation or a user action if integrated without arbitration.

**U** — Real GUI/application correctness, model-boundary/token savings, end-to-end latency, natural workload frequency, multi-GPU portability, and production qualification remain unmeasured.

## Evidence index

- `FORMAL_SCOPED_RESULT.json`: 256 synthetic traces, 0 mismatches, 96 forced YIELD rows, raw hash and zero grants.
- `MUTATION_CONTROL_RESULT.json`: 96 forced-row hint mutations, 0 gate bypasses.
- `GPU_RESIDENT_RESULT.json`: one resident/transfer contrast.
- `GPU_RESIDENT_5SEED_RESULT.json`: five-seed resident/transfer contrast.
- `GPU_BATCH_CONTRAST_RESULT.json`: batch sizes 1, 8, 64, 256 and 4096.
- `cuda_composed_gate.py`: reproducible CUDA runner and Docker command.
- `CONTAINER_RESULT.json`, `REPETITION_RESULT.json`: earlier construction records, retained without relabeling.

## Integration boundary

Current #57's frozen integrated-efficiency plan explicitly excludes local learned controllers. Therefore this bundle is `RETAIN_SCOPED_EVIDENCE` and `HOLD_FOR_BUNDLE_SELECTION`. Adoption requires a new #57-compatible preregistration covering cold/warm/invalidation/repair phases, all-attempt accounting, GPU-resident/transfer provenance, and an explicit benefit rule. No result here claims task success, token reduction, or production readiness.
