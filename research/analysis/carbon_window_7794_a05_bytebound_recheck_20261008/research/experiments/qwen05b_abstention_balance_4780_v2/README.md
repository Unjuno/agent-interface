# Issue #5014 — balanced safety-class support, fresh successor

This additive research branch continues #4988 after its terminal pre-fit runner/schema STOP. It uses fresh seeds 73194101 and 73194109 and regenerates every input row. The prior STOP and all predecessor artifacts remain unchanged.

The protocol and H/T/D/C/U are frozen in `FREEZE.json` and `PREREGISTRATION.md`. Before GPU execution, pinned-image tests and CPU preflight-only validation must pass, GitHub-readback hashes must match, and the host RTX 3080 must be freshly observed idle. The exact one-run command has no retry.

The model, inputs and code use read-only mounts in an offline, resource-bounded Docker container. Outputs will be independently audited on CPU before a result is reported.