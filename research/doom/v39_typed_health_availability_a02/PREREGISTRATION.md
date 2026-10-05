# V39 capture-versus-emit timing replay A02 — preregistration

Status: FROZEN AFTER A01 PRE-CANDIDATE SYNTAX STOP; BEFORE A02 CANDIDATE RUN
A01 runner STOP: `v39_typed_health_availability_a01/runner-stop.json`.
Immutable source commit: `2fbfc00f8e38f33d7d74fb7cc734fbf5b0a11ab0`.
Report blob `bff2459036dcdcc44ed100b0c0bc657e1bb8e69a`; event blob `cbaeed9c7ba27b53cef9d10730ae33313371ad9a`.

## H/T/D/C/U

- **H:** The capture-time replay may misstate when the same signal becomes available to a monitor. Applying the exact frozen rule using emitted-time could change triggering sequences or measured lead time.
- **T:** Replay all six model waits, in both capture_ns and enclosing typed-observation emit_ns clocks, with the same downward-transition rule and full W grid {0.5,1,1.5,2,2.5,3,4}s. Compare trigger state, sequence, timing offset, and capture-to-emit delay for every selected row.
- **D:** The exact pinned report/events files above; expected 634 JSONL records, 218 typed observations, six decisions.
- **C:** Only timestamp source changes between runs. Sort by selected timestamp; baseline is latest valid observed numeric health sample at/before report controller_model_started_ns; each adjacent observed decrease counts; trigger is the second decrease if two are within W. Unknown rows clear the chain. Emit-time is the outer typed_observation event's emit_ns; capture-time is nested signals.health.capture_ns. Retain the full 2×6×7 result grid; no best clock/horizon selected.
- **U:** Saved-trace availability-time analysis only. No actual monitor dispatch, interrupt request/ack, model behavior, input, or task effect is simulated.

## Gates

- **PASS_SCOPED:** exact source identity/counts, all 84 clock/wait/window entries, and independent alternate implementation agree.
- **FAIL:** inputs parse, but a frozen result contradicts the timing hypothesis.
- **HOLD:** pinned timestamps are missing/inconsistent.
- **STOP:** any live runtime/model/game/input is invoked or authority is inferred.

A01's runner failure is not erased or relabeled. A02 gets one candidate execution; no retry after candidate failure.
