# #3311 OrbStack image-store recheck — 2026-10-05

Status: `STOP_IMAGE_STORE_BLOB_UNAVAILABLE_AFTER_HOST_CAPACITY_RECOVERY`.
This is an exploratory read-only follow-up, not a preregistered allocation.

## H/T/D/C/U

- **H:** If the earlier image-store failure was caused only by exhausted host disk space, the already-cached pinned image may become inspectable after host capacity recovers.
- **T:** On 2026-10-05, `df -h <workspace-root>` showed 641 GiB available. Using the explicit `orbstack` Docker context, inspect the previously frozen Linux/arm64 image ID `sha256:e47cbddc70722a816758a4a1c27cf2a38071c889670be98bf3eacdc9fff17916` once. No pull, build, container start, image mutation, CLI call, model request, GUI or input.
- **D:** PASS only if the daemon returns that exact image ID and Linux/arm64 platform; otherwise stop and retain the result.
- **C:** The exact inspect still fails with `operation not supported` while opening the matching containerd content blob. The same command using the same daemon/client had failed earlier. These observations do not identify whether the root cause is a blob, backing store or daemon defect.
- **U:** The pinned image remains unavailable for the one-shot #3489 preflight. Running VM ownership and a maintenance window remain unconfirmed. Do not repair, prune, restart or reset the shared store without its owners and a scoped recovery plan.

This is a read-only environment recheck, not the frozen #3489 allocation and not a container experiment. No formal allocation or task-effect result is claimed.

## Runtime version context — 2026-10-05

After the failed image inspect, the local `orbctl version` command reported OrbStack `2.1.3` (commit `7a3258b7336a8a47b75771e87ef7b74ba4bba8eb`); its output is preserved in `orbctl-version.txt`. The [official release notes](https://docs.orbstack.dev/release-notes) list `2.2.3` dated 2026-08-07 and state that `2.2.2` added general protection against data corruption with automatic recovery. They do not identify this specific containerd blob error or establish that an update would fix it. This is a possible diagnostic lead only. No update or VM operation was attempted because the owners and maintenance window for currently running machines are not confirmed.
