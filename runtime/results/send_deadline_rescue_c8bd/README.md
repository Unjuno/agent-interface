# Send-deadline rescue intake and composition boundary

Original PR #6965, source `c8bdf4de32f5f09146ce295ab0629dc3e40fc62b`.
V1/V2/V3 inert evidence packages are restored unchanged. Original science,
RED/GREEN, publication/construction failures and withdrawn V2 adoption remain.
The active client is a composition, not a wholesale old-branch replacement.
The native-suite runner remains unchanged.

Fresh comparison against main `e14246bcb` identifies incompatible wholesale
application: original branch would remove explicit UTF-8 Popen decoding,
Boolean reply-ID rejection, reader-alive timeout and bounded journal-lock close.
Its native-suite image would remove existing reader/journal, reply-ID and UTF-8
registrations. Those main changes must be preserved in any production composition.
The useful nonblocking send/deadline/sticky uncertainty/known EOF and frozen-wire
journal changes require composed tests, not original 32/32 evidence alone.

This intake is not a substitute for that production rescue. No new native trial,
formal allocation, implementation correctness, content quorum/current-tree
certificate or sender handoff is inferred. Original Windows/custom-stream,
concurrent EOF and whole-call deadline limits remain. Current source/main
integration and local CI are still pending; source ref
must not be retired yet.

Fresh RED: original unchanged send-deadline test restored to active test path;
`test_request_spends_one_budget_on_send_and_response_wait` against unchanged
main client exits 1, one assertion failure: supplied deadline `[None]` instead
of `[0.05]`. Full `red-budget.log` retained. This controlled-clock/mocked-send
test establishes missing budget propagation, not a native pipe deadline bound.
That RED was recorded before the production composition. Real-pipe and composed
existing UTF-8/ID/close regressions remain necessary before integration.

Fresh archive checksum checks PASS: V1 159, V2 35, V3 52 targets (246 total),
zero mismatches. This verifies original public bytes, not historical execution.
Two owned-pipe tests also fail against unchanged main due to unsupported
`deadline` keyword; full `red-pipes.log` retains both errors. They do not yet
demonstrate actual saturation timing because the call is refused before writing.

Composition preserves main's explicit UTF-8, Boolean-ID rejection, reader-alive
timeout, and bounded journal-close implementation. Restored source runtime test
call expectation is updated to include main's explicit UTF-8 parameter. Existing
EOF tests now require an admitted request before its reply; unsolicited future-ID
responses cannot authorize a new send after known EOF. UTF-8 tests now use an
owned child process which observes the actual JSONL request before replying,
with the process factory's CP932 default retained to detect encoding regressions.
First package-import errors, subsequent 19-test failures, and initial composed
47-test run's three encoding-call expectation failures are retained, not erased.
