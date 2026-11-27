# Issue #8641 T0 A01 — uncertainty-source intervention choice

## Disposition

`PASS_METHOD_SCOPED / H_FAIL_NO_ADDED_DECISION_VALUE`. The frozen candidate ran once; the independent auditor reconstructed all 4,800 rows with zero errors. All hard-gate records matched exactly. The four construction mutation controls (source label, dependence, stale-epoch action, and cost) were rejected. The candidate received only observation-derived cue features; the separate oracle file was auditor-only.

Source-classification accuracy was 83.3% (5/6 authored profiles). On 1,200 repeated decisions per policy, DECOMPOSED produced 88.9% correct decisions at mean observation cost 0.258, versus 64.4% and 0.200 for TOTAL_UNCERTAINTY, and 85.5% and 0.158 for DECISION_VALUE. Decision changes were 40.9%, 25.3%, and 31.8%, respectively. DECOMPOSED abstained on half of decisions, including the correlated-duplicate and low-confidence/misspecified controls; all arms had zero hard-gate violations. The auditor-only ORACLE_INTERVENTION reference was 86.4% correct at cost 0.133.

The source decomposition improved correctness over both deployed-style baselines in this authored fixture, but it failed the preregistered cost endpoint at matched correctness: mean cost was 0.058 above TOTAL_UNCERTAINTY and 0.100 above DECISION_VALUE, rather than at least 0.020 below each. The formal disposition is therefore H FAIL, not an audit failure. This fixture supports no general claim that source labels predict useful interventions or reduce observation burden.

## Limits and custody

This is a deterministic synthetic policy-method test using six profiles, 200 held-out seeds per profile, hand-authored cue summaries and outcome probabilities. The oracle labels and probabilities were withheld from the candidate and used only by the auditor. The oracle intervention arm is diagnostic only. The source estimator was deliberately simple, and no real uncertainty model, GUI, user data, model, live action, latency, or product behavior was tested.

The allocation was frozen before execution against current-main `b4046798ed8902745a36e8fda091204233bb06d3`; runtime was CPython 3.14.5 on macOS 27.0 ARM64. Formal raw output, audit, fixtures, construction attempts, and SHA-256 manifest are retained alongside this report. The candidate was not rerun.
