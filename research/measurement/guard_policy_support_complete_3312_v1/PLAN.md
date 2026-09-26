# Issue #3312 — support-complete guard calibration allocation

Allocation: `guard-support-complete-3312-20260923-01`
Intake main: `2aac474ff82b5f8b1a90708850a39bb853ee19c2`
Owned additive path: `research/measurement/guard_policy_support_complete_3312_v1/**`

## H
The inherited recoverable-X11 route can retain non-zero, prospectively allocated support for every #3312 stratum—stale refusal, fresh refusal, stale action + independently scored recovery, fresh successful action, and right-censored recovery—without pooling #1793/#2546 rows, leaking the independent stale/fresh oracle to the selector, or changing the inherited route/cost semantics. The complete-support ledger is auditable from raw fixture events and same-clock timestamps.

## T
Preserve the exact parent `fixture.py` and parent helper source from `GUARD-POLICY-RECOVERABLE-X11-CALIBRATION-A3-20260918-003`: private Xvfb/Tk/XTEST route, left cached target, 32x32 ROI guard, 120 ms success horizon, 3 ms stale-no-effect boundary, baseline-subtraction cost equations, q tiers 1/100, 1/20, 1/5, 1/2, selector formula, and terminal button-neutrality semantics.

Change only episode allocation/support audit. Formal schedule is deterministic and frozen before input:
- calibration: 16 blocks; each block has BASE_FRESH, STALE_REFUSAL, FRESH_REFUSAL, STALE_ACTION_RECOVERY;
- evaluation support: 6 rows per required stratum (30 rows), with calibration/evaluation IDs disjoint;
- q-tier selector transfer: 32 paired PRE_GUARD/POST_ONLY episodes per q tier using the inherited seeded Bernoulli generator, kept diagnostic because this rung's scientific decision is support completeness;
- right-censored rows use a fixed 5 ms post-stale-action recovery horizon and stop before fallback. They are retained as censored and excluded from c_f/c_y estimates.

One excluded construction block checks one row of each support type and fixture cleanup. One formal invocation only; reruns/replacements/tuning 0. Provided Linux x86_64 execution container, CPython 3.13.5, Tk 8.6, python-xlib 0.15, private TCP-disabled Xvfb. Docker CLI/image attestation is unavailable, so no Docker/OrbStack replication claim.

## D
`PASS_SUPPORT_COMPLETE_CALIBRATION_AUDITED` iff:
- exact formal denominator and frozen schedule reconcile;
- calibration and evaluation episode IDs are disjoint;
- each of five required evaluation strata has >=6 retained rows;
- stale/fresh truth is reconstructed from fixture reset position/event history, not a selector input field;
- every STALE_REFUSAL has guard reject before task input and later exact recovery success;
- every FRESH_REFUSAL is explicitly forced policy refusal after a naturally fresh guard, followed by exact recovery success;
- every STALE_ACTION_RECOVERY has actual stale cached click -> independently logged noop -> fallback success;
- every FRESH_SUCCESS has one correct cached click success;
- every RIGHT_CENSORED has actual stale cached click -> noop, fixed horizon expiry, no fallback, and remains censored/unknown;
- all complete rows end button-neutral; censored rows also end button-neutral;
- c_y_stale, c_y_fresh, c_f are computed only from complete calibration blocks using the inherited equations and have nonnegative mean plus nonnegative 95% paired-bootstrap lower endpoint;
- q tiers and inherited selector formula are retained, with any unresolved tier reported UNKNOWN rather than forced;
- independent raw-only auditor has zero errors and rejects >=8 semantic corruptions.

Missing support => `HOLD_NEGATIVE_SUPPORT_UNOBSERVED`; incomparable clock/censor evidence => `HOLD_CENSORING_OR_CLOCK`; leakage/relabeling/unsafe effect => `FAIL_LEAKAGE_OR_RELABELING`; source/process/denominator/cleanup failure => `STOP_INFRA_OR_PROVENANCE`.

## C
The support strata are deliberately allocated, so counts are not natural incidence estimates. Forced fresh refusal is a policy control, not a naturally occurring false reject. The right-censor horizon is authored. One synthetic private-X11 route cannot establish production economics, model benefit, human tempo, or cross-application reliability.

## U / bounded roadmap
A PASS repairs only #3312's missing support-evidence gate. It does not retroactively rewrite #2546, and it does not establish a universal guard selector. Next valid step is to compare the resulting same-route support estimates against a held-out real application route or integrate only if #2789's selected path needs this guard policy. Stop after one formal result, independent audit, publication and review.
