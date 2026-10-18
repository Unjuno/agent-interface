# A01 freeze: typed health-envelope replay over retained V28 threat spans

## Question

Does the exact current-main V39 observable-signal health guard mechanically
coalesce health changes in the five interrupted source-to-invalidation spans
from retained `map01-fixed-threat-v28-live-01`, and how does interruption count
depend on the authored `maximum_health_loss` values permitted by V39 (0–20)?

## H / T / D / C / U

- **H:** A typed absolute health floor can classify some exact historical
  source-to-trigger transitions as `SOFT_CHANGED` rather than
  `HARD_INVALIDATED`. The number of invalidating spans depends on the bounded
  authored loss envelope.
- **T:** Pin source main `6a2826d391b77496b69752609a6f07b6971b4b6f`, the exact V39
  controller and `ObservableSignalGuard` source files, V28 `report.json`,
  `runtime/events.jsonl`, and manually reviewed exact-frame transcription
  `analysis/threat-review.json`. Extract only the five V28 decisions whose
  planner turns were interrupted. For each source/trigger pair, instantiate the
  current V39 guard with `critical_health_minimum=35`, the swept
  `maximum_health_loss=0..20`, `max_source_age_ms=30000`, the exact sequence and
  capture timestamps, and one fixed synthetic binding. Evaluate the source
  health/ammo against the destination health/ammo. Do not feed images or run a
  controller, model, game, GUI, X server, or input backend.
- **D:** `PASS_COUNTERFACTUAL_REPLAY` only if all five exact report/event/manual
  frame joins validate, all 21 sweeps run through the pinned guard, and the
  independent auditor reproduces every per-span guard outcome and summary
  count. A mismatch is `FAIL_REPLAY_OR_AUDIT`. Results may select health-loss
  values for a separately frozen live test; they cannot establish that any
  continued cover was tactically appropriate.
- **C:** The V28 invalidations were triggered by a changed-pixel region guard,
  not by typed health alone. Damage is not causally attributed to any cover.
  The source-to-trigger pairs are cross-bound snapshots; intervening frames and
  state may contain important changes not represented by the health/ammo
  transcription. A single source-relative health budget may be semantically
  wrong for combat.
- **U:** This is an offline counterfactual over five historical spans. Replaying
  the threshold assumes the recorded destination evidence is the only input to
  the health guard; it does not emulate concurrent model completion, cover
  renewal, planner scheduling, position, enemy range, damage timing, or immediate
  re-admission after invalidation. The configured binding is synthetic and
  constant. No live allocation or fresh model call is authorized or inferred.

## Frozen source identities

- Current-main commit: `6a2826d391b77496b69752609a6f07b6971b4b6f`.
- Exact reviewed inputs: `research/doom/results/map01-fixed-threat-v28-live-01/analysis/threat-review.json`;
  `runtime/events.jsonl`; `report.json`; existing `audit.json`.
- Guard source: `research/live_control/observable_signal_guard_v2.py`.
- Controller source used to establish V39 floor construction:
  `research/doom/map01_overlap_controller_v39.py`.
- The candidate and independent auditor must read these paths as read-only and
  write only to a new output directory. The already-consumed V28 allocation and
  its evidence remain unchanged.

## Frozen span selection and boundaries

Include only report decisions `[0, 2, 3, 4, 5]`, each with
`planner_turn_status == "interrupted"` and a `policy_invalidation`. Pair that
decision's `source_image` with its invalidation image. Use the frame SHA256,
health, ammunition, sequence, and `capture_ns` from the retained review/event
records. Do not include completed decision 1 as an invalidation span. Its
authored nonempty cover is context for why decision 2 is relevant, not a test
outcome for that cover.

The guard's source-relative floor is fixed by the current implementation:
`max(critical_health_minimum, source_health - maximum_health_loss)`. Health
equal to the floor is within the current guard envelope; only a lower value
invalidates. The ammo guard floor is fixed at 1 when ammo is observed. No
threshold is selected post-run; all 21 supported loss values are enumerated.

## Environment and execution

The primary host is Windows. `wslc.exe` is unavailable. This analytical replay
uses the locally installed Python 3.11 runtime; Docker/Engine is not required
by the frozen protocol and is not used. There is no game, OS input, model,
network service, GPU, GUI, or live allocation in scope.
