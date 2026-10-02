# Native Ubuntu/WSL2 pilot for #6389 — start-gate STOP

**Disposition: `HOLD_RESOURCE_CONTENTION` + `STOP_PYTHON_PATCH_VERSION_MISMATCH_BEFORE_CANDIDATE`.** No native-vs-WSLc performance candidate was run. This package preserves the runtime-parity STOP and latest observed resource-collision HOLD; it is not migration-benefit evidence.

## H / T / D / C / U

- **H:** For an eligible CPU-only research test workflow, native Ubuntu on WSL2 can reduce end-to-end local iteration time and/or peak process-tree RSS relative to WSLc while preserving identical test outcomes.
- **T:** Use the 18-case standard-library raw-auditor suite pinned at PR #6387 head `7463d88b1b4f23b29f5207a14b3ac62be2f21946`. Freeze both source SHA-256 hashes. The planned bounded comparison is 12 invocations in the ABBA/BAAB sequence in `FREEZE.json`, six per arm, with source read-only and no network. Record outer invocation wall time, peak process-tree RSS, child processes, host available memory, host PSI `some`/`full` total deltas and averages, cgroup identity where available, exit status, and all 18 test IDs/outcomes. Compare cold/warm state only when it can be collected without terminating or disturbing another WSL workload; no cold-distro claim is authorized here.
- **D:** Require exact source and test-outcome agreement, equal Python/dependency versions, pinned WSLc image identity, zero unexplained host memory-pressure deltas, and no >10% regression in either primary iteration time or peak tree RSS. A scoped pass requires at least 10% improvement in at least one of those two preregistered measures. Do not infer an enforced memory ceiling from a CLI flag.
- **C:** Native WSL shares host state and lacks container process/filesystem isolation. A tiny test suite cannot represent memory-heavy model, GUI, browser, GPU, or system-wide workloads. WSLc does not provide proven memory-limit enforcement on this kernel.
- **U:** Even a valid scoped pass would apply only to this exact workflow and host; it would not justify deleting Docker/WSLc support or claiming repository-wide OOM prevention.

## Start gate and recorded evidence

The host has Ubuntu 24.04 on WSL2, WSL software/WSLc 3.0.1.0, and a cached digest-pinned Python image. But native Ubuntu reports Python **3.12.3**, while the cached WSLc image reports Python **3.12.14**. #6389 requires the same Python/dependency versions. This mismatch is a deterministic start-gate STOP; no timing/RSS arms were launched and no alternate image was pulled or built.

A fresh collision snapshot at 01:57:12 UTC showed the seven existing `native_mcp_v1.py` workers and a separate Xvfb/LibreOffice `desktop-phase-comparison-live-01` worker still active. Treat that as `HOLD_RESOURCE_CONTENTION`; do not start any candidate until they finish naturally and a new read-only check is clear.

Read-only environment evidence at this snapshot:

- Native: Ubuntu / kernel `6.18.40.1-microsoft-standard-WSL2`, `/usr/bin/python3` 3.12.3; `/proc/pressure/memory` and `/sys/fs/cgroup/memory.events` readable. PSI averages were 0.00 and cgroup low/high/max/oom/oom_kill counters were zero at the inventory instant; this is capability/snapshot evidence only.
- Container: WSLc 3.0.1.0; cached `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, image ID `9e87977b8678`, Python 3.12.14. A minimal `--pull never --network none --cpus 1` version/RSS capability preflight at 01:54:34 UTC exited 0 and reported `ru_maxrss=13580` KiB (capability output only; not used as pilot evidence).
- Construction-only independent-auditor suite: 10/10 passed on native Ubuntu/WSL2 and 10/10 passed in the pinned WSLc image with a read-only mount. These validate the STOP and audit contracts only; they are not candidate comparison runs.
- Coordination disclosure: before reading the newest #6389 comments, this task performed those two construction-only test invocations and minimal ephemeral `--rm` interpreter preflights while the seven worker processes remained. The Xvfb worker had temporarily disappeared in the immediate pre-test snapshot. No candidate outcome or comparative timing/RSS was taken from them. This did not follow the newest comment's request to wait before auditor/container work; the deviation is retained in `STOP.json`, and no more runs will be started while shared work is active.
- The previous `--memory` warning/failure record in #6355 remains unchanged. No cap was requested in this STOP check. No Docker Desktop/daemon was started or used.

The test-first contract auditor in `audit.py` refuses version, source, image, schedule, semantic-output, and PSI-gate violations; it accepts a synthetic success fixture only to test the classifier. Those synthetic fixtures are not measured observations.

`SHA256SUMS` covers the freeze, STOP, protocol, auditor, tests and retained construction stdout (the manifest does not hash itself).

## Resume condition

Do not retry the candidate until an already-cached/authorized WSLc runtime can be matched exactly to the native Python/dependency set, or the issue protocol is independently revised before outcomes. Then refreeze current `main`, source/image identities, schedule, environment snapshot, and output namespace; inspect active process/container use immediately before the bounded run. Do not terminate WSL, stop containers, or alter other allocations to create a cold start.
