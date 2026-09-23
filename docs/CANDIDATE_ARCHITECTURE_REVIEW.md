# Candidate architecture review against current evidence

This note responds to the user's “Current State and Candidate Architecture
Report”, supplied as design material rather than implementation instructions.
Review baseline: `bdc3334`. The report is not an approved API specification or
an instruction to rewrite frozen research. The overall objective is unchanged:
persistent, low-idle, closed-loop computer control by a capable remote planner.

## Decisions

Prioritize planner-boundary reduction with explicit validity and observation
semantics. Keep exact transport and deterministic local control as components.
Do not spend the next iteration on PNG tuning, a binary protocol, a large
behavior-tree dependency or a local neural controller. The DOOM integration
remains a transfer environment, not a reason to optimize one-room gameplay while
the interface's validity and measurement semantics remain incomplete.

| Candidate | Current evidence | Next distinction to establish |
|---|---|---|
| Action future and lease | IDs, accepted/running/terminal events, cancel, key release, `decide` | A duration ends a step; it does not expire the authority for subsequent input. Add a separately defined validity interval and an explicit expired outcome. |
| Semantic state version | `expected_sequence` equals latest observation counter | Equality neither proves freshness nor observes external focus/modal changes. Begin with directly observed OS focus/window facts, keeping image sequence separate. |
| Reliable subscriptions | Known color events are retained in session memory until acknowledgement, with archived evidence | No general WATCH registration, reconnect replay or durable delivery guarantee. Specify event IDs, retention, acknowledgement, gaps and failure behavior before calling this reliable delivery. |
| Real planner loop timing | Runtime image-ready, command receipt, acceptance, input acknowledgement and terminal timestamps | Tool/model ingress and generation boundaries are not yet instrumented. Expose missing fields, do not infer them from local time or the goal token counter. |
| Reactive capsule | Finite programs, known local tracking method and explicit decision boundaries | Branches must encode bounded, justified recovery; compare successful-task planner boundaries without silently adding new intelligence to one arm. |

## Important qualifications

**Expiration is a control invariant, not just another terminal label.** A lease
must have a stated clock origin and time domain. Distinguish a planner intent's
freshness from an execution budget starting at acceptance. Delayed admission
can consume an intent's validity; starting a fresh timer on receipt must not
silently authorize stale intent. Check validity at each input boundary and
inside held input, discard the tail on expiry and verify release. Cleanup key-up
events are allowed after expiry; new key-down/motion actions are not. Current
blocking X11/PNG/stdout paths cannot promise a hard release deadline. Report
observed overshoot and failures instead of claiming a watchdog that does not exist.

**Semantic versions should follow declared dependencies.** Start with a focus
or window epoch supported by observable facts, not an all-purpose assertion
about application meaning. A global version incremented by every completed
action may reject unrelated work. Cursor animation should not invalidate focus
authority, while a focus change must be checked even if no new image was emitted.
Selection/modal identity requires a supported sensor or explicit uncertainty.

**Acknowledgement is not resolution.** Clearing a notification does not prove
that the underlying condition vanished or that a next action is valid. Preserve
the distinction between event delivery, planner acknowledgement, condition
resolution and permission to resume. Program `completed` is also not semantic
task `SUCCEEDED`; retain independent task verification.

**Planner interaction is not automatically planner idle.** A long interval
between commands includes inspection, reasoning, tool work and potentially
context handoff. Attribute those components only when instrumented. Record
actual text/image token usage from the inference provider when available;
presentation bytes, API reward and aggregate goal accounting are not substitutes.

## Next experiment order

1. Add a new research revision for expiry, alongside input-boundary timestamps.
   Compare duration-only and independently expiring intent under delayed
   submission, delayed cancellation and injected slow observation. Measure new
   input after expiry, release overshoot, task correctness and completion time.
   Freeze the protocol and preserve the existing executor sources.
2. Test visual-sequence versus directly observed focus/window validity on
   harmless animation, focus transfer and supported modal cases. Record false
   rejection and unintended input to the wrong target, not just guard hit counts.
3. Generalize the retained-event mechanism into a small subscription contract;
   compare latest-only against retained subscribed events with late polling,
   duplicate acknowledgement and disconnection. Do not claim reconnect behavior
   before it is implemented and tested.
4. Compare bounded conditional programs with per-step planner return using the
   same planner/task/environment and explicit correctness gates. Primary outcome:
   planner boundaries per successful task, alongside wall time and recovery.
   Keep DOOM as a transfer check; include practical GUI work as well.

Planner timing instrumentation starts with step 1, rather than waiting until
every runtime feature exists. The report's B0–B4 ladder is a useful eventual
ablation, but first isolate each change so failures remain attributable. A
scripted delay study is development evidence, not a replacement for that real
planner comparison.

## Measurement contract to prepare

Record fresh useful observation ready, adapter dispatch, runtime acceptance,
response-generation start, first executable planner instruction, OS injection,
and first verified visible effect as distinct events. Label their clock domains
and correlation IDs. Cross-process clocks require calibration; remote intervals
need round-trip bounds or clock synchronization. Mark unavailable events as
unavailable. Never derive a visible effect merely from successful input injection.

This is a decision record and experiment backlog. No candidate future states,
lease guarantees, semantic sensor coverage or token savings become implemented
by publication of this note.
