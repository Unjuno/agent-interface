# MAP01: unchanged versus synthetic pending-turn change

Two predeclared WSLc allocations, fixed order on main a8d430f0f976ede5b7efe44e1b4deb8662ce9082, use a private Xvfb and the same MAP01 setup. Each first cancels held input, verifies release and reviews the binding, then obtains a model decision from a full-screen image. In ai01 no overlay is mapped; in ai02 a synthetic magenta overlay is mapped after the client receives turn acceptance. The host checks its notification queue after acknowledgement and has not observed turn completion. This does not establish the provider's internal inference state. The stale proposal is withheld by the local visual gate before native input; after overlay removal and review, ai02 makes one fresh model call and revalidates.

| Condition | Calls | First 8x8 mean absolute difference | Decision interval | Ammo before / immediate / final | Kills before / immediate / final |
| --- | ---: | ---: | ---: | --- | --- |
| unchanged | 1 | 0 | 3.913 s | 50 / 48 / 48 | 0 / 0 / 0 |
| overlay and replan | 2 | 164.307 (>32 threshold) | 8.200 s | 50 / 49 / 48 | 0 / 0 / 0 |

Both final guarded actions completed; all tested keys were up and owner and host closed. Decision interval is runner monotonic time from observation through decision readiness, including host handshake and gate/review; it excludes final action execution. Input token counts were 12,473 for ai01 and 12,473 + 14,194 for ai02; cached counts and model durations are in `audit-result.json`. The pre-cancelled action may have had an effect; it is not represented as undone. Ammo loss demonstrates game response, not a hit or MAP01 completion.

These are one fixed-order pair, with different model calls, context, cache and game trajectories. They do not estimate general speedup, correctness, provider state, or real-world change detection. The overlay is synthetic; local patch checks do not establish semantic target identity or that all dangerous changes are detected. The first stale action was locally withheld rather than refused by a native input admission. Eight passive observations are finite, not proof that every later effect is absent.

`public.zip` retains conditions, runner, adapter, exchange, native observations, game samples and logs. Private model session/call artifacts are excluded and their SHA-256 hashes recorded in `private-hashes.json`. Run `python audit.py` with Pillow to recompute screenshot patch differences and check observed control flow, release and outcomes. Raw retained evidence may support further analysis; zero kills here requires no success claim.
