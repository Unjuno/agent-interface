## V39 accept-first admission boundary construction — 2026-10-05

Refs #59 and #7589. Additive evidence is retained in [Draft PR #7692](https://github.com/Unjuno/agent-interface/pull/7692), commit `36b5a689b02744ac7e46cfc6ce3454da706866c3`, under `research/doom/v39_cover_admission_acceptance_first_a01_20261005/`.

The frozen accept-first FIFO is: neutral prior observation 8, matching cover `accepted`, then hard-health observation 9 (health 65 below floor 73). The current-main wait closure and the exact #7589 PR-head helper both return `accepted` with observation 8 still the latest planner source. The caller starts the planner before the next monitor-enabled wait consumes observation 9. That next wait does observe the hard event; the controller's existing path interrupts/discards the planner result. Current-main wait tests pass 7/7, PR-head wait tests pass 8/8, and the independent raw/source audit passes 35 checks; five corruption controls pass.

Disposition: `FAIL_ACCEPT_THEN_HARD_BEFORE_PLANNER_MONITOR` for this deterministic synthetic queue ordering. This shows that the #7589 pre-acceptance monitor does not by itself close the acceptance-first ordering or prevent a planner turn from starting on the prior observation. It does not show a missed invalidation, accepted stale answer, task effect, input-authority bypass, measured interruption latency, game/model/OS behavior, or any live efficacy. No live allocation or GUI/input was used; #59 remains open and its live gate remains ungranted.

The full H/T/D/C/U, frozen source blobs, first candidate/auditor attempts and corrections, raw traces, exact commands, stdout, corruption tests, and SHA-256 manifest are in the linked package.
