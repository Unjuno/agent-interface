# Resource-scoped arbitration between threat authority and no-progress deoptimization

Task `MAP01-THREAT-DEOPT-ARBITRATION-20260917-001`, Issue #609.

## Decision

**`PASS_THREAT_DEOPT_AUTHORITY_ARBITRATION_SCOPED`.**

This is a deterministic container-only composition study. It does not run ViZDoom or claim that either the retained threat-control mechanism or repeated-no-progress deoptimization improves survival. It asks one narrower scheduler question: when both mechanisms want the same motor resource, what may execute while a valid threat authority still owns that resource?

## Hypothesis and single factor

The negative-control policy `latest_ready` ignores authority ownership and selects the most recently ready proposal per resource. The candidate `authority_guarded` changes only admission arbitration:

- while exactly one valid threat lease owns a resource, only a matching threat proposal may execute on that resource;
- a non-authority proposal is deferred rather than silently overwriting the threat owner;
- if the threat lease expires, its context is invalidated, or no threat lease exists, ordinary latest-ready selection resumes;
- unrelated resources remain independently executable.

## Formal block

Source-first publication and Git blob readback completed before measurement. Formal runner invocation count: **1**. No rerun, replacement, extension, threshold change, GUI/model/game/input call, or mutation of active Issue #575.

Eight scenarios × four repetitions × two policies = **64 retained first rows**, including 32 candidate outcomes.

| Scenario | `latest_ready` | `authority_guarded` | n/policy |
|---|---|---|---:|
| active threat; deopt arrives later | deopt | threat | 4 |
| active threat; threat arrives later | threat | threat | 4 |
| active threat lease; threat command absent | deopt | no locomotion action | 4 |
| expired threat lease | deopt | deopt | 4 |
| invalid threat context | deopt | deopt | 4 |
| threat fire + deopt locomotion | both | both | 4 |
| deopt only | deopt | deopt | 4 |
| threat only | threat | threat | 4 |

## Frozen audit

Independent auditor decision: **PASS**, errors **0**.

- candidate ground-truth correct: **32/32**;
- authored baseline active-authority violations exposed: **8/8**;
- candidate deopt selections during those active overlapping authority cases: **0/8**;
- candidate deopt liveness after expiry / invalidation / no threat: **12/12**;
- candidate preserves simultaneous threat-fire + deopt-locomotion: **4/4**.

Four postformal copied-evidence corruption controls were rejected **4/4**: wrong candidate selection, missing row, duplicate row ID, and false `correct` flag.

## Interpretation

The useful mechanism is not “threat always has global priority.” It is **resource-scoped authority ownership**. A valid threat lease protects only the resource it owns. That prevents a later navigation repair from stealing locomotion while still allowing a fire-only threat authority and locomotion deoptimization to coexist.

The `active_lease_missing_threat_command` stratum is intentionally fail-closed: the absence of a currently ready threat command is not treated as permission for another mechanism to seize the still-live locomotion authority. Availability resumes when the lease is explicitly no longer active/valid.

This is consistent with the retained normal-MAP01 deoptimization result: navigation deoptimization can remain useful, but composition should not erase another live authority merely because its proposal is newer.

## H / T / D / C / U

**H:** a valid threat authority and deoptimization need explicit resource arbitration; recency alone can violate authority.

**T:** standard-library deterministic fixture, eight scenarios, four repetitions, one formal invocation, one frozen audit.

**D:** PASS at the frozen gate above.

**C:** the fixture authors lease validity and proposal readiness. A real threat controller may itself become stale or choose poor actions; arbitration cannot make a bad authority good.

**U:** no real-time scheduling, physical input, ViZDoom hazard, preemption rollback, fairness, multi-owner arbitration, natural overlap rate, or model interaction is measured.

## Next single question

Transfer only this arbitration rule into one real normal-MAP01 diagnostic where a validated threat-aware local authority and the already-retained no-progress navigation deoptimization can actually overlap. Hold both component policies fixed. Measure whether arbitration prevents resource theft while retaining navigation recovery after threat authority ends. Do not add a second recovery/threat mechanism in that transfer.
