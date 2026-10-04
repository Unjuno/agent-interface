# V39 dual-signal paired-epoch construction probe (A03)

**H.** For a retained typed observation used as a cover baseline, independently valid health and ammo readings may only preserve an existing policy when both belong to the same current typed frame. Measures are the pair decision and per-signal guard outcomes. This is an offline contract probe, not controller integration or game evidence.

**T.** Compare a naive composition of the current per-signal guards with paired-frame validation over seven frozen cases: coherent positive, minimum positive ammo, zero ammo, health below floor, sequence skew, capture skew, and binding skew. Four unit checks include the naive counterexample, current producer validation, candidate decisions, and malformed-source fail-closed behavior. An independent auditor derives pair identity and threshold outcomes directly from fixture/result JSON without importing candidate code.

**D.** PASS if both coherent safe cases preserve, hard-floor violations and all epoch mismatches replan, malformed source fails closed, the A02 control still preserves the sequence-skew counterexample, and the raw auditor passes. Any discrepancy is FAIL. No retry policy is used; this is local construction work.

**C.** Candidate relies on the current typed snapshot builder plus explicit exact-integer/common-identity checks, and the existing one-way `ObservableSignalGuard`. It assumes health and ammo floors 90 and 1 and the existing preserve-on-soft-change contract. It does not prove producer correctness, freshness under runtime scheduling, action admission, release, recovery, or task success.

**U.** No live V39 assignment, controller wiring, useful feedback loop, input event, or MAP01 outcome is exercised. Host-specific timing, actual image extraction, and combined invalidation delivery remain unmeasured. Result applies only to the frozen current-main source and synthetic fixture.

`python -m unittest discover -s research/doom/v39_ammo_cover_epoch_join_59_a03_20261005 -v` runs the unit probe. `python research/doom/v39_ammo_cover_epoch_join_59_a03_20261005/probe.py` writes the retained result once. `python research/doom/v39_ammo_cover_epoch_join_59_a03_20261005/audit.py` independently audits it.
