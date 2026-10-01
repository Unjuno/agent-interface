# MAP01 bounded-recovery mechanism v4

Status: **CONSTRUCTION FROZEN BEFORE FORMAL WORKFLOW.**

Allocation reserved: `map01-recovery-cover-mechanism-live-v4-01`.

## Why v4 exists

Formal mechanism v3 did not execute its formal block. Workflow run `34974265196` stopped in construction revalidation because the preregistered SHA-256 for `audit_map01_recovery_cover_mechanism_v3.py` disagreed with the checked-out source. No coast/recovery arm was run under that allocation.

After that failure, the retained local real-MAP01 interruption matrix at `a74c5cb704c17bc63e6d73aa98a4bac62d738c47` established a stricter measurement contract: completed input with missing/unverified direct release is invalid evidence rather than zero occupancy, overlapping key intervals are unioned once, and interrupted input remains interval-censored to independently verified empty-input evidence.

V4 preserves the v3 scientific condition and replaces only the measurement/audit/protocol defects. It uses a new allocation ID.

## Frozen condition

Three counterbalanced pairs reload the same `map01-threat-contact-v2` fixture, seed `990619`. Each arm executes the same 180 ms `d` prelude, then a runtime-measured 600 ms simulated planner interval.

- **COAST_CONTROL:** no fallback input.
- **BOUNDED_RECOVERY:** reuse the immediately preceding `d` motor intent as five 50 ms holds separated by observation, under a 400 ms authority lease and 1000 ms source-age limit. Fresh typed health is required; any health loss, unavailable health or non-fresh sequence cancels.

No frontier model is called. A positive result is mechanism-only.

## Measurement repair

`map01_recovery_cover_mechanism_v4_measurement.py` adapts the retained `container_interruption_v1.occupancy.analyze_program` implementation to the matched runner. It therefore fails closed on missing completed releases, unions simultaneous keys once and preserves interruption censoring.

The accounting window is actual runtime planner-start to planner-return clock, not nominal hold duration and not a claim about frontier-model latency.

## Decision

Hard failure includes launch-owner violation, duplicate formal execution, malformed/invalid occupancy evidence, coast input admission, failure to expose recovery input, negative independent recovery event, unverifiable terminal release, scorer leakage or terminal-score disagreement.

If hard gates pass, all three pairs must reduce the no-retained-input upper bound and the paired median reduction must be at least 10% for `PASS_MECHANISM_ONLY`. Otherwise the scientifically valid first outcome is `HOLD`.

Scorer missed sampling periods are retained per arm but are not by themselves a hard failure. The scorer signals here are persistent state/counters and final terminal state is separately checked for exact five-field agreement; a cadence miss therefore degrades event-time precision rather than proving measurement invalidity.

## Construction / workflow split

V4 deliberately freezes source and thresholds in a construction commit **before** introducing its triggering workflow. The later workflow must compare all experimental source paths against this immutable construction commit before entering the formal step. This avoids the v3 self-hash failure class: there is no hash assertion for a source file that is being created in the same commit as its asserted hash.

## H / T / D / C / U

**H.** Source-bound reuse of the immediately preceding motor intent causally reduces measured input-free planner-wait time in the fixed real MAP01 fixture while preserving the retained release/scorer/terminal safety contracts.

**T.** One new workflow-path-global allocation, three fixed counterbalanced pairs, six terminal-score audits, direct windowed any-key occupancy, zero model calls and no retry after a formal step.

**D.** Exactly `PASS_MECHANISM_ONLY`, `HOLD` or `FAIL` under the frozen preregistration. No threshold relaxation after the outcome.

**C.** Recovery can be mechanically continuous but useless, immediately guard-cancelled, harmful, or measurement-invalid. Synchronous capture work can also lengthen requested holds; actual retained occupancy is measured rather than inferred from requested duration.

**U.** This remains one fixture with simulated planner delay and sparse independent useful events. Even `PASS_MECHANISM_ONLY` does not establish frontier-model efficacy, general DOOM competence, human reaction time or general GUI speedup.

## Related domains

- **Control systems:** separates actuator authority, cancellation and useful effect.
- **Measurement science:** treats missing/censored release evidence explicitly and avoids overlapping-key double counting.
- **Distributed systems / experimental systems:** one-shot allocation ownership and immutable pre-experiment source closure are part of causal validity.
