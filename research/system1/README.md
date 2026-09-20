# System-1 research

This directory contains bounded fast-path / local decision experiments associated with System-1-style low-latency control.

These studies do not imply that a local model replaces the rich planner. Current project policy is to preserve rich-model intent and use local mechanisms only inside bounded, fresh-evidence-controlled authority.

## Relationship to Local System-1

```mermaid
flowchart LR
    R[Rich-model intent<br/>semantic goal + policy envelope]
    S[system1/<br/>representation · last-effect · exit]
    L[local_system1/<br/>decision kernel · cost · TTC · frontier gap]
    A[Deterministic authority<br/>fresh evidence · admission · release]
    Y[YIELD<br/>stale · ambiguous · novel]

    R --> S
    R --> L
    S --> A
    L --> A
    S --> Y
    L --> Y
```

This is a navigation view, not a mandatory runtime pipeline. Individual studies may test only one representation or decision boundary.

## Track map

| Theme | Retained studies |
|---|---|
| Latency-aware exit | [`latency_aware_exit_v1/`](latency_aware_exit_v1/), [`latency_aware_exit_v2/`](latency_aware_exit_v2/) |
| Last-effect receipt | [`map01_last_effect_receipt_v1/`](map01_last_effect_receipt_v1/) |
| Last-effect representation | [`map01_last_effect_representation_v1/`](map01_last_effect_representation_v1/), [`map01_last_effect_representation_v31_r2/`](map01_last_effect_representation_v31_r2/) |
| Intent-preserving Needle distillation | [intent_distillation_3458_pilot_01/](intent_distillation_3458_pilot_01/) |
| Online role-adapter update | [needle_lora_3441_online_stream_v1/](../needle_lora_3441_online_stream_v1/) — host-CPU online run; both online and batch misses the 0.90 gate; not container or runtime evidence. |
| Representation collision / ambiguity | [`map01_representation_collision_v1/`](map01_representation_collision_v1/) |

For lower-level local decision mechanics, route cost, TTC admission, typed evidence, and useful-work-per-frontier-boundary studies, use [`../local_system1/`](../local_system1/).

## Read next

- Current governing direction: [`../../docs/CURRENT_GOAL.md`](../../docs/CURRENT_GOAL.md)
- Research method: [`../../docs/RESEARCH_METHOD.md`](../../docs/RESEARCH_METHOD.md)
- Evidence ledger: [`../../RESEARCH.md`](../../RESEARCH.md)
- Research workspace map: [`../README.md`](../README.md)

Read each child experiment for its allowed decision vocabulary, authority boundary, and scoped disposition.


## Needle distillation successor

- [`intent_distillation_3458_pilot_02_stratified/`](intent_distillation_3458_pilot_02_stratified/) — balanced class and boundary suite; disposition FAIL_BOUNDARY_FIDELITY.


## Hybrid Needle margin successor

- [`intent_distillation_3458_pilot_03_hybrid/`](intent_distillation_3458_pilot_03_hybrid/) — scoped synthetic pass with deterministic boundary YIELD.


## Multi-seed hybrid Needle successor

- [`intent_distillation_3458_pilot_04_multiseed/`](intent_distillation_3458_pilot_04_multiseed/) — three-seed confirmatory synthetic result.


## Learned role-adapter graph

- [`needle_role_graph_3780_compact_v1/`](../needle_role_graph_3780_compact_v1/REPORT.md) — receipt-gated A→B→C LoRA role graph; scoped synthetic PASS with independent audit and an explicit provenance-label warning. #3778's separate output-capture STOP is preserved.
