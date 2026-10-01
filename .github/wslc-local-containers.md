# Local container-backed research with WSL Containers

## Status

WSL Containers (`wslc`) is the preferred **pilot runtime for eligible local, single-container research iterations on this Windows host**. It can avoid starting Docker Desktop for those runs and provides resource limits and disposable containers. This is a scoped migration, not a claim that every Docker workflow is interchangeable.

Pilot verified on 2026-10-02 with WSL `3.0.1.0`, WSLc `3.0.1`, and `python:3.12-slim` (`python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, linux/amd64):

- A Python smoke command completed with `--network none`, `--memory 512M`, `--cpus 1`, and `--pull never`.
- A Windows-host file bind-mounted with `:ro` was readable; an attempted write failed with `EROFS`.
- Both containers were run with `--rm`; `wslc container list --all` showed no residual containers afterward.
- WSL emitted `kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.` The memory cap was accepted, but swap isolation was not available in this environment. This pilot is **not** a measured Docker-vs-WSLc performance or peak-memory comparison.

Existing WSLc research evidence is also recorded in [PR #6114](https://github.com/Unjuno/agent-interface/pull/6114): a read-only, network-disabled Python replay ran two tests successfully. That evidence does not establish complete Docker flag parity, GUI performance, or Docker Desktop removal readiness.

## Recommended local invocation

Run from PowerShell with the source tree in the WSL Linux filesystem when practical; Microsoft recommends keeping Linux-tool projects there for filesystem performance. For a source tree on a Windows drive, use a read-only bind mount and treat its slower I/O as a separate measurement condition.

```powershell
$repo = (Resolve-Path .).Path
wslc run --rm --pull never --network none --cpus 1 --memory 512M `
  --volume "${repo}:/src:ro" --workdir /src `
  python:3.12-slim python -B -m unittest -v path.to.test_module
```

Before an evidence-bearing run, replace the illustrative image tag with the exact approved image digest, confirm the full resolved command and source hashes, and retain stdout, stderr, exit status, runtime/image identity, and output hashes. Never point writable output into the read-only source mount; use a distinct, explicitly writable output mount when the study requires outputs.

To smoke-check that WSLc is installed, the approved Python image is already cached, the no-network/resource options are accepted, and a read-only bind mount actually rejects writes, run `.github/scripts/test_wslc_local_runtime.ps1` from PowerShell. It uses only a GUID-named temporary directory and removes that exact directory in a `finally` block. It is an environment compatibility check, not a scientific result or a Docker parity suite.

## Migration gates

1. **Eligible now for pilot:** disposable single-container local tests that need a pinned Linux image, no network, bounded CPU/memory, read-only source bind mounts, and ordinary process exit codes.
2. **Validate before migration:** image architecture/digest behavior, bind-mount path and permission semantics, UID/GID mapping, signal/timeout propagation, artifact write paths, memory enforcement under pressure, and cleanup after abnormal termination. Record a representative Docker baseline and WSLc result without pooling them as scientific outcomes.
3. **Keep Docker/OrbStack or another validated runtime for now:** Docker Engine API/socket consumers, Compose orchestration, workflows requiring unsupported isolation flags or cgroup/swap guarantees, privileged/capability manipulation, daemon-specific behavior, or any study whose frozen protocol names a required runtime/engine version. Use a separately frozen successor to test a runtime substitution; never rewrite a consumed allocation or its historical STOP/FAIL/HOLD.
4. **Keep hosted CI unchanged:** GitHub Actions remains the shared review gate. WSLc is a local iteration and resource-control option, not an Actions runner or a substitute for successful required checks.
5. **Promote only after evidence:** update a workflow or repository-wide default only after an audited compatibility matrix and representative runtime/resource measurements pass. Do not infer lower memory use or faster iterations from this smoke test.

The WSLc CLI does not expose a Docker Engine-compatible socket; do not point Docker SDKs, Testcontainers, or Docker Compose at it. Microsoft documents WSLc as included with WSL `2.9.3+`; the `3.0.1.0` shown above is this host's WSL release, while the Ubuntu distribution itself remains WSL version 2.

## References

- [Microsoft: WSL containers general availability](https://blogs.windows.com/windowsdeveloper/2026/09/29/wsl-containers-now-generally-available/)
- [Microsoft Learn: Get started with WSL containers](https://learn.microsoft.com/en-us/windows/wsl/tutorials/wsl-containers)
- [Microsoft Learn: WSL advanced settings](https://learn.microsoft.com/en-us/windows/wsl/wsl-config)
