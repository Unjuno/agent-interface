# #6241 T0 — calibrated success-history transfer discriminator

Allocation: `CROSS-TASK-SUCCESS-HISTORY-CALIBRATION-6241-T0-20261002-01`  
Frozen main: `d7e8a932da27e7f271920de409b079fedc75dee1`  
Branch: `research/6241-success-history-calibration-t0-20261002`  
Path: `research/analysis/context_success_history_calibration_6241_t0_20261002/`

## H / T / D / C / U

**H.** A prior task's successful route history is warranted evidence for current task B only when a predeclared relation says A and B share the same latent capability/regime and the route precondition identity is unchanged. An identical success streak from an independent regime, or after a changed precondition, must not be transferred. Unknown dependency and ambiguous current effects must fail closed while preserving unresolved obligations.

**T.** A finite deterministic T0 uses eight authored cases. The paired discriminator keeps B's task, intent, observation, authority and route fixed while varying only typed history relation/counts and the explicitly frozen pending-effect state. A Beta(1,1) prior is used as a transparent synthetic calibration oracle: for an eligible history, posterior mean is `(1 + successes)/(2 + successes + failures)`; ineligible histories retain the base 0.5. A 0.70 decision threshold is fixed before execution. This is a method test, not an LLM call or a model-attention experiment. Candidate and independent raw-only auditor are each invoked once after construction tests.

Cases cover: shared-regime 8/10 success; independent-regime 8/10 with identical counts; changed route precondition; shared-regime 2/10; ambiguous pending effect plus open obligation; unknown relation; private A artifact; and shared-regime success with capability mismatch.

**D.** `PASS_METHOD_SCOPED` requires exact reconstruction of all eight rows, same-streak discrimination (0.75 transferable vs 0.50 neutral), changed-precondition and capability mismatch resets, weak-history 0.25, unconditional HOLD for ambiguous effects and unknown dependencies, exact preservation of the open obligation and current B identity, omission of private artifact text, and rejection of all six frozen output mutations. Any mismatch is STOP; this finite method result does not qualify H for model behavior.

**C.** The decision rule is intentionally explicit and synthetic; typed relation labels are assumed correct. It does not test whether an LLM infers/calibrates those relations. Prompt wording, token position, hidden model state, or real GUI execution are absent.

**U.** Eight authored cases, one synthetic calibration prior, one Windows host, CPython 3.11.9, stdlib CPU only. No GUI, model, GPU/CUDA, WSL/WSLc, Docker, network, user data, actuation, empirical error rate, privacy/security guarantee, or product claim.

## Frozen execution boundaries

1. Run the construction suite before the formal candidate.
2. Freeze SHA-256 of this plan, fixtures, candidate, auditor and tests plus Python version and exact main SHA.
3. Require a fresh absent candidate-output and audit-output path; no seed is used.
4. Invoke candidate once; only on exit 0 invoke the auditor once against raw JSON.
5. No retry, tuning, fixture replacement, or model/GUI/GPU/container work.
