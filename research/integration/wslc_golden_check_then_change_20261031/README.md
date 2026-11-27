# WSLc checked target changed before click

One network-isolated no-model Chromium trial on main `f97532d7a1e877a61af1d11aaea8b1ddb2b6462e` minted a field reference on layout A and checked it as `VALID` and eligible. The driver then navigated to layout B before submitting a click against the old reference. The click terminated `needs_decision` with zero pointer admissions and a verified empty release. This is a sequential controlled check/change/click case, not a stress test of all concurrent races.

The driver explicitly minted fresh layout-B references from known points and completed task 4; independent history recorded exactly one correct submission. All 14 program releases were verified with no held inputs. The six-task evaluator correctly remained false. All 2029 source hashes matched, exact container inspection returned not found, and raw.zip passed ZIP integrity verification. Network was disabled except the isolated loopback fixture.

This does not establish model-guided recovery, unknown-effect recovery, latency/token economics, broad reliability, or MAP01 completion. The checked client explicitly selected the installed Chromium path; exact mounted source hashes are retained.
