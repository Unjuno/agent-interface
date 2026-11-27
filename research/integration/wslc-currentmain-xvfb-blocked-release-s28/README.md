# S28 current-main WSLc private-Xvfb replicate

One preregistered same-condition replicate of S27 at a 3,930 ms pause; no retries. The unique session/container names and conditions are in the preregistration, with machine paths redacted. Only the exact generated container name was queried inside the fresh session; no global inventory or Docker operation was used. The container used network-none mode and read-only inputs.

Result: pass; independent audit 29/29. Both task oracles passed, while the old canceled call stayed UNKNOWN/replay-denied/`task_success=null`. The transaction margin was 4.798 ms. Together S27/S28 provide two scoped synthetic samples, not a hard guarantee or reliability estimate. See `RESULT.md`, `AUDIT.json`, and `POST_CLEANUP.json`. The terminated session's unique storage VHDX remains and is hash-recorded.
