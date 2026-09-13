# Real focus faults inside the nine-step bundle

Physical input release and tail stop are verified at three points in the registered
nine-step bundle: the first selection click, the X-field click, and Ctrl+A's held
Control modifier. These are actual private X11 backend trials with a separate focus
controller, not model/socket delivery tests. The runtime/executor is unchanged.

The complete probe suite did **not** pass. Its original failures are retained and
classified separately from the physical-stop evidence.

| Trial | Focus injection | Physical release / tail stop | Other result |
|---|---|---|---|
| bundle-focus-01 select button, step0 | yes | verified | fresh observe has no old cause |
| bundle-focus-01 field button, step2 | yes | verified | fresh observe has no old cause |
| bundle-focus-01 Ctrl+A, step3 | **not triggered** | not tested | probe's event-field assumption was wrong; full bundle completed |
| bundle-focus-02 Ctrl+A, step3 | yes | verified | `decision_reason` null despite recorded focus cause; probe assertion fails |

## Method

Each trial uses a fresh seed224 fixture and the exact ordered nine-step list from
the published pair. The emitter blocks after the selected input admission. A
separate X connection verifies Button1 or Control_L is physically down, transfers
focus to a private sink, and checks input is physically up while output is still
blocked and before a terminal appears. Then it restores focus and unblocks output.
This exercises independent owner release even when the execution/output path stalls.
It is not a normal-latency benchmark or an arbitrary-event fault simulator.

Properly injected cases return needs_decision with completed prefix lengths0,2,3.
No later input is admitted and no later bundle step starts. For the key case the
only keyboard admission is Control_L: no A, replacement text, Return or save chord
follows. Release-to-terminal gaps were2.247432,7.546479,1.441162 ms respectively;
they are individual scripted observations, not timing guarantees. Earlier completed
steps are not rolled back. Input release is not transactional task rollback.

## Two retained failures

In probe v1, the trigger required `id`/`step` on all input events. Pointer admission
events carry them, but keyboard admission events do not. Consequently the key trial
ran normally and the wait for the injection point failed. It provides no focus-fault
evidence. `probe_bundle_focus_v2.py` changes only the key trigger to track the enclosing
single executor worker's step_started context and executes the key case in a new
cohort. The old result is not overwritten or relabeled as a successful injection.

The corrected trigger observes Control physically released and the tail stopped.
Its assertion requiring `decision_reason='focus_changed'` then fails. The terminal
contains a verified `interruption.record.reason='focus_changed'`, but the flat
`decision_reason` is null. The final release also has no active deadline; the
per-intent interruption record retains the original deadline. Do not substitute
the global final release for the intent's causal record.

Code inspection shows executor_v5 copies `str(DecisionRequired)` to decision_reason
and converts an empty string to null. Owner rejection paths can raise a parameterless
DecisionRequired. This explains a reachable reason-formatting gap, not a failure to
stop the keyboard tail in this trace. The next precise fix should preserve the
per-intent first cause when an exception supplies no explanation, without inventing
causes or carrying them into later intents. Both original frozen executor and failed
probe outputs must remain unchanged.

The key probe aborts before its fresh-observation isolation check, so that property
is **not tested for the key case here**. It is verified for both button cases using
a new intent with the same deadline. Both probe processes exit1 because failures
are retained; each resource-close call recorded in the trials returns normally.
There is still no independent per-child process inventory.

## Audit and scope

`audit_bundle_focus_v1.py` checks source pins, original step-list hash,38 exact
PNG/AIT frames, owner causal records, completed prefix, no admission after release,
and event-context attribution. It explicitly expects and preserves both failure
classes. An audit pass means this evidence is internally consistent, not that every
probe passed. The report is `results/bundle-focus-audit-01.json` and creation is
exclusive:

```sh
python3 research/live_control/audit_bundle_focus_v1.py
```

No socket-response, model-visible interruption behavior, generic fault coverage,
speed/token gain or default promotion follows. After fixing and testing the missing
reason presentation, proceed to another desktop domain/conditional boundary rather
than repeating normal Inkscape throughput cases. Research Freeze remains open.
