# Independent progress clock v2 — terminal scorer-epoch lock

Status: **CONTRACT REPAIR PASS / SESSION INTEGRATION NOT RUN**

Task: `O3-PH48-G3-PROGRESS-TERMINAL-V2-001`  
Base: `9aed27c74c968bec71ef2e3fdf965d43332a8dd5`  
Branch: `orchestrator/O3/G3-progress-terminal-v2-9aed27c7`

## Why v2 exists

The retained v1 scorer contract correctly separated independent progress from controller-visible health/ammo/pixel evidence, but review exposed one terminal-state ambiguity. After v1 observes `episode_finished=True`, it rejects only a regression back to unfinished. A later same-epoch sample can therefore keep `episode_finished=True` while changing counters or `map_exit=False -> True`, and v1 may emit a new useful event after the episode was already declared terminal.

That is not an acceptable causal clock. A scorer epoch must have one immutable terminal state.

V1 remains retained unchanged as the first contract result. V2 is a separately versioned repair.

## V2 contract

One `ProgressClock` instance represents exactly one scorer epoch.

Before terminal, v2 preserves the v1 rules:

- the first sample establishes a baseline;
- timestamps are monotonic;
- same-timestamp exact duplicates are idempotent;
- same-timestamp mutation fails closed;
- kill/death counter regression requires a new epoch;
- useful positive events remain `KILL_COUNT_INCREASE` and `MAP_EXIT` only;
- negative events remain death/player-dead/non-exit terminal;
- every event is `controller_visible=false`.

After the first sample with `episode_finished=True`:

- a later timestamp carrying the **exact same terminal state** is accepted as a no-op and advances only the observed sample clock;
- any later kill/death counter change, player-dead change, map-exit change, or terminal-state mutation raises `ValueError` and requires a new scorer epoch;
- specifically, `EPISODE_FINISHED_NO_EXIT -> later MAP_EXIT` in one clock is forbidden.

A fresh `ProgressClock` object is the explicit epoch reset boundary. Persisting/associating that epoch with a concrete MAP01 session is intentionally left to the integration layer.

## Isolation hardening

V2 continues to expose no controller delivery method. `append_jsonl()` accepts only v2 scorer events and now also rejects an event whose `controller_visible` field is not exactly `False`.

This is defense in depth. A future MAP01 adapter must still write the scorer stream to a separate file and must never reuse the controller `emit` path.

## Exact-byte validation

The exact source/test bytes committed on this branch were first written into the authoring container and executed before upload.

Environment:

- CPython 3.13.5
- Linux 6.18.44 x86_64

Results:

- `python -m py_compile`: **PASS**
- deterministic unit tests: **15/15 PASS**

The regression set includes:

1. baseline/no event;
2. positive kill event;
3. positive terminal MAP exit;
4. negative non-exit terminal;
5. later identical terminal-state sample is a no-op clock advance;
6. non-exit terminal -> later MAP exit rejected;
7. terminal -> later kill increase rejected;
8. terminal -> later death increase rejected;
9. terminal player-state mutation rejected;
10. same-timestamp exact duplicate idempotence;
11. same-timestamp mutation rejection;
12. timestamp regression rejection;
13. preterminal counter regression rejection;
14. invalid map-exit state rejection;
15. scorer-only JSONL schema/controller-visibility enforcement.

Machine-readable result:
`research/orchestration/o3-g3/results/independent-progress-clock-v2.json`

## H / T / D / C / U

### H — falsifiable hypothesis

Locking terminal scorer state per epoch removes the post-terminal false-positive path without changing valid preterminal useful-event semantics.

### T — minimum test

Exercise positive/negative preterminal events, exact terminal repeats, every material post-terminal mutation class, timestamp/counter regressions, invalid map-exit state, and scorer-only persistence. No ViZDoom/session call is required for this contract repair.

### D — decision

**PASS contract repair.** The tested terminal mutation classes fail closed and exact later terminal repeats remain idempotent/no-event.

This does **not** pass scorer polling/session integration. The concurrent main-thread polling construction remains a separate gate.

### C — competing explanations / break modes

- a concrete session adapter may accidentally reuse one clock across two episodes without explicitly resetting the scorer epoch;
- actual ViZDoom `episode_finished`/map-exit observation ordering may require an adapter-specific sampling rule;
- sparse kill/exit events still do not measure navigation progress continuously;
- a privileged scorer payload can still leak if a future adapter incorrectly routes it through controller `emit` despite this module having no such path.

### U — uncertainty

Remaining uncertainty is integration-level: epoch identity, actual ViZDoom getter timing/ordering, main-thread polling cadence, persistence latency, and scorer/controller stream isolation. No live timing distribution is claimed by this task.

## Next gate

Review the existing `O3-G2-SCORER-POLLING-BOUNDARY-001` branch against v2 rather than integrating progress-clock v1. If the scheduling construction is accepted, a new versioned MAP01 telemetry-only session adapter should bind:

- release telemetry v2 already retained on main;
- main-thread scorer polling;
- independent progress clock v2;
- separate scorer-only persistence.

That adapter must compile/test and freeze exact sources before one no-retry telemetry validation. Recovery-vs-coast policy comparison remains blocked until that measurement run succeeds or fails informatively.
