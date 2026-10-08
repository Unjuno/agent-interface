# Runbook — Issue #6505 audit-only A01

Run the host-only construction tests before the formal audit. Before formal launch, verify the current branch/base, all frozen Git blob identities, source SHA-256, and that the exact output path does not exist or is empty. Do not start any container if a gate fails.

From the repository root, with OrbStack context and the cached image already present:

```sh
mkdir -p research/analysis/partial_order_audit_6505_orbstack_a01_20261003/results/formal_01
docker create --pull=never --name issue6505-audit-orbstack-a01-20261003 \
  --network none --cpus=1 --memory=512m --pids-limit=64 --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=32m \
  --cap-drop ALL --security-opt no-new-privileges --user 1000:1000 \
  --mount type=bind,source="$PWD",target=/repo,readonly \
  --mount type=bind,source="$PWD/research/analysis/partial_order_audit_6505_orbstack_a01_20261003/results/formal_01",target=/evidence \
  --workdir /repo \
  --env SOURCE_ROOT=/repo --env EVIDENCE_ROOT=/evidence \
  python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9 \
  python -S -B /repo/research/analysis/partial_order_audit_6505_orbstack_a01_20261003/auditor.py
docker inspect issue6505-audit-orbstack-a01-20261003
docker start --attach issue6505-audit-orbstack-a01-20261003
```

Capture stdout and exit status verbatim into the mounted `results/formal_01/` directory. Inspect once after exit and preserve container ID, configuration, exit state, and runtime warnings. The container runs the new auditor only; it does not run `runner.py` or the predecessor `audit.py`. No retry is permitted, even for an infrastructure or auditor error.

After outputs are copied and all hashes are verified, remove only this exact stopped container by its frozen name; do not prune or alter any other container. If removal is not permitted or a required process is still using it, retain it and record why.
