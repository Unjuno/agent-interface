# Owned lifecycle busy receipts: r551

One fixed-order isolated Linux Fake X run passed three scoped checks: direct
startup/close returned busy; manual MCP busy preserved a preexisting canonical
close file while retaining a per-call report; and lifespan busy wrote a separate
pending UNKNOWN record without overwriting that file. The last case used an
event to confirm the pending write before releasing the startup gate. Captured
synthetic records and test output are in `raw.zip`.

The receipt test's fixture kills any surviving child during cleanup; it does not
claim that shutdown retained or retired the child. The separate r550 custody
regression still fails. A pending receipt is not a final close, input release or
task-success receipt. Persistence failures, interruption, concurrent close,
ordering against earlier records and consumer interpretation remain unverified.
The fixture directly starts an owner and uses Fake X, not real input or MAP01.

The archived manual report also shows `state=opening` with `owner_process.pid`
null and `alive=false` while the fixture had spawned a child before parent
registration. That field reflects the registered process reference and is not
proof that no child exists; the public representation needs separate repair.

`raw.zip` SHA-256
`f50c28b38cea1cbc64468a3ce9db47e23c3b1f46a3739457ab8a9e400b86e3f6`
contains pre-run conditions, base and diff, source status, output, exit and
synthetic records. ZIP integrity was checked. The image digest and flags are
recorded conditions, not independently attested by the test output.
