# V15 startup release-closure A02

A02 is a newly frozen successor to A01, retained as `STOP_CANDIDATE_IMPORT` before backend or input-owner construction. A01 installed an incomplete fake `executor_v3` module; the real current-main V13→V12→V11 import correctly required `executor_v3.Executor`. A02 removes that stub and imports the actual current-main executor chain. No A01 candidate rerun is made.

## H/T/D/C/U

- **H:** Calling actual current-main `session_map01_v15.main()` selects `doom_owner_thread_release_batch_backend_v1.Backend` and `executor_v13.Executor`. Through a declared test shim replacing only the V12 session entrypoint, the selected backend executes two distinct DOWNs and reverse UPs using current-main InputOwner V12; it preserves no-inter-UP-query ordering and publishes two identity-bound verified rows plus empty batch state.
- **T:** One FakeXlib candidate execution through the V15 wrapper. Fake game/progress/scorer modules and V12 `main()` are test seams; `executor_v3`, V13, V12, V11 and the selected backend are imported from exact current main. No actual game, X server, GUI, model, or OS input.
- **D:** Runner verifies frozen source and harness hashes before candidate start. It retains one trace and one independent audit. PASS requires V15-selected backend/executor identity, exact source manifest, reverse UP order with no intervening keymap query, per-key owner receipts, verified empty batch, and explicit no-real-I/O scope. Preserve any failure without retry.
- **C:** Current main `f32f0fd3d6e171b6d010b1f9782d0152c88cd39c`; local `python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016` Python 3.12.15 linux/amd64; WSLc network disabled, read-only repository bind mount, one configured CPU, 512 MiB memory, 32 MiB tmpfs. WSLc's swap/cgroup warning is retained; memory enforcement is not inferred.
- **U:** This qualifies the V15 `main()` composition patch and selected backend with a fake V12 session entrypoint. It does not run the actual V12 CLI/session lifecycle, current V39 threat exposure, real X11, useful task feedback, live recovery, ammo/progress, or terminal outcome.

## One-shot gate

The candidate and audit run once after all hashes validate. A01 is immutable and remains a setup STOP. No live allocation is used.
