# A09 — Revalidate readable-history result with corrected runner exit gate

## H/T/D/C/U (fixed before A09 execution)

- **H:** An interrupted turn's delayed stale response remains absent from both App Server notifications and `thread/read(includeTurns: true)` after a same-thread replacement turn completes with fresh text+PNG.
- **T:** Repeat A08's single loopback-only, non-ephemeral-thread sequence in a new process and output directory. A08's retained JSON result met the behavioral checks, but the runner returned 1 because its final condition compared against the A07 disposition label. A09 fixes only that runner disposition comparison and uses A09-specific turn/sentinel names. After late response and both turn completions, read the same thread and save only summarized history predicates. No retries, external provider, GUI, game, or OS input.
- **D:** PASS only if the turn and ordering conditions, successful `thread/read`, fresh sentinel present, stale sentinel absent, notification isolation, and both App Server and runner exit 0. FAIL if stale content appears or an accepted behavior condition is contradicted; HOLD if history coverage or transport state is unavailable/ambiguous.
- **C:** This is a corrected construction replay, not an independent additional sample. It tests only readable App Server history and notifications under one deterministic mock schedule; no V39 safety, real-provider behavior, latency benefit, useful feedback, per-key release, recovery, or gameplay claim.
- **U:** One Windows host and one installed App Server build.

## Execution identity

Probe ID: A09. A08 source, result, runner exit, and failed auditor remain unchanged. Output directory: `results/a09-thread-history`.
