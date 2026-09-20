# Passive-clock / scorer-snapshot reconciliation

Disposition: `HOLD_LIVE_PHASE_UNIDENTIFIED`. This is excluded container
construction evidence, not the frozen 120-row allocation. It qualifies the
earlier broad statement that the engine clock itself had been proved static:
the read-only ViZDoom state exposed to Python was static during waits, while a
later one-tic action call revealed a large tic catch-up. Those observations do
not identify the instantaneous engine tic at the scorer call.

## H / question

Can the exact current-main `_coherent_progress_sample` observe the live 35 Hz
phase in a passive `ASYNC_SPECTATOR` MAP01 session, with no clock-driving call
during the measured interval?

## T / excluded container checks

All runs use fresh Freedoom MAP01 sessions, no gameplay buttons, a read-only
WAD mount, `--network none`, and separate raw/output directories.

- `construction-clock-08` to `-09`: ViZDoom 1.2.3, minimal hidden then visible
  Xvfb/Openbox setup. Three repetitions per run. All 2.0 s read windows showed
  no `get_episode_time()` change.
- `construction-clock-10` to `-11`: ViZDoom 1.3.0, normal visible MAP01
  configuration, Xvfb/Openbox, and an explicitly focused ViZDoom window.
  Again, all 6/6 2.0 s windows reported a fixed `get_episode_time()` value.
- `construction-clock-12` to `-15`: same 1.3.0 setup. After the 2.0 s passive
  observation, a single `advance_action(1, True)` returned tic deltas of
  +71/+71/+72/+72/+71/+72 over 10.6–54.3 ms. This is consistent with a
  wall-clock async engine whose Python snapshot is only refreshed by an action
  call, but does not by itself prove that interpretation or locate tic edges
  during the preceding interval.
- `construction-clock-16`: replacing that endpoint call with
  `advance_action(0, True)` changed no reported tics in 3/3 sessions. Zero-tic
  calls did not refresh the exposed snapshot.
- `construction-clock-17`: exact unchanged current-main scorer called once in
  each of three fresh sessions after a 2 s passive interval. All calls returned
  on the first internal attempt, with same-tic pairs 17→17, 17→17, and 16→16;
  outer call spans were 112,660 ns, 119,118 ns, and 111,785 ns. No
  `advance_action` occurred during the observation interval or scorer call.
  Cleanup succeeded in all three sessions.
  The run-17 raw schema labels a counter `passive_interval_api_calls`; that
  counter only tracks `advance_action` and is zero. Read-only tic/state getters
  and external XWD checkpoints did occur. The precise claim is therefore no
  clock-driving `advance_action` between checkpoints or during the scorer,
  not “no API calls.”
- `construction-clock-18` stopped before game initialization because the
  read-only container root's default working directory rejected creation of
  `_vizdoom/` and `_vizdoom.ini`; retain as setup evidence only.
- `construction-clock-19` initialized and cleaned up 3/3 sessions but used the
  wrong Python binding name (`get_state_state`, from an older C++-style API
  table), producing `AttributeError` on every server-state sample. It is a
  harness/API-name diagnostic, not a clock observation.
- `construction-clock-20` used the actual ViZDoom 1.3.0 binding
  `get_server_state()`. Three fresh visible MAP01 `ASYNC_SPECTATOR` sessions
  each sampled for ~2.00 s without an advancing action (155/157/155 samples).
  In every sample `ServerState.tic`, `get_episode_time()`, and `get_state().tic`
  all stayed at 3; no getter errors occurred, and all sessions closed. The
  median `get_server_state()` call spans were 57.6/53.6/57.9 µs. Thus this API
  does not supply an independent live-tic witness in this fixture either.
  Its additional multiplayer fields (`players_in_game`, AFK, last-action tics)
  were also stable and are not clocks.
- `construction-clock-21` repeated the 2 s no-action window and then made one
  endpoint `advance_action(1, True)` call. Across 3/3 sessions all three tic
  APIs agreed at tic 3 before/after the passive wait, then all exposed tic
  77/75/75 after the action call (deltas +74/+72/+72; `GameState.number` moved
  1→2). The call took 17.4/38.5/38.6 ms. This confirms that the reported
  snapshot update is associated with the action boundary in this setup, but
  does not locate the live tic edges during the preceding wait or establish
  whether the engine itself advanced autonomously.
- `construction-clock-22` removed the X server/window and repeated the passive
  observation in three fresh headless `ASYNC_SPECTATOR` sessions using the
  pinned ViZDoom 1.3.0 arm64 image. Each session ran for at least 2.00 s,
  sampled all three tic APIs 150/154/160 times, and made zero
  `advance_action`/`make_action`/`set_action` calls. Every sample in every
  session remained at `(get_episode_time, get_state().tic,
  get_server_state().tic) = (1, 1, 1)`. The unchanged scorer then returned its
  first coherent sample at tic 1 in 3/3 sessions. This independently repeats
  the no-autonomous-progress observation without a display server, but still
  does not identify live tic phase or explain whether the engine is paused.
  It is excluded construction evidence; formal rows remain 0/120.
- `construction-clock-23` tested whether the unchanged clock result was only
  caused by omitting the standard explicit `new_episode()` call. Six fresh
  hidden `ASYNC_SPECTATOR` sessions alternated matched start/no-start
  conditions (3 each), each with a 2 s no-action interval. In all 6, episode,
  game-state, and server-state tics remained 1 across 155–169 samples; the
  exact scorer returned coherent at tic 1 and every session cleaned up. The
  explicit call returned in 81.5–83.4 ms, but `is_new_episode()` was true both
  before and after it. Thus the missing explicit call alone does not explain
  the passive tic result; this still does not establish engine pause or supply
  live phase. Audit: `HOLD_NEW_EPISODE_DID_NOT_UNLOCK_PASSIVE_TIC`; construction
  only, formal rows remain 0/120.
- `construction-clock-24` stopped before game initialization because the old
  local image tag lacked the runner's required Dockerfile provenance file.
  No session or raw scientific row exists; log SHA-256
  `d36c41a37d8659f2193d5b6aae0543c53333f1d74a9df1072344647cc7f1259a`.
- `construction-clock-25` retained three rows but its audit correctly returned
  `FAIL_CONSTRUCTION_INTEGRITY`: wrong package-bundled WAD hash and missing
  image ID. Raw/log/audit SHA-256 values are `62aa8fbe590adf4c5c702b68e726e79a1d792806a5d8ad41b15902b917a42dab` /
  `53a12617676dfb543bc9419c607adb92d474103b8eef9f7d371c178e3efb8ba5` /
  `6c8228d2263583bf064e86a8876ef94c5376d5049e4abffc16db4e3a0803a678`.
- `construction-clock-26` reran the existing empty-button action-driver
  construction with the correct 0.13.0 WAD and image identity. Rates were
  33.25/34.54/36.92 Hz in idle/load/delayed-read; independent reconstruction
  found all 3 scorer phases, with `PASS_CONSTRUCTION_ONLY`, no errors/warnings.
  Host/container audit bytes match (SHA-256
  `be46c77c9dbece6b8b6ef0ac2e809a32e742a543951419b861f13c6d9119e17b`). It
  remains an explicit advancement intervention, not a passive-clock result.
- `construction-clock-27` made one empty `set_action([0]*9)` assignment after
  explicit episode start in three of six matched headless 1.3.0 sessions; the
  other three received no assignment. Every session stayed at tic tuple
  `(1,1,1)` for 2 s, scorer returned at tic 1, cleanup 6/6. No `advance_action`
  or `make_action` calls occurred. Independent host/container audit matched,
  `HOLD_EMPTY_SET_ACTION_DID_NOT_UNLOCK_PASSIVE_TIC`, zero errors. Raw SHA-256
  `a15eefca951e014ca6e3b6b56f0cab2f3d2e85e76f724437e18b9e884f1bf5f9`; audit
  SHA-256 `3c527da4d3a70484fcc685188fdb0f5ff2f283b873af4efb26008120248b1d02`.
- `construction-clock-28` compared `available_buttons=[]` with nine
  registered-but-unused buttons in three matched pairs. All 6 sessions stayed
  at tic tuple `(1,1,1)` for at least 2 s, with no set/advance/make-action calls;
  scorer and cleanup succeeded 6/6. The independent audit is
  `HOLD_BUTTON_INVENTORY_DID_NOT_UNLOCK_PASSIVE_TIC`, zero errors, and host /
  container bytes match. Raw SHA-256
  `261a3cf2887117bf1da30d87ea5135633327e2b4e849849092028b2ebf2e9d3b`; audit
  SHA-256 `1c0531fc5404f08ba3b768914e9bd533a58f2caf2624cd3baa489dda0e234bb2`.
  All 16 focused tests passed locally and in isolated arm64 Docker.
- `construction-clock-29` compared `ASYNC_SPECTATOR` and `ASYNC_PLAYER` in
  three alternating matched pairs, all on hidden MAP01 with Freedoom 0.13.0,
  explicit `new_episode()`, nine unused buttons, and no advancement API calls.
  All 6 sessions remained at their session-initial tic (first pair: 2; next
  pairs: 1) across 146–155 samples, with all three API views equal. Exact
  scorer and cleanup succeeded 6/6. The host/container audit is byte-identical,
  `HOLD_BOTH_ASYNC_MODES_PASSIVE_TICS_STATIC`, zero errors; the current 17
  focused tests pass in isolated arm64 Docker. Raw SHA-256
  `5d3312c4b4628ccc1681446c4a39122c1d0911b2e38cc7034c49b08b9993c88c`; audit
  SHA-256 `b48ec5266772ce2246b1646c4b8236429e76d27ac28f75fcb41528180451a2c2`.

The visible X11 window was captured independently at 250, 500, 1000, and
2000 ms in runs 14–17. The retained lossless XWD captures mostly show the same
scene; measured adjacent-frame differences in run 14 affected only 64–379 of
293,940 pixels (0.022–0.129%). Comparing the final passive frame with the frame
after `advance_action(1, True)` in run 15 changed only 60–78 pixels, localized
to the weapon area. These sparse pixels are not a validated game-clock witness
or a phase estimator. Full XWD bytes are gzip-compressed without changing
their contents; raw JSON and container logs remain uncompressed.

## D / interpretation

The exact scorer is callable and its raw getters, return, call span, and cleanup
are retained in `construction-clock-17/raw.json`. However, its same-tic result
is based on the last state exposed to Python, which remained stale through a
2 s wait. The post-wait `advance_action(1, True)` catch-up cannot be used as an
instantaneous phase observation without proving its refresh semantics. The
available read-only observations therefore do not independently reconstruct
phase, spans relative to live tic edges, or the intended phase-stratified
outcome. This evidence does not establish either a stopped async engine or
normal-rate visual/gameplay progression.

### ViZDoom 1.3.0 source boundary

I also checked the exact tagged 1.3.0 C++ implementation. [`getState()` and
`getServerState()`](https://github.com/Farama-Foundation/ViZDoom/blob/1.3.0/src/lib/ViZDoomGame.cpp#L422-L430)
return the wrapper's stored pointers. [`advanceAction()`](https://github.com/Farama-Foundation/ViZDoom/blob/1.3.0/src/lib/ViZDoomGame.cpp#L170-L180)
calls the controller's `tics(...)` and then, when `updateState` is true, calls
`updateState()`, which creates new `GameState` and `ServerState` snapshots and
sets their tic fields from [`DoomController::getMapTic()`](https://github.com/Farama-Foundation/ViZDoom/blob/1.3.0/src/lib/ViZDoomController.cpp#L1078).
[`getEpisodeTime()`](https://github.com/Farama-Foundation/ViZDoom/blob/1.3.0/src/lib/ViZDoomGame.cpp#L610)
also delegates to `getMapTic()`, which reads the mapped `gameState->MAP_TIC`
field. This explains why the two object snapshots advance together at the
explicit action boundary; it does not explain why the shared MAP_TIC read stayed
fixed through the passive interval, nor establish whether the engine process
was paused or autonomously progressing. Keep that runtime/lifecycle question
open; no source-only claim upgrades the experiment to PASS.

Keep the original `STOP_SETUP_OR_INFRA` record for the earlier 1.2.3 candidate
unchanged as history. The current 1.3.0 clock/snapshot finding is a new,
scoped `HOLD_LIVE_PHASE_UNIDENTIFIED`, not a formal STOP/FAIL/PASS and not a
reason to relabel the earlier construction runs. Formal rows remain 0/120.

## C / scope and U / next gate

This applies only to ViZDoom 1.3.0 in the pinned arm64 Xvfb/Openbox fixture and
to its Python-visible scorer snapshot. It says nothing about other ViZDoom
versions, a native desktop display, gameplay progress, or human tempo.

Before a new freeze, establish an independent, non-perturbing live-tic witness
whose timestamps bracket scorer getters, or show from the current-main runtime
call path that a specified refresh is part of the scorer's actual production
boundary and freeze that estimand explicitly. Reconcile the witness against
the API-visible tic and retain its calibration/uncertainty. Do not infer phase
from requested sleep, XWD file hashes, or post-hoc `advance_action` catch-up.

## Provenance

The PR review audit also identified and this follow-up fixes two classification
integrity cases: the failure event now requires exactly three complete,
API-successful incoherent attempts; any API-failed attempt is a fatal audit
integrity error, not just a non-failure; and each `case_id` is checked against
its frozen phase target, stratum, and deterministic seed. The separate
ServerState audit also requires the full 0/1/2 repetition set for every
three-session run. Regression tests cover incomplete/API-failed attempts,
schedule-cell reassignment, and missing/duplicate repetitions. The latest
review also pointed out that getter-error events must prevent formal PASS even
when the third retry has a complete-shaped trace; the auditor now records
`api_attempt_error`, treats incomplete attempts as errors, and classifies both
as fatal integrity outcomes. Tests assert those error classes are fatal.

- Current scorer source SHA-256: `1a6da676db9c6b2aa61ccf0f600a1565395e906736bb07a50b2006e100d7ca98`.
- WAD SHA-256: `a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b`.
- ViZDoom 1.3.0 focused/XWD image: `sha256:65c2693c72adad38c529f1483e7b315defce13c59eb02bcd459285716379c826` (`linux/arm64`).
- Run 17 raw JSON SHA-256: `5b4ea860d60a1a6ebb8e91056b124afded9a46a5b1b398952db6219a29d2db47`.
- Run 17 container-log SHA-256: `7b5437c4b361c49fb854a50f949a6cd45a32a3595cc1d10e99bcc88d5f757ad5`.
- Run 17 mounted construction script SHA-256: `7769c7b1e2100715b37abedf1a7561093f13ba96904d8fb32fa086d938aeb4ab`.
- Runs 08–16 retain their own raw JSON, logs and build logs; exploratory script revisions were not separately hashed at execution, so those earlier runs are explicitly lower-provenance diagnostics.
- Independent construction-artifact audit: `results/construction-clock-audit-01/audit.json`, SHA-256 `5333ed2a4fd5c63c27627aa604d9fc28ec9de411daf78df109098c0a93f67cad` (`PASS_AUDIT_ONLY`, 30 rows, 57 retained XWD hash/size checks, zero errors). It verifies retained evidence consistency only; it does not supply a live phase witness.
- Review-fix container image: `sha256:4320dd483b24ea91c1481f12fd5799c903d9daa99a517b994f607037098ea41d` (`linux/arm64`). Build log: `results/container-review-gate-build.log`, SHA-256 `544f092cd150a6308e0ca66d313a941d084bb0eb04c671e8475464e2124f1586`; local and isolated-container `test_audit.py` runs both passed 12/12.
- ServerState probe audit: `results/server-state-witness-audit-01/audit.json`, SHA-256 `1315aa70e5481fa9b21aa0f84e1fced1fd4ddcd1ce4db578f9d5b64cbcada174`; the same bytes were reproduced inside the isolated container (`container-audit.json`). Decision `HOLD_NO_INDEPENDENT_LIVE_TIC`, three valid run-20 and three refresh-characterization run-21 sessions, no formal allocation. Passive probe source SHA-256 `cbc8a718ebb8ea96680a3ccfa31c2f43a3c558e1b33d55567a85404425f1ba38`; refresh probe SHA-256 `64cd3aad4368b5f4de39fa266beb0601a8c2a5fad0b14d708e495a803b57d628`.
- Run 18 log SHA-256 `8de57339204a4d1bb0d814ef7fd241a6b25a87cb7a6ca40e2f28b83c80b5df9f`; run 19 raw/log SHA-256 `f1eaf8429ab3c2a1a7a4c75da158a421bdc302eb03124ec3a714f8c69124c43f` / `379336d1d30753e477129eb28f5186cf4ac20e9bcb3a073b631f3b4978ee5e91`; run 20 raw/log SHA-256 `457e9342ee52382f69eb95576cbe4e77682975b9df6c87045baf74786b4ecfb5` / `74cb980ea04ec285cefe11a2f2bd5adcceee8118e057b74a64e3a1a7595a4d9e`.
- Run 21 raw/log SHA-256 `6fb00340f7a36234d6186528020efd7ff69bcfc47b9f51dc33bf5cc6c39c83cf` / `5496c99cb3fbad09bffbe75992c169553d9bbfa346ae555606f150adcd793bcb`.
- Run 22 probe source SHA-256 `137274bc845cefd9efbd718f1ec18c5815b1a50de896578367d0338b95afbf72`; raw JSON SHA-256 `92993b9ad9050b0872a5b6f5dc68444885b85d0c66d4226f6e84ecc3f4e0b909`; container log SHA-256 `d24e349beaf931a8de4fc961da0cd8b471abcc61bee58707f2c5f7c135bb55ad`.
- Run 22 independent audit: `results/construction-clock-22/audit/audit.json`, SHA-256 `0997107aea26b5fea68b24d9b50428891e8b1d670b5c7ef5c620c1c47facd64e`; the isolated arm64 container reproduced byte-identical `container-audit.json`. Decision `HOLD_NO_INDEPENDENT_LIVE_TIC`, zero audit errors, 3/3 valid headless sessions. The current 15 focused tests pass locally and in isolated arm64 containers. This is construction-only and formal allocation remains 0/120.
- Run 23 probe source SHA-256 `05365999504cfdca805b711601740159e10bc83c3e73e1d26546d53e8c8fa1c4`; raw JSON SHA-256 `9464eb45a83271313ec2aac8c8e5845979eec4cc48e102a200745b9f76a65da6`; container-log SHA-256 `536cce6bd151fe3b38679f4a49b1e737628f613fa74b1304a56c86bc7be592d7`.
- Run 23 auditor source SHA-256 `5c23559b1e3723a14957db00afeaceda772bd652335ee142c9162b1c75ed6557`; audit JSON SHA-256 `5eff632881a36708be34c4b40aed851f7bfffba2353d5c67b24e13604e9cbb28`.
- Run 23 independent audit: `results/construction-clock-23/audit/audit.json`; host and isolated arm64-container JSON are byte-identical. Decision `HOLD_NEW_EPISODE_DID_NOT_UNLOCK_PASSIVE_TIC`, zero errors, three explicit-start and three implicit-start sessions. Construction only; no formal allocation.
- The official ViZDoom API documents `get_server_state()` as returning the current `ServerState`, and `get_episode_time()` as returning the current episode tic: https://vizdoom.farama.org/api/python/doom_game/. The run-19 method-name discrepancy was resolved against the actual 1.3.0 Python binding, not assumed from that documentation alone.
- Source audit is pinned to ViZDoom tag `1.3.0`, commit `c8e0a31182d98c6f40a65674283e736b851e8e59`: `src/lib/ViZDoomGame.cpp` Git blob `33c096fdbaa0ff670aad46dc0e65b1c10e949070`; `src/lib/ViZDoomController.cpp` Git blob `1d4d2860b8ca786096a3376071f49d24b6f29ce6`; `include/ViZDoomGame.h` Git blob `d9ab5d5e782f6765fa8c5b2a3b78588195c0925a`.
