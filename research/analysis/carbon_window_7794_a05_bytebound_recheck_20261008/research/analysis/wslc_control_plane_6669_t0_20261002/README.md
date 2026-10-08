# WSLc control-plane applicability T0 — Issue #6669

**Scoped source result: FAIL_APPLICABILITY for direct reuse of the #40519 distro-cgroup hook in the reviewed source snapshot. Overall runtime/control-plane pressure result: HOLD; no pressure run.** The source reviewed is Microsoft/WSL commit `0e04306fc21ed022460a6af947493f552a4943f9`; source files are linked below with their Git blob SHAs. The installed WSL/WSLc version was read-only captured as 3.0.1.0, but its binary-to-source-commit correspondence was not established, so the source conclusion is not promoted to a tested-runtime result.

## H / T / D / C / U

- **H:** An isolated, kernel-bounded WSLc workload may be able to fail or be stopped while the management path remains usable. The narrower prerequisite is that WSLc's actual control/runtime path uses the cgroup protection/reservation at issue in Microsoft PR #40519.
- **T:** Trace the source path from WSLc VM construction through init-mode selection, containerd/dockerd launch, and the `IsolateDistroCgroup` early-config handling. Compare the WSLc path with the WSL distro path changed by #40519. No load, memory-pressure, OOM, or live-runtime operation is part of this T0.
- **D:** `PASS_APPLICABILITY` only if an explicit source/runtime chain shows the tested WSLc management path reaches the claimed protected boundary. `FAIL_APPLICABILITY` only if an explicit path shows it does not. `HOLD` if the connection is not demonstrated or build/runtime identity is missing. This audit is HOLD; it does not infer absence of protection.
- **C:** A dedicated WSLc utility VM may have independent initialization or protection; source paths not traversed here could connect it to shared mechanisms. CLI availability alone would not prove stop/cleanup safety.
- **U:** Source commit, WSL build, Windows build, cgroup mode, VM topology, and runtime configuration may differ. Even a future applicability pass would not establish memory-limit enforcement, control-plane liveness, cleanup, or general OOM safety.

## Source-path trace

| ID | Observation | Evidence |
|---|---|---|
| S1 | WSLc constructs an HCS `VirtualMachine`, takes session `MemoryMb`/`CpuCount`, boots the WSL VM-mode initrd, and adds `WSLC_ROOT_INIT=1` to the kernel command line. | [`HcsVirtualMachine.cpp`](https://github.com/microsoft/WSL/blob/0e04306fc21ed022460a6af947493f552a4943f9/src/windows/service/exe/HcsVirtualMachine.cpp), blob `c09c9fe8a13fdf92cbc6bd3b822fe258ec3bced2` |
| S2 | WSLc session bring-up starts containerd and dockerd; `StartProcess` launches them through `m_runtime.Vm()`. | [`WSLCSession.cpp`](https://github.com/microsoft/WSL/blob/0e04306fc21ed022460a6af947493f552a4943f9/src/windows/wslcsession/WSLCSession.cpp), blob `094fa269088f75327e0958410ee9e8981f487b65` |
| S3 | `main.cpp` checks `WSLC_ROOT_INIT` and immediately returns through `WSLCEntryPoint`, before the normal WSL distro init path. | [`main.cpp`](https://github.com/microsoft/WSL/blob/0e04306fc21ed022460a6af947493f552a4943f9/src/linux/init/main.cpp), blob `5d0f1f32d390bc7e149f9b8715a760c45f15bd2c`; [`lxinitshared.h`](https://github.com/microsoft/WSL/blob/0e04306fc21ed022460a6af947493f552a4943f9/src/shared/inc/lxinitshared.h), blob `be69c734344a45a3771f73ceffe1cdd44acdf6d5` |
| S4 | The separate WSLc init entrypoint mounts cgroup v2 and handles WSLc service messages. It contains no `LxMiniInitMessageEarlyConfig`, `IsolateDistroCgroup`, or `SetupWslUserCgroup` handling. | [`WSLCInit.cpp`](https://github.com/microsoft/WSL/blob/0e04306fc21ed022460a6af947493f552a4943f9/src/linux/init/WSLCInit.cpp), blob `189fb355caf192f02759bb4715d54c7440d91ed0` |
| S5 | In the separate WSL distro init path, `EarlyConfig.IsolateDistroCgroup` plus cgroup v2 availability gates `SetupWslUserCgroup()`. `WslCoreVm.cpp` sends that early-config message from `m_vmConfig.IsolateDistroCgroup`. | [`main.cpp`](https://github.com/microsoft/WSL/blob/0e04306fc21ed022460a6af947493f552a4943f9/src/linux/init/main.cpp), blob above; [`WslCoreVm.cpp`](https://github.com/microsoft/WSL/blob/0e04306fc21ed022460a6af947493f552a4943f9/src/windows/service/exe/WslCoreVm.cpp), blob `73849b09ee67a9fa2bf1125f4def1f919395ee7f` |
| S6 | WSLc does share a different idle memory-reduction path: after chroot, `WSLCInit.cpp` starts `StartMemoryReductionThread(DropCache)` once. This is cache/page reclamation, not the #40519 distro cgroup isolation hook, a container memory cap, or proof of control-plane survival. | [`WSLCInit.cpp`](https://github.com/microsoft/WSL/blob/0e04306fc21ed022460a6af947493f552a4943f9/src/linux/init/WSLCInit.cpp), blob above; [`util.cpp`](https://github.com/microsoft/WSL/blob/0e04306fc21ed022460a6af947493f552a4943f9/src/linux/init/util.cpp), blob `7ed311f111365532565efa132bec523f438e085b`; [Microsoft PR #40376](https://github.com/microsoft/WSL/pull/40376) |

Microsoft describes #40519 as protection/isolation for critical WSL processes and distro cgroups, not as an unconditional WSLc guarantee. WSL 3.0.1's release and general availability do not by themselves establish that a particular WSLc control path receives this protection. See [PR #40519](https://github.com/microsoft/WSL/pull/40519), [WSL 3.0.1 release notes](https://github.com/microsoft/WSL/discussions/41724), and the [WSLc overview](https://learn.microsoft.com/windows/wsl/wsl-container).

## Decision and next gate

The code-level trace shows that the pinned source's WSLc init selects `WSLCEntryPoint`, which mounts cgroup v2 but does not implement the `EarlyConfig.IsolateDistroCgroup` / `SetupWslUserCgroup()` path used by ordinary distro init. Therefore **direct applicability of the specific #40519 distro-cgroup hook is FAIL_APPLICABILITY for this source snapshot**. This is not a claim that WSLc has no other cgroup or HCS protection. WSLc's separate DropCache memory-reduction thread is positive counterevidence to any broader claim that its init has no memory-management behavior.

The exact installed binary/source correspondence is unavailable, so tested-runtime applicability remains **HOLD**. The broader hypothesis—whether WSLc management operations survive a kernel-bounded workload pressure event and verify cleanup—also remains **HOLD/unrun**.

T1 pressure testing is **not authorized by this result** and remains unrun. It requires (1) tested build identity, (2) explicit source/runtime proof of the protected-boundary applicability or a revised hypothesis, and (3) a disposable isolated VM with a kernel-confirmed hard ceiling. Shared-host pressure/OOM remains prohibited. Configured WSLc memory values alone are not a safety boundary.

## Read-only runtime fingerprint (2026-10-02)

Commands executed in PowerShell:

```text
wsl.exe --version
wsl.exe --list --verbose
wslc.exe --version
wslc.exe info --format json
```

Observed: WSL and WSLc client `3.0.1.0`; WSL kernel `6.18.40.1-1`; WSLc Session Manager `3.0.1`; Windows `10.0.26200.9550`. The successful `wslc info` response reported two active sessions. Session names and creator PIDs are deliberately omitted from this public report; neither session was attached to, listed, started, stopped, or otherwise changed. `wsl.exe --list --verbose` failed with `Wsl/EnumerateDistros/Service/E_ACCESSDENIED`, so distro identity and per-distro cgroup state remain unavailable. `wslc info` exposes client/server/session metadata only; it does not expose the utility VM's cgroup tree or prove the installed binary corresponds to the pinned source commit above.

This improves runtime attribution to reported software/kernel/Windows versions, but does not establish the installed binary's source commit, live WSLc cgroup tree, or a kernel-confirmed test ceiling. No WSLc workload, pressure allocation, or OOM test was run.

## Independent review checklist

This claim/evidence crosswalk is intentionally falsifiable. A follow-on reviewer should verify each cited path at the pinned commit, check that S1/S2 do not imply S4, and reject any promotion of this HOLD to a protection-absence or liveness claim. No raw pressure-run artifacts exist because no pressure run occurred. Branch/PR collision search for `6669` was empty at intake; it is not a global novelty proof.
