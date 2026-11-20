# V15 startup release-closure A01

## H/T/D/C/U

- **H:** On exact current-main source, calling V15's actual `main()` selects `doom_owner_thread_release_batch_backend_v1.Backend` and `executor_v13.Executor`. When the selected backend is exercised through a deterministic V12-main test seam with two distinct held keys, its current-main owner emits reverse-order UPs without `query_keymap` between them, then publishes two identity-bound rows and one empty post-batch owner state.
- **T:** One FakeXlib run. Import and call the current-main `session_map01_v15.main()`; replace only `session_map01_v12.main()` with a declared test shim that asks the classes V15 selected to perform two DOWNs and reverse UPs. Use current-main V15, release-batch backend, V4/V3 and V12 source files from the read-only repository mount. No real X server, game, GUI, model, or OS input.
- **D:** Retain the ordered XTest/keymap trace, selected backend/executor identity, V15-merged source manifest, per-key receipts, batch state and independent audit. PASS requires exact frozen source hashes, correct V15-selected types, two reverse UPs with no inter-UP keymap query, owner identity and token agreement, verified empty batch, and no real-I/O claims. Any other result is preserved without retry.
- **C:** Main `f32f0fd3d6e171b6d010b1f9782d0152c88cd39c`; V15 package image `python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016` (Python 3.12.15, linux/amd64), already locally available; WSLc network disabled, one configured CPU, 512 MiB memory, 32 MiB tmpfs, repository mounted read-only. WSLc warned swap/cgroup memory accounting is unavailable; configured memory enforcement is not inferred.
- **U:** This qualifies V15's actual composition patch and selected release backend against a test-only replacement for the V12 session entrypoint. It does not run the V12 CLI/controller, X11, V39 threat exposure, game time, visual feedback, physical input, or any live task. It cannot prove the live lane's stop/switch, recovery, ammo/progress, or terminal requirements.

## One-shot gate

Freeze candidate, auditor, runner, protocol and source SHA-256 values before candidate start. Runner verifies them before launch, runs candidate once, and runs the independent auditor once on captured raw output. Preserve the first PASS, FAIL or STOP; no retry or live allocation.
