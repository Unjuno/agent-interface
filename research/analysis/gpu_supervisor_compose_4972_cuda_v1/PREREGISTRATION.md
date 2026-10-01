# Issue #4972 CUDA supervisor hint — fresh synthetic allocation

Allocation `GPU-SUPERVISOR-4972-20261001-01`; this is a new successor execution after #4973's row-level-raw/auditor gap was discovered. It preserves all #2583/#4973 outcomes and does not repair, reuse, or relabel them.

## H / T / D / C / U

- **H:** On a fixed synthetic 256-trace contract set, the RTX 3080 CUDA implementation of a confidence-only `CONTINUE`/`YIELD` hint exactly matches an independent CPU oracle, while a separate final gate admits only fresh, unambiguous, non-forced rows. High-confidence stale/ambiguous/forced-YIELD rows must never gain authority from the hint.
- **T:** Dataset generated with Python `random.Random(497201)`; 64 rows in each of four explicit strata: fresh-valid, stale-high-confidence, ambiguous-high-confidence, and forced-YIELD-high-confidence. Source values and per-row raw decisions are retained. CPU and CUDA run 30 timed repetitions; timings are diagnostic only. No model, game, GUI, input, network, Docker, or training.
- **D:** `PASS_CUDA_PARITY_AND_NONAUTHORITY_SCOPED` requires all 256 CPU and CUDA hints match independent recomputation; all final admissions match the independent gate; zero stale/ambiguous/forced admissions; raw-only auditor errors=0; all three frozen mutations reject. Any mismatch is `FAIL_CUDA_PARITY_OR_GATE`; source/raw/auditor integrity failure is `HOLD_INTEGRITY`. Timing is reported without a speed gate.
- **C:** Windows host, one NVIDIA GeForce RTX 3080 Laptop GPU, CPython 3.11.9, PyTorch 2.5.1+cu121 / CUDA 12.1, current device/driver and system load. Tiny synthetic rows do not represent a natural route distribution.
- **U:** This is arithmetic/contract evidence only. It does not establish learned-supervisor quality, real workload prevalence, latency benefit, model-call savings, GUI/task quality, runtime safety, or product readiness. The hint has no authority; only the synthetic final gate admits.

## Frozen one-shot boundary

Branch `research/gpu-supervisor-cuda-4972-20261001-01`; additive path `research/analysis/gpu_supervisor_compose_4972_cuda_v1/`. Base is recorded in `FREEZE.json`. Local RTX 3080 host-only window: 2026-10-01 05:15–05:45 UTC, assigned by the user's direct instruction in this conversation; separate from the OrbStack CPU queue. Verify GPU idle and CUDA device immediately before one candidate process. Candidate command: `python runner.py`; run `python audit.py` once only if the candidate exits 0. No retries, tuning, external effects, or process/container termination. If the GPU is busy or the window expires, preserve STOP and do not invoke the candidate.

