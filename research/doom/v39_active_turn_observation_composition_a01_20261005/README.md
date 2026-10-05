# V39 active-turn observation composition A01

Disposition: `PASS_CONSTRUCTION_ONLY`. Parent question: [Issue #59](https://github.com/Unjuno/agent-interface/issues/59).

## Question and scope

The current V39 controller used a paired typed health/ammo monitor to retain soft changes for the *next* planner turn. This construction connects one current soft change to the already-running planner turn, so a pending answer can see it before returning. It sends only a full observation whose sequence matches the monitor's latest paired soft event, binds the PNG bytes by SHA-256 in the receipt, sends at most one event per planner turn, and leaves action authority and final fresh admission unchanged. Existing hard/unknown invalidation still takes the immediate cover-cancel and planner-interrupt path.

The App Server uses the `turn/start` `toolOutput` form established by the separate loopback protocol probe in [PR #7951](https://github.com/Unjuno/agent-interface/pull/7951). That PR remains separate protocol evidence: its mock received a second Responses request with the exact image, but performed no inference. This A01 tests the current V39-to-adapter composition with deterministic fakes; it does not rerun or replace that protocol probe.

## H/T/D/C/U

- **H:** On the current-main V39 dispatch path, a matching soft event is sent once to the same active planner turn with its exact full-observation PNG, while hard invalidation, cancellation, and ordinary action admission retain their existing authority boundaries.
- **T:** Exercise the production nested `wait()` dispatcher with typed/full paired rows and a duplicate frame row; exercise the planner adapter with a fake App Server; separately verify hard invalidation dispatch, interruption refusal, the local RPC timeout parameter, exact-artifact RGB digest revalidation at send time (including same-sequence file replacement), and existing V39 controller regressions.
- **D:** PASS if the matching row is forwarded at most once, the adapter's returned thread and turn IDs equal the active handle, malformed/stale/cancelled/duplicate updates do not attach, and hard invalidation remains higher priority. Any model, action, or live-game effect is outside this decision.
- **C:** Acknowledgment may only mean the App Server queued untrusted context. A real model may ignore it, misunderstand the frame, finish before reconsidering, or spend more input tokens and latency. A 500 ms RPC timeout may leave delivery ambiguous; the controller then invalidates the dependent answer and uses its existing interrupt/release route without retry.
- **U:** No real inference, App Server process, game, GUI, OS input, physical release measurement, useful feedback, replacement-plan recovery, latency/usage comparison, or task effect was run. No live allocation is implied; Issue #59 records the private lane as unassigned.

## Freeze and changed files

- Base: `origin/main` `402c7d1b5147b2a905098f082233db60a47d68db` (2026-10-05).
- Current-main verification rerun after syncing the branch: `6860b585305e539ec93896f5adcbf658cbbd8592` (which includes `62da4c836a2419d0b1261708b5a59ee3d82db618`). The intervening commits add unrelated analysis packages and do not modify the three runtime files under test. The saved suite outputs and exit codes correspond to the post-sync rerun. `run_tests.ps1` now allows unittest's normal stderr output and relies on explicit process exit codes.
- Frozen source SHA-256 at base:
  - `research/doom/map01_overlap_controller_v39.py`: `4548ca30b5a962946c7f81a58784a5b8e672a10635f4737c36b38f596b2c27ca`
  - `research/live_control/persistent_planner_adapter_v2.py`: `e00ca6b8f20ee1081dc57a0ccd754115fe81f9bf5fa36553ed7c98add873fc0e`
  - `research/live_control/codex_app_server_client_v2.py`: `d140fec92cb7e81a439d7cda95c67d63d902af08fc4997bfa5df7933aa14deb4`.
- Changed runtime files are limited to the three sources above. Tests update those sources' existing adapter, app-server client, nested-wait, paired-signal, and production wait-dispatch suites. `run_tests.ps1` preserves exact output and exit codes under `results/`; `audit_results.py` independently checks the saved exit codes, test counts, compile result, and byte manifest.
- CPU-only Windows CPython 3.11.9. No external endpoint, credentials, GUI, game, image-generation service, or shared resource was used.

## Result

All 53 focused tests pass: planner adapter 12, app-server client 4, V39 paired-signal controller 21, V39 controller 5, nested wait 10, and production paired wait dispatcher 1. The send path now requires `exact is True` and validates decoded RGB pixels from the exact bytes later encoded for transfer against the observation's `frame_rgb_sha256`; the production nested wait test replaces a same-sequence PNG only after the monitor accepts it and verifies delivery is refused. The delivery receipt records both the PNG-byte digest and validated RGB digest. The result is a source-composition construction pass only. It does not establish that the model changes its plan, that the new request improves control, or that this should become the default without a separately authorized live evaluation and matched cost/benefit measurement.
