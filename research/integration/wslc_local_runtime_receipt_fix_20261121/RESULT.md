# Result — scoped pass with receipt limitation

Disposition: **`SCOPED_PASS_WITH_RECEIPT_LIMITATION`**.

The captured run exited 0. It read the pinned Python image without pulling or
network access, verified the read-only bind by observing `EROFS`, and reported
container cleanup as verified. WSLc also warned that swap-limit capabilities
were unavailable or cgroups were not mounted; the requested memory flag does
not establish swap isolation, a hard memory bound, or peak-memory enforcement.

The script retained the outer invocation log and runner summary, but its success
path deleted the unique probe directory. That also deleted the full container
ID file and exact-CID cleanup-query raw stdout, so this packet cannot
independently replay that cleanup receipt. The run stays a scoped pass with a
custody limitation; no retry was made to repair evidence after the fact. The
previous read-only zero-process snapshots do not resolve shared WSLc ownership,
and Issue #7924 remains STOP/HOLD.

## Repair

The harness now emits one JSON `WSLc cleanup receipt` line after a completed
exact-CID query. It retains the exact container ID, CLI exit code, raw stdout
and stderr strings, and UTC observation time in the captured outer log before
the unique local probe directory is removed. The container query remains
scoped to the generated ID. Uncertain or failed cleanup still preserves the
local probe directory and raw files.

The offline fake-runtime harness passed under Windows PowerShell 5.1. It now
checks that a successful path emits the exact ID and empty-query response while
still deleting the local probe directory. A separate attempt to run that same
harness under PowerShell 7.6.9 stopped before the test at `Add-Type`, because
that host rejects the harness's `ConsoleApplication`/`WindowsApplication`
output kinds; this is a harness-host compatibility limitation, not a WSLc or
product failure. No live WSLc run was repeated after the repair.

## Limits

This result is not a computer-control task, GUI/provider trial, input-release
or recovery result, task-effect observation, Docker comparison, performance
measurement, reliability estimate, or Research Preview acceptance. It does
not clear Issue #7924's owner-reconciliation STOP or the separate #5130 Docker
resource gate.
