# Issue #6669 T0: WSLc control-plane applicability audit

**Disposition: `HOLD_APPLICABILITY_UNRESOLVED`.** This source/runtime audit does not establish whether the protection described by WSL PR #40519 preserves the WSLc management path under bounded workload pressure. No pressure test or candidate/auditor allocation was run.

## H / T / D / C / U

- **H:** In an isolated, kernel-bounded WSLc workload, the tested WSL 3.0.1 management path may remain able to report state and stop/verify cleanup while the workload fails explicitly. T0 can falsify applicability before any pressure test.
- **T:** Pin Microsoft WSL release tag `3.0.1` to commit `91f161fa240dc355c1a88daabc8aac4273e35ba5`; inspect the WSLC VM client/container/init and Linux utility-VM initialization/cgroup paths; take read-only WSL/Arch cgroup observations. Source blob IDs and the normalized terminal transcript are retained beside this report.
- **D:** T0 would pass applicability only if the release-pinned source and live WSLc VM view showed the tested workload and protected control path on the claimed bounded cgroup boundary. **That gate is not met.** The available host snapshot is from the Arch distro's cgroup namespace, not a live WSLc utility VM. Keep T1 stopped until the path is observable and a disposable VM with a kernel-confirmed memory ceiling is available.
- **C:** The Arch distro cgroup namespace hides parent cgroups. WSLc has a separate utility-VM path; the VM's actual live cgroup hierarchy, limits and API responsiveness were not observed. Source code describes implementation but does not prove the installed binary's runtime containment or survival behavior.
- **U:** No workload pressure, OOM, WSLc stop, cleanup, per-container cap, memory improvement or general resilience was tested. This is a scoped applicability HOLD, not a FAIL or PASS for control-plane survival.

## Findings

Microsoft's WSL 3.0.1 release tag includes the WSLC implementation inspected here. In the release-pinned source, `WSLCVirtualMachine.cpp` describes the client as connecting to a virtual machine created by `IWSLCVirtualMachine` in the SYSTEM service. `WSLCContainer.cpp` creates containers through the runtime's Docker-compatible client/schema; `WSLCInit.cpp` configures the guest Docker daemon. The Linux init source selects a distinct `InitEntryUtilityVm` path when `UtilIsUtilityVm()` is true, and cgroup initialization has a separate utility-VM branch.

WSL PR #40519 describes critical WSL processes outside a resource-limited `wsl-user` cgroup, with 32 MiB and 0.01 CPU reserved, and per-distro cgroups below it. WSL PR #41512 adds per-distro cgroup namespaces, and release 3.0.1 lists follow-up PR #41642. These facts establish relevant WSL mechanisms, but do not show which of those boundaries the WSLc utility VM, its runtime API, and a running container actually use.

The read-only host snapshot reports WSL package 3.0.1.0, kernel `6.18.40.1-microsoft-standard-WSL2`, and only `Arch Linux` registered as a WSL2 distro. Within Arch, `/proc/self/cgroup` is `/non-systemd`; cgroup v2 exposes controllers `cpuset cpu io memory hugetlb pids rdma`, subtree controllers `cpu memory pids`, and visible root values `memory.max=max`, `cpu.max=max 100000`. This view cannot expose the parent cgroup hidden by the distro namespace and is not a WSLc container measurement.

## Safe disposition

Do not perform T1 on the shared host or treat `wslc --memory` as the safety boundary. Resume only in a disposable VM with a kernel-confirmed ceiling, an observable workload/control cgroup relationship, exact WSL build/image identity, frozen probe deadlines, and independent raw-only audit/mutation controls. This result does not authorize repository-wide Docker support removal. For eligible CPU workflows, WSLc can be used without Docker Desktop; workflows requiring Engine/Compose semantics, special isolation/resource guarantees, GUI support or CI compatibility need separate evidence.

## Pinned source references

- [WSL 3.0.1 release](https://github.com/microsoft/WSL/releases/tag/3.0.1) and [release commit](https://github.com/microsoft/WSL/commit/91f161fa240dc355c1a88daabc8aac4273e35ba5)
- [WSL PR #40519](https://github.com/microsoft/WSL/pull/40519), merged 2026-07-14
- [WSL PR #41512](https://github.com/microsoft/WSL/pull/41512), merged 2026-09-18
- [WSL PR #41642](https://github.com/microsoft/WSL/pull/41642), included in the 3.0.1 release notes
- [WSLCVirtualMachine.cpp](https://github.com/microsoft/WSL/blob/91f161fa240dc355c1a88daabc8aac4273e35ba5/src/windows/wslcsession/WSLCVirtualMachine.cpp)
- [WSLCContainer.cpp](https://github.com/microsoft/WSL/blob/91f161fa240dc355c1a88daabc8aac4273e35ba5/src/windows/wslcsession/WSLCContainer.cpp)
- [WSLCInit.cpp](https://github.com/microsoft/WSL/blob/91f161fa240dc355c1a88daabc8aac4273e35ba5/src/linux/init/WSLCInit.cpp)
- [init.cpp](https://github.com/microsoft/WSL/blob/91f161fa240dc355c1a88daabc8aac4273e35ba5/src/linux/init/init.cpp)
- [config.cpp](https://github.com/microsoft/WSL/blob/91f161fa240dc355c1a88daabc8aac4273e35ba5/src/linux/init/config.cpp)

Formal pressure candidate=0; independent formal auditor=0; pressure blocks=0; retries=0.
