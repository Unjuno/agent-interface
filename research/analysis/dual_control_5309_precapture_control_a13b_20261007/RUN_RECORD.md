# A13B one-shot execution record

- Allocation: `5309-PRECAPTURE-CONTROL-A13B-20261007`
- Freeze commit: `9f3ab7bb92ddc026330677a1cb71844883c62c5b`
- Frozen main: `9fb2dd6782d1d1477a00d14be870487fd4c54fa2`
- Image: `node:26-alpine@sha256:0b36e8c136b94cd4fcf02188228e76c31ad5872eef3fec8cbd2eee500cfd9e80`
- Container platform/version: linux/arm64, Node v26.10.0.
- Network: none. Root filesystem: read-only; `/tmp` tmpfs 32 MiB, noexec/nosuid; 1 CPU, 256 MiB memory, 64 PIDs; all capabilities dropped; no-new-privileges. Containers used `--rm` and stage-specific mounts from `RUN_PROTOCOL.md`.

## Preflight (not a formal stage)

One container mount smoke returned exit 0 and stdout `v26.10.0 2319 oracle=absent`. It read `candidate_stage/cases.json`, verified `/candidate/oracle.json` absent, wrote and removed a temporary mount marker. This did not execute candidate source. The preflight container was auto-removed.

## Formal stages

Each command is listed literally in `RUN_PROTOCOL.md`; each was invoked exactly once. All returned exit status 0 with empty stdout and stderr as exposed by the command runner. No retries occurred.

| Stage | Invocations | Exit | Retained output | SHA-256 |
|---|---:|---:|---|---|
| Candidate | 1 | 0 | `out/candidate/choices.json` | `cca5ba584f791ea64c6431b7e48d3b8a8eb4f669faa8f28c4de18142fdc49544` |
| Environment | 1 | 0 | `out/environment/events.json` | `2461ed036db799771f771bdd9d81d99007e45f07c73eaacaeee8189f88af275b` |
| Auditor | 1 | 0 | `out/audit/audit.json` | `aef8708581abf580897ebda49be1d981cc6f218effd2fbdd5e73008fc93cbbd0` |

Auditor disposition: `PASS_PRECAPTURE_CONTROL_SCOPED`; rows 12; errors 0; authority grants 0; sole-witness completions TASK_ONLY 1/2, WITNESS_AWARE 2/2. All three stage-specific post-run container-label queries returned no remaining containers. Source, inputs, report, index, and outputs are covered by their respective checksum manifests.
