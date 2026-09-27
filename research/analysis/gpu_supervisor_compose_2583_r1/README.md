# GPU supervisor composition evidence (Issue #4972)

This directory is an additive evidence bundle. It does not modify runtime code, predecessor #2583, or the current #57 formal allocation.

## H / T / D / C / U

**H** — A small local CUDA supervisor can provide only a binary CONTINUE/YIELD hint while a separate final gate owns freshness, ambiguity, and authority admission.

**T** — Run deterministic typed traces in the pinned Docker image `pytorch/pytorch:2.5.1-cuda12.1-cudnn9-runtime`, with CPU oracle comparison, GPU-resident versus CPU-to-GPU input contrasts, mutation controls, and zero authority/input/task-success grants. Preserve source, environment and hashes.

**D** — Scoped evidence passes when labels agree with an independently declared oracle, stale or ambiguous rows always yield, mutation controls cannot bypass the gate, and all authority/input/task-success counts remain zero. Earlier self-derived fresh-row results remain retained but are not treated as independent task-oracle evidence.

**C** — GPU/CPU floating-point values can differ while discrete labels agree; transfer overhead can erase local inference savings; synthetic feature traces do not represent real application observations; a local hint can conflict with another continuation or a user action if integrated without arbitration.

**U** — Real GUI/application correctness, model-boundary/token savings, end-to-end latency, natural workload frequency, multi-GPU portability, and production qualification remain unmeasured.

## Evidence index

- `INDEPENDENT_FRESH_ORACLE_RESULT.json` and `gpu_independent_fresh_oracle.py`: 160 independently declared fresh-valid oracle rows, 96 independent blocked rows, CPU/GPU agreement.
- `INDEPENDENT_CPU_CUDA_ADDENDUM.json` and `gpu_independent_cpu_cuda_addendum.py`: same-weight CPU/CUDA agreement and fail-closed blocked-row oracle.
- `FORMAL_SCOPED_RESULT.json`: original 256 synthetic traces, retained unchanged; its fresh-row oracle was partly self-derived and is not treated as independent.
- `MUTATION_CONTROL_RESULT.json`: 96 forced-row hint mutations, 0 gate bypasses.
- `GPU_RESIDENT_RESULT.json`, `GPU_RESIDENT_5SEED_RESULT.json`: resident/transfer contrasts.
- `GPU_BATCH_CONTRAST_RESULT.json`: batch sizes 1, 8, 64, 256 and 4096.
- `cuda_composed_gate.py`: reproducible CUDA runner and Docker command.
- `CONTAINER_RESULT.json`, `REPETITION_RESULT.json`: earlier construction records, retained without relabeling.

## Integration boundary

Current #57's frozen integrated-efficiency plan explicitly excludes local learned controllers. Therefore this bundle is `RETAIN_SCOPED_EVIDENCE` and `HOLD_FOR_BUNDLE_SELECTION`. Adoption requires a new #57-compatible preregistration covering cold/warm/invalidation/repair phases, all-attempt accounting, GPU-resident/transfer provenance, and an explicit benefit rule. No result here claims task success, token reduction, or production readiness.
