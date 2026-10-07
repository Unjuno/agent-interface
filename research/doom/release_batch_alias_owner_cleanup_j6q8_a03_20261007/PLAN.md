# A03 protocol

- **H:** A candidate-only duplicate-keycode guard rejects `up_batch(["a", "A"])` through actual V4→V3→V12 composition without releasing the held key; a subsequent real V4 owner close yields verified empty cleanup.
- **T:** One isolated Xvfb run, one admitted `a`, one guarded alias batch, one close, then event/keymap/receipt/thread/server checks.
- **D:** PASS only for refusal-with-key-retained followed by matching KeyRelease, neutral map, verified empty close receipt, stopped owner thread and zero Xvfb exit. Contradiction after completion is FAIL; setup/incomplete evidence is STOP. One invocation only.
- **C:** This tests explicit owner-close cleanup; it does not prove every V15/V39 caller reaches close after an exception.
- **U:** One synthetic Xvfb case only; no physical input, app/game, task effect, latency/recovery, live threat exposure, or MAP01 result.

A01's runner/output mismatch STOP and A02's pre-keypress owner-reference STOP are kept as separate predecessor evidence. No production source is changed.
