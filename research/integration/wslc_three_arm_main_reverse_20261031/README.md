# Current-main WSLc Chromium: reverse-order comparison

This prospectively fixed follow-up reverses the prior block's order from persistent → ephemeral → plain to plain → ephemeral → persistent. It uses the same 2,092 exact-byte-hashed mounted source files, same pinned image, model, seed 991036, tasks and experimental host bridge. The preceding snapshot was checked against main `3dfd373c` after CRLF normalization; the follow-up main `49eae27e` added only the preceding evidence packet, with no relevant runtime or live-control changes. Each arm ran in a separate WSLc container and fresh model session.

| Arm | Measured lifecycle | Calls: preflight + tasks | Input tokens (cached subset) | Output tokens | Exact tasks | Neutral terminal events |
|---|---:|---:|---:|---:|---:|---:|
| plain | 45.627 s | 1 + 6 | 104,070 (80,640) | 466 | 6/6 | 18 |
| ephemeral | 48.020 s | 1 + 6 | 105,400 (83,456) | 848 | 6/6 | 48 |
| persistent | 37.537 s | 1 + 2 | 36,850 (20,608) | 394 | 6/6 | 57 |

All 18 submissions matched the independent fixture history; all 123 recorded terminal releases were neutral. The source hashes, task IDs, layouts and expected tokens match the prior block, while all 17 preflight/task call IDs in this block are disjoint from its 17 call IDs. In this block persistent had 64.59% fewer recorded input tokens and a 17.73% shorter measured lifecycle than plain. In the preceding block the corresponding differences were 64.54% and 7.85%. Cached tokens are part of input; output is separate and provider billing is unknown.

The measured lifecycle includes preflight, schema validation, model-host and container/app startup, tasks, scoring, cleanup and polling; source preparation, launcher bootstrap, image build/pull and postrun audit are excluded. The separately retained earlier startup failure's preflight tokens are not included. The two blocks used the same fixture seed and ran sequentially; changing order does not control host load, cache, provider timing or the differing tool behavior. Two single observations per arm cannot establish a general speedup or reliability estimate. This is one synthetic Chromium domain, not a second-domain comparison or MAP01 result; issue 57 remains open.

`public.zip` retains the frozen scripts, conditions, schemas, call/usage records, screenshots, independent histories, input-release events, timers, source verification and cleanup. Six private model-protocol journals are hash-indexed separately. The source and image bytes are not included, and host/provider dependencies are not fully frozen. `python audit.py` verifies this packet and compares its task signatures, source hash manifest and call IDs with the preceding packet; it does not independently reconstruct the omitted source. No permission-retry or host-failure marker occurred in this block.
