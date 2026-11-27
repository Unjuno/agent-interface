# A14 result summary

Status: **FAIL_METHOD**. The one candidate invocation completed all 390 planned calls (360 queries, 30 consolidations); row IDs are contiguous, no call returned an error, and every request recorded the frozen model tag and loaded digest before and after. The independent transition auditor ran once and returned 21 errors.

Observed failure classes (repeated across seeds where applicable):
- False conflict claims for `exact_effect` when repeated successful effects agree.
- Premature `revision-r7-mode` conflict at batch-2 prefix 4 before contradictory episode 5 is visible.
- Incorrect r7 conflict claim payload at batch-2 prefix 6.
- Terminal arm changed the rare exception's exact effect from the fixture's `no_external_effect` to `draft_saved`.

The A14 prompt intervention did not yield faithful transitions. Per-seed answer accuracies are in `audit.json` (episodic-only .2667; per-episode .5000; batch-2 .6000 or .6333; terminal .6667). These remain descriptive only and do not support schedule-effect claims under the preregistered rule. No inference is made about GUI use, real user memory, or product effectiveness.

Raw SHA-256: `e40a6516249a1d3c7bfb4a740f1d601159729eaa44e1376fc40d460e5e89cb47`
Audit SHA-256: `b212b62a7db76f5071e338ab3746984315de08c62ef79f229fa617ded5834fac`
Preflight SHA-256: `57368dc377d3e4ed681a0fe7f4147b9d6222a44cc9df0c24e95d1fc25c772268`
