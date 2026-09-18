# MODEL-BRANCH-COST-RETAINED-IDENTIFIABILITY-20260918-001

H: Existing grouped/ungrouped MAP01 retained model traces do not identify marginal semantic-branch authoring cost because decision-level pre-model evidence/session/cache state are not matched while branch counts differ.
T: Freeze a normalized 24-row ledger from exact GitHub report blobs; enumerate all 12x12 grouped-vs-ungrouped candidate pairs; require model/effort, exact model image SHA, effect-memory, action-state, primary-command shape, input/cached counters, and model-session state to match before allowing different branch count. Retain whole-run usage/wall deltas as noncausal diagnostics only. Confirm provider usage endpoint exists from model-boundary probes 01/02.
D: PASS_RETAINED_MODEL_BRANCH_COST_NOT_IDENTIFIABLE_SCOPED iff admissible different-branch pairs=0, every 144 pair fails >=1 preregistered pre-model matchedness gate, provider usage endpoint exists, and no per-branch cost is emitted. PASS_IDENTIFIABLE only if >=1 fully matched pair exists. HOLD on source/data gap.
C: Equal image SHA would still not prove hidden conversation/session equality; cache counters/session ID are additional necessary gates, not sufficient proof. Sequential MAP01 trajectories can diverge after different admissions.
U: Retained-data identifiability only. No new model call and no model-cost estimate if matchedness fails.
