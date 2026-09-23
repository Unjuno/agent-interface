# #4151 minimal task-node semantics versus guarded macro

Allocation `task-node-semantics-4151-20260923-01`. Private Xvfb/Tk/XTEST only.

## H
With identical observations, task actions, effect oracle and lifecycle predicate, a minimal explicit task-node lifecycle may expose a behavioral/control advantage over the existing guarded-macro representation. If both representations make the same nominal continuation and mutation YIELD decisions with identical effects, retain `FAIL_NO_TASK_NODE_VALUE` and do not justify a new task-node runtime abstraction from this discriminator.

## T
Two policies x two conditions x three fresh sessions = 12 formal sessions. Task keys F8 then F9. An independently labelled fixture mutation uses F7 after F8 and sets `enabled=false`. Both policies see the same current `enabled && phase==1` predicate before F9. GUARDED_MACRO applies it as an ordinary current-state guard; MINIMAL_TASK_NODE applies the byte-equivalent predicate as `maintain_condition`. No repair, learned policy, scheduler or model. Nominal must complete; mutation must YIELD before F9. Actual XTEST press/release and terminal X keymap neutrality are retained.

## D
- `PASS_TASK_NODE_SEMANTICS_SCOPED` only if task-node has a preregistered behavioral/control advantage while all correctness/release gates pass.
- `FAIL_NO_TASK_NODE_VALUE` if both arms are externally behaviorally equivalent in all 12 complete sessions: nominal exact completion 3/3 per arm, mutation zero F9/no effect 3/3 per arm, terminal neutral 12/12, independent audit and >=8 mutations pass.
- `FAIL_TASK_NODE_WRONG_CONTINUATION` if task-node emits F9 after invalidation or produces wrong effect.
- `HOLD_NONDISCRIMINATING_FIXTURE` only if the mutation is not actually observed before the decision boundary.
- source/process/evidence ambiguity is STOP/HOLD.

## C
This deliberately gives both arms the same lifecycle predicate. Therefore an equivalence result says the *representation* added no behavior here; it does not show richer task networks are useless. Giving task-node a better predicate would confound representation with evidence/guard quality.

## U
One cooperative Tk task, one mutation, no model, no multi-node scheduling/resources/replanning, no token benefit or cross-app claim. X-server key state is not physical HID telemetry.

## Excluded construction chronology
- construction1: harness invocation created the output directory before the runner, so the no-overwrite guard stopped before X11.
- construction2/3: the socket readiness helper incorrectly required nonzero `st_size` for a Unix-domain X socket; stopped before app/action evidence.
- construction4: after socket/Xauthority setup repair, four excluded live cells (one per policy x condition) reached the intended boundary: both nominal arms completed F8→F9, both mutation arms observed the F7 state invalidation and emitted no F9/no task effect, all terminal F7/F8/F9 key states neutral. The formal aggregator intentionally reports its 12-row denominator unmet on this four-cell construction and is not interpreted as a scientific result.

No formal case has run. Scientific predicates, conditions, repetitions and decision gates above were not changed from construction outcomes.
