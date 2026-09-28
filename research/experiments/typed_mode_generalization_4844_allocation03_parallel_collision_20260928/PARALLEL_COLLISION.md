# Parallel allocation collision

This evidence bundle records a completed local formal execution for allocation `typed-mode-4844-successor-20260928-03` under source commit `2a96313df5edffb1f7d180bee6c142917ac79e37`.

At publication time, another agent's Issue #5189 and remote branch claimed the same allocation ID, original v3 path, and formal seed pair 484431/484432, but a different frozen implementation. The peer's freeze commit is `fcf06f1bf4ce85952658cf9f53e38899dfc51530`, timestamped `2026-09-28T13:22:33+09:00`; this runner started at `2026-09-28T13:18:08.7893132+09:00`. The shared branch was not overwritten. The peer was notified that the pair had already been consumed and must not be run again.

This result is preserved for provenance and review, not as an independent replication of the peer implementation. Do not pool results across the two source implementations. The raw evidence SHA-256 is `51d9c7fed88a5a491a7e1f4fb5a33349ffe58c486a44a946b573a1a18838e300`; the audited disposition is `HOLD_COVERAGE_TRADEOFF`. Any new confirmatory experiment requires a fresh allocation and new seeds.
