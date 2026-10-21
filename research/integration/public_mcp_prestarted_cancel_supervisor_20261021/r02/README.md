# r02 targeted blocked-helper confirmation

The single public-MCP blocked-helper test passed in normal Python (5.080 s)
and optimized Python (5.068 s). Its assertion reads the retained terminal
cancellation receipt and requires `owner_client_disconnect.worker_retired ==
true`, while the independent Fake X oracle remains down with zero accepted
effects. Cancel response was 296 ms; 13 event-loop heartbeats were serviced.
The result remains cleanup UNKNOWN, `release_confirmed=false`,
`task_success=null`, and replay denied.

Conditions and source fingerprints are in this directory. The raw stdout and
stderr plus exit codes are retained. This confirms only the local Fake X
construction path and does not bound OS process termination in general.

The r02 source fingerprint includes the r01 checksum-manifest hash as it
existed at r02 execution; r01's manifest was later extended to add its exact
test-source snapshot. The r01 test-source snapshot itself is present and its
SHA-256 matches the r01 run fingerprint.
