# Caller integration candidate A01 — 2026-11-28

## Question and disposition

Can a strict post-load clock proof be refreshed after a slow owned-backend startup without weakening the clock, display, neutral-input, or fixture identity checks?

**Local construction result: PASS.** The caller re-runs the full proof against the same game object, session object, and exact loaded fixture tic after backend startup. The gate records the second proof separately and does not grant authority. It still refuses a stale first input until the new proof passes.

## Frozen basis and checks

- Base `origin/main`: `8b6fb7ea8be249731c69c6a9e45d9df59329e485`.
- Runtime: installed `Ubuntu` WSL distribution and pinned Python at `/home/user/.cache/agent-interface-map01-20261103/bin/python`.
- Six related suites: post-load clock gate, V39 caller, V15/V12 session, candidate setup evidence, candidate setup synthetic, and session retirement boundary.
- Normal mode: 85 tests passed; exact output is `normal.stdout.log`.
- Optimized mode (`-O`): 85 tests passed; exact output is `optimized.stdout.log`.
- `git diff --check` was clean before this test packet was added.

The checks cover stale-proof refusal, same-generation revalidation, candidate-evidence hash binding, argv propagation, typed authority-reducing invalidation, and existing release/retirement boundaries.

## Scope limits

This is local regression evidence only. It did not start Doom, call a model, send OS input, or consume a new live allocation. A separate retained Astra run exercised the revalidation path, but remained unfinished and did not establish threat-response effectiveness, ammo feedback, physical-target release, or a clean Astra/Terra comparison. That allocation's raw package is kept separate from this implementation candidate; this result does not depend on it.

This candidate repairs a construction blocker for later real-time-control research; it does not satisfy Issue #59's live threat-exposure or MAP01 exit gate.
