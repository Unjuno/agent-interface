# formal05 STOP — sealed host plan readiness was misdetected

Allocation: `5260-a15-model-paired-formal05-20261004`

Preflight validated the frozen 137-source plan and exact WSLc/model/container
command. The trusted host launch began and successfully published its sealed
plan at `host/host-plan/`. That record is a directory containing `payload.bin`
and `ready.json`; the new launcher incorrectly waited for `host/host-plan` to
be a regular file. It consequently classified a ready host as not ready and
terminated the host after the finite readiness deadline.

No candidate WSLc process, private GUI, exchange request, or provider call was
started. `host-launch/attempt.json`, `stdout.bin`, `stderr.bin`, and
`receipt.json` preserve the exact attempt, wrapper stop, streams and hashes.
The plan, host-plan, outer-plan and source capsule are retained unchanged. This
allocation is stopped and is not retried.

The successor launcher must verify the sealed host-plan marker and exact
payload bytes/hash before starting the candidate. It must treat missing,
malformed or mismatched seals as a pre-candidate STOP.
