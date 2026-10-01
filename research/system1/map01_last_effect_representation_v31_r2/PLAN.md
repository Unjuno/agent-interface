# v31 last-effect representation R2

Task: `LOCAL-SYSTEM1-MAP01-LAST-EFFECT-REPRESENTATION-V31-R2-20260918-001`
Issue: #1511

H: Holding #937 eligibility/teacher-label normalization fixed, adding only the immediately preceding admitted/completed plan's final typed `{action,extent,result}` effect receipt to exact prompt bytes separates the known v31 iter1/2 teacher-label collision and creates no eligible enriched collision across the five retained eligible rows.

T: Exact GitHub-retained v31 report + #937 SOURCE_ROWS -> frozen fixture. Toy-only construction controls. Freeze fixture/run/audit/controls before the first scientific replay. One deterministic replay over all eight retained rows; independent auditor recomputes eligibility, prompt Git blobs, prior-receipt provenance and collision groups without importing runner. Formal1/reruns0.

D: PASS_LAST_EFFECT_REPRESENTATION_V31_R2_SCOPED only if eligible rows5, prompt-only collision exactly [1,2], iter1 receipt NONE, iter2 prior receipt retreat_fire/short/visible_change from iter1, enriched collisions0, no leakage/source/integrity error, independent audit PASS.

C: Finite non-collision is not population sufficiency; exact Astra imitation may be stricter than task-effect equivalence; receipt may correlate with omitted visual state.

U: Retained-evidence replay only. No learner/model/GUI/task input/authority/timing/token claim.
