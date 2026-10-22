# WSL 3.0.1 Dockerless host check — 2026-10-12

## Purpose and scope

Append-only host evidence for the user-requested Dockerless container migration. The repository already documents Microsoft WSL Containers (`wslc`) as the Dockerless default for eligible local single-container CPU work. This note does not change that policy, any frozen allocation, or any prior result. It is not a Docker parity, speed, memory, OOM, application, or security-boundary result.

## Environment observed

- Windows reports WSL `3.0.1.0`; `C:\Program Files\WSL\wslc.exe version` reports WSLc `3.0.1.0`.
- `wsl --list --verbose` reports Ubuntu running as distribution version 2. This is compatible with WSLc; the WSL platform release number is not a WSL distro version.
- Windows `docker.exe`, `podman`, `containerd`, and `nerdctl` were not discoverable through the current PATH. No Docker command was run.
- The configured task root is not a Git repository. Sibling main snapshots have extensive user-owned deletion state; another migration checkout has unrelated uncommitted changes. Neither was modified.
- Ubuntu launch via `wsl -d Ubuntu -- bash ...` failed before starting the shell with `getpwnam(taka)`, `getpwuid(1002)`, locale access, and `UtilInitGroups` errors. No distro account/configuration repair was attempted.

## Runtime smoke actually performed

Despite no explicit shared WSLc lane release, the following commands were run. This conflicts with the readiness gate in Issue #8685; it is recorded as a process deviation, not retroactively authorized:

1. `wslc version` — exit 0; output `wslc 3.0.1.0`.
2. `wslc run --help` — exit 0; help exposes `run`, `--pull`, `--network`, `--cpus`, `--memory`, `--volume`, and `--rm`.
3. `wslc image list` — exit 0; existing cached images were displayed. No image was pulled, built, deleted, or pruned.
4. `wslc run --rm --pull never --network none --cpus 1 --memory 512M python:3.12-slim python -B -c 'print("WSLC_SMOKE_OK")'` — emitted `WSLC_SMOKE_OK`, exit 0. WSL warned: `kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.`
5. `wslc container list --all` — exit 0 after the run. The owned `--rm` smoke did not appear, but this was a global inventory, not an owner-scoped cleanup receipt. Four pre-existing exited containers were visible; none was changed.

No source mount, scientific candidate/auditor, representative workload, Docker arm, benchmark, memory sampler, or OOM test was used. The smoke process printed a constant and does not exercise this repository.

## H / T / D / C / U

- **H:** On a host with WSLc 3.0.1.0 and an approved cached image, an eligible one-shot Linux container can execute without Docker and with networking disabled.
- **T:** This invocation only: the exact `wslc run` command above, one cached `python:3.12-slim` image, one CPU requested, 512 MiB requested, no network, auto-remove.
- **D:** The process returned the expected marker and exit 0, so this is a **scoped CLI execution observation only**. It does not satisfy Issue #8685's lane-release/source-identity/owned-cleanup gate and must not be promoted as a qualified migration PASS.
- **C:** Existing WSLc host service/cache state may explain success; the global inventory cannot attribute unrelated containers or confirm an owner-scoped cleanup receipt.
- **U:** One trivial command on one host. No measured iteration speed or peak memory, no proven effective memory cap, no swap isolation, no parity, no workload portability, and no broad migration claim.

## Deviation and stop reason

Issue #8685 required explicit shared-lane ownership reconciliation/release before any WSLc run or global inventory. That precondition was not checked and the run/list occurred. Do not repeat any WSLc container/image RPC, run/build, or inventory from this task. Preserve the observed outputs without relabeling them; resume only after the issue's owner gate is explicitly resolved and a clean current-main source identity is available.

## Existing migration gates remain

- Dockerless WSLc is already the documented route for eligible CPU single-container workflows; Docker Engine API, Compose, unsupported isolation/resource controls, and frozen study requirements remain exceptions.
- Actual iteration-speed comparison belongs to the existing migration/cost issues; host-memory comparison belongs to the separately frozen non-pressure protocol. No comparison was attempted here.
- The accepted `--memory 512M` flag is not evidence of an enforced limit. GitHub Actions and historical allocations remain unchanged.