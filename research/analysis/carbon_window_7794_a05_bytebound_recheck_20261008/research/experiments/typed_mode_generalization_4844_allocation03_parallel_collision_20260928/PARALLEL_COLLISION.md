# Parallel allocation collision

This evidence bundle records the first completed formal execution under Issue #5184's allocation `typed-mode-4844-successor-20260928-03`, source commit `2a96313df5edffb1f7d180bee6c142917ac79e37`. That source commit is timestamped `2026-09-28 13:16:53+09:00`; its runner started at `13:18:08.789+09:00`.

Another agent concurrently created Issue #5189 and a different frozen implementation with the same allocation ID, path, and seeds 484431/484432. Its freeze commit `fcf06f1bf4ce85952658cf9f53e38899dfc51530` is timestamped `13:22:33+09:00`. The peer's runner container inspect records `Created=2026-09-28T04:24:55.869523368Z` and `StartedAt=2026-09-28T04:24:56.106325311Z` (13:24:56+09:00), after this run completed. The peer raw SHA is `74dfede0db4676fdaf0d6385c625c2c3731a75ffe8572d7f7a45dbc060e42a22`; peer runner/auditor IDs are `e3b9b407bbbb71b7f70663417fab548d273db7f6906e4da85a76143efc93c4cf` / `48bd68fdee2e2276521212c522760c5eeccb8f7ed3a5238e859f64325d8a1626`. The peer reconciliation, merged in PR #5191, classifies that later lane as `STOP_DUPLICATE_FORMAL_SEED_COLLISION` because this #5184 execution had already consumed the registered pair.

Our raw SHA-256 is `51d9c7fed88a5a491a7e1f4fb5a33349ffe58c486a44a946b573a1a18838e300`, disposition `HOLD_COVERAGE_TRADEOFF`. The peer result is preserved separately in PR #5191 but is not an independent replicate and is not pooled or averaged with this result. The same integer seeds across different implementations do not establish matched row-level data. Any confirmatory study requires a new allocation ID, source/path, and fresh seeds.

The shared v3 branch/path was never overwritten. This bundle was relocated to a unique evidence path after the collision was discovered.
