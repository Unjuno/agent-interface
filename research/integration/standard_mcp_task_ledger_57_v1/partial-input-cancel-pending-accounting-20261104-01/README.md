# Public pending-cancel composition with provider ledger — 2026-11-04

## Question and test boundary

Can the public computer-control path retain custody when cancellation is still pending after partial input, and can the caller retrieve the same operation without replay while preserving the provider attempt and raw control receipts?

This is a synthetic offline composition check. One fake provider attempt (reported fixture usage: 61 input, 13 output tokens; cached input 8 is a subset) submits one public `interface_guarded_compiled` call. Fake X holds keycode 1 down at its input synchronization boundary. A test-owned cleanup supervisor gate keeps cancellation pending long enough for the public response to return `pending`; the test then releases the gate and polls `interface_results` against the original call ID and cancellation operation ID.

## Result

Both normal and optimized Python passed 1/1 in Windows Python 3.11 and in the pinned Docker image. Docker exited 0. In each retained Docker run:

- initial cancel response: `pending` for the original compiled call and cancellation operation;
- results polling: same call ID, statuses `pending` then `completed`;
- provider ledger: exactly one synthetic model attempt and one compiled request, 61 input / 13 output / 8 cached-input-subset / 2 reasoning-output fixture tokens;
- control calls retained: observe, mint, compiled, cancel, two result polls, close;
- no second model attempt, direct input, recovery input, or replay;
- cleanup supervisor's Fake X record changes held key `[1]` to no keys down and records a KeyRelease;
- the runtime cancellation receipt still says `cleanup_status=UNKNOWN`, `release_confirmed=false`, `task_success=null`, `replay_allowed=false`.

The independent Fake X cleanup record is not promoted into a runtime release confirmation. This test demonstrates custody and accounting through the pending response, not successful task completion or recovery.

## Preserved runs

`generic-public-cancel-poll-04/` is the final deterministic pass, with command, pinned image/runtime identity, normal and optimized raw stdout, exit codes, provider ledgers, request/response bytes, reconciled events, key-down snapshot, and independent Fake X cleanup record. Its two `joined-result.json` files directly link call IDs and operation IDs across the pending and terminal receipts.

Earlier trials are retained separately and are not counted in the final result:

- `invocation-discovery-failure-01/`: unittest discovery invocation rejected the non-package directory before test execution.
- `generic-public-cancel-poll-01/`: the generic path completed, but cancellation finished before its first response; this did not exercise pending.
- `generic-public-cancel-poll-02-missing-asyncio/`: the forced pending branch reached the polling delay but the test lacked an `asyncio` import.
- `generic-public-cancel-poll-03/`: passed after the import fix; the final rerun adds explicit assertions tying the compiled event to the model attempt and every unlinked control result to the same call ID.
- `assertion-run-*` folders preserve the earlier Calc-profile wrapper exploration, including timing variation and a timeout-boundary failure. That path was replaced by a smaller generic public compiled fixture; its outcomes are not pooled with the final result.

## Conditions and limitations

Docker Engine 29.8.1; image `agent-interface-xvfb-mcp:late-input-r19`, ID `sha256:bd191d30ea94871a1d3ca717252cd07a276e8ef7d1bcb4a130b63935ce075425`; network disabled; 2 CPUs, 4 GiB memory and total memory+swap, 256 PIDs; source mounted read-only. The two modes each ran only the new focused test. Source was current checkout `b7fe79a9e739ac31079bea4d677ea3a8cf025ada` plus the uncommitted test source whose SHA-256 is recorded in `generic-public-cancel-poll-03/conditions.json`.

All provider usage is synthetic fixture data; there was no provider/model request, live GUI action, or user-facing task effect. The test does not establish verified runtime release after cancellation, fresh-attempt recovery, live Calc, WSLc/MAP01, comparative efficiency, or general reliability. The broader cold/warm/invalidation/repair and second-domain gates in Issue #57 remain open.

`SHA256SUMS.txt` hashes every other file in this packet. Packet-specific `.gitattributes` disables text conversion so retained raw bytes can be checked against committed blobs.
