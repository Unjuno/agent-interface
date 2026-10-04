# A01 — paired-monitor ordinary-observation dispatch boundary

This is an exploratory construction probe against PR #7717 head `40f118fef7757744f09c0683870517e94ff5109f`, controller blob `41c1f9744c65704b6f55b8826c010552d6325998`. It is deliberately labeled **not preregistered**: the first execution occurred before this record was written. That output is preserved and the candidate was not rerun.

## H/T/D/C/U

- **H:** The controller's exact nested `wait()` dispatch does not call `DoomCoverSignalPairMonitor.observe()` for an ordinary `observation` row because the monitor advertises only `{"typed_observation"}`. Thus the monitor's ordinary-observation fallback cannot invalidate a fire cover when the typed companion is absent.
- **T:** AST-extract the exact `wait()` definition, `_typed_json_equal`, `_signal_pair_matches`, and `DoomCoverSignalPairMonitor` from the pinned controller. Run one synthetic same-epoch ordinary observation whose readers report health 100 and ammo 0; compare with a typed observation control and a dispatch-enabled ordinary-observation control.
- **D:** The ordinary row returned normally with monitor sequence still 10 and no invalidation. Both controls returned `policy_invalidation` with `ammo:below_hard_minimum` and sequence 11.
- **C:** `PASS_DISPATCH_BOUNDARY_COUNTEREXAMPLE` for this construction boundary only. This confirms the reported ordinary-event dispatch gap in the exact pinned source.
- **U:** No evidence about live event ordering/frequency, game behavior, cancellation timing, physical key-up, task effect, bounded recovery, or MAP01 progress. This does not close Issue #59.

## Execution

Candidate ran once in WSLc, offline, with read-only source bind mount, requested one CPU and 512 MiB, image `post-guard-game-59-4d74:20261004` (local image ID prefix `94014a0f7757`). WSLc emitted: `Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.` Therefore memory enforcement is not independently claimed. Exact candidate command and first stdout are in `FREEZE.json` and `test-output.txt`.

`dispatch_probe.py` executes extracted production AST for the controller's nested `wait()` and pair-monitor class; its controls vary only event type dispatch. `independent_audit.py` separately checks the source AST and first-output invariants. No repository source was modified by this probe.
