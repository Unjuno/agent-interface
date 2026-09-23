# Local Docker contract reproduction

This is a model-free, GUI-free reproduction of the adapter contract gate. It does not allocate the V5 model/control study and does not grant live authority.

From the repository root, run the following with Docker Desktop:

```powershell
$docker = "C:\Program Files\Docker\Docker\resources\bin\docker.exe"
$repo = (Resolve-Path .).Path
$dockerConfig = (Resolve-Path work\docker-config).Path
$env:DOCKER_CONFIG = $dockerConfig
& $docker run --rm -v "${repo}:/repo" -w /repo python:3.12-slim bash -lc "python -m pip install --disable-pip-version-check -q pytest && python -m pytest research/integration/golden_v3_cli_adapter_2203_v2 -q"
```

Expected result for the pinned contract suite is `8 passed`. The container is ephemeral; pytest is installed only inside it. Record the exact main SHA, image, test output, and any setup stop in the successor issue/PR discussion. Do not interpret this gate as evidence of model usage, GUI correctness, task success, token efficiency, or cross-domain transfer.

The Docker mount must point at the checkout being tested. A missing pytest package is a setup stop, not a contract failure. A successful contract run remains separate from the V5 retained audit and from any future live allocation.
