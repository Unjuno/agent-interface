# A06 — Explicit interrupt followed by fresh image observation (schema-corrected)

## H/T/D/C/U (fixed before A06 execution)

- **H:** On installed Codex App Server 0.160.0, an explicit interrupt cancels a held inference and permits a new same-thread turn with fresh text and image input to reach the provider mock before the cancelled response is released.
- **T:** Repeat the A05 one-process loopback construction, but encode top-level v2 `UserInput::Image` using `{ "type": "image", "url": <data URI>, "detail": "auto" }`, as specified by the official v2 `UserInput` schema. Use a fresh isolated `CODEX_HOME`, new output directory, and valid 2×2 PNG. Keep all other timing/order criteria from A05. A05 is preserved as HOLD and is not overwritten or counted as an A06 run.
- **D:** PASS only if `turn/interrupt` succeeds, turn 1 completes as `interrupted`, the same-thread fresh-observation turn reaches the mock before response 1 is released, the second request contains the observation text and exact PNG data URI, turn 2 completes, and App Server exits 0. FAIL if the corrected request is accepted but these behavioral conditions fail; HOLD if the harness or transport cannot establish them.
- **C:** Even a PASS is mock transport construction only. It does not establish model comprehension, net latency/token savings, safe V39 cancellation, useful task feedback, earlier physical release, recovery, or gameplay.
- **U:** One construction probe on one Windows host and App Server build; no general latency distribution or provider-frequency estimate.

## Execution identity

Probe ID: A06. A05 remains retained as the original schema-rejection HOLD. Official input schema: <https://github.com/openai/codex/blob/main/codex-rs/app-server-protocol/schema/typescript/v2/UserInput.ts>.

