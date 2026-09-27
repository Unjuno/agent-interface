# MAP01 sector165 temporal workflow handoff — retained result

Task: `MAP01-SECTOR165-TEMPORAL-WORKFLOW-HANDOFF-20260917-001`  
Issue: #831  
Decision: **PASS_TEMPORAL_WORKFLOW_HANDOFF_SCOPED**

## Question

Does the retained #820 temporal drop-completion gate remain useful when composed into one slightly longer local workflow: fixed drop phase -> optional continuation -> fixed next `Right` 190 ms subgoal? Only completion-gate evidence changes between arms.

## First formal outcome

Twelve fresh first sessions completed, one case per outer invocation, formal reruns **0**.

- 55/75° positive discriminator: endpoint gate issued the redundant 350 ms forward **4/4**; temporal gate **0/4**.
- Raw-timestamp matched workflow-time reductions were **490.102, 780.537, 486.417, 599.887 ms**; median **544.994 ms**.
- Mandatory next `Right` 190 ms subgoal produced `|Δyaw| >= 5°` and verified neutral release **12/12**.
- 35° positive control: both gates correctly skipped extra forward **2/2**.
- wall negative: physical drop **0/2** and both gates preserved the 350 ms continuation **2/2**, then both executed the mandatory next subgoal.
- Frozen independent audit errors: `[]`; decision `PASS_TEMPORAL_WORKFLOW_HANDOFF_SCOPED`.

## Integrity

Frozen science source rehash after formal: **9/9 exact**. The frozen audit recomputes the #820 optical-flow relation from retained PNG bytes and checks selected-gate action, next-subgoal event/release shape and evaluator-only effect. Hard copied-evidence mutations for gate action, wall drop, next release, yaw effect and missing case fail; changing two timing rows crosses the preregistered timing gate to `HOLD_NO_WORKFLOW_DISCRIMINATOR`.

A postformal integrity check exposed one frozen-auditor limitation: `workflow_release_elapsed_ms` is consumed but not independently recomputed from `workflow_start_ns` and `next_subgoal_release_done_ns`. Because the formal gate permits one of four matched timing pairs to miss the >=200 ms criterion, one derived-field-only corruption can still leave the frozen aggregate decision PASS. The separately labelled `posthoc_timing_verifier.py` recomputes timing from raw timestamps: untouched evidence passes and reproduces median **544.994 ms**; the derived-field-only corruption is rejected. The frozen auditor/source/result are not repaired retroactively and formal is not rerun.

## Interpretation

The #820 temporal completion signal is not only a standalone diagnostic in this fixture: it can suppress a redundant continuation and hand off to a subsequent bounded ordinary-X11 action without breaking effect/release semantics. The measured time reduction is mechanistically explained by removing the authored continuation; it is **not** a claim that the retained primitives execute faster.

## Retention and scope

GitHub publication binds the frozen source, readable formal result/audit/summary, postformal timing verifier, and the formal evidence-manifest digest; the full manifest bytes and PNG evidence remain container-side. The full PNG/JSON/stdout/stderr archive is container-side only: `map831_full_evidence.tar.gz`, 26,077,985 bytes, SHA-256 `c39635d7c0f6932a24e136f14bb7faa2843a3f16bfa8aca33f03a5e4bcf705de`. The compact JSON archive is `map831_compact_evidence.tar.xz`, 21,408 bytes, SHA-256 `378b96ae6847e63ca87e862a4c6515955d9d2d0954f594296d56c5281549779a`.

Scope remains one no-monsters MAP01 boundary with setup-only hidden evaluator state and one fixed next turn. No combat, threat-survival, model/token, MAP01-clear, generic multi-subgoal, human-tempo or production-runtime claim follows.
