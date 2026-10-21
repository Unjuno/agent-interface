# Issue #8631 — T0 A03 learned applicability boundary

**Disposition: PASS_METHOD_SCOPED (finite authored fixture only).**  
This does not establish real guard calibration, a GUI safety property, external generalization, runtime behavior, speed, or authority.

## Frozen source and method

- Repository main at freeze: `3daf9e167f1e7896ad682ac1d22134618f70a23c`.
- Issue: [#8631](https://github.com/Unjuno/agent-interface/issues/8631).
- Allocation: T0-A03, fresh authored fixture. A01's auditor STOP is preserved; A02 used a hand-authored boundary and is retained as a construction-only result, not training data.
- Runtime: host Python 3.12.10, standard library only. No GUI, model, Docker, WSLc, private data, or external effect was used or needed by this finite method test.
- Candidate command: `python candidate.py fixture.json`, one invocation, exit 0.
- Independent auditor command: `python auditor.py fixture.json <candidate-json>`, one invocation, exit 0.

Frozen fixture grammar: conjunctions over `target_current=true`, `age=fresh`, `route=A`, and `version=v1`. The learner enumerates conjunctions by increasing width, returns the first zero-training-error predicate in fixed atom order, and uses only train rows. Five positive train rows include one stale positive; one negative train row has `target_current=false`. The independent falsifier and held-out route rows are not used for learning.

## Result

The learned boundary was the one-atom predicate `target_current=true`, covering all 5/5 training positives and rejecting the sole training negative (training accuracy 1.0). The independent raw-only auditor confirmed that it is the minimum-width consistent conjunction under the frozen grammar.

Falsification found both planted failures inside the learned boundary: `A3F1` (version drift on route A) and `A3R1` (failure on held-out route B). This shows why training accuracy alone does not justify reuse. The held-out B stratum also contains one success and one failure; the in-envelope failure is surfaced rather than hidden by route name.

Support audit returned `UNKNOWN_SUPPORT` for `A|stale|1` (one positive, zero failures) and for the empty `C|fresh|1` stratum. No absent negative support was imputed as evidence of safety. Perturbing the declared irrelevant `noise` value did not change the learned predicate. Candidate authority effect: none.

Independent audit: 10/10 named checks reconstructed, zero errors. Four output-integrity invariants were checked; they are not represented as a separate adversarial mutation-execution suite.

## H / T / D / C / U

- **H:** On this finite fixture, learning a compact applicability predicate and falsifying it can reveal an overgeneralization that aggregate training accuracy misses, while preserving UNKNOWN for strata with no observed failures and leaving authority unchanged.
- **T:** The frozen conjunction enumeration above; independent labels; train-only learning; separate falsifier/held-out rows; per-stratum failure-support table; irrelevant-covariate perturbation; independent raw-only reconstruction.
- **D:** PASS_METHOD_SCOPED because the learner found the shortest consistent conjunction, the auditor independently reconstructed it and all denominators, both planted in-envelope failures were found, stale/empty support remained UNKNOWN, noise was invariant, and authority remained unchanged. A failure to detect either counterexample, upgrading either unsupported stratum, leakage from falsifier/held-out outcomes, or audit mismatch would be FAIL_METHOD. This result is not a production or empirical guard claim.
- **C:** Explicit strata tables and support counts may provide the same protection more simply and transparently; a learned predicate may be an unnecessary abstraction or may hide route/version confounding.
- **U:** Tiny authored data, unmeasured prevalence, arbitrary feature grammar and training distribution, only one target-negative example, no statistical uncertainty, and no empirical GUI outcomes. No claim generalizes beyond these finite rows.

## Retained allocation chain

- **A01:** candidate ran once and identified F1, but the independent auditor stopped before audit because its CLI treated candidate JSON text as a file path. `STOP_AUDITOR_INPUT_CONTRACT`; no scientific result and no retry. Candidate stdout SHA-256 `777B4C65FBBE61094C2E3E4DFBCB6BEE4A14EA69E740AB5F22FF32219B34FF72`; fixture SHA-256 `180238D9E10A459F4C7789D3256EC23087AA8EBE116A93259964CB011DA1E2F2`.
- **A02:** corrected the auditor input convention and both processes exited 0, with 9/9 checks and 4/4 logical output-integrity conditions satisfied. However, its predicate was authored rather than learned, so this is diagnostic construction only and not evidence for the Issue's learning hypothesis. Candidate stdout SHA-256 `F675A290AA604CF36060BEB37ADBB50DF4A3B60D5102E72E81067ABC8D07A5D4`; fixture SHA-256 `69C3B93BDA7040246172ED6C3ADA4760EE11546A0B55D8552E1E4C986A89A0FB`.
- **A03:** candidate stdout SHA-256 `9CF1C34932D32B8D506429F0112D458E3B0650A9CB0807F566426B7E32151C98`; fixture SHA-256 `15D4705A33205AFD8F851F456640F4ADE8A42537A3E86643D2DD34739228FF09`; candidate source SHA-256 `B15997CE621519611BB50293C46BA04FA40FC5898CD9B748E1036280640EF0A2`; auditor source SHA-256 `EFB92CF354268968E288A7F8F94861BC31DF80DBD33CAAB4165042BE4B3CCC47`.

All outcomes are additive; A01/A02 are not rewritten or promoted. No further sweep is authorized by this T0.
