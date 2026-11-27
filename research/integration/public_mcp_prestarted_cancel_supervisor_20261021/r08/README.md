# R08 — corrected PID source, focused Fake X composition

R08 repeats the four focused modules on the local PID-source correction. Normal
and optimized Python each pass **108/108 tests**. The suite includes public MCP
composition, the stale-cache/missing-owner-map PID regression, cancellation
supervisor validation, and XRes client-fence tests. Exact commands, source
hashes, environment, start/end times, raw stdout/stderr, and exit codes are
retained in this directory.

The source correction uses the parent's retained `Process.pid` for both
`owner_pid` and `owner_generation.child_pid`. This removes the mismatch found
in Xvfb runs 39620589667 and 39620978807 at the request-construction boundary.
R08 supports the local Fake X composition only; it does not prove the corrected
request against live Xvfb or prove XRes disconnect, physical input release,
late queued-effect exclusion, task success, or recovery.

No WSLc or Docker allocation was used. Keep all prior failed first outcomes
immutable. The next live discriminator must use the corrected pushed source and
separately retain supervisor acceptance, XRes result, release request, readback,
and independent task-effect evidence.
