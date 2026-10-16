# Issue #59 retained V39 decision/effect diagnosis A01

This read-only reconstruction uses the exact retained V39 report and 634-row runtime event stream pinned in `FREEZE.json`. It does not rerun the game, model, controller, GUI, or input.

## Findings

- Six model turns lasted 5.720–8.916 s; the run retained 218 typed health/ammo observations.
- The active policy for each `cover-N` is joined by exact iteration and `cover_policy_source_iteration`; decisions 0, 2 and 3 used unauthored coast. Decision 1 carried decision 0's policy, and decisions 4 and 5 carried policies from decisions 3 and 4. Rejected returned actions did not become the next active cover. The model-authored next policy is retained separately. Typed health/ammo first/last values are joined by exact `cover-N` event identity.
- At decisions 1 and 2, returned plans were rejected as no longer current. At decision 5, the health guard reached `HARD_INVALIDATED` (source 61, current 48, hard minimum 51); the planner answer was ineligible and the running action was canceled with a verified empty release.
- The six model-authored assessments describe a distant target, a close enemy on the right, a close enemy ahead, persistence of that enemy, a second enemy firing from the left, then an interrupted turn. Those descriptions are not an independent threat oracle.
- Four per-action receipts are `visible_change` with scope `viewport pixels only`; there is one post-control score row after all decisions: alive, one kill, no MAP01 exit. The score cannot be attributed to an individual policy or action. No contingency was authored or taken.

## Interpretation

This improves the retained-failure diagnosis and localizes one successful health-triggered invalidation/release sequence. It does not show that stale cover caused harm, that an authored threat response improved survival, that viewport changes were useful task progress, or that the single kill came from a particular action. There is no matched fixed-safe counterfactual. The next decisive run still requires an independently scored threat-change/effect sequence and bounded recovery under a fresh authorized allocation, followed by a separately labelled MAP01 attempt.

Reproduce with `python3 -B research/doom/v39_retained_diagnosis_59_a01_20261005/analyze.py`, then `python3 -B research/doom/v39_retained_diagnosis_59_a01_20261005/audit.py`.
