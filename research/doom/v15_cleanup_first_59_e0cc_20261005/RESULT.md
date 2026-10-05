# V15 cleanup-first cancellation: receipt retention and finite handback

## Result and decision

Adopt the scoped repair for review in #8094; do not claim main integration or live control success. On the current measured V15 path, emergency owner cleanup previously erased actuation identity before releasing keys. When that cleanup finished before the caller's deferred UP batch, the late batch also raised a generic inactive-lease ValueError. The real V39 controller stopped even though the real child executor's synthetic X state was already neutral.

The repair reuses existing per-key query/retry observations for separately labelled `per_key_cleanup_snapshot` measurements. It retains the admitted owner/intent/key/actuation identity for confirmed UP, leaves unknown/failed/no-op edges unconfirmed, and adds no cleanup keymap queries. Measurements travel in the existing `input_released.owner_release.key_release_attempts` record and terminal interruption. No new bridge event, ordinary-release promotion, input authority, or application-consumption claim is introduced.

A successful owner cleanup remembers the exact lease object and interruption reason. A subsequent UP batch for that exact retired lease raises the existing Cancelled, Expired, or DecisionRequired signal without display I/O. A foreign lease with the same token, an old lease while a new hold is active, an ordinary already-released lease, and failed cleanup do not gain this exception mapping. The executor still performs and verifies final cleanup; V39's terminal verification remains unchanged.

## Evidence

- Baseline owner `a946b428...`: 7 of 9 initial focused tests fail because cleanup measurements are absent. Initial sparse-checkout import failure is retained separately.
- Measurement-only repair: focused 9/9. Watchdog cases were then tightened to await the actual cancellation, expiry, or focus cleanup before asserting the reason.
- First full child run `full01`: actual V39 main → real child V15/ExecutorV13/V4/V3/V12 owner. A schedule-only shim waits at an already requested UP batch until the owner watchdog records cleanup. UP identity reaches `input_released` intact, but terminal is `failed` with `ValueError('up_batch requires the active input lease')`; V39 stops. This first result is retained.
- Cause regression: 3 of 14 focused tests error before the cause repair; final 14 focused plus 33 adjacent tests pass normally and under optimized Python (47 distinct methods, not 94 independent experiments).
- `full02` hard health change and `full03` UNKNOWN: identical cleanup-first shim; terminal is cancelled with verified empty release, stale model answer is discarded, and the next model turn begins after terminal verification. Each retains one exact-admission cleanup UP and three ordinary primary-plan measured pairs. Cancellation remains incomplete in the ordinary projector.
- `full04` persistent lost UP: owner publishes `input_release_unverified`, terminal remains failed, child exits 1, no next model turn runs, and fake key 24 remains down. Five fake connections close in every run; that does not turn the negative case into successful release.
- Raw audit v3: 75/75 checks, using raw Session/owner/barrier/model timeline records rather than trusting the report's success wording. Versions v1 and v2 failed on audit assumptions (integer policy count; unverified event kind), are retained, and were corrected without rerunning any construction.

Two adjacent runner setup failures are retained: mixed sparse/export import resolution, then absent doom PYTHONPATH. The successful runner uses one source export with live_control before doom. No product threshold was relaxed for these failures.

## Scope and relation to earlier work

Predecessors #7533/#7754/#7769/#7774/#7801/#7805/#7847 motivated this repair. #7805 merged into inspected main `6f4a288d...` as an additive older candidate; it was not the current measured V15 runtime. This work ports the relevant retention rule into current owner code and resolves the reproduced cleanup-first control race. The previous #8094 full-05/full-06 runs covered explicit batch UP winning the race and remain unchanged.

All runs are ordinary regressions on macOS arm64 with Python 3.12.14, real Python controller/child/thread/pipe control, and synthetic external X/game/capture/HUD/model. No native display, real game, model inference, container, shared allocation, application input consumption, game progress, live latency, or recovery effectiveness was measured. The fake model's final `dead` answer is scripted termination, not a death/success result. Historical text in production reports is preserved verbatim and does not override these limits. #59 and the full computer-control objective remain open.

Exact source hashes, commands, platform, and loaded closure are in `execution.json`, `source-closure.json`, and per-run loaded-source lists. Raw observations, all first outcomes, and source variants are inert archive files. Technical peer review is not a nonauthor content vote or merge authorization.
