# Early-warning signals for interface-service degradation

This family tests whether finite warning statistics identify loss of service resilience under specified synthetic dynamics. Ecological or stochastic-dynamical early-warning results motivate questions; they do not predict a software incident or provide an operational alarm. Keep every fixture result, artifact-integrity failure, and preflight STOP separate.

## #5776: recovery-rate sentinel

- **Status:** open; several finite and construction records exist, but no general warning or service-reliability claim follows.
- **Idea:** Test whether a frozen recovery-time statistic distinguishes gradual loss from abrupt or demand-drift controls in a synthetic pipeline.
- **Outcome and qualification:** The reported v2 detector result was `FAIL_METHOD_SCOPED`: the recovery-ratio sentinel warned in 0/16 high-load gradual-recovery episodes and 16/16 high-load demand-drift episodes. Merged [PR #5798](https://github.com/Unjuno/agent-interface/pull/5798) later recorded `FAIL_ARTIFACT_FIXTURE_HASH_MISMATCH`: the committed fixture digest disagreed with the frozen manifest and the audit stopped before replay. Preserve the historical reported result, but do not call its published audit receipt reproducible from main. Other #5776 probe/dose allocations have their own scoped construction results and STOPs; they are not pooled with this sentinel test. The source archive and qualifications are retained through merged [PR #5903](https://github.com/Unjuno/agent-interface/pull/5903).

## #8525: pseudo-bifurcation false warnings

- **Status:** open, unverified idea; no formal execution.
- **Idea:** Test whether transient amplification in a stable, non-normal staged pipeline can produce warning signatures that look like recovery slowdown even though the system remains spectrally stable. The transfer target is the interpretation of service warnings, not a new motor-prefix safety check or a claim that this repository is unstable.
- **Pre-run disposition:** A01 remained an incomplete preflight STOP: the shared volume was full (about 116 MiB available), OrbStack Docker was unavailable, local main had advanced, and the frozen package lacked `FREEZE.json`. A correction withdrew the earlier mistaken claim that `audit.py` was absent. A subsequent daemon-starting diagnostic failed with `no space left on device`; it did not establish that a VM was idle. Candidate/auditor stayed at 0/0, no container was started, and no formal allocation was consumed. Do not repeat that allocation or infer scientific evidence from the STOP.
- **Protocol clarification:** Before any future freeze, explicitly require the `abrupt_breaker` and `normal_stable` arms to have identical pre-break warning flags/ticks. The preregistered detector windows end at the breaker transition, so that control should not generate a precursor warning.
- **Novelty boundary:** #5776 studies recovery-rate precursors and demand drift, not stable non-normal transient amplification. #6195 already contains a stable/non-normal counterexample for finite-horizon motor-prefix safety; #8525 explicitly keeps that separate question out of scope. Open [#8872](https://github.com/Unjuno/agent-interface/issues/8872) asks a different magnitude-by-spacing disturbance boundary question.

## Scope

These records do not establish empirical incident prediction, false-alarm rates in production, GUI/model behavior, or a deployed warning policy. Preserve #5776's reported method failure and later custody issue, #8525's infrastructure/preflight STOP, and #8872's unverified successor question independently.
