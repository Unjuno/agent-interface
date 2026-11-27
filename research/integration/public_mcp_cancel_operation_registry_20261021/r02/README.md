# r02 — terminal receipt binds operation and owner generation

This recheck follows r01 and changes no test conditions. The runtime now writes
the full cancellation subrecord to `cancellation.json`, including operation ID,
admission/deadline timestamps, owner generation, terminal result and status.
The test independently compares the file's operation ID and generation with
the `interface_results` record.

Both focused suites passed 77/77 in normal and optimized Python. Exact commands,
stdout/stderr, exit codes, conditions and source hashes captured at r02 are
preserved in `source-hashes-at-run.txt`. Packet `SHA256SUMS` binds the r02
conditions and outputs. Later source changes mean the fingerprints are
historical; r04 binds the current source. The remaining scope limits in the
parent packet are unchanged:
no operation-wide deadline, prestarted process, live X11/physical release,
independent task effect, WSLc, MAP01, matched efficiency, or reliability result.
