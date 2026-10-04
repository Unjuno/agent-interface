# Local container-backed research with WSL Containers

## Status

Microsoft WSL Containers (`wslc`) is the **default local container runtime** for eligible single-container research and test iterations on this Windows host. WSL Containers is generally available with current WSL releases, including this host's WSL `3.0.1.0` / WSLc `3.0.1`; starting Docker Desktop or installing Docker Engine is not required for the covered build/run path. This is a scoped workflow migration, not a claim that every Docker workflow is interchangeable or that switching runtimes resolves memory pressure.

The local run path is established for ordinary CPU-only tests using a pinned Linux image, `--network none`, read-only source mounts, ordinary process exit codes, and disposable containers. Use native WSL execution instead when a test does not need a container boundary and its frozen protocol permits that. Use WSLc when container isolation and image packaging are useful but no Docker Engine API/Compose behavior is required.

Compatibility smoke checks were recorded on 2026-10-02 and 2026-10-04 with WSL `3.0.1.0`, WSLc `3.0.1`, and `python:3.12-slim` (`python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, linux/amd64):

- A Python smoke command completed with `--network none`, `--memory 512M`, `--cpus 1`, and `--pull never`.
- A Windows-host file bind-mounted with `:ro` was readable; an attempted write failed with `EROFS`.
- Both containers were run with `--rm`; `wslc container list --all` showed no residual containers afterward.
- WSL emitted `kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.` The memory cap was accepted, but swap isolation was not available in this environment. These checks are not a measured Docker-vs-WSLc performance, peak-memory, or OOM-prevention comparison.

Existing WSLc research evidence is also recorded in [PR #6114](https://github.com/Unjuno/agent-interface/pull/6114): a read-only, network-disabled Python replay ran two tests successfully. [PR #7020](https://github.com/Unjuno/agent-interface/pull/7020) records a narrow Dockerfile build/run. These results establish scoped Dockerless capability, not complete Docker flag parity, GUI performance, memory relief, or blanket Docker Desktop removal readiness.

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

## Dockerless Dockerfile build — scoped verification, 2026-10-03

[PR #7020](https://github.com/Unjuno/agent-interface/pull/7020) retains a real WSLc build/run of a tiny local Dockerfile on this Windows host: cached digest-pinned Python base, `WORKDIR`/`COPY`/`ENTRYPOINT`, exact copied-payload hash, exit 0, and verified removal of the named container. Five regression/mutation tests passed. Its separate offline auditor exited 0, but independent review found missing receipt-hash and run-record image-ID checks; read the [review qualification](../research/analysis/wslc_dockerfile_build_smoke_t0_20261003/REVIEW_QUALIFICATION.md) rather than treating that CLI output as a fully verified audit gate. This establishes a narrow Dockerless build/run capability, not general Dockerfile parity.

For an eligible new local iteration, `wslc build --file Dockerfile --tag <fresh-owned-tag> .` is the Dockerless build route. Use a digest-pinned base and a fresh owned build context/tag. Before an evidence-bearing run, resolve and freeze the resulting image identity, source hashes and full run command; use the cached-image/no-network/read-only-source invocation above where the protocol allows it. Do not reuse #7020's consumed formal allocation or silently replace the runtime of another frozen study.

The tested Dockerfile had no `RUN` instruction or dependency installation. Build-level network isolation was not established; `--network none` applies to the subsequent container run. Workflows involving package installation, other Dockerfile features, signals, writable outputs or stronger isolation need their own compatibility checks. The cgroup/swap warning remains, and the accepted `--memory` request is not a proven hard cap.

Keep speed and memory-benefit measurement under [#6693](https://github.com/Unjuno/agent-interface/issues/6693), including its same-host Docker and owner-release gates. [#6389](https://github.com/Unjuno/agent-interface/issues/6389) is a separate native-Ubuntu/WSL2 comparison; its scoped A03 result measures one small CPU workflow's iteration time, not peak memory or OOM avoidance. Do not start Docker Desktop, restart shared WSL, change global WSL settings or launch memory-pressure tests merely to use this local route.

## Migration gates

1. **Default now for eligible local container work:** disposable, single-container CPU tests that need a pinned Linux image, no network, ordinary process exit codes, and read-only source mounts. Prefer native WSL for eligible tests that do not require a container boundary.
2. **Validate before expanding a workflow's use:** image architecture/digest behavior, bind-mount path and permission semantics, UID/GID mapping, signal/timeout propagation, artifact write paths, memory enforcement under pressure, and cleanup after abnormal termination. Record a representative Docker baseline and WSLc result without pooling them as scientific outcomes.
3. **Use another validated runtime only where required:** Docker Engine API/socket consumers, Compose orchestration, workflows requiring unsupported isolation flags or effective cgroup/swap guarantees, privileged/capability manipulation, daemon-specific behavior, or any study whose frozen protocol names a required runtime/engine version. In particular, the observed `--memory` flag acceptance did not prevent a 384 MiB allocation under a 128 MiB setting on this host (#6309); do not use this option as a hard memory ceiling until a cgroup-capable environment passes a fresh successor test. Use a separately frozen successor to test a runtime substitution; never rewrite a consumed allocation or its historical STOP/FAIL/HOLD.
4. **Keep hosted CI unchanged:** GitHub Actions remains the shared review gate. WSLc is a local iteration and resource-control option, not an Actions runner or a substitute for successful required checks.
5. **Promote only after evidence:** migrate each application-specific workflow after its compatibility requirements are identified and its representative tests pass. Do not infer lower memory use or faster iterations from the availability of WSLc alone.

The WSLc CLI does not expose a Docker Engine-compatible socket; do not point Docker SDKs, Testcontainers, or Docker Compose at it. Microsoft documents WSLc as included with WSL `2.9.3+`; the `3.0.1.0` shown above is this host's WSL release, while the Ubuntu distribution itself remains WSL version 2.

## References

- [Microsoft: WSL containers general availability](https://blogs.windows.com/windowsdeveloper/2026/09/29/wsl-containers-now-generally-available/)
- [Microsoft Learn: Get started with WSL containers](https://learn.microsoft.com/en-us/windows/wsl/tutorials/wsl-containers)
- [Microsoft Learn: WSL advanced settings](https://learn.microsoft.com/en-us/windows/wsl/wsl-config)
