# Issue #5791 T0-v2 preregistration

## H/T/D/C/U

- **H:** Receipt-aware anti-windup reduces post-unblock overshoot/duplicate effects against unrestricted accumulation; it may or may not add value beyond a one-slot queue cap that remains occupied until semantic-effect receipt.
- **T:** One deterministic run of all 15 policy/case pairs: integrator saturation/release, transport ACK before semantic effect, no-integrator negative control, target-generation change during block, and mandatory cancel bypass. Candidate and independent raw-event auditor run once each in local Docker. No model, GUI or external service.
- **D:** Method gate passes only if independent replay matches each action/effect, overshoot, final target error, duplicate effect, UNKNOWN interval, old-generation cancellation and critical cancel latency; no-integrator outcomes must match across policies. H adds value only if C improves over both A and the stronger B on a frozen eligible trace without worse final error or delayed cancel. If B matches C, retain `FAIL_INCREMENTAL_VALUE_VS_SIMPLE_CAP` for this family. Synthetic PASS cannot establish live benefit.
- **C:** A one-slot queue held until semantic-effect observation may be sufficient; generation cancellation may handle stale commands independently; observation freshness may be the real residual.
- **U:** All quantities and schedules are synthetic. No LLM/PID equivalence, live accumulated state, real effect/harm, calibrated prevalence, causal claim, runtime promotion or product/speed claim.

V1's construction/audit failure remains immutable. V2 uses a distinct allocation and path. Freeze hashes before run; pinned local Docker, network none, 1 CPU/256 MiB/64 pids; no retry.
