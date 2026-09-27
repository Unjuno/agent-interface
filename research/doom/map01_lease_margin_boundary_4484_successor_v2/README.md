# Issue #5054 — nested frozen-sender boundary experiment

Successor to #5052 attempt 01, whose AST top-level lookup STOPped before any cases. This version walks the full AST and requires exactly one `_LeaseClockStdin` class, then compiles that unchanged node.

The test simulates three positive-duration clock probes totaling exactly 250,000,000 ns. It exercises host deadlines of 5.000s, 5.249s, 5.250s and 6.000s plus a >1s uncertainty control. No real socket, game, model, or OS input is involved.

Pinned source: Git blob `096adf9b60eaf6a31fe92c836f57d1a4d26b177e`; SHA-256 `edd4cea89c541d42457e8c48992d3efe1bcb0ab7610489b47e8efa60660aab3a`. Docker Desktop context is `desktop-linux`, Engine 28.5.1 Linux/amd64, local image ID `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`, network disabled, root/source read-only, output-only writable, 1 CPU / 512 MiB / 32 pids.

Reproduce the one-shot construction with Docker Desktop and the local image:
```powershell
docker --context desktop-linux run --rm --pull=never --platform linux/amd64 --network none --read-only --cpus=1 --memory=512m --pids-limit=32 --tmpfs /tmp:rw,nosuid,nodev,size=32m -e IMAGE_ID=sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9 -v "${PWD}/work/issue-5052-lease-margin-boundary-v2-20260928:/src:ro" -v "${PWD}/work/issue-5052-lease-margin-boundary-v2-20260928/out:/out:rw" -w /src python:3.12-slim sh /src/run.sh
```

Attempt 01's exact source-location STOP is retained separately in `attempt-01/STOP.json`. This v2 run is separate, additive evidence and does not change #4484 or authorize a future live MAP01 run.
