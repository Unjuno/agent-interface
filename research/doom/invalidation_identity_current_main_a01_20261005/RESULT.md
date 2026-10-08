# Result — current-main invalidation identity replay A01

Disposition: `PASS_CURRENT_MAIN_INTEGRATION_REPLAY`.

The exact merge tree of current `main` `5db548aa351c8ccd351831485d5e5940a4967ff3` with PR #8031 head `bbdede97bf0ccfc1c3a0b6454422b402e8cf0b6f` was `74e24a812f6ffa2bf9a79b310ae76eb9070eb44b`. The local staged merge tree matched before test execution. Four frozen source/test SHA-256 values are in `FREEZE.json` and both run receipts.

Using cached image `agent-interface/native-suite-wslc-a08:20261004` (image ID `sha256:1b4a8bd7c0fe372cc0cafa74af433b8ae1f73f1bee0f11a028f126b08b2c128a`, Python 3.12.14), two separate containers ran with `--pull never --network none --cpus 1` and a read-only source bind:

- focused monitor/controller selection: 16 tests, exit 0;
- adjacent wait, cleanup, dual-signal, duplicate-consistency and dispatch selection: 40 tests, exit 0.

Raw stdout/stderr, exact argv, timestamps, exit codes, and source/output hashes are in `results/current-main-a01/`. `audit_replay.py` then ran in a separate network-disabled WSLc container. It independently rehashed all four source files and the four output streams, confirmed the test counts and zero exit codes, and returned `PASS_CURRENT_MAIN_INTEGRATION_REPLAY` with no audit errors.

The retained tests exercise the real health-only monitor and frame barrier through deterministic fake readers, images, queues, process/executor and planner schedules. They verify source identity preservation, hard and unknown invalidation handoff, and rejection of incomplete identity, older captures, wrong pointer bindings and wrong RGB hashes. The controller schedules deliver invalidation after model completion; neither this replay nor the source change tests pending-model-loop timing, real provider cancellation, GUI/X11/native input, physical release, live threat exposure, useful-feedback onset, bounded recovery benefit, or MAP01 progress. No game, model inference, GPU, GUI, or formal/live allocation ran.

The candidate code remains in draft PR #8031, not on `main`. This replay verifies current-main integration only; it does not close Issue #59.
