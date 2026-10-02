# Recovery-arm useful-effect gate audit T3

## H / T / D / C / U

**H.** The current frozen v2 paired adjudicator may emit `PASS_DIRECTIONAL_FIXTURE_SCOPED` when the recovery arm has no independently positive MAP01 endpoint (no kill and no exit), because a positive kill in the coast arm satisfies its global `useful_present` gate while survival can dominate the paired progress tuple. If so, the current rule does not establish a recovery-arm useful-effect advantage as worded in the #59 preflight hypothesis.

**T.** Freeze the exact v2 adjudicator source and five synthetic six-session records: (1) recovery survives with zero kill/exit while coast kills then dies, with recovery having lower unsafe exposure in all pairs; (2) same but recovery also gets a kill; (3) neither arm has kill/exit; (4) no realized threat contact; (5) overlapping unsafe intervals. Run the existing adjudicator once on each; then run a separate raw-only auditor once. No live experiment or rule mutation.

**D.** `COUNTEREXAMPLE_SCOPED` iff case 1 passes while recovery has zero kill/exit and coast has a positive kill, and controls 2–5 respectively pass, HOLD, HOLD, and non-PASS. Otherwise report the exact mismatch as `HOLD_OR_FAIL_CONSTRUCTION`.

**C.** Deterministic stdlib-only host construction, frozen to current main at start. Source rows are synthetic; no model, game, GUI, input, GPU, container or shared allocation. Container use is omitted because the exact Boolean behavior is completely determined by frozen pure Python and a container lease is not authorized; no platform-dependent behavior is under test.

**U.** A counterexample would show only a specification/estimand gap in the synthetic adjudicator: whether survival alone is a sufficient recovery-arm useful outcome needs an explicit decision. It cannot establish enemy-relative policy suitability, task-effect measurement validity, live efficacy, safety, or justify a live allocation. Preserve v1/v2 adjudicator results and this package separately.

## Frozen semantics

Use the v2 adjudicator unchanged. Recovery progress is its lexicographic tuple `(map_exit, alive_at_horizon, -death_count_gain, kill_count_gain)`. Its separate `useful_present` is currently true when *either* arm has a kill or exit in *any* pair. A positive recovery-specific task-effect requirement is deliberately not added; the test asks whether the existing code can pass without it.
