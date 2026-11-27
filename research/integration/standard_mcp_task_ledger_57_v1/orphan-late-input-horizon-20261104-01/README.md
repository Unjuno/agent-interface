# Orphan recovery late-input horizon gate

## Finding

At base `80444fe3a407bfb7aa0aa724b7ace06c74933d5a`, orphan recovery released tracked input, performed one neutral observer readback, and could return `recovered` without running the configured late-input horizon. `OwnedWin32SessionOwner` then cleared its unresolved gate and fenced only the source target generation, allowing a different generation to be admitted while a late request remained possible.

## Change

The source custody record now requires an explicit boolean `late_server_request_possible`. For `true`, recovery remains unresolved unless the supervisor returns a matching recovery receipt with a positive bounded horizon (at most 60 seconds), at least two independently sampled neutral observations, monotonic release/end times covering that horizon, and sample gaps within the configured limit. The supervisor repeats observation against the same operation, target generation, and recovery ID after release. Any nonneutral, mismatched, invalid, late, or incomplete observation returns UNKNOWN; the owner keeps new actions fenced. A verified horizon permits a new target generation, while the original source action remains UNKNOWN and replay stays denied.

## Verification

Windows CPython 3.11.9; focused owner, supervisor-helper, public supervised-Win32 composition, and process-cancellation suites:

- `normal.log`: 105/105 passed; `normal.exit` = 0.
- `optimized.log`: 105/105 passed; `optimized.exit` = 0.
- `git diff --check`: passed.

The retained console logs are line-ending normalized to LF. The focused controls cover missing/nonboolean risk flags, release without horizon evidence, a valid identity-bound horizon, new-generation admission only after that horizon, and a delayed down-state inside the observation horizon. Source action status and replay denial remain unchanged.

## Limits

These are local synthetic/helper tests. They do not inject a real delayed Win32 request, exercise a live GUI or provider, prove physical device-level input neutrality, or qualify WSLc/MAP01. The horizon is a finite observed-state gate under the configured supervisor, not a general proof that arbitrary external processes cannot inject input.
