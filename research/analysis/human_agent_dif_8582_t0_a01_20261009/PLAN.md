# Issue #8582 T0 A01 — human–agent item DIF method sensitivity

## Scope and H / T / D / C / U

This executes only the no-participant, no-model T0 in [Issue #8582](https://github.com/Unjuno/agent-interface/issues/8582), based on current `main` `4758a95cd4a0aaa78e9cdc9d774f298d4ccf0e36`. It is a synthetic binary item-response method fixture. It does not test real human/agent differences, fairness, a latent ability construct, or actual benchmark bias. Authority is `NONE`.

**H.** A preregistered conditional item screen will detect strong planted uniform and nonuniform group effects after conditioning on the declared operational capability strata, avoid flagging invariant/placebo items, mark low-discrimination and insufficiently observed items as non-estimable, and refuse comparison when common support or anchor validity fails.

**T.** Enumerate eight deterministic scenarios with 100 assigned response slots per supported group × stratum × item cell and six binary items: two anchors, a null, uniform-DIF target, nonuniform-DIF target, and low-discrimination target. Scenarios are invariant, uniform DIF, nonuniform DIF, placebo group labels, low discrimination, no common support, invalid common anchors, and missing/UNKNOWN outcomes. Row-level candidate data contain every assigned item response; the missingness case retains 50 null outcomes in its denominator. The candidate reports crude group marginal means, within-stratum group differences, and item classifications. A separate auditor reconstructs all response slots, means, classifications, and gates from raw rows. This is an exact deterministic sensitivity fixture; it does not fit a generalized logistic model or estimate population uncertainty.

**D.** `PASS_METHOD_SCOPED` only if all 18,000 assigned rows reconstruct; uniform and opposing-stratum nonuniform effects are detected in their planted cases; invariant and placebo null items remain `NO_FLAG`; the zero-discrimination item is `LOW_INFORMATION`; absent common support returns `HOLD_COMMON_SUPPORT`; shifted anchors return `HOLD_ANCHOR_INVALID`; the missing cell remains visible and its target returns `UNKNOWN_LOW_SUPPORT`; and seven raw mutations are rejected (row loss, response flip, UNKNOWN imputation, false null flag, false overlap acceptance, ignoring invalid anchors, authority inflation). Any false flag or false certification is `FAIL_METHOD`; missingness or output/audit contract defects are retained as HOLD/STOP without retry. One candidate and one auditor invocation, zero retries.

**C.** The planted effects are large and deterministic, and the cutoff of 0.2 is a method-test threshold rather than a validated practical effect. Perfect anchor behavior is assumed in most cases. The screen may not detect subtle DIF, complex interactions, response dependence, or effects under realistic sample sizes.

**U.** No participants, model, GUI, empirical response data, consent, or external service is used. Results establish only scorer sensitivity and fail-closed bookkeeping for these authored rows. They do not license mean comparisons, fairness claims, general human/agent superiority, or T1.

## Construction and formal gate

Construction tests must pass and the candidate/auditor must complete a separate temporary-output replay before freeze. Freeze and push exact source/spec hashes, preregister on #8582, then read back the Issue comment and remote source before the one-shot formal candidate. Run the raw-only auditor once only after candidate exit 0 and raw hash capture. Do not retry or tune after formal start.
