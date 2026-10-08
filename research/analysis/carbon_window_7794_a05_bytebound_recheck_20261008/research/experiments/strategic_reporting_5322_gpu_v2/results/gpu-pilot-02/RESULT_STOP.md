# GPU pilot-02 STOP — capture channel lost

The frozen Issue #5397 runner was invoked exactly once. Its final result bundle was not recovered: the command exceeded the shell tool's initial wait, and the orchestration code failed to retain the returned session handle before the runner later exited. The in-memory output disappeared with that process.

During the live process, a separate read-only `ollama ps` check showed both expected models at `100% GPU` and context 4096 on the RTX 3080 host. This confirms GPU-backed model residency during the run, but it does not establish how many calls completed or provide response/output evidence.

No raw call bundle, independent audit, score summary, or completion status is available. Therefore this is **STOP / unverified**, not a result. Do not retry or reinterpret pilot-02. Any new execution needs a successor issue, a source-frozen per-call durable capture channel, and a new seed/allocation. The original pilot-01 digest STOP and the CPU formal-01 FAIL remain unchanged.
