# Issue #6035 — T0 A01 protocol

## H / T / D / C / U

- **H:** On a finite synthetic 2×2 model-profile-by-interface-route fixture, all-assigned outcome accounting and a predeclared difference-in-differences gate distinguish additive effects from a planted route-effect crossover; hard safety violations fail and non-comparable contracts hold regardless of favorable synthetic rates.
- **T:** Four authored scenarios; two *labels* for simulated model profiles × two route labels × four common task IDs = 64 assigned rows. Each row retains terminal state, including `NOT_STARTED`, `TERMINAL_SAFE_STOP`, `ADMIN_CENSORED`, and `OUTCOME_MISSING`. Compare verified success by deadline over the same all-assigned denominator in all four cells. Compute route effect per profile and the difference-in-differences (profile B minus profile A). Freeze practical interaction margin 0.25. Scenarios: additive control; planted rank reversal; forbidden-attempt hard gate; non-comparable tool contract. A deterministic candidate runs once; a separate raw-only auditor independently reconstructs all 64 assignments once. Five corruption tests cover omission, outcome relabeling, order corruption, hidden safety event, and hidden contract mismatch.
- **D:** `PASS_METHOD_SCOPED` only if candidate and auditor exit 0, all 64 rows and equal per-cell denominators reconstruct, the additive and crossover controls classify correctly, the hard safety and contract gates override interaction arithmetic, and all five mutations are rejected. Any formal mismatch is terminal FAIL/STOP; no source edit, retry, substitute seed, or rerun.
- **C:** The interaction fixture is deterministic and tiny; it tests ledger/scoring logic, not model performance or sampling variability. No confidence interval or p-value is justified. A real same-model route contrast may not share a common tool contract.
- **U:** No actual models, providers, prompts, images, GUI, input, GPU/CUDA, WSL/WSLc, or containers are involved. `profile_A/B` are synthetic labels. No actual cross-model interface crossover, route choice, safety, latency, efficiency, or model-agnostic claim follows.

## Allocation and freeze

- Allocation ID: `MODEL-INTERFACE-CROSSOVER-6035-T0-A01-20261002`.
- Owner: Codex task `01a0b990-3d17-72f1-a908-9a2072104ce5`.
- Frozen main: `7c310860ca34d944da3a6c58c09a298c508355de`.
- Branch: `research/6035-model-interface-crossover-t0-a01-20261002`.
- Path: `research/analysis/model_interface_crossover_6035_t0_a01_20261002/`.
- Bounded UTC window: 2026-10-02 18:03–18:15.
- Runtime: Windows host CPython 3.11.9, standard library only. No shared runtime or external dependency.
- Candidate then auditor, each one invocation maximum; retry=0.
- Formal outputs must be absent before launch: `results/formal_01/candidate/raw.json` and `results/formal_01/auditor/audit.json`.
- A changed main SHA, source/hash mismatch, occupied output, inadequate C: capacity, or any process/runtime ambiguity that could affect this host-CPU-only run is a terminal pre-candidate STOP. Preserve the STOP; no automatic rebooking.
- A01 of this Issue is not present in any existing branch or open PR at source freeze. Recheck current main, related issue/PR/branch ownership, and these exact gates immediately before candidate.

## Execution boundary

This T0 does not consume the shared WSLc/container/GPU lane. The candidate and auditor are small standard-library host-CPU programs and must not invoke Docker, WSL, CUDA, a model server, network, GUI, game, or task input. Do not inspect or stop other workers' processes. If an unexpected environment change appears, STOP.
