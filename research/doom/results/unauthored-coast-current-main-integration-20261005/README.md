# V40 unauthored-coast monitor on current V39 — local integration construction

This construction ports only the exploratory typed-health coast monitor and
fresh-frame handoff into a versioned controller derived from the exact current
main V39 source. The published V40 controller was an older full-file copy and
omitted current V39's paired health/ammo cover monitor. This derivative keeps
that current-main code and changes only monitor selection plus invalidation
handoff (recorded in `FREEZE.json`).

The controller applies the fixed exploratory threshold of two of the latest
three typed health samples at least five points below the source baseline, and
does so only for the unauthored empty coast. It interrupts the matching planner
turn, requires verified empty release, and waits for the matching or newer
screenshot before replanning, including the completed-future fallback.

## Verification

- Base: current `main` commit `267dbf61e19efe94299b681dcda89925aae5b935`.
- Base V39 controller blob: `cdf61eec2c030d7456b34a58907e9c43d5d72084`.
- Candidate controller starts as those exact V39 bytes and retains its paired
  health/ammo guard; the test `test_current_main_fire_cover_keeps_paired_health_ammo_guard`
  protects that property.
- `py_compile` passed for the controller and monitor.
- Normal Python: 18 focused V39, V40 monitor/handoff, and current-main V40
  integration tests passed.
- Optimized Python (`-O`): 13 V40 monitor/handoff and integration tests passed.
- `git diff --no-index --check` reported no whitespace errors for the V39 to
  candidate controller patch.

This is local deterministic construction evidence only. The threshold remains
retrospective/exploratory. No live/game/model/input allocation was run. It does
not establish tactical benefit, recovery, survival, or MAP01 completion. A new
prospective freeze and explicitly assigned live allocation are still required.
