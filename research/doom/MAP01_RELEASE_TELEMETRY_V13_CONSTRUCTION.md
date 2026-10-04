# MAP01 v13 per-key release telemetry composition — 2026-10-04

Status: **PASS — opt-in source composition only; no session or live allocation ran.**

Base: current `main` at `2ed11c5552956499454e8a99acf5a2f374106d34`.

## Question and decision

**H:** Selecting the already-tested v2 typed release backend in an opt-in copy of the current v12 MAP01 session runner is sufficient to emit the v11 per-key ordinary-release RPC receipt, while leaving the v12 session body and default backend unchanged.

**T:** Copy current-main `session_map01_v12.py` to `session_map01_v13_release_telemetry.py`; change only its module description, backend import, and source-hash list (replace the v1 backend hash with v2 and add the v11 owner hash). Compare the entire candidate file byte-for-byte against that expected transformation. Run the focused composition test and compile both session modules.

**D:** Pass composition only if the whole-file comparison is exact, the import resolves to `doom_typed_release_backend_v2.Backend`, source hashes cover both `doom_typed_release_backend_v2.py` and `input_owner_v11.py`, the candidate compiles, and its module-specific tests pass. Any other session-body change is a failure pending separate justification.

**C:** A v13 session copy can drift from future v12 safety or behavior changes; the exact-delta regression makes such drift visible but does not prove the two runners behave identically in a real session. Backend construction tests cover the v11/v2 contract separately.

**U:** No X11 session, VizDoom game, key input, model call, useful-feedback scorer, recovery condition, matched condition, or formal allocation ran. The v11 receipt brackets the existing X11 release-plus-sync RPC; it is not an exact hardware transition time, continuous keyboard-state proof, or application-consumption time. The v39 useful-feedback and bounded-recovery gates remain open.

## Change

`session_map01_v13_release_telemetry.py` is opt-in. The default `session_map01_v12.py` remains unchanged. V13 selects the existing `doom_typed_release_backend_v2` and adds hashes for that backend and its `input_owner_v11` dependency to the runtime `sources.json` receipt. The v11 wrapper records a per-key caller interval around the unchanged v10 owner operation; it does not add an X11 round trip between key releases.

## Executed construction check

The new exact-delta and import-selection tests first failed while the copy still selected v1, then passed after the v2 selection and two provenance-list changes. Final verification:

```text
python -B -m unittest research.doom.test_session_map01_v13_release_telemetry -v
Ran 2 tests ... OK
python -B -m py_compile research/doom/session_map01_v12.py research/doom/session_map01_v13_release_telemetry.py research/doom/test_session_map01_v13_release_telemetry.py research/doom/doom_typed_release_backend_v1.py research/doom/doom_typed_release_backend_v2.py
git diff --check
```

The compile and diff checks exited successfully. The existing v11/backend-v2 suites were not runnable on this Windows host because PyXlib is absent. WSLc inventory showed a foreign container active at observation time, so no WSLc workload was started. No dependency was installed and no other worker's container was touched.

This construction result makes no claim that v13 has run. A prospective session needs a new frozen source set and allocation under the current #59 gate; the consumed `MAP01-V39-RELEASE-TELEMETRY-LIVE-59-T0-20261004-01` remains STOP and is not reusable.
