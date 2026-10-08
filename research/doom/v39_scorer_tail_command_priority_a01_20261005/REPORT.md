# Report — scorer tail command readiness under callback overrun

**Disposition:** `FAIL_READY_COMMAND_STARVATION_ON_SAMPLE_OVERRUN` (synthetic source-boundary construction). The adapter's stated ready-command behavior is bypassed when a synchronous scorer call lasts longer than its sample period: both deterministic overrun cases completed four more scorer samples and reached the 100 ms deadline without a readiness poll. The fast control returned `command_ready` after one poll.

The independent audit reconstructed all result fields from the frozen case definition and verified all three source hashes (7/7 checks). Four tests passed, including mutations to the sample count, readiness-poll count, and disposition. Candidate and audit output are retained as `RESULT.json` and `AUDIT.json`; exact source/config pins are in `FREEZE.json`.

This finding applies only to the source-pinned adapter behavior and the deterministic fake callbacks. It did not test real pipe readiness, command handling, gameplay, keys, safety, production latency, or task benefit. No formal/live allocation was used. PR #7692 was reported at head `0c3627d63072b89d1c769fd0048e93baf157f5c7` in the preceding inspection; this turn's unauthenticated `gh` prevented confirming whether the remote head changed. The retained adapter raw still shows the same conditional readiness poll.

## Suggested repair

Poll command readiness before every scorer callback, including iterations where sampling is already due after a callback overrun. Preserve the no-consumption behavior. Add deterministic tests for ready-at-entry and readiness becoming true during an overrun; ensure a ready command yields `command_ready` before the next scorer call.
