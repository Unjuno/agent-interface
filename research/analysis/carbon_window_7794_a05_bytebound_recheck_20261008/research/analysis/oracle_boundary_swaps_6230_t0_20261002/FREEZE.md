# Issue #6230 T0 freeze — 2026-10-02

## H / T / D / C / U

**H.** In a finite fixed-model decision fixture, independently replacing only task-relevant observation, only execution of the model's frozen intent, or both can distinguish observation-, execution-, interaction-, and semantic-limited outcome classes. This is a method-validation hypothesis, not an estimate of deployed headroom.

**T.** One no-model deterministic finite simulator with seven frozen cases and four arms (`actual`, `observation_oracle`, `execution_oracle`, `joint`). The four identified cases plant semantic-limited, observation-limited, execution-limited, and joint-only outcomes. Three guard cases plant a non-unique task, an answer-leaking oracle, and cross-arm reset/carryover contamination. The observation oracle must not supply answer, plan, future state or authorization. The execution oracle must preserve the exact model intent. Every formal arm must share an independently reset initial-state digest. Ambiguous cases remain `UNDEFINED`; leaked oracle arms are rejected, never scored as wins. A separate raw-only auditor does not import candidate code and executes seven corruption controls.

**D.** `PASS_METHOD_SCOPED` only if the 4×4 planted effect table matches, all 28 outcomes are retained exactly once, execution swaps preserve intent, oracle leakage and ambiguity receive no success credit, all arms in a case share reset identity, no safety bypass occurs, the independent raw-only audit passes, and all seven corruptions are rejected. Otherwise `FAIL_METHOD`. This cannot pass any empirical #59/headroom or deployability claim.

**C.** Hand-authored cases make the true class observable by construction and omit stochastic model behavior, GUI semantics, actuator timing and task-population selection. Simulator/auditor agreement validates only this accounting fixture.

**U.** Real oracle sufficiency, oracle-to-deployable availability gap, adaptation, intent equivalence, independent effect scoring, reset quality, task transfer, human tempo and model stochasticity are untested. T1 requires a separately gated disposable #57 task family, held-out tasks, paired deployable-evidence gap and external allocation.

## Frozen execution contract

- Issue: `Unjuno/agent-interface#6230`; branch: `research/oracle-boundary-swaps-6230-t0-20261002`.
- Exact source base: `18ae2231df50b83920f4aadf26913bb4af4c4b62` (GitHub main observed at 2026-10-02 intake).
- Additive evidence path: `research/analysis/oracle_boundary_swaps_6230_t0_20261002/`; no runtime/main behavior changes.
- Candidate: one formal invocation. Only if candidate exits 0, independent auditor: one invocation. Retries/substitutions: 0. Construction tests are separate from formal invocations.
- Python: CPython 3.12 on Windows x64; stdlib only; no network/model/GUI/task effects.
- Docker Desktop is installed but `com.docker.service` is Stopped/Manual. Engine status did not respond to a bounded request. No container or shared allocation is changed. This finite method fixture has no Docker-dependent semantics, so host CPU is an explicitly scoped fallback, not container evidence.
- No result, candidate output or audit output existed at freeze time. Source/test SHA-256 values are recorded in the preregistration comment on Issue #6230 before formal invocation.
