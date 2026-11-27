# R14 — ten fixed repetitions of held-keyup recovery

## Question and scope

Under the single frozen fault condition used by R13, does the production supervised-Win32 caller repeatedly recover an already-down SHIFT key after its producer blocks at the SHIFT-up backend-send boundary, and retain the release result through the public caller before the three-second monotonic cleanup deadline?

This is a conditional repeatability estimate for this exact fixture and injected fault. It does not test a stall inside the native SendInput implementation or kernel, arbitrary blocked I/O, other keys/apps, stdio transport, task success, MAP01, matched efficiency, or broad reliability.

## Frozen procedure

- Use the authorized local Windows PC; do not access WSLc or Docker.
- Target the existing blank Notepad window HWND 24840738, PID 18100, generation `ff2b6086b6d8dcff988483ce4294eb3962d5864a0941b0e50bd820d8a120636a`.
- Before each trial, require the same generation, SHIFT-up, and empty document. No input is sent if preflight fails.
- Start a fresh public in-process MCP server, operation owner, producer and recovery helpers for each trial.
- Send native SHIFT-down, block the producer before native SHIFT-up, independently observe SHIFT-down, call cancellation once, then collect terminal dispatch and retained result.
- Pass requires terminal action/cancellation both recovered, release confirmed, replay false, same-generation SHIFT-up, empty document, completion before monotonic deadline, and internally consistent `perf_counter_ns` interval. `task_success` must remain null because this is recovery-only.
- Run at most ten trials sequentially. If any terminal state is UNKNOWN, a key remains down, target generation changes, or preflight fails, preserve that result and stop the series before another input. Record any stopped/failed trial in the denominator; do not retry it under the same trial number.
- Preserve each trial's full raw request/reply, screenshot, script, preflight and result; compute per-trial checksums and a parent manifest after the series.

The principal result is successes/completed trials with exact fault definition and an exact binomial interval. Do not combine these repetitions with R11/R12 or other fault conditions.