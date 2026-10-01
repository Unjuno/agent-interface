# Independent source and maintenance-test review

No blocking findings remained at the reviewed source hashes below. This is an
independent review of the narrow precedence adapter and its synthetic tests,
not a review or validation of Formal06's experimental eligibility.

## Static finding and resolution

The initial test helper used reason membership assertions. The reviewer asked
for exact ordered reason-list equality so unrelated extra reasons cannot satisfy
the asserted contract. The test helper was strengthened; swapped-direction now
expects exactly both row-order reasons and each other named evidence mutation
expects exactly its single reason. Gate and fixture sources did not change.
The separate `review_strengthened_green` evidence retains the author's 17/17
recheck. Initial red and green reports remain unchanged.

## Independent batch 1: preserved pre-import failure

- Process exit: 1
- Stage: source-hash guard, before any repository import or test
- Expected README SHA-256: `1db912004503ab7e318739f3eb280d870ae4ab83b2ec3c4cf25565bc854b3332`
- Observed README SHA-256: `b77f9602453aa50ef64541d4349e6a8f411ba944b82585bd91aa415befd48ad6`
- All executable/dependency hashes matched
- Repository imports: 0; tests executed: 0

Cause: the author concurrently added the README paragraph recording the
exact-reason test strengthening. No executable source changed. Files were then
held stable. The reviewer did not automatically retry; the next independent
batch received separate explicit authorization after review of that text delta.
This was an ordinary maintenance source-identity check, not an experimental STOP
or a Formal06 retry.

## Independent batch 2: reviewed stable artifact

- Process exit: 0
- Test methods: 17
- Failures: 0; errors: 0; skips: 0; warnings: none
- Unittest duration: 0.016 seconds
- Import plus suite duration: 0.020624250000309985 seconds
- Python: 3.12.14
- CPU affinity: `[0]`
- Address-space limit: 536,870,912 bytes (soft and hard)
- CPU-time limit: 60 seconds (soft and hard)
- Wall alarm: 60 seconds
- Sources unchanged across the batch: true

Only the selected new in-memory tests and the exact predecessor pure function
were imported/run. No old CLI, historical test suite, runner, child process,
native/GUI/provider/model/network work, source mutation or GitHub write occurred
in the independent review. Repository-wide tests and CI remain unrun.

## Reviewed identities

| File | SHA-256 |
| --- | --- |
| `gate.py` | `9ba52c993ee817ed6402f65cfcc616daf7c3b76d57b7a27fb73041f5b2d0b756` |
| `fixtures.py` | `0d0c67ed39ca8eb4565ff64aa13963008651cba8aa6ace4cf4c1b8b14dbd272e` |
| `test_gate.py` | `e073aee1ff1ed1bd5708a5930027db651e3f9d7435169b1a7284e25bea68d3f7` |
| `README.md` | `b77f9602453aa50ef64541d4349e6a8f411ba944b82585bd91aa415befd48ad6` |
| predecessor `audit.py` | `028eb71821cdcf162f1cc0efed722351bd310c7261564c2ba904ae22f721508a` |

Predecessor Git blob: `e29c897961668d4607b2d2b5608c7ab17554b155`; 12,609 bytes.
It is an existing unchanged repository dependency, not a file to republish.

This record transcribes the independent review's returned measurements and
findings. The reviewer did not generate a separate on-disk test log. The retained
author logs and this independently reported result have distinct provenance.

Formal06 remains `STOP_PROTOCOL_DEVIATION` and diagnostic-only. The adapter
only prioritizes reasons already emitted by that pinned auditor; it does not
repair malformed-input behavior, fill missing validation, authenticate bytes,
or establish preregistration.
