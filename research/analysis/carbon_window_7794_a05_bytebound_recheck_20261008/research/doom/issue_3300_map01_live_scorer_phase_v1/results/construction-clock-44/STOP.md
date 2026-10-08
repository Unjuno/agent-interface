# Construction-clock-44 — kernel uprobe feasibility STOP

Disposition: `STOP_KERNEL_UPROBE_UNAVAILABLE_IN_DEFAULT_CONTAINER`.
No ViZDoom session was launched and no scientific phase row was produced.

## H / T / D / C / U

- **H:** A kernel uprobe attached to the pinned engine's `VIZ_Tic` entry could timestamp the function boundary before any C/C++ prologue or source clock call, using a kernel event clock shared with scorer monotonic timestamps.
- **T:** Read-only capability/tracefs inspection inside the same linux/arm64 Docker environment, with `--network none --read-only`, no extra capabilities, and no host tracefs mount. The probe checked `perf_event_paranoid`, effective/bounding capabilities, tracefs mount table and the uprobe event-control path. No `perf` event or tracefs state was written.
- **D:** `perf_event_paranoid=2`; `/sys/kernel/tracing` exists but is empty and not writable; `/proc/mounts` reports no tracefs/debugfs mount; `uprobe_events`, `kprobe_events`, `trace_clock`, and `available_tracers` are absent. Effective/bounding capability masks are both `00000000a80425fb`, without `CAP_SYS_ADMIN` (bit 21) or `CAP_PERFMON` (bit 38). Exact read-only probe output and command are retained in `container.log` / `invocation.txt`.
- **C:** Uprobe feasibility is blocked in the default container security context. No function-entry timestamp, sample, or experiment result exists. This is an environment capability STOP, not evidence for or against the MAP01 hypothesis. No privileged container, host tracefs mount, or capability escalation was attempted.
- **U:** Whether this VM permits a separately authorized tracefs/perf setup remains unknown. Until such a mechanism is available within approved isolation, run43's in-process clock sample remains the best tested witness but does not bound function-entry latency. Formal allocation remains 0/120.
