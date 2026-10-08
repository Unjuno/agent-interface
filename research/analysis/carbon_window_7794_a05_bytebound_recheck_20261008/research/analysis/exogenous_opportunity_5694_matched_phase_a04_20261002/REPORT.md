# #5694 A04 — matched-capture phase result

**Disposition: `PASS_METHOD_SCOPED`.** The frozen hit/miss phase pair shared capture schedule `[10, 50]` ms, horizon 60 ms, and expiry 20 ms. Cue onset was 9 ms for `c01` and 11 ms for `c02`. Candidate output classified `c01` as `eligible_effect` and `c02` as `not_acquired`. The independent auditor reconstructed 9/9 rows with zero errors and rejected all five frozen raw corruptions.

## H / T / D / C / U

- **H:** In this exact synthetic schedule, moving cue onset from just before to just after the same first capture changes the declared outcome from an eligible effect to a non-acquisition.
- **T:** One native-Windows CPython 3.11.9 stdlib candidate process and one separate raw-only auditor process. Each ran once and exited 0; retries 0. No container, WSLc, GPU/CUDA, model, network, GUI, or input was used.
- **D:** `PASS_METHOD_SCOPED`: all nine rows present once; the phase pair matches capture schedule, horizon, and expiry; expected phase classifications observed; independent replay errors `[]`; corruption controls rejected 5/5. Post-formal local suite: 9/9 tests and py_compile pass.
- **C:** The effect follows from an authored event fixture and deterministic cue/capture joins. This demonstrates the measurement method's behavior on this fixture, not a live causal effect or a prevalence estimate.
- **U:** No real clock drift, capture pipeline, model behavior, GUI task, safety rate, #59 result, human-tempo, or product benefit is established. The opportunity oracle and event identities are authored.

## Formal case ledger

| Case | Boundary | Reason |
|---|---|---|
| c01 | eligible_effect | verified_effect |
| c02 | not_acquired | no_capture_before_expiry |
| c03 | acquired_not_delivered | delivery_after_expiry |
| c04 | delivered_no_decision | no_decision_before_expiry |
| c05 | decision_no_effect | no_verified_effect |
| c06 | decision_no_effect | safe_stop |
| c07 | UNKNOWN | clock_unsynced |
| c08 | UNKNOWN | right_censored |
| x01 | NOT_APPLICABLE | no_exogenous_opportunity |

Candidate raw SHA-256: `f0241a5057a9bab84a0a4283b3254860f076a9a1b7ccd91a48c7c017c5a63fcb` (1,526 bytes). Auditor JSON SHA-256: `7877eabc1a46828be9c35aaa70df9fecac2e354f2bc74838d9e2cdea780fdcb0` (247 bytes). Full output bytes, logs, process windows, allocation freeze, and checksum manifest are retained in this directory.

This successor corrects A03's unmatched design while preserving A03's original HOLD and outputs unchanged. Result is synthetic method evidence only.
