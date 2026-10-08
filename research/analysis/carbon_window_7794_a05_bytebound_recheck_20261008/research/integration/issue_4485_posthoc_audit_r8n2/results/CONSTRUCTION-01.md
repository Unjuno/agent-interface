# Obstac construction 01 — `PASS_CONSTRUCTION_ONLY`

This is mount/runtime plumbing evidence only; no raw audit, broker, fake,
model, or scientific case was executed.

- OrbStack: `29.4.0`; Docker context `orbstack` at the local OrbStack socket.
- Pinned image reference:
  `python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`.
  Host inspection returned the same image ID and `linux/arm64`; its repo digest
  is `python@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`.
- Container controls: `--network none`, `--read-only`, 16 MiB noexec/nosuid
  `/tmp`, 1 CPU, 256 MiB memory and swap, 32 PIDs, all capabilities dropped,
  no-new-privileges, and `--pull=never`.
- `/repo`, `/study`, and `/audit` were read-only; `/evidence` was writable.
  The in-container write probes confirmed those mount boundaries.
- All frozen `OBSTAC_*` metadata matched the committed freeze and source
  commit/tree. Construction stdout:
  `OBSTAC_POSTHOC_CONSTRUCTION PASS source=ro study=ro audit_spec=ro evidence=rw broker=0 fake=0 model=0`.
- `CONSTRUCTION.json` SHA-256:
  `0702da68e6f832ba4471059489bf4356ec24461d66dd03d6c730061746027821`.
- The container was removed at exit. This record does not infer anything about
  the original allocation or broker contract.

The single posthoc audit invocation remains unused at this point. It will use
the same frozen image, context, resource controls, and read-only inputs with a
separate fresh writable evidence directory.
