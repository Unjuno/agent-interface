# ExecutorV12 partial-release composition A01

The pre-fix owner loses its completed F8 release record when the second
`KeyRelease` raises during owner expiry. The A02 owner candidate preserves
the confirmed F8 UP in one explicitly unverified partial record. ExecutorV12
then retries the remaining F9 release at its terminal cleanup barrier,
publishes F9's confirmed UP, and emits one `expired` terminal with verified
neutral state. A subsequent DOWN is rejected without injection because the
owner remains faulted.

Paired outcome: baseline RED (1 test failed at the expected missing partial
record); candidate normal and optimized GREEN (1 test passed in each, exit 0).
Source identities and full
outputs are in `EXECUTOR_V12_FREEZE.json`, `EXECUTOR_V12_SOURCE_LOCK.json`,
`EXECUTOR_V12_RED.txt`, `EXECUTOR_V12_GREEN.txt`, and
`executor-v12-partial-release-raw.json`.

The integration source files for ExecutorV12, its lease, and owner harness
match main `e7c916989da30741b00c234efd264067d0899851` byte-for-byte. The
owner/bridge candidates and test harness are pinned to PR #7864 head
`de9a37d5d0eca2b258982b02f2fb2a401bba293c`; baseline owner source is the
exact parent #7847 source. This remains fake-display construction evidence,
not live input or application-effect evidence.
