# A05 — Explicitly interrupt a pending inference, then start with fresh observation

## H/T/D/C/U (fixed before the probe)

- **H:** On installed Codex App Server 0.160.0, `turn/interrupt` with the active `threadId` and `turnId` cancels an open inference quickly enough to complete that turn as interrupted and admit a new turn carrying current text and image before the held mock response is released.
- **T:** Use one isolated app-server process, a loopback-only mock Responses API, and a valid generated 2×2 RGB PNG. Hold the first mock response open, send `turn/interrupt` for the returned active turn, wait for its terminal notification, then start a new turn with the observation. Record request ordering, text/image delivery, both turn statuses, transport closure, and process exits. No retries, external provider, GUI, game, or OS input.
- **D:** PASS only if the interrupt request succeeds, the first turn ends `interrupted`, the fresh-observation turn starts on the same thread and reaches the mock API before the first response is released, that API request contains the observation text and PNG, the second turn completes, and the app-server exits 0. FAIL if these observed conditions are false; HOLD if the harness cannot establish order or a process/transport failure makes state ambiguous.
- **C:** A deterministic mock does not establish model comprehension, an improved answer, net latency or token savings, safe interruption in V39, earlier per-key release, useful feedback, recovery, or live gameplay. Cancellation may discard useful work and a second inference adds its own cost.
- **U:** This is one construction probe on one installed App Server build and Windows host; no timing distribution or production/provider frequency is estimated.

## Execution identity

Probe ID: A05. The first outcome is written only to `results/a05-interrupt` and preserved unchanged after execution.

