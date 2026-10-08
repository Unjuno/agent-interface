# Issue #5036 formal result — consumed allocation

## Disposition

**HOLD_EVIDENCE_INCOMPLETE** (harness timeout case did not establish that the fake child started). The formal wrapper has one retained execution record; its runner exited 0 and its raw auditor exited 1 with exactly one baseline error, `timeout_child`. This is not a scientific PASS or FAIL. Allocation `broker-fake-child-boundary-4485-20260928-02` is consumed. Do not retry it.

## Frozen identity and integrity

- Broker Git blob: `5734f54f318db9ac5e96b2bed6f6bed105ac39ff`, equal to current main at readback.
- Docker image: `sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e`.
- Execution record contains that image ID and all five expected mounted-source SHA-256 values.
- Runner raw SHA-256: `e7634845bd20e963c5ac8326edf0aee8bfbe285681d7f61a9701c79ec41fa397`.
- Manifest lists 51 payload files. An independent local read-only verification found 51/51 listed files present with matching SHA-256 and byte counts, zero mismatches. The retained output directory contains those 51 files plus `manifest.json`.

## Observations

- `exit-0`: broker exit 0; one fake-child call; receipt return code 0.
- `exit-23`: broker exit 23; one fake-child call; receipt return code 23.
- `timeout`: broker emitted `TimeoutExpired` / `HOST_BROKER_SUBPROCESS_TIMEOUT` and an empty response, but the child call log is empty. The registered broker timeout is 0.1 seconds; the fake child did not record its start before that deadline. Thus this did not test a running fake child's timeout behavior.
- `missing-executable`: typed `FileNotFoundError` / `HOST_BROKER_EXECUTABLE_UNAVAILABLE`; no fake-child invocation.
- `malformed-json`: rejected without fake-child invocation.
- `idle-once`: externally timed out, with no IPC receipt/response.
- `sorted-once`: lexical-first request `a` was handled; `z` was left untouched.
- All authority fields remain false. All 8/8 copied-evidence corruption controls were rejected.

Because the timeout child never started, the seven-case acceptance gate is incomplete. Preserve the raw disposition; do not relabel the audit error as a broker semantic failure.

## Invocation provenance limitation

The retained `execution.json` binds the image and source hashes, and `FREEZE.json` contains the preregistered command template. The output bundle does **not** include a host-side launch receipt with the exact realized `docker run` command and concrete mount paths. Therefore the exact executed resource/mount flags cannot be independently recovered from this bundle alone. Keep the result at HOLD pending a genuinely fresh successor; no retry or pooling with this allocation.

The original #5013 STOP and PR #5034 remain unchanged. No broker/runtime source was modified.
