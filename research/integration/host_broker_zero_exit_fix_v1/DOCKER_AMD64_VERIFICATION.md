# Local Docker linux/amd64 verification — Issue #4520

Disposition: `PASS_LOCAL_DOCKER_AMD64_CONTRACT_TESTS_SCOPED` for PR head `71adf863725b1ad4d8a33e0298b07bb85e2a10f4`.

This is exact-head contract-test verification for the zero-exit fix; it is not a model, provider, GUI, or scientific performance experiment.

## Environment

- Docker Engine `29.8.0`, server architecture `x86_64`, OS `linux`.
- Locally cached image `agent-interface-golden-ipc-2705:20260920-wmctrl`, immutable ID `sha256:7e4a3b6f3917baa9f153b4dfd011a4ea528a3d200a7a3d274aa9479900ee7b41`, `linux/amd64`.
- Python `3.11.16`; `jsonschema 4.26.0`.
- `--pull=never --network none --read-only`; bounded `/tmp` and `/dev/shm` tmpfs; exact PR checkout mounted read-only. No dependencies installed and no GitHub Actions result used.

The cached `python:3.12-slim-bookworm` image was also checked locally (`linux/amd64`, image ID `sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e`) but does not contain `jsonschema`. Network-disabled policy precluded installing it. Therefore this run verifies the amd64 container/runtime contract under Python 3.11.16; the separately recorded host run covers Python 3.12.10. It does not claim their environments are identical.

## Exact command

```powershell
$repo=(Get-Location).Path
docker run --rm --pull=never --network none --read-only `
  --tmpfs /tmp:rw,nosuid,nodev,size=256m `
  --tmpfs /dev/shm:rw,nosuid,nodev,size=64m `
  --mount "type=bind,source=$repo,target=/repo,readonly" --workdir /repo `
  --entrypoint python3 agent-interface-golden-ipc-2705:20260920-wmctrl `
  -m unittest -v runtime.test_docker_host_model_bridge_v1 `
    runtime.test_host_model_ipc_broker_v1 runtime.test_docker_schema_preflight_v1
```

## Result

Exit `0`; **28/28 passed** in `0.194s`:

- host model bridge: 2/2
- one-shot IPC broker: 8/8, including child exit 0, exit 23, timeout, and unavailable executable
- Docker schema preflight: 18/18

The regression suite proves the targeted mapping and its adjacent deterministic contracts on linux/amd64. The prior Python 3.12.10 host result remains separately scoped (28/28); the ARM64 Docker verification is separately retained under `research/integration/issue_4520_docker_arm64_verification_v1/`. No result here resolves unrelated historical-object failures in the GitHub Actions run, and no production, live-model, or GUI claim follows.
