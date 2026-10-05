# A01 result

Run 01 disposition: `STOP_PRECONDITION`. Before candidate code loaded, the runner resolved the repository root as `/private/tmp` rather than the checkout root; no candidate output was created. The attempt is not retried under its original run ID.

Run 02 disposition: `STOP_PRECONDITION`. The runner attempted to call nonexistent `load` on the harness module before candidate code was loaded. No candidate output was created; the path is not reused.

Run 03 disposition: `STOP_PRECONDITION`. The runner looked for the fixture class on the test module rather than the returned fixture module. Candidate code was not executed and no output was created.

Run 04 disposition: `PASS_EXECUTOR_V12_COMPOSITION_SCOPED`. The single completed candidate run produced 7 events: accepted, step_started, input_admission, cancel_requested, input_release_measurement, input_released, terminal. The per-key receipt is confirmed physical-up with retired actuation identity; aggregate release is verified empty; both receipts precede the cancelled terminal. Fake physical keys and backend held keys are empty. Independent audit passed.

The exact run is in `results/formal_04/candidate.json`; auditor output is `results/formal_04/audit.json`. SHA-256 values and test commands are retained in `SHA256SUMS.txt` and `COMMANDS.txt`.

Scope is fake-display software composition only. See `PROTOCOL.md`; no live input/game or Issue #59 exit claim follows.
