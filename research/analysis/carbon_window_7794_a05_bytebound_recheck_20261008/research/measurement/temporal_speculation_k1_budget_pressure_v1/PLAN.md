# TEMPORAL-SPECULATION-K1-BUDGET-PRESSURE-20260918-001
BASE=09f41a7512724e1239057bc2eb98305bd2123fb2

H: Hold the #1127 40 ms planner-gap fixture and authored 400k distribution fixed; change only speculative branch budget K=2 -> K=1. Current-only uses fixed source-independent tie-break +1. Temporal selects +1 for monotone-right, -1 for monotone-left, +1 for ambiguous. Symmetric corpus makes tie-break sign aggregate-neutral.
T: fresh seed112820260918001; exact category counts; WAIT/current/temporal arms; same fresh exact-match authority/expiry gate; 24 monotone-left subprocess discriminators; detached one-shot formal; reruns0.
D: PASS iff current hits151814, temporal231610, temporal mean >=3 ms below current and >=10 ms below wait, live temporal<5 ms/current+wait>=25 ms, 72/72 correct independent effects, wrong/stale/authority0, source/audit integrity exact.
C: a PASS means temporal history matters under tighter branch-budget pressure; trivial velocity remains sufficient in this fixture.
U: controlled synthetic/subprocess result only; no frontier/model/task/MAP01 claim.
