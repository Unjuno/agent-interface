# Useful-control measurement contract v2 (draft)

**Allocation:** `O2-G1-W2-MEASUREMENT-02`  
**Base:** `086233b30090d56b117a648226367a529dd553ad`  
**Status:** deterministic source/schema construction only; no live authority.

## Purpose and boundaries

This contract keeps four questions separate: what program was requested, what authority was valid, what owned input the backend/server confirmed, and what an independent scorer established as an effect. A fifth event, feedback delivery, records what evidence actually became available to the controller. These are overlapping evidence planes, not one state machine or one duration.

A program envelope, lease, requested hold, screenshot change, health/ammo sample, or terminal program status alone never proves useful control. Historical and scorer-only evidence never grants input authority. Empty input can be correct; confirmed held input can be useless.

## Event identity and clocks

Every event has a unique `event_id`, trace/session identity, typed `event_type`, `source_role`, clock domain and epoch, interval timestamp in integer nanoseconds, explicit input/semantic-authority values, lineage references, and a payload. Null/missing lineage means unknown; it must not be filled from chronology or a nearby event.

Compare timestamps only within the same monotonic clock domain and epoch. Cross-domain comparison needs a retained calibration/conversion receipt whose uncertainty is carried into the result. Duplicate IDs, reversed causality, invalid interval endpoints, unbound clocks, or unexplained out-of-order events yield HOLD for the affected trace; sorting rows must not repair them.

The JSON Schema validates row shape. The independent auditor must additionally enforce ID uniqueness, clock declaration, interval ordering, event lineage, and the trace rules below.

## Occupancy and authority

A backend/server-observed edge bracket estimates the physical transition in `[lo, hi]`. For one complete key lifecycle with down bracket `[d_lo,d_hi]` and up bracket `[u_lo,u_hi]`:

- guaranteed server-observed held time is `[d_hi,u_lo)` when `d_hi < u_lo`;
- possible held time is `[d_lo,u_hi)` when `d_lo < u_hi`;
- overlapping brackets yield no guaranteed interval and do not justify selecting a convenient endpoint;
- missing down/up edges are censored, not replaced by requested hold duration, program terminal time, or a neighboring release.

All intervals are half-open. For multiple keys/buttons, compute a union per surface/session; overlapping key intervals count once for any-input occupancy. Preserve per-key intervals too.

“Physical” here means the owner/server-observed X11 state supported by the receipt. It does not prove keyboard-device state, application consumption, or user-visible effect. Report these separately.

Authorized occupancy is the intersection of guaranteed observed owned-input intervals and a currently valid lease interval with matching owner, session, and actuation lineage. Input outside that intersection is unauthorized/unknown even when a program or lease exists. Lease duration, program-active duration, input occupancy, and effect timing must never be substituted for one another.

## Effect, feedback, and causality

- `OBSERVED_CHANGE` is a current lineage-bound observation. Pixel change is not automatically task-relevant.
- `RESOURCE_CHANGE` records independently measured public state such as health/ammo. It may be relevant feedback, but does not by itself establish a task effect or causation.
- `TASK_EFFECT` is domain-specific, independently scored, and bound to a plan/actuation under a declared scorer rule. It must retain positive, negative, or unresolved disposition. A run-level score is not plan-bound.
- `FEEDBACK_DELIVERED` records when the evidence became available to the decision-maker; a capture timestamp alone is not delivery.
- First useful feedback is the earliest qualifying delivered, current, decision-relevant evidence under a preregistered definition. Keep its time interval and uncertainty. Do not infer causality merely because it followed admission.
- An effect without matching actuation lineage is observed but unattributed. No qualifying sample by the deadline is `UNRESOLVED`, unless a complete scorer window supports an explicit negative result.

Independent scorer/game state must stay on the evaluation plane. It must not enter controller observations, policy selection, or authority admission.

## Trace disposition and intervals

Keep model-wait, program, policy-source, lease, input, resource, effect, feedback, release, and terminal intervals separately. Intersections and unions are calculated only when the relevant identities and clocks match. The guaranteed lower occupancy bound uses confirmed brackets; the possible upper bound uses the widest admissible brackets. Unbounded/censored endpoints remain unknown.

For intervals measured in nanoseconds, duration is `Δt_ns = end_ns - start_ns`; milliseconds are `Δt_ms = Δt_ns / 10^6`. Both sides have time dimension `[T]`; the divisor is the exact ns-per-ms scale factor. Do not add counts, pixels, model tokens, or unrelated clock values to durations.

A correct no-input decision may have zero occupancy and an unresolved or independently observed environment effect. A long hold with a complete unchanged scorer window may have occupancy but no useful effect. Neither case is an error by definition.

## Required trace classes

The companion `trace-cases.json` includes: authorized idle; input after authority expiry; input-free coast with damage; release before program terminal; overlapping key holds; missing and out-of-order edges; no-input with an unbound environment effect; and held input with a bound but no-effect scorer result. Examples are non-executable records and authorize no action.

## Evidence mapping and unresolved limits

This draft reuses, without relabeling, #64/#65 interval-censored occupancy, #503 state-feedback/schema limits, #1340 same-process physical-edge plus independent-effect mechanics, #1530's distinct effect-type HOLD, and #974 provenance composition. The current MAP01 attack/effect lanes remain separate and are not inputs to this static construction.

Known gaps remain: MAP01 has no retained run that combines exact physical occupancy, plan-bound independently scored task effect, and delivered first-useful feedback on one admissible clock; public GitHub state does not resolve external Worker/lease presence. The contract cannot select a recovery policy, claim MAP01 efficacy, or authorize any live experiment.
