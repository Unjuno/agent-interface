# Issue #5791 T0 preregistration — local Docker

## H/T/D/C/U

- **H:** Receipt-aware anti-windup can prevent correction windup/over-effect after blocked or ambiguous delivery, but may add no value over a simple queue cap where semantic effects are promptly known.
- **T:** Execute the finite fixture once across unrestricted accumulation, transport-ACK queue cap, and receipt-aware anti-windup for five frozen cases: explicit integrator saturation/release, transport ACK before semantic effect, no-integrator negative control, goal-generation change during block, and mandatory cancel bypass. Independent oracle checks all 15 policy/case rows. No model, GUI, OS input, or external service.
- **D:** `PASS_METHOD_SCOPED` only for planted mechanism/oracle integrity if the auditor reconstructs expected overshoot, duplicates, UNKNOWN, generation invalidation and immediate critical cancel, and the no-integrator negative control has no policy difference. H value requires C to improve over both A and B on eligible cases with no worse final error and no safety delay. If B equals C on known-saturation traces, record the simpler-cap counter-hypothesis; this fixture cannot establish live benefit.
- **C:** Idempotency, a bounded one-slot queue, generation cancellation, or fresh effect observation may suffice. Repeated commands without explicit accumulated controller state are not evidence of windup.
- **U:** Everything is synthetic and deterministic. No LLM planner is assumed to be PID; no real runtime latent state, live GUI effect, deployment frequency, safety rate, latency benefit, or product claim follows.

## Freeze/run policy

Source/fixture hashes are recorded in `FREEZE.json` before Docker execution. Candidate and independent auditor run once each in separate `python:3.12-slim` containers pinned by digest, network none, 1 CPU, 256 MiB, pids 64. Preserve first outcomes; no retry.
