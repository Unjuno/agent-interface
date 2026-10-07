# Issue #59 — ammo depletion during model-pending fire cover (A01)

## H / T / D / C / U

**H.** Current v39 cover validity monitors typed health only. If a fire-containing `next_cover` was selected while ammunition was positive and the visible ammo later reaches zero during a slow model call, the existing cover monitor may preserve the fire policy instead of requesting a fresh decision. This tests the Issue's explicit ammunition-aware fire / stale-policy gap, not live game behavior.

**T.** Freeze the current-main v39 controller, responder prompt, `ObservableSignalGuard` implementation, and a deterministic two-frame fixture before execution. Run the exact dependency-free guard/monitor classes from current main. Keep health constant and above the authored hard floor while ammo changes from 4 to 0 under a notional active `fire` cover; then exercise a health hard-floor control. Record monitor outcomes and whether each event would request policy invalidation. No controller, model, Doom process, GUI, OS input, or game is launched.

**D.** Method gate passes only if zero ammo causes a policy-invalidation event before the old fire cover can be renewed, and an unchanged-ammo positive control preserves it. The health hard-floor control must invalidate. Otherwise FAIL the tested guard contract and report exactly which event remains invisible. This gate is falsifiable but is not a live safety claim.

**C.** Ammo may be advisory during an already admitted short cover, the HUD read may lag, or health-only invalidation plus immediate action admission may be sufficient for product behavior. This fixture does not measure firing usefulness, game effect, time-to-cancel, key release, or survival.

**U.** Synthetic monitor-boundary test only. No live threat, firing, model latency, actual renewal, physical release, useful feedback, recovery, or MAP01 outcome was tested. A FAIL indicates a current-main source/contract gap worth a separately authorized prospective live experiment; it does not authorize that allocation.

## Execution

`FREEZE.json` binds source and fixture hashes. `probe.py` runs the current-main guard/monitor once and writes only `RESULT.json`; `audit.py` independently checks the raw input/outcome relation and writes only `AUDIT.json`. The preferred container route was checked first, but OrbStack's Docker Engine failed read-only image inventory with a cached containerd blob `operation not supported`; no pull, build, repair, or restart was attempted. The exact guard code is stdlib-only, so this narrow boundary test ran under host CPython 3.14.5 without an isolation claim.

## Limits / next gate

Even a method PASS would not establish live fire behavior. Any successor live experiment must use an additive allocation, a fresh exact-main freeze, an explicitly assigned live lane, and measured typed-ammo observation-to-empty-release timing with independent audit. Never rerun this frozen A01 output in place.
