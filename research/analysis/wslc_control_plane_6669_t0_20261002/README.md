# WSLc control-plane applicability T0 — Issue #6669

**Status: HOLD (source applicability not established; no pressure run).** This is a bounded source-path audit, not a runtime result. The source reviewed is Microsoft/WSL commit `0e04306fc21ed022460a6af947493f552a4943f9`; the source files are linked below with the Git blob SHAs returned by GitHub. The test machine's installed WSL/WSLc build was not independently identified in this audit, so the reviewed source cannot be equated with its runtime.

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
| S3 | The WSL init source has a `WSLC_ROOT_INIT` entrypoint selection. This proves a distinct explicit mode marker exists, but this audit did not establish its complete downstream startup/control flow. | [`main.cpp`](https://github.com/microsoft/WSL/blob/0e04306fc21ed022460a6af947493f552a4943f9/src/linux/init/main.cpp), blob `5d0f1f32d390bc7e149f9b8715a760c45f15bd2c`; [`lxinitshared.h`](https://github.com/microsoft/WSL/blob/0e04306fc21ed022460a6af947493f552a4943f9/src/shared/inc/lxinitshared.h), blob `be69c734344a45a3771f73ceffe1cdd44acdf6d5` |
| S4 | In the distro init path, `EarlyConfig.IsolateDistroCgroup` plus cgroup v2 availability gates `SetupWslUserCgroup()`. `WslCoreVm.cpp` builds/sends that early-config message from `m_vmConfig.IsolateDistroCgroup`. | [`main.cpp`](https://github.com/microsoft/WSL/blob/0e04306fc21ed022460a6af947493f552a4943f9/src/linux/init/main.cpp), blob above; [`WslCoreVm.cpp`](https://github.com/microsoft/WSL/blob/0e04306fc21ed022460a6af947493f552a4943f9/src/windows/service/exe/WslCoreVm.cpp), blob `73849b09ee67a9fa2bf1125f4def1f919395ee7f` |
| S5 | WSLc VM creation is implemented by `HcsVirtualMachine`, while the observed `IsolateDistroCgroup` forwarding point is in `WslCoreVm`. The reviewed evidence does not show whether/how the WSLc VM receives equivalent early config or protection. | S1 and S4; comparison is limited to the cited source paths, not a claim that no other path exists. |

Microsoft describes #40519 as protection/isolation for critical WSL processes and distro cgroups, not as an unconditional WSLc guarantee. WSL 3.0.1's release and general availability do not by themselves establish that a particular WSLc control path receives this protection. See [PR #40519](https://github.com/microsoft/WSL/pull/40519), [WSL 3.0.1 release notes](https://github.com/microsoft/WSL/discussions/41724), and the [WSLc overview](https://learn.microsoft.com/windows/wsl/wsl-container).

## Decision and next gate

The code-level trace positively identifies a dedicated WSLc HCS VM and its containerd/dockerd process route. It also identifies the distro-cgroup configuration gate. The bridge between those paths is not established by this evidence, and the tested machine's runtime build was not captured. Therefore applicability is **HOLD**, not pass and not fail.

T1 pressure testing is **not authorized by this result** and remains unrun. It requires (1) tested build identity, (2) explicit source/runtime proof of the protected-boundary applicability or a revised hypothesis, and (3) a disposable isolated VM with a kernel-confirmed hard ceiling. Shared-host pressure/OOM remains prohibited. Configured WSLc memory values alone are not a safety boundary.

## Independent review checklist

This claim/evidence crosswalk is intentionally falsifiable. A follow-on reviewer should verify each cited path at the pinned commit, check that S1/S2 do not imply S4, and reject any promotion of this HOLD to a protection-absence or liveness claim. No raw pressure-run artifacts exist because no pressure run occurred. Branch/PR collision search for `6669` was empty at intake; it is not a global novelty proof.
