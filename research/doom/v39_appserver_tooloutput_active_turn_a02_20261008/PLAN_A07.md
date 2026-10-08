# A07 — Verify that a late response from an interrupted turn stays discarded

## H/T/D/C/U (fixed before A07 execution)

- **H:** After App Server marks turn 1 interrupted and admits an observation-driven turn 2, a deliberately delayed final response from turn 1 cannot reappear as output or complete/alter either turn.
- **T:** On App Server 0.160.0, hold mock Responses request 1 open, interrupt turn 1, start turn 2 with fresh text and a valid PNG, and wait until its provider request is observed. Only then release request 1 with a unique stale-response sentinel. Retain all App Server JSON-RPC notifications, per-turn completion/status counts, mock ordering, socket-write result, and process exits. One isolated process, loopback only, no retries, external provider, GUI, game, or OS input.
- **D:** PASS only if turn 1 has exactly one `turn/completed` with status `interrupted`, turn 2 has exactly one `turn/completed` with status `completed`, request 2 is observed before request 1 is released and contains the text/PNG, and after release the stale response has a terminal transport outcome (fully written, or explicit peer-close/reset) while its unique sentinel never appears in App Server output; both processes must exit 0. FAIL if the stale sentinel is surfaced or a turn status/count violates these conditions; HOLD if the stale response or notification state cannot be observed or its transport outcome is ambiguous.
- **C:** This tests stale-output isolation in one deterministic mock schedule only. It does not prove real provider cancellation, controller safety, decision quality, lower end-to-end latency, useful feedback, per-key release, recovery, or gameplay.
- **U:** One Windows host and one installed App Server build; no frequency, timing distribution, or cross-platform claim.

## Execution identity

Probe ID: A07. Output directory: `results/a07-late-response`. The stale assistant text is uniquely tagged `A07_STALE_AFTER_INTERRUPT` and is absent from the request input.

