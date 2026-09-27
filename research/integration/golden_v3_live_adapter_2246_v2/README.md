# Golden v3 live-adapter current-main preflight v2

This additive successor preserves the failed v1 source-pin result and binds a new
preflight path to the source identities verified on current `main`.

H: The current-main golden launcher, CLI adapter, retained report, and explicit
authority gate can be checked before any disposable live allocation.

T: Run the verifier in a digest-pinned `python:3.12-slim` container. A source
mismatch is `STOP_SOURCE_IDENTITY_GAP`; absent provider/model authority is
`HOLD_NO_MODEL_AUTHORITY`. This preflight performs no model, GUI, input, or
network task call.

D/C: PASS means only that source identity and the no-authority fail-closed boundary
are machine-checked. It is not live adapter, task-effect, latency, token, or
generality evidence. A later experiment must add a disposable fixture, independent
effect scorer, held-out cases, stale/ambiguous delivery, release, and cleanup.

U: The runtime adapter's live semantic preservation remains unverified.
