# Pre-freeze construction record

- Confirmed the pinned Python runtime imports Pillow 12.3.0; system Python lacks Pillow. No dependency was installed.
- Direct production-monitor probe against current-main source `51ceed1e…` returned no event for health 89, no event for exact hard floor 88, and `health:below_hard_minimum` for health 87. This resolved the initially assumed inclusive boundary: the implementation deliberately invalidates only below the floor.
- First pending-loop prototype stopped because it expected health 88 to invalidate. The terminal then followed the non-invalidated path. This was an incorrect test expectation, not a source failure.
- The corrected sequence added health 87 but its first harness version failed to enqueue that third observation. The exact production loop therefore received the terminal before an invalidation and reached an unavailable test stub. The harness now enqueues all three ordered samples.
- Corrected pre-freeze construction execution passed: 89 and 88 preserved the cover, 87 invalidated, the cover cancellation preceded planner interruption, and the final admission rejected the answer-eligible fake result. The output was written only to `/tmp/v39-health-boundary-construction.json` and is not a retained result.

These are construction findings. The frozen candidate has not yet been invoked.
