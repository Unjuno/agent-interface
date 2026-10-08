# Formal guest commands (run only after exact #5085 assignment)

This is an execution aid. It grants no resource authority. Never point these commands at the shared `orbstack` or `default` Docker context.

Current state (2026-10-01): #5704 requested 04:40–05:10 UTC after #5681's early release, but the latest queue readback contains no explicit grant. Do not execute guest creation or either container command until a named allocation is confirmed and the full fresh start gate passes. Candidate/auditor counts remain 0/0.

## Guest creation and daemon

```sh
orbctl create --isolated --isolate-network --cpus 1 --memory 2G --disk 16G ubuntu:24.04 selfstab-t0-5704-20261001
orbctl run -m selfstab-t0-5704-20261001 -u root apt-get update
orbctl run -m selfstab-t0-5704-20261001 -u root apt-get install -y docker.io
orbctl run -m selfstab-t0-5704-20261001 -u root systemctl enable --now docker
```

Stop before candidate if setup fails or does not fit the awarded slot. Verify only the named guest and its own Docker endpoint. Pull and inspect the exact pinned arm64 image; verify a unique empty output directory and all frozen source hashes before proceeding.

## Candidate and independent audit containers

Candidate command inside the guest (with `/tmp/5704-src` frozen read-only and `/tmp/5704-formal01` newly created and writable by UID 1000):

```sh
docker run --rm --cidfile /tmp/5704-formal01/candidate.cid --platform linux/arm64/v8 --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=32m --cpus 1 --memory 512m --pids-limit 64 --user 1000:1000 --mount type=bind,src=/tmp/5704-src,dst=/src,readonly --mount type=bind,src=/tmp/5704-formal01,dst=/out --workdir /src docker.io/library/python:3.12-slim-bookworm@sha256:eb5be8e5b4d0a159c237946bbdd06356dda5d19c30fc4f7843e8046d3a590333 python -B /src/model.py --output /out/candidate.jsonl
```

Only if that exact invocation exits 0, create separate read-only input `/tmp/5704-audit-input/candidate.jsonl` from the newly emitted file and writable `/tmp/5704-audit-output`. Then run:

```sh
docker run --rm --cidfile /tmp/5704-audit-output/auditor.cid --platform linux/arm64/v8 --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=32m --cpus 1 --memory 512m --pids-limit 64 --user 1000:1000 --mount type=bind,src=/tmp/5704-src,dst=/src,readonly --mount type=bind,src=/tmp/5704-audit-input,dst=/in,readonly --mount type=bind,src=/tmp/5704-audit-output,dst=/out --workdir /src docker.io/library/python:3.12-slim-bookworm@sha256:eb5be8e5b4d0a159c237946bbdd06356dda5d19c30fc4f7843e8046d3a590333 python -B /src/audit.py /in/candidate.jsonl --out /out/audit.json
```

Capture each exact command, stdout, stderr, exit code, cidfile, Docker server/image identity and UTC start/end. Pull only these task-owned output files back to the host. Do not retry either invocation.
