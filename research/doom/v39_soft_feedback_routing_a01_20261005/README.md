# A01 — soft-signal routing during a pending V39 planner turn

## H / T / D / C / U (frozen before candidate execution)

**H:** When a fire-cover monitor receives an advancing, correctly bound ammo observation that changes 46→37 but remains above its hard minimum, the current V39 path records a soft event and preserves the cover. Because the model turn has already begun, that event is not delivered to the in-flight planner or used to change the current cover before that turn returns; it is serialized only after the turn into the decision record and can enter a later planner prompt.

**T:** On current `main` `f60752d0fb71595363a80977636ca74c1fd10b21`, execute the exact `DoomCoverSignalPairMonitor`, `guard_spec`, `ammo_guard_spec`, and `begin_model_turn` AST nodes from the frozen V39 controller against the frozen production `ObservableSignalGuard` source. Use a synthetic paired observation: health 100→100, ammo 46→37, increasing sequence/capture time, unchanged binding, and a changed frame hash. Stub only the planner API; do not start the model, game, session, GUI, input, container, or live allocation. Independently inspect the V39 `wait` / planner loop AST to establish event ordering and the post-turn decision-record route.

**D:** `FAIL_NO_INDEPENDENT_IN_FLIGHT_FEEDBACK` if the real monitor records the ammo change as `SOFT_CHANGED` with no invalidation; the planner prompt is formed before the new event; the event arrives inside the pending-turn monitor loop; no in-flight planner update/cancel or policy change is invoked for that soft event; and the current decision records the event only after `future.result()`. Any unexpected status, ordering, additional feedback API, or missing decision route is retained as an exact non-pass.

**C:** This is a deterministic source-composition probe with one synthetic observation and a stub planner. It checks signal routing/timing, not a live image reader, model output, event cadence, physical input, key release, useful task feedback, response latency, or recovery.

**U:** It cannot establish whether a specific ammo change is strategically useful, whether real OCR reads it correctly or soon enough, how often it occurs, whether later model use helps, or task/survival/MAP01 outcome. No live allocation is assigned or implied. The existing Issue #59 live threat-exposure gate remains open.

## Frozen identities and run protocol

- Main base: `f60752d0fb71595363a80977636ca74c1fd10b21`.
- Controller: `research/doom/map01_overlap_controller_v39.py`, SHA-256 and Git blob in `FREEZE.json`.
- Production guard: `research/live_control/observable_signal_guard_v2.py`, Git blob `c0955f976e3a0af6ce926f22cee4a5ddf70ef543`; source copy is included here because this checkout sparsely materializes that path. The copy’s SHA-256 is in `FREEZE.json`.
- Exactly one candidate invocation and one independent audit invocation. Any failure is retained; no repair/retry is part of this frozen allocation.
- Exact commands are listed in `COMMANDS.txt`.
