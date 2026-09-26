# Running-action freshness exception boundary — 2026-09-27

## H / T / D / C / U

- **H:** If the controller decision timestamp is 1 ns earlier than the current snapshot capture timestamp, the existing freshness evaluator raises before the running-action guard records an invalidation. The guard may retain its prior active-state receipt; this output must not be mistaken for a safe continuation.
- **T:** Read exact action_validity_admission_v1.py and running_action_guard_v1.py from main commit 4c3d6f1240896d4441ecb37e447760a3847012ae. Execute them from standard input in the pinned linux/arm64 image issue2679-map01-runtime@sha256:029e1867aeb843f2d63080343bfbb61540b64852ce00d4d99ec0be51796a093e, with --network none --read-only. Probe decision time one nanosecond before capture, equal to capture, and one nanosecond after capture. Run both unchanged upstream unittest modules in the same container.
- **D:** PASS_RUNNING_GUARD_EXCEPTION_STATE_CONTRACT_SCOPED. The before-capture case raises “controller decision precedes current snapshot”; after the exception, state is INPUT_ACTIVE, current_input_authority=true, physical_input_may_be_down=true, physical_release_verified=false, requires_new_decision=false, with no invalidation receipt and no appended validity check. Equal/after-capture controls remain active as expected. Independent assertions: 3/3. Existing action-validity/running-guard tests: 16/16 passed.
- **C:** This is a deterministic contract probe over two exact main modules plus their existing tests. It does not execute the production MAP01 caller, catch-and-continue behavior, Docker game session, model, or input. The prior formal seed 990641 is consumed and unchanged; the probe is not evidence that this exact exception caused that historical HOLD.
- **U:** The guard's returned state after an escaping exception is not itself a release/cancellation receipt. The production runner's exception/teardown behavior and the exact historical comparison operands remain outside this test. No fix or formal allocation is proposed by this result.

## Frozen identities

- Main source commit: 4c3d6f1240896d4441ecb37e447760a3847012ae
- research/live_control/action_validity_admission_v1.py: Git blob 31bd30bd9baf6b7d56494cc3a18b2c6c70ffbc5e; SHA-256 f102cbde4f0e46c9f8e974e9f0a7d1c47f3fc662d7c8ba32699d16799d3db98a
- research/live_control/running_action_guard_v1.py: Git blob d54047e78bc76f53ef47c6f70fd4a3be6318f09c; SHA-256 2d5feb69efd59fdca22e0db9e561923411490eb758eab9e2b8379714e20e5c62
- Container image: issue2679-map01-runtime@sha256:029e1867aeb843f2d63080343bfbb61540b64852ce00d4d99ec0be51796a093e (linux/arm64)
- Docker controls: --pull=never --platform linux/arm64 --network none --read-only; no repository checkout or files mounted.

The probe program was supplied on stdin; no source or result file was written in the container. The output above is the retained stdout summary. No model, GPU, GUI/game, or task input was used.
