# S19 result — WSLc runner stopped before test body

**FAIL_OR_UNKNOWN (pre-test harness/setup).** The exact generated-name preflight passed in a new WSLc 3.0.3.0 session. One digest-pinned Python image pull and one network-disabled container creation succeeded. The runner verified all 31 wheel hashes, then pip returned exit 1 because it requested `/wheels/requirements-cp312.lock`, while the mounted immutable wheelhouse contains `requirements-s15-cp312.lock`. No unittest started, no Fake X interaction or raw candidate receipt occurred, and this attempt was not retried.

The exact container deletion, image deletion, and session termination receipts all passed. The unique 213,909,504-byte VHDX remains at the exact path in `STORAGE-CLEANUP-STATUS.json`, with its SHA-256 retained. S19 therefore classifies a runner path defect only; it says nothing about relay cancellation, release, or computer control.

A fresh attempt may correct the lockfile path after this failure is preserved. Its identifier and preregistration must be distinct; it cannot replace or pool S19.
