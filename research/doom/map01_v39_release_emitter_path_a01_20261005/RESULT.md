# V39 per-key release emitter path audit (A01, 2026-10-05)

## Finding

The retained run `map01-v39-coast-liveness-live-01` did not select the per-key release-batch telemetry composition. Its runtime source manifest lists `doom/session_map01_v12.py`, `live_control/input_owner_v10.py`, and `doom/doom_typed_release_backend_v1.py`; it does not list `session_map01_v15.py`, `doom_owner_thread_release_batch_backend_v1.py`, `doom_typed_release_backend_v2.py`, `input_transition_owner_v3.py`, or `input_transition_owner_v4.py`. The retained `backend-setup.txt` contains only Xauthority warnings and does not establish those later modules were imported.

The selected v15 construction wrapper explicitly imports `session_map01_v12` as its base, then monkeypatches `base.Backend=TelemetryBackend` and `base.Executor=ReleaseOrderedExecutor`. This makes v15 the concrete bridge required to reach the per-key emitter while preserving controller/session-v12 behavior. Merely pinning the v3/v4 owner modules in an inventory is insufficient; the runner must select the v15 wrapper and its `_merge_sources` must retain those module hashes in runtime `sources.json`.

The retained event stream has 39 `input_admission`, 28 `keys_held`, and one aggregate `input_released`; it has zero `input_release_transition`. The owner sidecar has 13 aggregate `owner_release` and zero `owner_explicit_keyup`. This is consistent with the older v1 backend/v10 owner path recorded in the source manifest. It does not indicate that the later emitter failed after selection: the later emitter was not evidenced as selected.

## Verification

- Fetched `origin/main` at `abfd01b729886f9a152bbf7246708aebf6ab328f`.
- Full SHA-256 values on current main match the four prefixes from the fresh Issue #59 report:
  - `research/live_control/input_owner_v12.py`: `cbfe57373a029aa7d0ae9e70e6cf99806262f8565e27a4415d060bdf73702d9a`
  - `research/live_control/input_transition_owner_v3.py`: `b6fc1c92c34bbb82f7542c303acf2004dfc7d99f471aa328cafbc710e7aec456`
  - `research/live_control/input_transition_owner_v4.py`: `dce08b87532dcaeac85b22be8820a4d30064fed458ae438d5ae956eeae2a70c3`
  - `research/doom/doom_owner_thread_release_batch_backend_v1.py`: `925e9499cc46682f739ab5a754979aeeeac26c75217b22b0ac3b054926392cc9`
- Direct parsing of the retained source manifest and rows yielded the counts above.
- `construction02/source/session_map01_v15.py` on current main contains the backend/executor selection and merges selected source hashes after run.
- No game, GUI, model, or input execution was performed. This is a static retained-artifact/source audit only.

## Outcome and boundary

**PASS — emitter selection gap localized.** The actual retained V39 run is not evidence against the per-key emitter implementation; its manifest points to the older path. The integration gap is selecting the v15 composition in a future authorized runner and verifying that the resulting retained `sources.json` names it and that `events.jsonl`/owner sidecar contain identity-bound per-key release rows. This does not establish that the selected composition works end-to-end, nor provide live threat-control, recovery, or MAP01 progress evidence. No live allocation was used or inferred.

## Follow-up construction feasibility check

- The existing `research/doom/test_session_map01_v15.py` runner-selection/lifecycle suite passes 8/8 on local CPython 3.14. Its selection case mocks `session_map01_v12.main`; it proves v15 assigns the V3 release backend and V13 executor and writes pinned module hashes, but it does not execute a key transition or recorder round trip.
- A stronger fake-owner composition check was not run. OrbStack context is `orbstack`, but `docker info`/image inventory failed while reading the containerd content-store blob `sha256:05e01176ffcc2258ca88f7d8aafb6bd9e3915cd7ad19af196924008ff16f84b6` (`operation not supported`). Host CPython also lacks the repository's PIL/Xlib/ViZDoom dependencies. No dependency install, image pull, daemon repair, or host-side substitute was attempted.
- Disposition: **STOP_CONSTRUCTION_ENVIRONMENT** for that stronger isolated test. This does not invalidate the static finding above. The next eligible step is to rerun a frozen source-composition construction in a healthy approved CPU container, asserting the selected v15 backend's per-key rows arrive through the same recorder callback and survive its JSONL round trip. It still would not qualify live input/game behavior.

## Related current-main selector candidate: PR #7843

PR #7843 adds an explicit `--measurement-session` opt-in to V39 while retaining V12 as the default. I independently composed its head `758d803ff2842a0e4f9ded8db119d84c02360a9f` with current main `abfd01b729886f9a152bbf7246708aebf6ab328f`; `git merge-tree --write-tree` produced conflict-free tree `ab50233b2cbc681ae39ef5745f7b5bf4ad87cdb9`. A saved standard-library check extracts and executes `session_command` from that exact merged Git tree and verifies the parser has a `store_true` opt-in, default selection stays on `session_map01_v12.py`, opt-in selects `session_map01_v15.py`, and every remaining child argument is identical. Result: **PASS_SELECTOR_ON_CURRENT_MAIN_MERGE_TREE**.

Reproduce after fetching PR head with `git fetch origin refs/pull/7843/head:refs/remotes/origin/pr/7843`, then run `python3 research/doom/map01_v39_release_emitter_path_a01_20261005/check_pr7843_merge.py`. Raw result is `PR7843_MERGE_CHECK.json`. GitHub reports #7843's replay-gate and workspace-index checks passed; formal was skipped.

This closes the source-level session-selection gap conditionally when the opt-in is used. It does not prove the actual V15 child process, runtime manifest, emitted per-key rows, live game/input behavior, feedback onset, bounded recovery, or task effect. The merged selector check starts no child process or game. The stopped container-backed callback round trip and separately gated live threat run remain outstanding.

## Refresh after current main and PR #7843 advanced

The latest observed current main is `e2c58048bbaa9653f10e003bceb2e1c60e74a9da`; the latest PR #7843 head is `a7450117f19c092f285ea28f7e9eb76fc0a0abc3`. Their conflict-free merge tree is `6ef0bfb197125cdbf42adf8839371586da4b7e5f`. The saved selector check was rerun from that merge tree and still passes V12-default / explicit-V15 selection / identical remaining CLI arguments.

I independently reran two relevant current-main suites on local CPython 3.14 after confirming byte identity of the exercised test and implementation files against `origin/main`: `test_session_map01_v15.py` passed 8/8, and `test_release_backend_v3_composition.py` plus `test_release_backend_v3_actual_composition.py` passed 14/14. The latter suite exercises the real V3/V4 wrapper and release-batch backend with a fake lower-level owner and sink callback; the callback is an in-memory list, not V12's JSONL recorder. These local unit runs use no container, GUI, game, or input owner.

PR #7843's latest body also records Windows CPython 3.11.9 results for its two release-backend suites (2/2 and 12/12) and the prior selector/scorer checks. GitHub reports its replay-gate and workspace-index checks passing. It remains open; this is not runtime deployment. A separate current-main custody failure is pinned to the PR #7829 bridge/owner source pair. That pair differs from V15's V4 transition owner and release-batch backend, so its result is neither evidence that V15 fails nor proof that V15 is immune; transfer under an explicitly matched V15 schedule remains unknown.

The verified scope now reaches selected-backend behavior through a callback and source-level V39 opt-in composition. It still does not exercise the actual V15 child process with V12's file/pipe recorder, runtime source manifest plus retained JSONL, the transferred custody schedule, any live/game task effect, feedback onset, bounded recovery, or MAP01 progress.
