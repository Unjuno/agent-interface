## Summary

- Preserve the #3924 H/T/D/C/U, current-main source/image freeze, construction stops, formal raw IPC/receipt/process outputs, and independent audit under `research/integration/issue_3924_orbstac_broker_contract_v1/`.
- Record allocation 02 as `STOP_FAKE_EXECUTABLE_MOUNT_MISSING`. Seven rows ran, but the required fake executable was not mounted; the audit found nine provenance/expectation errors across 41 hashed files.
- Keep the evidence scoped: the explicit unavailable-executable receipt is typed, malformed input fails closed, one-shot chose only `queued-a`, and idle required the external bound. There is no zero-exit propagation conclusion and no production-source change.

## Validation

- Construction check passed in an isolated OrbStack container with zero broker/fake invocations.
- Formal matrix ran once in a pinned, network-none OrbStack container; all raw results are retained.
- Independent raw-only audit ran in a separate isolated container and retained its HOLD/errors.
- `git diff --check` passed. Runtime source was not edited.

Does not close #3924. The result is an infrastructure/provenance STOP, not a scientific PASS/FAIL.
