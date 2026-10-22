# Issue 59 — matched-v2 planner-window boundary repair

Status: local source repair and regression tests pass; no formal game/model allocation rerun.

## Provenance and scope

Compared with current main `9590ee9e0c74f7438306e8efb48b2af813f7a86b`; runner blob `59c071c3453b516ff370e1b3533511b1f3ce486f`. The initial finding is retained in PR #7576 as `FAIL_BOUNDARY_CONTAMINATION`. The frozen matched-v2 allocation remains untouched.

This repair corrects measurement-window construction only. It does not resolve the independent typed-observation UNKNOWN failure, prove useful recovery, establish a matched efficacy result, or provide authority for another live run.

## H/T/D/C/U

- **H:** Sampling `planner_end_ns` after fallback cancellation/release/terminal cleanup contaminates the common planner window with variable cleanup latency. Endpoints are session runtime-clock nanoseconds.
- **T:** AST regression enforces the ordering `timer.cancel < planner_end_ns sample < fallback cleanup`. Confirm the patched source passes and a deliberate after-cleanup mutation fails as a negative control. Run the matched-v2 runner unit suite and compile check.
- **D:** PASS for this source-order repair only when current candidate satisfies the ordering, after-cleanup mutation control fails, and the runner suite passes.
- **C:** Fallback cancellation and input release remain required safety cleanup, but occur after the planner decision interval. Stopping the local timer before sampling avoids including its cancellation overhead; cleanup starts only after the endpoint. This follows the already-retained v6 boundary pattern.
- **U:** These checks do not measure runtime clock behavior, live latency, release correctness, scorer closure, gameplay effect, recovery efficacy, or full-process termination.

## Change

Move the endpoint sample to immediately after `timer.cancel()` and before the fallback-cleanup conditional. Keep cancellation/release/terminal behavior unchanged. Add `end_boundary_phase` to serialized planner-window evidence.

## Verification

The runner suite passed 13 tests, including candidate ordering and a deliberate after-cleanup mutation control. The isolated prior construction also passed fake-session ordering and mutation checks. Python compilation and `git diff --check` passed. No model, game, scorer, live input, or formal allocation ran.
