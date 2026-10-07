# V39/V15 per-key X-server keymap sample A01

## H / T / D / C / U

**H:** The current V39 opt-in V15 path reports identity-bound KeyRelease/XSync receipts for each key-up but samples key state only after the whole release batch. A V15-only owner variant can add a server query_keymap sample after each key-up sync and require an UP sample before the batch is marked verified.

**T:** Freeze current main at 69dd261430cb1ed875f5a76411c4a2a54777c114 and replay two keys through the actual V15 release-batch backend and the V4/V3/V12 owner implementation over fake Xlib. Compare baseline backend V1 with candidate V2. In the candidate, enable per-edge sampling only through the V5 transition adapter and the V15-selected backend V2. Include DOWN and query-error controls. Run focused integration and compatibility suites in normal and optimized Python.

**D:** PASS_SOURCE_COMPOSITION_ONLY iff the V1 trace has both key releases before its only keymap query; V2 has a keymap query after the first release and before the second; V2 rows join each query to its release and show UP; and DOWN/UNAVAILABLE samples prevent owner_transition_verified.

**C:** The owner and release-batch code under test are the selected V15 implementation layers. The inherited game-facing backend base and Xlib are fakes. Fake Xlib deterministically updates a local key set and returns it from query_keymap. A query after each key-up is a synchronous operation between key-up calls and therefore changes inter-release scheduling. The recorded clock values describe only this fake-display run. physical_verification_authoritative remains false.

**U:** No live X server, application, OS input, game, model, GUI, container, threat exposure, useful feedback, recovery, physical-key transition, physical latency, gameplay outcome, or MAP01 run is established. This source-composition result does not authorize or satisfy a live allocation.

## Result

The baseline trace has two KeyRelease operations at positions 4 and 6, followed by the only query_keymap at position 9 during owner cleanup. Neither release row contains a per-edge keymap sample.

The candidate trace inserts query_keymap at position 6 after key a releases and before key b releases. The first query sees fake keycode 56 (b) still down; the second sees no keys down. Both emitted release rows report a sampled server state of UP, and the ordinary two-key batch passes its current verification gate. The physical-authoritative field remains false.

In the negative controls, a still-down a yields DOWN, blocks the batch verified decision, and is observed again during terminal cleanup, which raises RuntimeError. An injected query exception is recorded as UNAVAILABLE / OSError and also blocks the batch verified decision.

The focused integration, V15 selection, V12 cancellation, V4 receipt, and release-batch suites passed 28 tests in normal mode and 28 with -O. Raw traces and per-suite stdout are included.

Run the package audit from repository root:

    python -B research/doom/v39_perkey_server_sample_a01_20261005/audit.py

