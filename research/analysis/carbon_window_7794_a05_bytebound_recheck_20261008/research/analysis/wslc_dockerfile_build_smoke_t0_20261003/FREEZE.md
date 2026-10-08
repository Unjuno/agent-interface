# T0 preregistration — Dockerfile build/run with WSLc

## H / T / D / C / U

- **H:** WSL Containers 3.0.1.0 can build and run this minimal single-container Dockerfile workflow from a local cached base image without Docker Desktop or a Docker executable.
- **T:** Freeze these exact context files and the cached base identity below. Execute exactly one `wslc.exe build` and, only if it succeeds, exactly one `wslc.exe run`. The Dockerfile uses only `FROM`, `WORKDIR`, `COPY`, and `ENTRYPOINT`; it has no `RUN` instruction or third-party dependency. Do not invoke Docker. Candidate/build invocations=1 maximum; run invocations=1 maximum; retries=0. No GPU, GUI, model, or network-dependent build step.
- **D:** `PASS_WSLc_DOCKERFILE_BUILD_RUN_SMOKE` only if the single build exits 0, WSLc lists the uniquely tagged image, the single `--network none` run exits 0 and prints the expected schema/status plus exact payload SHA-256, and `wslc container list --all` has no container with this unique name afterward. Any build/run error, output mismatch, or surviving named container is the first STOP/FAIL; no retry. This is a scoped capability result, not a migration-benefit result.
- **C:** The base image is the already-cached `python:3.12-slim`, local ID `sha256:9e87977b867847e186d066f531ef783b006d582a985c341c269446088d90f2c4`, pinned repository digest `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f` (linux/amd64). The build context is fixed by SHA-256. Docker executable resolution failed before freeze. The build CLI does not expose a `--network none` option; therefore record its output and make no claim about builder-level network isolation. No `RUN` layer is present, and the pinned base is locally cached.
- **U:** One minimal Dockerfile is not a representative Docker compatibility suite. This cannot establish Compose/Engine API, `--read-only`, capability/PID isolation, Windows-path semantics for a real application, Docker replacement, effective memory/swap enforcement, lower peak memory, faster iteration, or hosted-CI suitability. `--memory 512M` on the one-shot `run` is not evidence that the host enforces that cap.

## Frozen source and runtime identity

| File | Bytes | SHA-256 |
|---|---:|---|
| `Dockerfile` | 336 | `ec8ab4d198d4a6cfc163e9cbd4098c7d68b86f0fa14f870fa5d8addee310352d` |
| `payload.txt` | 36 | `3280e32e693397e74af56b9f9f0dd473dd663224a3c62883b33cbc8828d7c383` |
| `probe.py` | 819 | `78a615ffacc99f453c7f81995db92d962ec0ec60069ebc3415d0a89ddcc20893` |

Pre-freeze construction check compiled `probe.py` in memory, validated the exact payload and digest-pinned base line, and confirmed there is no `RUN`/`ADD`; it passed. One preliminary ad-hoc checker invocation failed before freeze because its own path-join repeated the test-directory prefix, producing `FileNotFoundError`; no source file or runtime was touched. The corrected checker passed and reported the hashes above.

The build context and result path are separate: local working directory is this directory; final output records will be created only after the one-shot run. WSLc inventory before registration listed the cached base image and no matching smoke tag/container. No image has yet been built for this T0.

## Frozen commands and unique identities

Image tag: `agent-interface/wslc-build-smoke:20261003t0`  
Container name: `agent-interface-wslc-build-smoke-t0-20261003`

```powershell
wslc.exe build --progress plain --file Dockerfile --tag agent-interface/wslc-build-smoke:20261003t0 .
wslc.exe run --rm --pull never --network none --cpus 1 --memory 512M --name agent-interface-wslc-build-smoke-t0-20261003 agent-interface/wslc-build-smoke:20261003t0
```

The second command is conditional on build exit 0. Following the run, inspect `wslc.exe images` and `wslc.exe container list --all` for the exact image tag and exact container name. No image cleanup is pre-authorized in this allocation; retain the uniquely tagged, small build result until its outcome and evidence package are reconciled.
