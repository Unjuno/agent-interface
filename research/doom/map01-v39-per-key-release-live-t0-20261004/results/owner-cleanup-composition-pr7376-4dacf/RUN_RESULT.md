# Recorded construction composition result

Allocation `V39-CLEANUP-COMPOSITION-C01-20261004-01` completed one candidate invocation and one independent auditor invocation.

- Candidate: exit 0; `audit.json` gate `PASS_CONSTRUCTION_OWNER_CLEANUP_FAIL_CLOSED`.
- The audit verified a single admission and release receipt, cancellation snapshot before owner cleanup, correlated verified cancellation cleanup, fail-closed publication, one press/release pair, no key left down, and rejection of a mutation that marks the transition verified.
- Backend tests: 14/14 passed. Frozen live-allocation raw-auditor tests: 5/5 passed. Probe and auditor byte-compile successfully.
- A test-double setup failure before the recorded run is preserved in `setup-attempt-01.txt`.

This is a construction composition control using fake Xlib/XTest and a stub base hold sequence. It is not live X11, physical key-state, application-consumption, task-effect, latency, or safety evidence. The separate live allocation remains STOP and was not retried.

## Integrity

- `FREEZE.json`: `5673fdfd13e7a328375d7e2a5b027e2e2f5f880c81f53b2ffd7f6e19556c6c69`
- `candidate.raw.json`: `6d0742bc740dee53a61c03c53eb39b7a01aa4f82f1b3ae74b04790be1ba52d90`
- `audit.json`: `c1c25e1ecd7bd8e0162f0a02eba8b0d16464650fe0e3d43399f4493c58de3cae`
