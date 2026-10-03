# #6067 D01: deadline/resource diagnosis, not A01 replay

## Status and scope
Prospective design for diagnostic allocation PHASE-DEADLINE-6067-D01-20261003-3CBF. See audit/RESULT.json and REPORT.md for subsequently executed outcomes.
Intake main ba1c4d966bc098e8f9f7e9e6df85f1281daa1582. Canonical docs/CURRENT_GOAL.md r134 and #57/#59 remain unfinished.
Predecessor A01 (PR #7021) STOP_CAPTURE_TIMING_GATE is immutable: irregular first capture was 17.231413 ms late. It did not collect per-deadline CPU/sleep telemetry, so no cause can be backfilled.
D01 retains that result and investigates a resource-qualification question under the still-open #6067. It does not create a wrapper-only research Issue.

## H / T / D / C / U
- H: Is throttling by the container's own leaf CPU quota necessary for instrumented late waits? This narrow necessity hypothesis is not a claim about host scheduling.
- T: 16 fresh serial private-Xvfb dark cells / 128 acquisitions. Four cyclic Latin rows contrast CPU quotas 1 and 2 within fixed and irregular schedules. See exact plan.json. No frame/cell replacement, rerun, quota escalation outside that plan, threshold relaxation, live input or model call.
- D: Prospective raw before/after cpu.stat, optional cpu.stat.local, process/thread CPU, context switches, optional schedstat/enabled state; coarse-sleep request/return and spin-entry; actual XGetImage/extraction timestamps; all 1024 uint32 pixels, separate source/observer PIDs, epoch/window/journals, cgroups, full terminal Docker inspect, logs and hashes.
- C: Independent stdlib-only saved-byte auditor; 17 construction unit methods include type, duplicate/nonfinite JSON, pixel, counter, clock, sleep completeness, optional grammar/regression, command preflight and plan corruptions. Twelve saved-actual-raw corruption controls are run separately, without assuming the first frame contained a sleep. Original fixture/Xlib/policy/common are copied byte-for-byte from 48ce12d529c1a9127e46eda4b33bcaaa278129a2.
- U: Linux/macOS host/ancestor scheduling is uncontrolled; 16 serial cells cannot identify a cause or prove general tail absence. Post-wait snapshot and flushed trace precede acquisition; their measured cost makes this an instrumented variant, not an exact A01 replay. Dark cells cannot establish pulse detection, useful feedback/recovery, latency benefit, normal key-up, human tempo or end-to-end GUI/model performance.

## Frozen decisions
Any wait-return more than 10,000,000 ns after deadline with leaf nr_throttled delta zero is a counterexample ONLY to own-leaf-throttle necessity.
If no such late wait exists but all late waits show leaf throttling: ASSOCIATION_ONLY, not causal attribution.
If no wait exceeds the deadline tolerance: HOLD_NOT_REPRODUCED, not repaired/solved/PASS_T1. Separately report late native starts caused after wait return.
Acquisition timing is an outcome here, not an exclusion/retry gate. Missing frames, malformed counters, child failures, unsafe allocation or retention failures STOP at first occurrence. Auditor is admitted only after full producer exit 0, with all 16 cells retained.
Unavailable optional telemetry is explicitly absent, never converted to zero. The observer's own process schedstat is usable only if schedstats is enabled.

## Runtime and custody
Owner thread 01a0b98d-3cbf-7710-b1a4-28c16e0b49da.
Only owned private Docker engine on research-6183-t0-20261003; no default/shared Docker or peer VMs.
No host-exclusivity claim. Cached immutable arm64 image sha256:c4839671ed0625dd38a53d8ed542bab16407c2b4c88a5ac84431695438c2b816.
Native containers: CPU quota 1 or 2, 512 MiB memory, zero swap, PIDs64, network none, user501, read-only root/source, dropped ALL capabilities, no-new-privileges. Fresh owned Xvfb/window per cell; no input API called.
Source SHA-256 set, exact native and independent auditor commands, gates and one-shot budget are published in FREEZE.json before diagnostic execution. Construction uses separately named outputs and is excluded from the 128 frames.
No automatic scientific phase-matrix admission or A02: that requires a separately named prospective allocation and review. Review/CI may replay saved-byte auditing only, never the native allocation.
The runner checks every frozen command before output creation, then a separate producer-only guard validates retained telemetry and actual resource/terminal settings before advancing to the next cell. It never imports or invokes the official auditor. The official independent audit is admitted only after producer completion.

## Sources
Linux official cgroup v2 CPU counter/quota definitions: https://docs.kernel.org/admin-guide/cgroup-v2.html
Linux official schedstat fields: https://docs.kernel.org/scheduler/sched-stats.html
These documents bound interpretation; they are not experimental evidence.
