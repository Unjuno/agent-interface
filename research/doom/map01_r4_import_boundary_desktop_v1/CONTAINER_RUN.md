# Docker Desktop runbook — Issue #3903

The formal output root is `research/doom/map01_r4_import_boundary_desktop_v1/results/formal-01`. It must be newly created and empty immediately before the only formal invocation. The pinned input-source snapshot is `8652f6a3527d55610185d1103b87d5d9fd8fa985`; those two source blobs are unchanged at branch parent `55427ecda1474b43d8a58bbc5714de7285cc8390`. Source file and audit-code hashes are frozen in the Issue #3903 comment before execution.

Before freeze, run the construction-only classifier controls into separate fresh `results/construction-NN/` mounts using the same network/read-only/resource restrictions and the command below. Each writes `CONSTRUCTION.json`; these are not formal allocations. Supply all six `EXPECTED_*` source hashes from the working tree. Preserve each STOP; never reuse an output directory.

```powershell
docker run --rm --pull=never --network none --read-only `
  --tmpfs /tmp:rw,nosuid,nodev,size=64m --cpus 1 --memory 768m `
  --pids-limit 128 --cap-drop ALL --security-opt no-new-privileges `
  --mount "type=bind,source=<repo-root>,target=/source,readonly" `
  --mount "type=bind,source=<construction-output>,target=/out" `
  --workdir /source --env PYTHONDONTWRITEBYTECODE=1 --env OUT=/out `
  --env EXPECTED_MAIN=8652f6a3527d55610185d1103b87d5d9fd8fa985 `
  --env IMAGE_ID=sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9 `
  --env EXPECTED_TARGET=<sha256> --env EXPECTED_GATE=<sha256> `
  --env EXPECTED_ANALYZER=<sha256> --env EXPECTED_FORMAL=<sha256> `
  --env EXPECTED_VERIFIER=<sha256> --env EXPECTED_CONSTRUCTION=<sha256> `
  --entrypoint python sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9 `
  /source/research/doom/map01_r4_import_boundary_desktop_v1/construction.py
```

The exact formal container command, after replacing each `EXPECTED_*` placeholder with its frozen lowercase SHA-256, is:

```powershell
docker run --rm --pull=never --network none --read-only `
  --tmpfs /tmp:rw,nosuid,nodev,size=64m `
  --cpus 1 --memory 768m --pids-limit 128 --cap-drop ALL `
  --security-opt no-new-privileges `
  --mount "type=bind,source=<repo-root>,target=/source,readonly" `
  --mount "type=bind,source=<repo-root>\research\doom\map01_r4_import_boundary_desktop_v1\results\formal-01,target=/out" `
  --workdir /source --env PYTHONDONTWRITEBYTECODE=1 --env OUT=/out `
  --env EXPECTED_MAIN=8652f6a3527d55610185d1103b87d5d9fd8fa985 `
  --env IMAGE_ID=sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9 `
  --env EXPECTED_TARGET=<frozen-sha256> --env EXPECTED_GATE=<frozen-sha256> `
  --env EXPECTED_ANALYZER=<frozen-sha256> --env EXPECTED_FORMAL=<frozen-sha256> `
  --env EXPECTED_VERIFIER=<frozen-sha256> --env EXPECTED_CONSTRUCTION=<frozen-sha256> `
  --entrypoint python sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9 `
  /source/research/doom/map01_r4_import_boundary_desktop_v1/formal.py
```

Two preparatory commands on the collided predecessor branch stopped before target import (invalid entrypoint; malformed inline quoting). Their records are disclosed in [PLAN.md](PLAN.md). The Docker Desktop successor's own construction check is recorded separately at `results/construction-01/` and is not a formal row.

Formal writes `formal_result.json`, `independent_audit.json`, verifier stdout/stderr, and `RESULT.json` to `/out`. Do not rerun if the command fails or the output is partial; preserve it and classify the observed STOP/FAIL.
