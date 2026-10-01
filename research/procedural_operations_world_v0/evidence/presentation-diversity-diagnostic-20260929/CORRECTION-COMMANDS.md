# Corrected reproduction commands

From the repository root under WSL2:

```sh
mkdir -p work/opsworld-container-corrected-20260929
gcc -O2 -std=c11 -Wall -Wextra -Wpedantic -static \
  research/procedural_operations_world_v0/test_ops_world.c \
  research/procedural_operations_world_v0/ops_world.c -lm \
  -o work/opsworld-container-corrected-20260929/test_ops_world
gcc -O2 -std=c11 -Wall -Wextra -Wpedantic -static \
  research/procedural_operations_world_v0/evidence/presentation-diversity-diagnostic-20260929/variation_audit_corrected.c \
  research/procedural_operations_world_v0/ops_world.c -lm \
  -o work/opsworld-container-corrected-20260929/variation_audit_corrected
```

From Windows PowerShell, using Docker Desktop's `desktop-linux` context:

```powershell
docker run --pull=never --platform linux/amd64 --rm --network none --read-only `
  --cpus=1 --memory=512m --pids-limit=32 `
  --security-opt=no-new-privileges --cap-drop=ALL `
  --tmpfs /tmp:rw,nosuid,nodev,noexec,size=64m `
  --mount type=bind,source=C:/Users/junny/Documents/Codex/2026-09-19/goal-unjuno-agent-interface-github-mcp-2/scratch/opsworld-sparse-clone/work/opsworld-container-corrected-20260929,target=/work,readonly `
  --entrypoint /bin/sh `
  debian:bookworm-slim@sha256:3783cc01769c7b2b1b83a5c5ad96c815348e28ed7da68e2e3687004faa906251 `
  -lc "/work/test_ops_world && /work/variation_audit_corrected"
```

Observed stdout and exit code are retained in `CORRECTION-20260929.md` and
`RESULT-corrected.json`. The experiment container was automatically removed.
