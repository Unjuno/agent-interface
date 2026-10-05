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
