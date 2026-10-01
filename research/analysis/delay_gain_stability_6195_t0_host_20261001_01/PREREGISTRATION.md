# Issue #6195 T0 host-CPU allocation

**Allocation:** `DELAY-GAIN-STABILITY-6195-T0-HOST-20261001-01`  
**Owner:** Unjuno, local Windows Codex task `01a0b990-3d17-72f1-a908-9a2072104ce5`  
**Frozen main:** `3d33fe482ad55e99943f2c7b40e92c685c3bf92a`  
**Window:** 2026-10-01 19:05–19:20 UTC  
**Branch:** `research/6195-delay-gain-stability-t0-host-20261001`

## H / T / D / C / U

**H:** In the authored scalar plant `x[t+1]=x[t]+u[t]`, gain `k=6/5`, and initial state `x[0]=1`, fresh feedback is stable while treating a one-step-old state as current produces an unstable oscillatory recurrence. Reconstructing current state from the stale observation plus complete known actuation history should match fresh feedback; missing history, stale source identity, target replacement, plant-gain mismatch, or unmodeled release lag must fail closed in the finite method fixture.

**T:** Enumerate exact rational trajectories for fresh, naive one-step-delayed, history-aware, stale-input capped-hold, and saturated delayed routes over eight steps. Retain the exact recurrence controls, bounded actuator prefix, and five authored corruption/invalidity controls. A separately implemented raw-only auditor recomputes all trajectory strings and gate outcomes and rejects five mutated copies of the candidate output.

**D:** `PASS_METHOD_SCOPED` only if the fresh pole is `-1/5`, the delayed characteristic is `z^2-z+6/5` with root-modulus-squared `6/5`, candidate raw matches the independent exact-rational reconstruction, all five invalidity controls return their frozen YIELD/refusal labels, and all five auditor corruption probes are rejected. A mismatch is retained as FAIL; missing/invalid output is HOLD/STOP. No retries.

**C:** The model is intentionally authored and scalar; saturation and the finite horizon do not represent a real actuator or environment. Policy comparisons are deterministic method controls, not a matched empirical performance study.

**U:** No inference about GUI/DOOM stability, task effect, human control, real observation delay, runtime correctness, safety probability, or GPU value follows. T1 requires eligible retained traces; T2 needs a separately authorized disposable dynamic task and is not part of this allocation.

## Execution and isolation

The parent Issue prefers an isolated container for T0. This allocation is explicitly host-only because local Docker is not responsive and the shared container queue has unresolved ownership; no existing container is inspected or modified. Candidate and auditor use only Python 3.11.9 standard library and dedicated fresh output paths. No network, model, GUI, app, user input, CUDA, or GPU is used. This is a recorded execution-context deviation, not a claim that host and container isolation are equivalent.

Candidate source SHA-256: `5a0d9b55e288ea46ae89ae41273b57c23016d72463bc58c45fa25bfae6cf0e2c`  
Auditor source SHA-256: `941bd4a36557dd7413a9b329ee10edfc21000063cda74974c4f8cac16b800d90`

Formal candidate: once. Independent auditor: once only after candidate exit 0. Any failed start gate means candidate=0 and terminal STOP; no retry or replacement parameter set.

