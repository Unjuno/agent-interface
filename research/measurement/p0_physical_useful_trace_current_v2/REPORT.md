# P0 current physical-edge -> useful-effect source closure

Task `P0-PHYSICAL-USEFUL-TRACE-CURRENT-CLOSURE-20260918-002`, Issue #1100.

## Decision

**`PASS_P0_CURRENT_GAP_LOCALIZED_SCOPED`**.

This is deterministic retained-evidence/source closure only. X11/GUI/model/provider/network/task input/live authority allocations: **0**.

## What changed relative to historical #1006

#1006 correctly froze three unproven gates at its older BASE: owner-edge producer, stable hold identity and live causal sample. Current main now contains retained scoped evidence for two of those prerequisites:

- owner-thread keymap sample sequencing: `PASS_OWNER_PHYSICAL_SAMPLE_SEQUENCING_SCOPED`, source blob `17806e9ee6da361eb160f907c8cf993689dedad2`;
- stable physical-hold generation identity: `PASS_PHYSICAL_HOLD_IDENTITY_AUDITABLE_V4_SCOPED`, RESULT blob `11017cc3298061ced9cb3eb16016a4c35c94dd15`;
- exact source-first v12 offline composition: `PASS_INPUT_OWNER_V12_OFFLINE_MECHANICS_SCOPED`, RESULT blob `fbc43a770865274adf716e6959f4e072be774fc7`, retained source bundle SHA-256 `5960543c9d9193b5615da2b545eb7a385a4d2e17bfe12513731bf9e92f948422`;
- useful-effect clock-provenance admission: `PASS_USEFUL_EFFECT_CLOCK_PROVENANCE_FORMAL_SCOPED`, FORMAL_RESULT blob `2a4bec93f5df774df2c0456d390c60d9d5363dc3`.

Historical #992/#994/#996/#981/#988/#974 semantic nodes remain scoped contract evidence and are not promoted to live truth.

## Current closure

The current DAG is **offline-ready**: semantic contracts, stable lineage, sample sequencing, v12 offline mechanics, occupancy/effect-role/provenance semantics and clock-provenance admission are connected at their declared evidence classes.

But full useful control remains unproven. The two current required live gates are exactly:

1. `LIVE_PHYSICAL_EDGE_TRANSFER` — exact retained v12 must produce the expected physical DOWN/UP evidence on a real private X11 path without control regression;
2. `LIVE_CAUSAL_EFFECT_SAMPLE` — one separately bounded live sample must bind the resulting real physical actuation lineage to an independently scored application effect under valid clock provenance.

For a cross-process effect/scorer path there is one additional gate: `CROSS_PROCESS_CLOCK_AXIS`. Open #1000 construction intent is not retained completed clock-axis evidence and contributes zero reachability. A same-process live fixture can avoid that additional cross-process relation only if the actual retained live endpoints prove they use the same process/clock domain.

Queued Issue #1099 and its #60 live-lease request are plan/coordination evidence only; they contribute zero scientific reachability.

Result fields:
- `offline_ready=true`;
- `same_process_live_useful_control_proven=false`;
- `cross_process_live_useful_control_proven=false`;
- remaining current gates `[LIVE_PHYSICAL_EDGE_TRANSFER, LIVE_CAUSAL_EFFECT_SAMPLE]`;
- cross-process additional gate `CROSS_PROCESS_CLOCK_AXIS`.

Primary invocation1/reruns0. Independent audit PASS/errors `[]`. Evidence-class corruption controls reject **6/6** attempted promotions/substitutions. Frozen source rehash exact **5/5**.

Exact local result identities:
- RESULT SHA-256 `ab03252e6eb5b4c30e28efcb2dd4c8e870d52df4af16333c43aee51837425e14`;
- AUDIT `3d34809557b56bc6edc613c94b0d542023f7d8af7c13bcf8c7d3d514a6c00fdf`;
- CORRUPTION `88ac81bb153be7be261b19f177f2052f05eef0e40fc3e0456fc30dfd9f2aee13`;
- SOURCE_REHASH `1895098333300535a9ee4b57a97be85757b94274210d137c4b68eeaaccefd8f8`.

## Stop

Do not create another offline physical-edge implementation experiment. The immediate P0 successor is already #1099 and remains gated on an explicit #60 live lease. This closure neither grants that lease nor supplies any live result.
