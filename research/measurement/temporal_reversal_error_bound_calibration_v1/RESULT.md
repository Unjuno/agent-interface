# Error-bound calibration boundary under ±1% localization jitter

Issue: #1319  
Task: `TEMPORAL-REVERSAL-ERROR-BOUND-CALIBRATION-R1-20260918-007`

Preregistered scientific disposition: **FAIL_CALIBRATED_BOUND_SAFETY**.

Formal discipline: one invocation, zero reruns/replacements/tuning, 4800/4800 rows. The true observation process is fixed to the exact #1311 deterministic ±1000 micro-unit jitter schedule. Only the estimator's assumed position-error bound changes.

| assumed bound | 25 ms acc/wrong | 50 ms | 75 ms | 100 ms | 150 ms | 200 ms |
|---|---:|---:|---:|---:|---:|---:|
| B500 (0.5×) | .335/.185 | .525/.090 | .595/.055 | .755/.000 | .770/.000 | .725/.010 |
| B750 (0.75×) | .265/.070 | .500/.010 | .710/.005 | .945/.000 | .935/.000 | .925/.000 |
| B1000 (1.0×) | .240/.000 | .495/.000 | .740/.000 | .995/.000 | 1.000/.000 | .985/.000 |
| B1500 (1.5×) | .240/.000 | .495/.000 | .740/.000 | .995/.000 | 1.000/.000 | .980/.000 |

The nominal and conservative arms emit zero wrong directions across all measured ages. The 0.5× underbound emits confident wrong directions, including 1% at age200 ms. Therefore the observation-error bound is safety-relevant: underestimating it can turn noise on a true full-speed interval into a fabricated reversal.

## Frozen-auditor defect retained

The frozen auditor's raw decision is `FAIL_INTEGRITY`, with errors `ceiling_B500_25`, `ceiling_B500_50`, and `ceiling_B750_25`. This is an implementation-classification defect: the auditor appends scientific ceiling-gate failures to a generic `errors[]` array and then maps any non-empty array to `FAIL_INTEGRITY`. Issue #1319 explicitly preregistered any ceiling exceedance as `FAIL_CALIBRATED_BOUND_SAFETY`.

The frozen AUDIT is preserved unchanged. A separately labelled read-only postformal classification reports `structural_integrity_errors=[]`, exact source rehash, corruption4/4 rejected, and the preregistered scientific label. No scientific rows were regenerated.

The noiseless #1281 ceiling is itself not an information-theoretic upper bound on noisy-arm aggregate accuracy: noise can create accidental correct guesses together with wrong guesses. Its preregistered exceedance gate nevertheless remains binding for this allocation and is not relaxed post hoc.

## Scope

Synthetic only. Known unit speed, one reversal, and a hard jitter envelope are favorable assumptions. This result does not establish a real visual error bound, GUI/task correctness, model quality, production latency, or human-tempo performance.

Artifacts:
- FORMAL_RESULT.json SHA-256 `e99a808bab6288336251aa82eed0445864a1b62e2e25f20d9e1e5ef1c9673a71`
- frozen AUDIT.json `3ddf18e91740567d5f9d691ab2655ad124d42a6fa521c41b6dbc575b40d38db4`
- CORRUPTION.json `3822cfee67693e2fe2aa139b930d22e8488cf98a6d2e3a4c260af580457242cd`
- POSTFORMAL_CLASSIFICATION.json `8eb5d725e144e0555f7d686a73c00ecfd8954188fb544ed7ca45cf11cac9b0a5`
