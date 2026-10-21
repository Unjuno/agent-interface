# Current-main retained-trace replay (2026-10-17)

The original A01 freeze and its historical source snapshots remain unchanged.
The retained sequence-218 health breach and recovery trace was replayed against
current main `1ece47014d05db898bf73afcd722a14524462e15`, controller blob
`426d6bf2db631fb0e735da1f8e7e4c15b675ba45`. The paired monitor accepted the
valid sequence-220 health/ammo pair (health 51, ammo 37), but left its recovery
watermark at 218. The replay therefore failed its expected recovery assertion.

The current-main correction advances `last_pair_sequence` only after the normal
fully validated paired-observation path. Hard and unknown invalidations do not
advance it. The retained-trace test failed before the correction and passes
after it. A focused run of that test plus the current dual-signal, duplicate-
consistency, and wait-dispatch suites passed 23 tests.

The broader `test_map01_overlap_controller_v39.py` run had one separate error:
`test_production_source_refresh_stops_loop_on_terminal_health_zero` expects a
source substring that is absent from current main. The other 17 tests passed.
This pre-existing source-structure assertion is unrelated to the watermark
change and remains visible for separate cleanup.

This is a deterministic replay of retained data plus unit tests. It is not a
new live game, model, input, or task-effect result.
