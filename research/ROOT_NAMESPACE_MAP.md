# Research root namespace map

This page organizes retained research directories that live directly under `research/`. It is a navigation aid only: no directory is moved, renamed, promoted, rejected, or reclassified scientifically.

## Placement rule

```mermaid
flowchart TD
    Q[New research work] --> C{Existing category fits?}
    C -->|yes| N[Place under the narrowest category<br/>measurement / integration / live_control / observation / domain track]
    C -->|no| R[Direct research/<name>/ only when<br/>a genuinely new category is required]
    O[Existing direct-root research path] --> P[Keep exact path for provenance]
    P --> I[Index it here by theme]
    I --> S[Use its own report / audit<br/>for scientific status]
```

New work should normally use a category directory. Existing direct-root paths remain stable because Issues, PRs, hashes, reports, and audits may depend on their exact names.

## Preferred categories for new work

| Research scope | Preferred location |
|---|---|
| Analytical proof / exact derivation / identifiability | [`analysis/`](analysis/) |
| Offline audit and provenance review bundles | [`audits/`](audits/) |
| Scoped quantitative/formal semantics | [`measurement/`](measurement/) |
| Cross-component composition | [`integration/`](integration/) |
| Safe overlap / phase scheduling / concurrency | [`concurrency/`](concurrency/) |
| Live desktop control and caller integration | [`live_control/`](live_control/) |
| Continuous / real-time DOOM control | [`doom/`](doom/) |
| Observation/temporal representation | [`observation/`](observation/) |
| Observation gating / exact delta transport | [`observation_gating/`](observation_gating/), [`observation_tiles/`](observation_tiles/) |
| Fast bounded local decision research | [`system1/`](system1/), [`local_system1/`](local_system1/), [`needle_lora_3441_pilot_03_router/`](needle_lora_3441_pilot_03_router/) |
| Cross-domain transfer | [`cross_domain/`](cross_domain/) |
| Coordination semantics | [`coordination/`](coordination/) |
| Evaluation/convergence governance | [`benchmark_discovery/`](benchmark_discovery/), [`evolution/`](evolution/) |
| Conditional optimization/revisits | [`conditional_optimization/`](conditional_optimization/), [`optimization_revisits/`](optimization_revisits/) |
| Public presentation experiments | [`launch/`](launch/) |
| Small uncategorized experiments | [`experiments/`](experiments/) |

## Retained direct-root research families

- [`session_handoff/`](session_handoff/)
- [`gtk_fresh_post_effect_2673/`](gtk_fresh_post_effect_2673/)
- [`results/`](results/) — retained native-handle result bundles; each bundle's report defines its scope and status.
- [`audits/`](audits/) — retained independent audit/review bundles; use the referenced source snapshot and allocation to interpret each result.
- [`recovery/`](recovery/) — preserved source/evidence recovery capsules for interrupted or parallel research allocations; each status file records provenance and disposition without replacing the original result.

- [`x11/`](x11/)

The directories below predate or sit outside the newer category structure. Their placement is historical; read each experiment's own report/result for its exact disposition.

### Effect, admission, and delivery semantics

- [`golden_report_independent_scorer_2246_v1/`](golden_report_independent_scorer_2246_v1/)
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

### Coordination and handoff semantics

- [`session_handoff/`](session_handoff/) — authority-safe advisory handoff capsule contracts.

### Causality and temporal policy experiments

- [`causality/`](causality/)

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
- [`x11_text_german_layout_3668_v2/`](x11_text_german_layout_3668_v2/) — Issue #3741 frozen German XKB delivery run; audit FAIL is retained, with de-01 raw evidence missing and the independent re-audit limitation documented in RECOVERY_REVIEW.md.

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

## Cross-engine JSONL framing replication

- [`issue_3814_jsonl_framing_v1/`](issue_3814_jsonl_framing_v1/) — Issue #3814 Docker Desktop/Linux amd64 newline-framing audit; retain the overall `HOLD_EVIDENCE_INCOMPLETE` (75/76) and the single-dispatch receipt without replay.
- [`experiments/issue_3840_newline_frame_v2/`](experiments/issue_3840_newline_frame_v2/) — Issue #3840 Docker Desktop/Linux amd64 replication of the terminal-LF strict-prefix result; `RESULT.md` separates the corroborated row-level observation from the unresolved audit-provenance HOLD.

## Navigation check

The canonical top-level workspace check is [`check_workspace_index.py`](check_workspace_index.py), documented in [`README.md`](README.md). It verifies that this retained namespace map and the current workspace map together cover every top-level research directory.


### Guard calibration support preflight

- [`guard_calibration_support_2509_v1/`](guard_calibration_support_2509_v1/) — synthetic ledger/readiness gate for successor Issue #2509; this path is construction-only and not a formal route result.


### Fresh GTK effect receipt precheck

- [`gtk_fresh_post_effect_2673/`](gtk_fresh_post_effect_2673/) — additive precheck boundary for independent fresh post-effect drawable receipts; execution result is recorded in Issue #2673 and must not be inferred from this path alone.


### GTK research namespace

- [`gtk/`](gtk/) — retained GTK/X11 fixture and adapter research paths; consult each child report for scope and disposition.

### Recent additive namespaces
- [`gpu/`](gpu/) — archived local-GPU candidate triage snapshot and recovery status; not a current resource schedule or authorization.
- [`archive/`](archive/) — Legacy research archive; consult included manifests and reports for scope.
- [`archives/`](archives/) — Archived research bundles and their retained evidence indexes.
- [`container_control/`](container_control/) — Container-control research artifacts.
- [`control_codec/`](control_codec/) — Control-codec research artifacts.
- [`needle_online_lora_skill_stream_v1/`](needle_online_lora_skill_stream_v1/) — Needle online role-skill streaming study; see REPORT.md for disposition.
- [`orchestration/`](orchestration/) — Orchestration research artifacts.
- [`real_apps_v1/`](real_apps_v1/) — Real-application research artifacts, v1.
- [`real_apps_v2/`](real_apps_v2/) — Real-application research artifacts, v2.
- [`real_apps_v3/`](real_apps_v3/) — Guarded real-application research artifacts, v3.
- [`retention/`](retention/) — Retention research artifacts.
- [`visual_tracking/`](visual_tracking/) — Visual-tracking research artifacts.
- [`x11_private_xvfb_5286/`](x11_private_xvfb_5286/) — Issue #5286 private-Xvfb termination attempt; STOP retained, not a clean-termination result.
- [`x11_private_xvfb_5291/`](x11_private_xvfb_5291/) — Issue #5291 successor: scoped local construction/termination PASS; not GUI-input or product validation.
- [`needle_role_graph_3775_v1/`](needle_role_graph_3775_v1/) — Issue #3778 original role-graph allocation retained as `STOP_RESULT_CAPTURE_TRUNCATED`; see [recovery review](needle_role_graph_3775_v1/RECOVERY_REVIEW.md). Distinct compact successor #3780 is documented separately.
- [`needle_lora_3441_pilot_04d_corrected_base_v1/`](needle_lora_3441_pilot_04d_corrected_base_v1/) — Issue #4471 GPU formal STOP during result serialization; no scientific metrics were retained.
- [`needle_lora_3441_pilot_04e_result_schema_v1/`](needle_lora_3441_pilot_04e_result_schema_v1/) — Issue #4471 fresh-seed result-schema successor; scoped one-seed synthetic routing PASS with host-only CUDA limits, not recovery of the earlier STOP.
- [`needle_lora_3441_pilot_04f_seed_replication_v1/`](needle_lora_3441_pilot_04f_seed_replication_v1/) — Issue #4492 one-seed fresh replication PASS within the same synthetic task family; no population-reliability or runtime claim.

- [`audits/`](audits/) — retained audit-only evidence bundles; currently includes the scoped #3688 exact raw-byte-binding audit and its independent revalidation.
- [`event_delivery/`](event_delivery/) — retained event-delivery timing/gap/deadline research; consult each child result for scope and disposition.
- [`chromium/`](chromium/) — retained Chromium live-control, identity, and recovery experiments; consult each child report for scope and disposition.
- [`cli_fault_residue_3711_revalidation_v1/`](cli_fault_residue_3711_revalidation_v1/) — retained Issue #3711 CLI fault-residue revalidation; consult its report for exact scope and disposition.
- [`cli_retention_3711_short_write_v1/`](cli_retention_3711_short_write_v1/) — retained Issue #3711 short-write protocol; Ubuntu's required CLI workflow failed on selector mock imports, so no three-OS construction PASS is claimed.
- [`issue_3733_german_xkb_text_orbstack_v3/`](issue_3733_german_xkb_text_orbstack_v3/) — retained Issue #3733 German XKB formula-delivery experiment and immutable formal/audit evidence; consult its preregistration and result disposition before making claims.
- [`x11_midprogram_keymap_5236/`](x11_midprogram_keymap_5236/) — Issue #5236 Formal01 startup STOP bundle; preserve the failed run and do not infer a mid-program keymap result.
- [`x11_text_german_layout_3668_v1/`](x11_text_german_layout_3668_v1/) — original Issue #3733 setup STOP and frozen protocol; de-01 stopped before the hypothesis test, with a freeze/result-state discrepancy documented in the artifacts.
- [`needle_lora_3441_pilot_04c_multiskill_audit_complete/`](needle_lora_3441_pilot_04c_multiskill_audit_complete/) — Issue #3895 one-seed multi-skill audit; HOLD_PROTOCOL_DEVIATION because the run used 120 rather than the specified 400 base updates.
- [`needle_lora_3441_pilot_04d_multiskill_400base/`](needle_lora_3441_pilot_04d_multiskill_400base/) — retained direct-root Needle multi-skill pilot evidence; use its own report for exact scientific disposition and scope.
- [`needle_role_skill_reload_3780_v1/`](needle_role_skill_reload_3780_v1/) — Issue #3890 scoped three-seed synthetic cross-process role-skill reload PASS; see report and audit-source correction for limits.
- [`issue_3784_explicit_x11_receiver_v1/`](issue_3784_explicit_x11_receiver_v1/) — Issue #3784 explicit InputOnly receiver experiment; formal-01 stopped at its receiver-control oracle, so German formula delivery remains untested.
- [`issue_3784_focused_receiver_v1/`](issue_3784_focused_receiver_v1/) — Issue #3794 corrected KeyRelease oracle and formal German XKB formula-delivery experiment; formal-01 and independent artifact audit passed for the exact pinned X11/Xvfb scope.
- [`issue_3794_receiver_control_construction_v1/`](issue_3794_receiver_control_construction_v1/) — Issue #3794 construction-only pilot history and audit/corruption controls; no formal result is claimed and predecessor STOPs remain unchanged.
- [`issue_3784_explicit_x11_receiver_v2/`](issue_3784_explicit_x11_receiver_v2/) — Issue #3791 corrected-receiver successor; formal-02 stopped at the baseline layout parser, so candidate delivery remains untested.
- [`issue_3784_explicit_x11_receiver_v3/`](issue_3784_explicit_x11_receiver_v3/) — Issue #3796 construction-gated receiver successor; formal-03 passed the exact German formula-delivery gate, with scope limits in RESULT.md.
- [`needle_lora_3441_online_stream_v1/`](needle_lora_3441_online_stream_v1/) — retained Issue #3441 online-stream needle LoRA experiment; consult its report for exact scope and disposition.
- [`verification/`](verification/)
- [`needle_lora_3441_rank4_online_lr_half_multiseed_v1/`](needle_lora_3441_rank4_online_lr_half_multiseed_v1/) — retained Issue #3826 fixed half-learning-rate rank-4 five-seed online LoRA result; consult FREEZE, AUDIT, and REPORT for exact scope and disposition.
- [`issue_3349_event_replay_contract_v1/`](issue_3349_event_replay_contract_v1/) — retained Issue #3349 replay-contract evidence.
- [`issue_3676_audit_hardening_v1/`](issue_3676_audit_hardening_v1/) — retained Issue #3676 audit-hardening evidence.
- [`issue_3691_manifest_root_v1/`](issue_3691_manifest_root_v1/) — retained Issue #3691 manifest-root reproduction record.
- [`issue_3691_audit_integrity_v1/`](issue_3691_audit_integrity_v1/) — retained Issue #3691 independent-pin auditor construction; see `INTEGRATION_ADDENDUM.md` for the later exact-source #3722 result and remaining Docker Desktop gate.
- [`needle_lora_3441_rank4_curve_audit_v1/`](needle_lora_3441_rank4_curve_audit_v1/) — Issue #3875 CPU-only audit of immutable #3851 pre-rollback learning curves; see OUTCOME.json for the scoped finding and limits.
- [`needle_lora_3441_pilot_04_multiskill/`](needle_lora_3441_pilot_04_multiskill/) — retained Issue #3701 synthetic two-skill adapter-interference pilot.
- [`docker_ipc_schema_bridge_2818_v1/`](docker_ipc_schema_bridge_2818_v1/)
- [`semantic_checkpoint_contract_2661_v1/`](semantic_checkpoint_contract_2661_v1/)


- [`procedural_control_arena_v0/`](procedural_control_arena_v0/) — dependency-light mechanics/regression prototype; see its README and validation record for limits. It is not evidence of candidate or cross-domain performance.
- [`procedural_control_arena_v1/`](procedural_control_arena_v1/) — construction GUI benchmark with compound input primitives; paired baseline/candidate, held-out promotion, evaluator isolation, formal performance, and cross-domain transfer remain unvalidated.
- [`procedural_operations_world_v0/`](procedural_operations_world_v0/) — ultra-light native 2.5D operations-world substrate for agent-native concurrent control; usable for automated harness integration after validity-hardening, while secure paired B0/C1 evaluation and held-out promotion remain open.

### Needle / System-1 adapter research

- [`needle_lora_3441_pilot_02/`](needle_lora_3441_pilot_02/) — retained global-adapter forgetting result.
- [`needle_lora_3441_pilot_04_multiskill/`](needle_lora_3441_pilot_04_multiskill/) — retained Issue #3701 synthetic two-skill adapter-interference pilot; consult its README and FREEZE for evidence scope.


### Recent direct-root evidence

- [`cli_fault_residue_3711_revalidation_v1/`](cli_fault_residue_3711_revalidation_v1/) — retained Issue #3711 report-temp fault revalidation.
- [`needle_lora_3441_online_stream_v1/`](needle_lora_3441_online_stream_v1/) — retained Issue #3769 streamed online role-adapter experiment.
- [`needle_lora_3441_rank4_online_multiseed_gpu_v1/`](needle_lora_3441_rank4_online_multiseed_gpu_v1/) — retained Issue #3807 five-seed GPU rank-4 online LoRA failure; see the report for scope and limits.
- [`needle_role_graph_3780_compact_v1/`](needle_role_graph_3780_compact_v1/) — retained Issue #3780 role-adapter graph result and audits.
- [`needle_role_graph_3775_v1/`](needle_role_graph_3775_v1/RECOVERY_REVIEW.md) — Issue #3778 original role-graph allocation retained as `STOP_RESULT_CAPTURE_TRUNCATED`; distinct compact successor #3780 is documented separately.
- [`needle_lora_3441_rank4_online_multiseed_v1/`](needle_lora_3441_rank4_online_multiseed_v1/) — Issue #3790 CPU rank-capacity preregistration and immutable one-shot runner STOP evidence.
- [`needle_lora_3441_rank4_online_lr_half_multiseed_v1/`](needle_lora_3441_rank4_online_lr_half_multiseed_v1/) — Issue #3826 fixed half-learning-rate rank-4 online LoRA successor; consult its frozen report/audit for scope and disposition.
- [`needle_lora_3441_rank4_curve_audit_v1/`](needle_lora_3441_rank4_curve_audit_v1/) — Issue #3875 successor's CPU-only independent audit of the immutable #3851 learning-curve result; no training/CUDA, see its scoped report and predecessor STOP.
- [`needle_lora_3441_rank4_minibatch_seed_v1/`](needle_lora_3441_rank4_minibatch_seed_v1/) — Issue #3851 sampler-stream comparison formal STOP; no training comparison/result was produced, see retained stderr and REPORT.md.
- [`needle_lora_3441_rank4_minibatch_seed_corrected_v1/`](needle_lora_3441_rank4_minibatch_seed_corrected_v1/) — Issue #3887 frozen sampler-stream successor HOLD; legacy collapse gate was not reproduced, and full independent audit STOP is retained.
- [`needle_lora_3441_rank4_minibatch_seed_corrected_audit_v1/`](needle_lora_3441_rank4_minibatch_seed_corrected_audit_v1/) — Issue #3887 independent audit stopped before scoring because the frozen source/checksum pins do not match the committed artifacts; the original HOLD remains unchanged.
- [`needle_lora_3441_rank4_online_multiseed_gpu_v1/`](needle_lora_3441_rank4_online_multiseed_gpu_v1/) — Issues #3807/#3819 GPU rank-capacity failure evidence; #3822 separately records the learning-curve HOLD.

- [`procedural_control_arena_v0/`](procedural_control_arena_v0/) - Procedural control arena; consult its README and VALIDATION for scope and current evidence.
- [`procedural_control_arena_v1/`](procedural_control_arena_v1/) - Procedural control arena v1 construction environment; see README and VALIDATION for scope and open promotion gates.

- [`procedural_ops_facility_v0/`](procedural_ops_facility_v0/) — recovered Procedural Operations Facility v0 construction benchmark; see README, VALIDATION, and RECOVERY_STATUS for reproducibility and explicit non-efficacy limits.

- [`kernel_receipt_time_5215_20260928/`](kernel_receipt_time_5215_20260928/) — Issue #5215 kernel receipt timestamp construction probe; consult PLAN and REPORT for its contract-only scope and limitations.

### Issue #5236 X11 keymap successor evidence

- [`x11_midprogram_keymap_5236_formal02_20260930/`](x11_midprogram_keymap_5236_formal02_20260930/) — Formal02 import-path STOP; see immutable STOP record.
- [`x11_midprogram_keymap_5236_formal03_20260930/`](x11_midprogram_keymap_5236_formal03_20260930/) — Formal03 missing-Tk-runtime STOP; no fixture row completed.
- [`x11_midprogram_keymap_5236_formal04_20260930/`](x11_midprogram_keymap_5236_formal04_20260930/) — Formal04 focused-root delivery/effect STOP; independent audit and corruption controls retained.
- [`x11_midprogram_keymap_5236_formal05_20260930/`](x11_midprogram_keymap_5236_formal05_20260930/) — Formal05 STOP_PROVENANCE_OR_RUNNER; dispatch completed but independent saved effects were missing.
- [`x11_midprogram_keymap_docker_diagnostic_20260930/`](x11_midprogram_keymap_docker_diagnostic_20260930/) — Nonformal local Docker focus-versus-Entry-click diagnostic; not formal hypothesis evidence.


### Issue #5236 X11 keymap STOP evidence

- [`x11_midprogram_keymap_5236_formal02_20260930/`](x11_midprogram_keymap_5236_formal02_20260930/) — Formal02 import-path STOP.
- [`x11_midprogram_keymap_5236_formal03_20260930/`](x11_midprogram_keymap_5236_formal03_20260930/) — Formal03 missing-Tk-runtime STOP.
- [`x11_midprogram_keymap_5236_formal04_20260930/`](x11_midprogram_keymap_5236_formal04_20260930/) — Formal04 fixture-focus/effect STOP.
- [`x11_midprogram_keymap_5236_formal05_20260930/`](x11_midprogram_keymap_5236_formal05_20260930/) — Formal05 missing completed effects STOP.
- [`x11_midprogram_keymap_docker_diagnostic_20260930/`](x11_midprogram_keymap_docker_diagnostic_20260930/) — nonformal local Docker focus-versus-click diagnostic.

- [`aoi_43_t0/`](aoi_43_t0/) — executed Age-of-Information critical-event retention T0 for #43 (exploratory; not runtime validation).

- [`x11_midprogram_keymap_5236_formal05_save_diagnostic_20261001/`](x11_midprogram_keymap_5236_formal05_save_diagnostic_20261001/) — Local Docker diagnostics: post-save waits do not change the US control; mid-program XKB remaps produce wrong saved text in Debian Docker (not Arch formal evidence).
- [`x11_midprogram_keymap_5236_formal06_20261001/`](x11_midprogram_keymap_5236_formal06_20261001/) — Issue #5236 Formal06 `STOP_PROTOCOL_DEVIATION`: preserved raw predates freeze; auditor mismatch is diagnostic only. See `RESULT_DISPOSITION.md`.
- [`x11_midprogram_keymap_5236_formal07_20261001/`](x11_midprogram_keymap_5236_formal07_20261001/) — Issue #5236 Formal07 `STOP_PROVENANCE_OR_RUNNER`: the `missing_post_save_wait` corruption was a no-op and escaped; see the result disposition.


### Security evidence

- [`security/`](security/) — retained X11 UI-redress evidence, including Issue #5692 formal-01 `STOP`; see [its result record](security/ui_redress_5692_x11_a02_20261001/FORMAL-01-STOP.md).
