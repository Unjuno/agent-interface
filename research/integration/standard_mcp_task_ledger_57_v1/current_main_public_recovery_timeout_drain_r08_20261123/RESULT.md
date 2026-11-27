# R08 result: deterministic callback Future drain passed

Disposition: **PASS FOR THE SCOPED TEST-HARNESS LIFECYCLE**. Normal and optimized runs both exited 0 and passed the focused unittest (1/1 each).

Both samples held the fake observation worker beyond the unchanged 8-second caller Future timeout. The Future was still pending at timeout, the exact call ID was read from the current-server read-only call list, and the callback was released exactly once. The same Future then completed within the 30-second bound. The exact report existed with `status=returned`, no `.report.json.tmp` remained, and the exact-call readback retained the same call ID. The test exposed no input or replay; the one observer ran once. TemporaryDirectory teardown completed without a file-in-use error.

This demonstrates that explicit tracking and drain can safely handle this deterministic delayed **observation** callback in the local test harness. It does not establish production reliability and does not cover the separate detached dispatch worker/report-finalization timing found in R09.

Conditions, source hashes, raw logs, exit codes, preflight write probe, and SHA-256 manifest are retained in this packet.
