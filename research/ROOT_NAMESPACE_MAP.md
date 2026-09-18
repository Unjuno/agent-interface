# Research root namespace map

This page organizes retained experiment directories that live directly under `research/`. It is a navigation aid only: no directory is moved, renamed, promoted, rejected, or reclassified scientifically.

## Placement rule

```mermaid
flowchart TD
    Q[New research work] --> C{Existing category fits?}
    C -->|yes| N[Place under the narrowest category<br/>measurement / integration / live_control / observation / domain track]
    C -->|no| R[Direct research/<name>/ only when<br/>a genuinely new category is required]
    O[Existing direct-root experiment] --> P[Keep exact path for provenance]
    P --> I[Index it here by theme]
    I --> S[Use its own report / audit<br/>for scientific status]
```

New work should normally use a category directory. Existing direct-root paths remain stable because Issues, PRs, hashes, reports, and audits may depend on their exact names.

## Preferred categories for new work

| Research scope | Preferred location |
|---|---|
| Scoped quantitative/formal semantics | [`measurement/`](measurement/) |
| Cross-component composition | [`integration/`](integration/) |
| Live desktop control and caller integration | [`live_control/`](live_control/) |
| Continuous / real-time DOOM control | [`doom/`](doom/) |
| Observation/temporal representation | [`observation/`](observation/) |
| Observation gating / exact delta transport | [`observation_gating/`](observation_gating/), [`observation_tiles/`](observation_tiles/) |
| Fast bounded local decision research | [`system1/`](system1/), [`local_system1/`](local_system1/) |
| Cross-domain transfer | [`cross_domain/`](cross_domain/) |
| Coordination semantics | [`coordination/`](coordination/) |
| Evaluation/convergence governance | [`benchmark_discovery/`](benchmark_discovery/), [`evolution/`](evolution/) |
| Conditional optimization/revisits | [`conditional_optimization/`](conditional_optimization/), [`optimization_revisits/`](optimization_revisits/) |
| Public presentation experiments | [`launch/`](launch/) |
| Small uncategorized experiments | [`experiments/`](experiments/) |

## Retained direct-root experiment families

The directories below predate or sit outside the newer category structure. Their placement is historical; read each experiment's own report/result for its exact disposition.

### Effect, admission, and delivery semantics

- [`exact_runtime_staged_admission_v1/`](exact_runtime_staged_admission_v1/)
- [`external_effect_outbox_v1/`](external_effect_outbox_v1/)
- [`outbox_semantic_revalidation_v1/`](outbox_semantic_revalidation_v1/)
- [`receiver_concurrent_conflict_v1/`](receiver_concurrent_conflict_v1/)
- [`receiver_concurrent_identical_v1/`](receiver_concurrent_identical_v1/)
- [`receiver_outcome_replay_v1/`](receiver_outcome_replay_v1/)
- [`staged_dependency_acquisition_v1/`](staged_dependency_acquisition_v1/)

### Dependency, identity, and semantic contracts

- [`context_effect_commit_discovery_v1/`](context_effect_commit_discovery_v1/)
- [`noncooperative_indistinguishability_v1/`](noncooperative_indistinguishability_v1/)
- [`typed_dependency_trace_v1/`](typed_dependency_trace_v1/)
- [`grounding_commit_guard_v1/`](grounding_commit_guard_v1/)
- [`identity_rendering_discovery_v1/`](identity_rendering_discovery_v1/)
- [`scoped_predicate_envelope_v1/`](scoped_predicate_envelope_v1/)

### Git/reference coordination experiments

- [`git_dependency_completeness_v1/`](git_dependency_completeness_v1/)
- [`git_multiref_atomic_v1/`](git_multiref_atomic_v1/)
- [`git_noncoop_realapp_v1/`](git_noncoop_realapp_v1/)
- [`git_ref_cas_realapp_v1/`](git_ref_cas_realapp_v1/)

### Observation and visual-state experiments

- [`observation_addressing_v1/`](observation_addressing_v1/)
- [`visual_invalidation_discovery_v1/`](visual_invalidation_discovery_v1/)

### OpenTTD support paths

- [`openttd_oracle/`](openttd_oracle/)
- [`openttd_task/`](openttd_task/)

### LibreOffice / Writer experiments

- [`libreoffice_privsep_commit_owner_v1/`](libreoffice_privsep_commit_owner_v1/)
- [`libreoffice_save_conflict_v1/`](libreoffice_save_conflict_v1/)
- [`libreoffice_save_guard_v1/`](libreoffice_save_guard_v1/)
- [`libreoffice_staged_publish_v1/`](libreoffice_staged_publish_v1/)
- [`writer_uno_compare_replace_v1/`](writer_uno_compare_replace_v1/)
- [`writer_uno_durable_recovery_v1/`](writer_uno_durable_recovery_v1/)
- [`writer_uno_post_guard_race_v1/`](writer_uno_post_guard_race_v1/)
- [`writer_uno_prefix_recovery_v1/`](writer_uno_prefix_recovery_v1/)
- [`writer_uno_serialization_negative_v1/`](writer_uno_serialization_negative_v1/)
- [`writer_uno_x11_binding_v1/`](writer_uno_x11_binding_v1/)

### Runtime/backend research predecessors

- [`runtime_backend_x11_v0/`](runtime_backend_x11_v0/)
- [`runtime_native_core_v0/`](runtime_native_core_v0/)
- [`runtime_native_x11_v0/`](runtime_native_x11_v0/)
- [`runtime_native_x11_pacing_cost_v1/`](runtime_native_x11_pacing_cost_v1/)
- [`runtime_native_x11_text_pacing_v1/`](runtime_native_x11_text_pacing_v1/)
- [`runtime_native_x11_text_robustness_v1/`](runtime_native_x11_text_robustness_v1/)
- [`runtime_native_x11_xorg_transfer_v1/`](runtime_native_x11_xorg_transfer_v1/)
- [`runtime_office_writer_x11_pacing_v1/`](runtime_office_writer_x11_pacing_v1/)
- [`runtime_office_x11_text_pacing_v1/`](runtime_office_x11_text_pacing_v1/)
- [`runtime_office_x11_v0/`](runtime_office_x11_v0/)
- [`runtime_portability_v0/`](runtime_portability_v0/)
- [`runtime_x11_unicode_clipboard_v1/`](runtime_x11_unicode_clipboard_v1/)

These are research predecessors. Current promoted executable organization lives under [`../runtime/`](../runtime/).

### Text delivery / XKB experiments

- [`text_delivery_capability_v1/`](text_delivery_capability_v1/)
- [`text_observation_binding_v1/`](text_observation_binding_v1/)
- [`text_observed_prefix_resume_v1/`](text_observed_prefix_resume_v1/)
- [`text_payload_preflight_v1/`](text_payload_preflight_v1/)
- [`text_payload_xkb_altgr_v2/`](text_payload_xkb_altgr_v2/)
- [`text_payload_xkb_layout_v1/`](text_payload_xkb_layout_v1/)
- [`text_payload_xkb_native_map_v1/`](text_payload_xkb_native_map_v1/)
- [`text_payload_xkb_native_roundtrip_v1/`](text_payload_xkb_native_roundtrip_v1/)
- [`text_payload_xkb_xdummy_v1/`](text_payload_xkb_xdummy_v1/)
- [`text_payload_xkb_xdummy_v2/`](text_payload_xkb_xdummy_v2/)
- [`text_post_preflight_keymap_race_v1/`](text_post_preflight_keymap_race_v1/)
- [`text_route_keymap_freshness_v1/`](text_route_keymap_freshness_v1/)
- [`text_x11_server_grab_keymap_v1/`](text_x11_server_grab_keymap_v1/)

## Interpretation

- This file describes **where things are**, not whether their ideas are correct.
- Do not infer promotion from a directory name or from its location at the `research/` root.
- Do not move completed evidence solely to make the tree prettier; stable paths are part of the audit trail.
- If an old mechanism is revisited, create a successor in the appropriate current category and link back to the retained source rather than rewriting the old directory.
