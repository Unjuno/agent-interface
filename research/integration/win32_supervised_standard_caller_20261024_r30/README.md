# Win32 cancellation R30 — retirement-call boundary trace

R29 showed 21 exact-call polls remaining pending while an injected Q-down callback was held for 1304.466 ms. It did not identify which retirement call was waiting. R30 repeats the same 1250 ms native hook boundary once on a fresh fixture/generation and adds a trace-only wrapper around the actual `OperationCancellationSupervisor._retire_process` call and its exact producer Process methods (`is_alive`, `terminate`, `join`, `kill`). The wrapper records method entry/return/exception timestamps and does not change the method results or issue input.

The input-free preflight validates current-main/runtime hashes, R29 raw/audit hashes and semantics, the current registry value, Python syntax, the instrumentation module load, and the hash of `conditions.json` itself. The live strict-release gate is unchanged.

A diagnostic trace PASS identifies the retirement call boundary, not successful release. Strict action PASS still requires confirmed recovery and independent same-generation all-up during the full callback hold. One owned fixture, one dispatch, at most one cancel; no retry/replay, registry mutation, WSLc, or Docker.
