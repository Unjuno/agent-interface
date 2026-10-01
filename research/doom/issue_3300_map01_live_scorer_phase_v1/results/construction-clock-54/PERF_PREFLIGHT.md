# Non-instrumenting engine-tic witness preflight

Disposition: `HOLD_TARGET_ADDRESS_UNRESOLVED`. No MAP01 scorer row or formal sample was produced. This is an excluded tooling preflight attached to the run53 construction branch.

## H / question

Can OrbStack expose Linux `perf_event_open` in the pinned ViZDoom container for a hardware execution breakpoint, without patching the engine? Such a breakpoint could provide a kernel-timestamped `VIZ_Tic` witness if its exact runtime address can be resolved.

## T / tests

- Pinned Docker image `issue-3300-map01-fixture-smoke:v2`, ID `sha256:8d984b04efe5bca7bd9b3808aac4f56bd273a6a1ada76cd51939253b874244ca`, Linux/arm64, OrbStack kernel `7.0.14-orbstack-00380-ga7e0a2dc9535`.
- Preflighted default container tooling/tracefs and attempted one `PERF_COUNT_SW_CPU_CLOCK` self-event with raw `perf_event_open` syscall 241.
- Repeated only that capability preflight in a disposable container with `--cap-add=PERFMON` (no `--privileged`, no `SYS_ADMIN`, no network). The self-event opened successfully.
- Initialized the exact ViZDoom 1.3.0 MAP01 private fixture in an Xvfb/Openbox session, located the engine child, and parsed its ELF64 `.symtab` and `.dynsym` tables with Python stdlib to find a candidate `VIZ_Tic`/MAP_TIC symbol.

## D / outcome

- Default container: no `perf`, `bpftrace`, or `trace-cmd` binary; `/proc/sys/kernel/perf_event_paranoid=2`; tracefs directory exists but exposes no readable `uprobe_events`; seccomp mode 2. Self `perf_event_open` stopped with `EPERM` (errno 1).
- Container with the narrow `PERFMON` capability: self software CPU-clock event opened (fd 3). This confirms capability-gated perf event access, not support for attaching a breakpoint to the engine.
- Engine executable path: `/usr/local/lib/python3.11/site-packages/vizdoom/vizdoom`; SHA-256 `355235742626ed6152fa2ba8c2ddf82e03003b42033aa3d16baf22cbd317ec11`. No usable `VIZ_Tic` or MAP_TIC symbol was found in the executable symbol tables. Therefore no breakpoint was attached and no witness timestamps were collected.

## C / interpretation

The narrow `CAP_PERFMON` route is promising, but the target address is unresolved. No claim is made about OrbStack kernel support for hardware execution breakpoints, because only a self software event was tested. Do not infer that eBPF/uprobe or hardware watchpoints are impossible. No broad capability escalation was attempted.

## U / next gate

Resolve a target PC from a hash-matched symbol-bearing build/debug artifact and verify that the target address maps to the exact running binary, or choose another read-only witness. Then test a single hardware breakpoint on a non-formal fixture, compare event timestamps/counters against the known action-boundary control, and quantify missed/extra events and observer overhead before proposing a phase witness. Formal collection remains 0/120 and `HOLD_LIVE_SPAN_UNIDENTIFIED`.

## Evidence

`perf-preflight.json` contains the structured observations; SHA-256 `f41007d056b9fa5e7ef5279f1d879a3db227038500533919136e4faca3e36ff9`. The exact default-container command output is `perf-preflight.txt`, SHA-256 `d83c420aa228ff03790755e01e9b1daddcf31c5862f9ba93ec52b3e01c045b1a`. The self-event and target-symbol result rows are `perf-event-probe.json`, SHA-256 `de0dcc380d5756fa122255fbcb6b785ab0ab83ab434ad0a1bfdcaddc6cdb7400`. Re-runnable script: `map01_clock_witness_preflight.py`, SHA-256 `2607981ea311c823766022c88911b340a14bada8b0ee9cbb991dd2fc094e2dda`. Run it with the archived Docker image, `--network none --cap-add=PERFMON`, Xvfb/Openbox startup, and the read-only script bind mount. A separate initial probe invocation failed to enter Python due missing `docker run -i`; it was a harness error with no event/open and was not treated as kernel evidence.
