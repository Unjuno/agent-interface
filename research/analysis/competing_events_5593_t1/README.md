# Issue #5593 — T1 exact competing-event construction check

Status: METHOD_CONSTRUCTION_PASS_SCOPED; empirical hypothesis remains untested.

## Identity and execution
- Parent main at branch creation: `a44541541546290c4d2d5e6e6913ef07bc1f01f8`.
- Branch: `research/competing-events-5593-t1-20261001`.
- Source: [verify.py](verify.py). Local source SHA-256: `78d490e663072c0ba099e8008ab60687b9b1d0acf7502b9c3a63ea6e5529cf31` (read-back GitHub blob should be checked separately).
- Command: `python work/issue5593_competing_events_t1.py` from the Codex host workspace, CPython 3.12.10, exit 0.
- No Docker/container was launched: the shared slot was not assigned to this work. This is a host-only construction control, not the Issue's disposable-container formal rung.

Raw stdout:

```text
{'uncensored_AJ_t2': '2/5', 'uncensored_wrong_KM_t2': '1/2', 'censored_AJ_t3': '3/8', 'censored_wrong_KM_t3': '1/2', 'duplicate_and_unknown_event_rejected': True}
```

## Frozen synthetic rows and independent arithmetic
1. Complete ten-episode cohort: two terminal safe stops at t=1; four verified successes at t=2; four verified failures at t=3. At t=2, cumulative success incidence is 4/10 = 2/5. Wrongly treating the two stops as censoring yields 4/8 = 1/2.
2. Censored ten-episode cohort: two administrative censors at t=1; two terminal stops at t=2; three successes at t=3; three failures at t=4. The at-risk sets at t=2 and t=3 are eight and six. The stop transition leaves 6/8 survival mass; success at t=3 adds (6/8) × (3/6) = 3/8. Wrongly censoring the stops leaves success risk 6 and reports 3/6 = 1/2. This is a *synthetic independent-censoring demonstration*, not evidence that actual infrastructure loss is independent.
3. Duplicate launch ID and an unknown event type each provoke assertion failure. No row is silently dropped.

The code compares a cause-specific cumulative-incidence recursion with a separately written transition-mass product. The arithmetic above is a third, manual check. Ties between censoring and events, interval censoring, multistate recovery, and inference are not implemented; none occur in these frozen rows. The simple estimator here is for sanity checks only.

## Scientific scope and next gate
This verifies method behavior on two hand-authored synthetic cohorts and rejects two malformed-row controls. It does **not** supply a real same-policy launched-episode ledger, a defensible real censor mechanism, a route comparison, or a human-tempo/product claim. The previous #5593 T0 construction and retrospective HOLD remain unchanged. A future empirical rung requires the Issue's prospectively frozen time zero, first terminal type, deadline, recovery terminality, independent effect oracle, and complete attempted-row accounting. Do not pool earlier STOP allocations or treat unattempted tasks as censored launches.
