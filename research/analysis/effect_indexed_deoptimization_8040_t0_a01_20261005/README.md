# Issue #8040 T0 A01 — effect-indexed semantic deoptimization

This additive finite-method study tests the Issue's three-operation macro-deoptimization hypothesis. It compares only the candidate's reconstructed generic semantic cursor against a frozen independent oracle; no external action is emitted.

- Base: `d3a51bc4c962b223d05280225042b96a033df8bf` (main refreshed before freeze).
- Branch: `research/8040-effect-indexed-deopt-t0-a01-20261005`.
- Package: `research/analysis/effect_indexed_deoptimization_8040_t0_a01_20261005/`.
- Allocation: `UNJUNO-8040-EFFECT-INDEXED-DEOPT-T0-A01-20261005`.
- H/T/D/C/U and detailed gates: `protocol.md`.

The proposed OrbStack container route was not usable: Docker Engine answered on 2026-10-05, but an exact read-only inspection of the pre-existing `python:3.12-slim` image failed on containerd content blob `sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f` with `operation not supported`. No image pull, container create/start, or cleanup was attempted. The exact formal method is standard-library CPU-only and has no GUI, model, network, or external input; this A01 therefore uses a separate low-priority native-host process as an explicitly labeled environment substitution. It claims no container/OS isolation. Host load was elevated at preflight; the finite run remains one process at `nice -n 10`.

The method does not establish map completeness for real compiled procedures, authenticity of real effect receipts, GUI effect truth, safe runtime continuation, performance, or product benefit. Execution status and audit outcome are reported in `RESULT.md` after the one frozen allocation.
