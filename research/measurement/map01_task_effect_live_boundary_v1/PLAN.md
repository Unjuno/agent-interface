# Issue 4131 plan / H-T-D-C-U
H: plan-bound task-effect receipts must come only from application-declared task-key effects; later background/state-only events remain unresolved. Physical actuation and task effect share CLOCK_MONOTONIC but remain separate evidence planes.
T: private Xvfb/Tk/XTEST, four schedules x three fresh repetitions = 12 sessions. One formal orchestration after public freeze. No retries/replacements/tuning. Separate scorer and raw-only auditor. No model/MAP01/network/user data/shared runtime.
D: PASS_PLAN_BOUND_TASK_EFFECT_LIVE_BOUNDARY_SCOPED iff 12/12 reconcile; press/release each bind exactly one task effect; state/background unresolved; effect timestamps do not precede down emit; authority none; terminal key state neutral; >=8 semantic mutations reject.
C: single-actuation cooperative fixture; scorer consumes authored app journal; same-host monotonic only; X-server state is not physical HID; no general causal attribution.
U: no model/task benefit, MAP01 efficacy, production runtime, cross-platform, latency/token or human-tempo claim.
Roadmap: excluded construction -> GitHub source/gate freeze -> one 12-session formal -> audit/mutations -> additive evidence PR -> CI/diff review -> main readback if qualified.
