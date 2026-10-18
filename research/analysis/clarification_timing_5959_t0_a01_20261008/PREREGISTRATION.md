# Issue #5959 — T0 preregistration A01

## H — hypothesis and limit

On a finite authored event trace, a policy that waits for an explicitly
authorized low-interruption window can schedule an already-justified,
deferrable clarification before its latest useful delivery time. It must never
defer a nondeferrable safety/authority request, use an answer after its decision
version changes, or treat refusal/nonresponse as consent. T0 tests these
semantics and the scoring pipeline only; it does not test the hypothesis about
human interruption cost.

## T — frozen finite experiment

Compare three deterministic policies on every candidate-visible request:

1. `immediate`: present at creation when a response can still be timely;
2. `latest_safe`: present at the latest safe delivery tick;
3. `low_cost_window`: use the latest explicitly authorized low-cost-window
   tick no later than the latest safe delivery tick, otherwise fall back to
   `latest_safe`.

Ticks are nonnegative integers. A response arriving exactly at its deadline is
 timely; the commitment boundary is exclusive. For a deferrable request:

```text
latest_answer_tick = min(latest_useful_answer_tick, commitment_tick - 1)
latest_delivery_tick = min(safe_wait_through_tick,
                           latest_answer_tick - response_latency_bound)
```

If `latest_delivery_tick < created_tick`, every deferrable policy returns
`YIELD_NOW`; it does not send a question that cannot affect the pending
decision. Nondeferrable requests bypass the scheduler and deliver immediately.
At a delivery tick, a decision-version change at the start of that tick makes
the request stale and cancels it. A later version change invalidates any
answer. Only an on-time `AUTHORIZED_CHOICE` for an enumerated authorized option
with the unchanged decision version permits the modeled effect. Refusal,
nonresponse, late answer, or stale/invalid answer yields without an effect.
Mandatory events are delivered at their arrival tick on a separate bypass lane.

`audit_oracle.json` is not mounted into the candidate container. It contains
version changes, reply outcomes, authorized-choice truth, and a wholly
synthetic interruption-cost trace. The candidate receives only the
candidate-visible request and expressly authorized low-cost-window ticks. The
independent auditor reconstructs all policy schedules and outcomes without
importing candidate code.

## D — decision gates

`PASS_METHOD_SCOPED` only if the candidate and independent auditor agree on
every frozen request/policy row; all mandatory events bypass at zero modeled
delay; zero-slack requests yield immediately; stale/late/refused/unanswered
requests cause no modeled effect; only current authorized answers permit an
effect; the low-window control actually selects an in-bound authorized window;
the auditor reconstructs the hidden synthetic cost scores; and all five
construction mutations are rejected. Otherwise retain the exact first
`FAIL_METHOD_SCOPED`, `FAIL_AUDIT`, or `STOP` outcome. T0 cannot establish
`H_PASS_SCOPED` or `H_FAIL_SCOPED` for humans.

The cost discriminator is deliberately modest: at least one frozen row must
have a low-window delivery with a lower authored cost score than both immediate
and latest-safe delivery. This only checks that the finite scorer can express
the proposed tradeoff; the cost values are not empirically calibrated.

## C — alternatives and controls

Immediate ask-or-yield may dominate when no safe response window exists; a
simple latest-safe rule may capture all benefit; the availability signal may
not predict actual disruption; and asking later may increase reorientation or
expiry costs absent from this finite model. These alternatives remain open.

## U — scope

No participant, GUI, model, production service, private availability data,
real task, or runtime scheduler is involved. The discrete response bound and
synthetic cost values are authored. No result supports human benefit, attention
inference, consent by silence, privacy acceptability, or safety guarantees.

## One-shot commands and counts

After freezing and committing `FREEZE.json`, execute [RUN_COMMANDS.md](RUN_COMMANDS.md)
to run the candidate CLI exactly once
in the pinned OrbStack container, then run the auditor CLI exactly once in a
separate pinned OrbStack container. Candidate and auditor formal invocation
counts start at 0/0; construction calls are separately labeled and are not
formal invocations. No retries or post-freeze source/input edits are allowed.
Each container has no network, read-only root and source mounts, no Linux
capabilities, no-new-privileges, a non-root UID, and requested CPU/memory/PID
limits. Requested limits are not treated as independently verified enforcement.
