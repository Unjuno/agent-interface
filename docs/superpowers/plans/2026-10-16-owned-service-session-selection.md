# V15/controller explicitly select owned input service

Continue#59/#8999. `--owned-input-service` is opt-in, requires measurement V15
plus target process identity and refuses unqualified window-lifecycle transfer.
Validate in controller before planner/process startup and V15 before base import.
Strip wrapper flags before base argparse; pin newly selected runtime sources.

`session_owned_owner_backend.Backend` extends the actual selected Backend. Launch
one owned cancellation-enabled service, use its adapter, save exclusive file-fsynced
session startup/close receipts binding accepted startup and owned handle results.
Startup failures retain handle/cleanup evidence and original/secondary exceptions.
Close attempts real cleanup and preserves first receipt; unverified cleanup raises
after recording, so base V12 finally cannot silently accept false. No automatic
kill/retry. The control-effect fence also checks backend owner-service obligation.

Tests: inert controller/V15 selection and flag stripping/source manifests; actual
Fake X parent/backend/Executor through the session wrapper for normal and retained
blocked-release cleanup; receipt publication failure/partial startup and paired
errors preserve custody; effect boundary refuses adapter obligation even if local
Executor obligation is empty. No model/game/native display/WSL/container operation.
Use owned Python processes, private sockets and Fake X only. Actual controller/
session death remains a subsequent finite qualification, not proven by option tests.

Preserve first red/source/raw, normal/-O relevant regression, frozen source union,
offline byte/hash/selection/custody readback with altered negatives, bounded review,
verified integration and existing#59 continuation. No new coordination Issue or
reviewer quota; full live/task/economics goal remains active.
