# Owned startup/close race prototype r550

Main's direct owned-session close was observed to return `closed`, `verified`
while a spawned Fake X child was paused before parent registration. A prototype
uses a reentrant process-local lifecycle lock: direct close while startup holds
the lock returns `busy`, and a later normal close produced a verified receipt.
The MCP manual busy-close retry case passed after a candidate reservation
rollback change.

The third preregistered case still failed: MCP lifespan shutdown returned while
the separately initiated, gated startup subsequently exposed a live child.
This is injected private-API concurrency, not a natural frequency measurement or
real X/input-release trial. The candidate is not safe to merge: review also
found that writing a busy result to the final close receipt path can overwrite
earlier evidence. Startup, cancellation, shutdown and in-flight process custody
need a coherent bounded protocol. The fixture's worker timeout/cleanup paths
are not exhaustive; no hard syscall bounds or queued-X guarantees are claimed.

`raw.zip` SHA-256
`827c2420b916c14062afeafd3e05f5473c7e1f1d95a832a62c2cd3ed4a8b846f`
contains conditions, base, pre-run patch, source status, unittest output and
exit code. The archive passed member integrity checks. Docker image digest and
flags are recorded conditions, not independently attested by the test output.
