# Reproduction commands

The C source bundle is pinned in `REPORT.md`. Build the two static Linux
binaries under WSL2 (the repository path below is the local sparse checkout):

```sh
gcc -O2 -std=c11 -Wall -Wextra -Wpedantic -static \
  research/procedural_operations_world_v0/test_ops_world.c \
  research/procedural_operations_world_v0/ops_world.c -lm \
  -o work/opsworld-container-20260929/test_ops_world

gcc -O2 -std=c11 -Wall -Wextra -Wpedantic -static \
  research/procedural_operations_world_v0/evidence/presentation-diversity-diagnostic-20260929/variation_audit.c \
  research/procedural_operations_world_v0/ops_world.c -lm \
  -o work/opsworld-container-20260929/variation_audit
```

The single container invocation used a read-only executable bind mount and
disposable tmpfs; the host source was not mounted:

```sh
docker run --pull=never --platform linux/amd64 --rm --network none --read-only \
  --cpus=1 --memory=512m --pids-limit=32 \
  --security-opt=no-new-privileges --cap-drop=ALL \
  --tmpfs /tmp:rw,nosuid,nodev,noexec,size=64m \
  --mount type=bind,source=<local-work-dir>,target=/work,readonly \
  --entrypoint /bin/sh \
  debian:bookworm-slim@sha256:3783cc01769c7b2b1b83a5c5ad96c815348e28ed7da68e2e3687004faa906251 \
  -lc "/work/test_ops_world && /work/variation_audit"
```
