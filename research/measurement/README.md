# Measurement research

This directory contains scoped measurement, composition, timing, currentness, authority, readiness, concurrency, and related formal/controlled experiments.

Each child directory is an evidence unit, not a release or automatically promoted component. Typical contents include a frozen plan/source, candidate/oracle code, formal result, audit, corruption controls, and a report.


## Measurement families

```mermaid
flowchart TD
    Q[Scoped measurement question]
    Q --> CUR[Currentness / freshness<br/>epoch · request origin · validity]
    Q --> AUTH[Authority / release<br/>owner · lease · physical edge]
    Q --> TIME[Timing / useful effect<br/>endpoint · occupancy · lower bound]
    Q --> CONC[Concurrency / handback<br/>in-flight work · linearization]
    Q --> OBS[Observation / readiness<br/>relevance · capture · state]
    Q --> PROV[Provenance / attribution<br/>actor · receipt · authenticity]
    Q --> TEMP[Temporal / speculation<br/>buffer · reversal · planner gap]
    Q --> TARGET[Operation target / admissibility<br/>identity · row contract · corpus]

    CUR --> A[Plan / source freeze / result / audit]
    AUTH --> A
    TIME --> A
    CONC --> A
    OBS --> A
    PROV --> A
    TEMP --> A
    TARGET --> A
    A --> L[../../RESEARCH.md<br/>public evidence ledger]
```

These families are navigation aids, not a mutually exclusive taxonomy. A child experiment may span several families; its own `PLAN.md` / `REPORT.md` remains authoritative for scope.

## Common naming cues

| Prefix/theme | Usually concerns |
|---|---|
| `currentness_*`, `freshness_*`, `*_validity_*` | Whether evidence/authority is still current at the decision or input boundary. |
| `input_owner_*`, `ordinary_*`, `physical_*`, `release_*` | Input authority, physical edge bracketing, release, and ownership. |
| `timing_*`, `useful_effect_*`, `useful_control_*` | Named timing endpoints, effect intervals, occupancy, and causal timing. |
| `concurrent_fast_decision_*`, `*_handback_*`, `*_inflight_*` | Concurrent local work and frontier/authority handback semantics. |
| `observation_*`, `readiness_*`, `inference_gap_*` | Observation production/relevance/readiness and planner-gap transfer. |
| `mutation_actor_*`, `*_authenticity_*`, `*_provenance_*` | Attribution and evidence authenticity. |
| `temporal_*`, `queryable_temporal_buffer_*`, `speculative_*` | Temporal buffering, prediction/speculation, reversal, and invalidation. |
| `operation_target_*` | Operation-target identity, admissibility, corpus, and row contracts. |

Do not infer PASS/FAIL/currentness from a directory name or version suffix; open the retained report and its source/audit artifacts.

## Reading order

1. Start with the top-level [`../../RESEARCH.md`](../../RESEARCH.md) for the project evidence ledger.
2. Use the linked Issue/PR or a child experiment's `REPORT.md` / `PLAN.md` to determine scope.
3. Treat PASS/FAIL/HOLD/STOP as scoped to the experiment's declared H/T/D/C/U and environment.
4. Do not infer runtime or product support from a measurement directory alone.

The large number of child directories is intentional retained evidence. Repository cleanup should add navigation or archival explanation rather than merge/rename completed evidence paths without a provenance-preserving reason.

## Retained application-capture transfer

- [`o2_stream_real_capture_dot_v1/REPORT.md`](o2_stream_real_capture_dot_v1/REPORT.md) — Issue #4362 offline retained Calc/Inkscape/xterm transfer: 144-call exact wire/pixel/state parity; 12 changed transitions had median paired temporary traced-allocation ratio 0.667. No speedup, total-RSS, live-GUI, model or runtime-adoption claim; first outcomes and independent audit retained.

## Frozen O2 streaming source with formal-result publication HOLD

- [`o2_stream_memory_m6r1_v1/RECOVERY_STATUS.md`](o2_stream_memory_m6r1_v1/RECOVERY_STATUS.md) — Issue #4362 synthetic O2 streaming allocation: exact preformal sources and 12 inputs preserved and locally reconstruction-checked. The Issue reports a 12/12 formal PASS, but its raw result package is not in this branch/PR and the branch's two Actions runs have no artifacts; the reported formal outcome remains unaudited from repository-retained raw data. No formal rerun or runtime-adoption claim.

## Retained real-input transport accounting

- [Public-summary cost successor to #4395](retained_public_summary_cost_4395_dot_v1/REPORT.md): `STOP_CLOCK_GRANULARITY` after 225 calls; 42 of 54 CPU aggregates failed the frozen guard. Original output identities and fallback facts are retained, but no cost-characterization PASS or formal post-baseline control result is claimed. [Lossless raw restoration](retained_public_summary_cost_4395_dot_v1/PACKAGING.md).

## Retained exact-crop cache construction

- [#4083 source recovery](exact_crop_partial_recompute_1663_v1/RECOVERY_STATUS.md): preserves the exact 25-file branch package and six passing construction/unit tests, while the formal raw capsule and audit-v2 delivery remain incomplete. The Issue-reported 9-case contract/cost PASS is historical and was not re-audited by this recovery; original branch retained.
- [#5254 / source PR #5257 archival qualification](exact_crop_cache_memory_bound_4083_v1/ARCHIVAL_QUALIFICATION.md): 15 exact historical construction/preparation files; source-to-receipt reconstruction HOLD. Retained 12/12 score equality and 28,800-byte RGB-payload values are historical claims, not repository-reproducible execution; mismatched hashes, original failure, and bespoke-predicate control limits remain explicit. Formal workload unrun; source PR stays Draft and #5254 stays open.

## Verifier lifecycle T0 — formal raw-delivery HOLD

- [#5279 source recovery](verifier_lifecycle_5279_v1/RECOVERY_STATUS.md): exact source capsule restores 10 files / 43,307 bytes and six source tests pass in a network-disabled Linux/arm64 container. The Issue reports a scoped PASS, but the branch omits formal raw batches, final audit receipt, and corruption controls, so the result remains unverified here; no formal rerun or result promotion.

## Same-connection focus/key-state acquisition — raw-publication HOLD

- [#4389 / Draft PR #4410 archival qualification](key_state_piggyback_q4s8_v1/ARCHIVAL_QUALIFICATION.md): 18 exact source/freeze/audit blobs. The Issue-reported 612-acquisition contract PASS and full-cost HOLD are preserved as historical outcomes; the complete 261-file capsule and raw receipts remain absent, so no repository-only raw re-audit or full-cost benefit is claimed. Ten pure contract tests were run locally for this preservation; no allocation rerun. Keep the original Draft and branch for exact-byte recovery.

## Keymap synchronization-cost source recovery (#4357)

- [Source-only recovery status](keymap_sync_cost_q7m4_v1/RECOVERY_STATUS.md): preserves the frozen source group and explicitly records that the compiled probe, construction fixture, and formal raw/audit package are missing. Issue-reported request-accounting PASS and event-latency HOLD remain unverified here; no formal allocation was rerun.

## K2M6 clock/lease boundary — remote raw publication HOLD

- [#3880 / Draft PR #4440 archival qualification](clock_ipc_asymmetry_k2m6_v1/ARCHIVAL_QUALIFICATION.md): six exact original report/proof/verification/publication blobs, 29,842 bytes. The local allocation's reported clock-asymmetry result and `HOLD_REMOTE_RAW_INCOMPLETE` are retained separately; the 321-file canonical ZIP/patch are missing, so this archive does not independently reproduce the raw audit. This does not satisfy #3880's distinct OrbStack gate; keep its original Draft/branch and Issue open.

## Retained preformal temporal design — formal not started

- [X11 history depth #2542](x11_reversal_history_depth_2542_v1/ARCHIVAL_QUALIFICATION.md) — exact preformal ancestry, environment, freeze, plan and excluded construction summary retained; formal_started=false/reruns=0. Missing source and construction audit bytes remain explicit; no formal outcome is claimed.

## AoI critical-retention successor — runner-output STOP

- [#5494 / source PR #5497 qualification](aoi_backpressure_43_v2/ARCHIVAL_QUALIFICATION.md): five exact source/freeze/STOP blobs (21,407 bytes) already preserved by [#6334](https://github.com/Unjuno/agent-interface/pull/6334). One wrapper invocation returned exit 1 without stdout/stderr; runner execution and independent-audit completion remain unknown. Preserve `STOP_RUNNER_OUTPUT_UNAVAILABLE` and the separate transport sentinel STOP; no queue-policy benefit, scientific PASS/FAIL or rerun is claimed. Source PR #5497 is administratively closed and its historical branch ref is unavailable; #5494/#43 remain open.
