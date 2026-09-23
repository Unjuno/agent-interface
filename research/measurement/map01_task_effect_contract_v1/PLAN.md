# MAP01 plan-bound task-effect instrumentation contract — Issue #1839

Task: MAP01-TASK-EFFECT-INSTRUMENTATION-CONTRACT-20260919-001

H: a fresh MAP01 measurement can preserve PHYSICAL_ACTUATION, STATE_FEEDBACK and independently scored TASK_EFFECT as separate non-authoritative evidence planes, with TASK_EFFECT requiring plan/actuation lineage, a comparable timestamp and an independent scorer.

T: pure standard-library contract validation. Old v38/v39 evidence is used only as a missing-field refusal boundary. Source-map current typed observation, MAP01 session score and executor terminal semantics. Excluded prefreeze construction used seed 183920260919001 / 120000 rows and is never pooled. Source-frozen formal uses fresh seed 183920260919002 / 150000 rows exactly once; independent oracle and postformal audit regenerate the frozen corpus without invoking formal.main.

D: PASS_MAP01_TASK_EFFECT_INSTRUMENTATION_CONTRACT_SCOPED iff candidate/oracle mismatch0, all directed controls pass, all four evidence roles occur, authority remains false, and weak/late/unscored/unclocked evidence never becomes TASK_EFFECT. Otherwise fail closed. This is a contract result, not MAP01 efficacy.

C: temporal order is weaker than causation; a future live scorer may perturb timing; discrete kill/death/exit/progress does not cover every useful gameplay effect.

U: no model, GUI, X11, ViZDoom, task input, token, survival, human-tempo or production claim.
