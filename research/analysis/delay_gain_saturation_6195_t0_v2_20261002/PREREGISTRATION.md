# Issue #6195 successor T0 v2 — saturation boundary

Allocation: `DELAY-GAIN-SATURATION-6195-T0-20261002-01`  
Owner: local Windows Codex task `01a0b990-3d17-72f1-a908-9a2072104ce5`  
Frozen main at allocation creation: `936a86c1026e70ee68221c773b5e367b4ed1947a`  
Window: 2026-10-01 21:35–21:50 UTC  
Branch: `research/6195-delay-gain-saturation-t0-20261002`

## H / T / D / C / U

**H.** For the exact-rational authored plant `x[t+1]=x[t]+u[t]`, gain `6/5`, initial state `1`, horizon 8, actuator cap `1/2`, and forbidden magnitude `3/2`, correctly saturated fresh, delayed, and history-reconstructed routes remain actuator-feasible; history reconstruction equals fresh feedback. The unsaturated delayed recurrence is only a mathematical counterfactual and is never an admissible route.

**T.** One candidate invocation emits five rows: saturated fresh, saturated one-step delayed, saturated history-aware, saturated stale-source hold, and unsaturated delayed `counterfactual_only` with `actuation_admissible=false`. A separately implemented auditor reconstructs exact rational states, inputs, source ticks, saturation amounts, and boundary crossings. It rejects five copies corrupted by (1) an actuator-cap violation, (2) row deletion, (3) counterfactual relabeling, (4) source-tick drift, and (5) forged boundary-crossing metadata.

**D.** `PASS_METHOD_SCOPED` only when all four admissible rows obey `|u|<=1/2` at every tick; the unbounded row is unmistakably non-actuating; history-aware equals fresh exactly; saturated delayed does not reach `|x|>=3/2` in eight steps; unbounded counterfactual first reaches it at the frozen step; and all five corruptions are rejected. Candidate runs once. Auditor runs once only if candidate exits 0. Any start-gate failure or mismatch is terminal STOP/FAIL; no retry, seed, or alternate parameters.

**C.** Authored scalar recurrence and finite horizon only. Exact fractions establish arithmetic reproducibility, not plant validity.

**U.** No GUI/DOOM stability, physical actuator, safety probability, task effect, human control, real-delay envelope, GPU benefit, or product claim.

## Execution boundary

Host CPU / CPython standard library only. No container or WSL is invoked: #5085 has no #5139 GPU/Docker lease and container inventory is unresolved; this study has no container-dependent semantics. No network/model/GPU/CUDA/GUI/application/user-data/physical-input access. Construction tests may run before the formal window. Formal candidate and audit outputs must not exist before their respective single invocations. Dedicated output directory: `outputs/DELAY-GAIN-SATURATION-6195-T0-20261002-01/`.
