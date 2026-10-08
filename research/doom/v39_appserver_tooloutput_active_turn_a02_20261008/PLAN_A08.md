# A08 — Inspect readable thread history after an interrupted turn's late response

## H/T/D/C/U (fixed before A08 execution)

- **H:** After turn 1 is interrupted, turn 2 completes from fresh text+PNG, and the mock successfully sends turn 1's delayed stale response, `thread/read` with `includeTurns: true` contains the fresh response and excludes the stale sentinel.
- **T:** Repeat the A07 barrier-controlled loopback sequence under a non-ephemeral isolated thread. After the late response write has a terminal outcome and both turns complete, send one `thread/read` request for that same thread with `includeTurns: true`. Inspect the returned JSON for unique fresh/stale output sentinels and turn IDs/statuses. No retries, external provider, GUI, game, or OS input. Save only summarized checks, not the full thread payload.
- **D:** PASS only if the read succeeds, the returned history contains the replacement turn's unique fresh sentinel, contains no stale sentinel, and both turns remain exactly once completed (`interrupted` then `completed`); prior ordering, image, process-exit, and stale-notification criteria must also pass. FAIL if readable history contains the stale sentinel; HOLD if thread/read is unsupported or the returned history omits the fresh sentinel needed to prove coverage.
- **C:** This checks only App Server's readable persisted history in one deterministic mock schedule. It does not prove every private internal store, real-provider behavior, task-effect safety, net latency, V39 runtime integration, or gameplay.
- **U:** One installed App Server build on Windows; no frequency or cross-platform claim.

## Execution identity

Probe ID: A08. Output directory: `results/a08-thread-history`. `thread/read` schema reference: <https://github.com/openai/codex/blob/main/codex-rs/app-server-protocol/schema/json/v2/ThreadReadParams.json>.
