# Send-deadline rescue intake and composition boundary

Original PR #6965, source `c8bdf4de32f5f09146ce295ab0629dc3e40fc62b`.
V1/V2/V3 inert evidence packages are restored unchanged. Original science,
RED/GREEN, publication/construction failures and withdrawn V2 adoption remain.
The active client is a composition, not a wholesale old-branch replacement.
The native-suite runner remains unchanged.
The later high-FD repair additively registers all four new suites; existing
runner modules remain intact (no wholesale old-branch runner replacement).

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

Fresh composed relevant tests: 47 normal and 47 optimized PASS on local macOS
Python 3.12. The send test's wait context now advances the fake clock for both
select and sleep, addressing concrete CONTENT_CHANGES 5969663539/5971267227.
This does not transfer prior Windows results or count as Windows qualification.

Full native contract runner remains FAIL on both pinned main e14246bcb and
candidate 4b93f4194: protocol 445 tests, 4 failures, 6 errors, 5 skips; harness
205 tests, 31 errors. All 41 ordered FAIL/ERROR headers are identical. Both full
logs are retained with every failing test name and traceback. This comparison
shows no additional failing header, not full-suite PASS or equivalent behavior.
The clock-context-only follow-up is f6ba64192 and has fresh normal/optimized
47-test checks. No GUI/model/formal producer replay is represented here.

Adoption HOLD remains: original fixed committee's two V3 CONTENT_CHANGES are not
approval; exact new composition needs fresh review/current-tree applicability,
live platform/checks/rights and authorized sender disposition. No main merge or
source-ref deletion has happened in this rescue. Original first outcomes and
the 249 inert source files remain unchanged.

Local Analysis Index CI at f6ba64192 exits 0: 43 run steps, failures=[];
full local-ci.log retained. This is the scoped workflow, not all repository
workflows, full native-suite PASS, actual Windows or live GUI qualification.

## High-descriptor follow-up (nonvoting technical review)

Fresh first RED on an owned saturated POSIX pipe, F_DUPFD >=2048: expected
TimeoutError cause, actual ValueError("filedescriptor out of range in select()").
Only one new descriptor allocated, no unrelated descriptors overwritten.
POSIX wait now uses poll/POLLOUT, with individual waits capped at 1000ms to avoid
millisecond integer overflow for large valid timeouts. Windows sleep unchanged.
Reference: https://docs.python.org/3/library/select.html#select.poll.

After repair: 48 normal and 48 optimized methods PASS (no skips). Cancellation
test now checks the same interrupted client refuses followup without another
write/journal call. Four send-related suites are additively selected by the
native runner. Fresh full native output still FAIL; baseline/new failure/error
headers remain identical. This is not a full-suite or Windows result.
First RED and complete new normal/O/native logs are retained. Original archive
bytes/first outcomes and fixed committee conditions remain untouched.
