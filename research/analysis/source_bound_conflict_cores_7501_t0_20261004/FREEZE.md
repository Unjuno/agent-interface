# T0 freeze — Issue #7501

Freeze status: prospective, before formal candidate/auditor invocations.

- Repository: `Unjuno/agent-interface`
- Base: `main` at `fe5a9dddf11f0351eb65001f1a1ddb867e8a5012` (observed 2026-10-04 after #7599 integration; exact tree in detached local worktree)
- Issue: [#7501](https://github.com/Unjuno/agent-interface/issues/7501)
- Unique package: `research/analysis/source_bound_conflict_cores_7501_t0_20261004/`
- Image: `node:26-alpine`, immutable image ID `sha256:0b36e8c136b94cd4fcf02188228e76c31ad5872eef3fec8cbd2eee500cfd9e80`, `linux/arm64`
- Runtime: Node v26.10.0 (must be confirmed in the candidate/audit output)
- Container: OrbStack Docker Engine 29.4.0; network disabled; read-only root filesystem; one CPU; memory 512 MiB; memory+swap 512 MiB (zero swap); PID limit 16; process UID/GID equals host caller; only this package bind mount is writable.
- Candidate invocation cap: one. Auditor invocation cap: one. Retry cap: zero.
- Unique container names: `ai7501-conflict-candidate-a01-20261004` and `ai7501-conflict-auditor-a01-20261004`; retain stopped containers until actual engine limits and exit states are recorded, then remove only these exact stopped IDs after durable logs/output verification.
- No models, GUI, participants, external actions, or production runtime code.

## Frozen source digests

SHA-256 values below are recorded before execution and must be checked on the host immediately before and after both invocations. The candidate/auditor stdout also records their actual Node version, architecture, and UID. Docker inspection after each run supplies the actual engine resource configuration.

- `fixtures.json`: `3d61a39738d73a428f0c3598f4c7756a6a4e48d106814b3d3d93d0f9df869173`
- `candidate.mjs`: `41477bada35f082fae4de6f9d087404cc5f9fc5f523de8e98b65cfa458420c34`
- `audit.mjs`: `ef2c626588d0f1d13fd43b31977330615318e82a9dcd102b87599e96d611bd23`
- `README.md`: `25b35b7ffc4091df7f4472437635b57df24e234b9dae7c9cd02c4fd984cccd57`
- Base commit: `fe5a9dddf11f0351eb65001f1a1ddb867e8a5012`

No source or fixture edits are permitted after replacing the pending digest lines. Any needed repair becomes a separately identified successor; it cannot consume either one-shot invocation.

## Commands

Candidate (exactly once; expected process exit 0, disposition determined by the auditor):

```sh
docker run --name ai7501-conflict-candidate-a01-20261004 --pull=never --network=none --read-only --cpus=1 --memory=536870912 --memory-swap=536870912 --pids-limit=16 --user "$(id -u):$(id -g)" -v "$PWD/research/analysis/source_bound_conflict_cores_7501_t0_20261004:/evidence:rw" --entrypoint node sha256:0b36e8c136b94cd4fcf02188228e76c31ad5872eef3fec8cbd2eee500cfd9e80 /evidence/candidate.mjs /evidence/fixtures.json /evidence/formal_01/candidate.json /evidence/formal_01/candidate.stdout.json
```

Independent auditor (exactly once; expected exit 0 only when base oracle comparison and all mutation controls pass):

```sh
docker run --name ai7501-conflict-auditor-a01-20261004 --pull=never --network=none --read-only --cpus=1 --memory=536870912 --memory-swap=536870912 --pids-limit=16 --user "$(id -u):$(id -g)" -v "$PWD/research/analysis/source_bound_conflict_cores_7501_t0_20261004:/evidence:rw" --entrypoint node sha256:0b36e8c136b94cd4fcf02188228e76c31ad5872eef3fec8cbd2eee500cfd9e80 /evidence/audit.mjs /evidence/fixtures.json /evidence/formal_01/candidate.json /evidence/formal_01/audit.json /evidence/formal_01/audit.stdout.json
```

## Stop conditions and disposition

- Stop before candidate if base SHA, source/image digest, mount path, exact inputs, or output absence do not match this freeze.
- Any candidate/auditor nonzero exit, missing output, source mutation, hash mismatch, failed mutation control, or host/container resource warning is retained as the first failure/STOP; do not retry or relabel.
- The finite experiment has no allocation slot and cannot be interpreted as #59 live game/input evidence.
- Formal candidate/auditor invocation counts must end at 1/1 or remain 0/0 with an explicit STOP.
