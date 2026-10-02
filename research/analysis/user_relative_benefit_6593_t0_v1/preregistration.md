# Preregistration — Issue #6593 user-relative benefit method T0

Allocation `USER-RELATIVE-AGENCY-BENEFIT-6593-T0-20261002-01`  
Frozen main base `4a577c1bbb57c055bb489e57f513f8672126fe27`  
Additive path `research/analysis/user_relative_benefit_6593_t0_v1/`  
Scope: synthetic schema/accounting method test only. No human participants, accessibility assessment, participant data, or real benefit claim.

## H / T / D / C / U

**H.** A pooled standardized human-versus-agent timing contrast can point in the opposite direction from a pseudoparticipant's matched assisted-offer-versus-unaided contrast under one stable declared configuration, even when both arms pass the same independently scored required/forbidden effect gate. An all-assigned method should expose that reversal without treating a wrong/unfinished task as a speed win, conditioning away refusal, or pooling across changed configurations.

**T.** Freeze seven synthetic cases: planted pooled/within-person reversal, same-direction null, fast wrong-effect offer, offer refusal, missing outcome, changed AT configuration, and one-against-one inadequate support. Each case contains standardized benchmark observations and all assigned synthetic matched offer/control pairs. Compute pooled benchmark delta as mean(agent seconds minus standardized-human seconds). Within each participant × stable configuration × task family, compute mean(assisted-offer minus unaided seconds) only over exact matched pairs where the offer was used, both outcomes are independently marked verified, and required effects hold with forbidden effects absent. Need at least two such pairs. Prespecify meaningful directional margin as 5 seconds. Preserve assignment, uptake/refusal, every outcome, configuration, order, agency rating and missingness; report agency separately, never trade it against correctness or time. Missing, wrong, refused, changed-configuration, or under-supported strata are HOLD, not dropped successes.

**D.** `PASS_METHOD_SCOPED` iff construction tests pass; the reversal case has pooled delta >= +5s and within-person delta <= -5s on >=2 valid matched pairs; the same-direction case is not a reversal; wrong-effect, refusal, missingness, config change and insufficient support each remain non-benefit HOLD; and seven corruption controls are rejected by an independent raw-only reconstruction. No aggregate or synthetic row is a human-benefit result.

**C.** A pooled/within sign difference can disappear on other tasks or participants; a stable AT configuration and synthetic complete matching make the toy comparison easier than real use. Offer assignment does not imply use, and an offer policy may alter behavior even when declined.

**U.** This T0 measures no participant, preferred pace, active effort, interruption burden, agency, AT compatibility, recruitment, population effect, or uncertainty interval. Authored times/effects cannot show accessibility, efficacy, or causality. T1 requires separate consent, accessibility expertise, privacy review, resource ownership and an independently scored disposable task protocol; none is authorized or attempted here.

## Freeze and environment

One CPU-only standard-library host run is allowed for this synthetic method test; no GUI, model, network collection, human, or external effect is needed. Construction tests precede freeze. Freeze candidate, independent auditor, fixture and tests; verify formal outputs absent. After freeze, invoke candidate once and separate auditor once, zero retries; preserve stdout/stderr, raw ledger, audit, exits and SHA-256. The prior outcome PR #6648 is independent; this experiment has its own path and allocation.
