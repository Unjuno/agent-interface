# #4152 task ownership horizon — live private-X11 rung

H: A short explicit ownership horizon can preserve multi-cycle local work during a fixed planner delay without widening per-action authority; if ownership changes while focus/window/target geometry remain valid, the ownership layer must stop before a second action.

T: 12 fresh private-Xvfb/Tk sessions = STABLE vs INVALIDATE_AFTER_FIRST × NO_OWNERSHIP_HORIZON vs EXPLICIT_OWNERSHIP_HORIZON × 3 repetitions. One button effect increments an independently journaled counter. Both arms use identical current focus/window/geometry/lease admission before every XTEST click. No-horizon may execute one step then yields. Explicit horizon may execute up to three while ownership token task-v1 remains current. Mutation changes only token to task-v2 after first effect; target/focus/geometry remain valid.

D: PASS_TASK_OWNERSHIP_HORIZON_SCOPED iff stable explicit yields 3 effects per case versus 1 for no-horizon (aggregate +6 effects across 3 reps), every click has current authority, all invalidation cases have exactly 1 effect and zero click after invalidation, explicit invalidation stops OWNERSHIP_INVALIDATED while counterfactual ordinary authority remains admitted, terminal button state is neutral, raw audit errors=[], source/process evidence complete, reruns/replacements/tuning0.

C: Cooperative Tk fixture and authored ownership token. Gain may be equivalent to another existing validity abstraction; current authority uses cooperative known target geometry. Artificial planner delay is not a real model call.

U: No model/token benefit, natural mutation rate, arbitrary target finding, cross-app transfer, OS physical-HID proof, production adoption or universal ownership duration.
