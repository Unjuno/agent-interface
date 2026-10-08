# V39 observation-pump event-dispatch A02

This one-shot synthetic construction test executes the exact frozen V39 nested `wait()` function and the pending-future loop's dispatch/invalidation branch, with the production typed health guard, cover monitor, and `cancel_invalidated_cover` helper. A typed health sample moves from 100 to 84 against an authored floor of 88 while a fake planner future remains pending. The queue also contains the cover's verified-empty terminal.

A01 stopped before its candidate branch because its AST selector read `.test` before checking node type. That candidate and STOP are preserved in the sibling A01 package and were not rerun. A02 fixes that harness predicate and keeps the source freeze and hypothesis unchanged.

The test asks whether the production pump consumes the typed observation before the terminal predicate, evaluates the monitor while the future is pending, and routes its hard invalidation into executor cancellation before planner interrupt transport. Frozen source commit and blob/SHA identities are in `FREEZE.json`; first candidate output is in `RESULT.json` and its queue/event record is in `events.jsonl`.

## H / T / D / C / U

- **H:** The pinned wait loop dispatches a typed health observation to the actual cover monitor while the planner future is pending, then routes hard invalidation through the production cancellation helper before dequeuing the terminal.
- **T:** Extract only the exact pinned nested `wait()` and the first two statements of the exact `while not future.done()` loop AST. Run once with a synthetic 100→84 observation, deterministic planner/process fakes, and an empty verified terminal. Audit event order and source identities from raw output.
- **D:** Pass only if a pending future is observed at monitor delivery, hard invalidation requires a new decision without granting authority, executor cancel precedes planner interrupt transport, and the helper returns after verified-empty release.
- **C:** Source-slice execution tests this orchestration boundary. It does not run controller startup, a real observation producer, model service, game, GUI, OS input, or real key state.
- **U:** No HUD extraction accuracy/cadence, wall-clock response bound, physical key-up time, independently useful feedback, recovery efficacy, progress, survival, or task outcome is measured.

## Reproduction

From repository root:

```text
python -m research.doom.v39_observation_pump_event_dispatch_a03_20261008.candidate
python -m research.doom.v39_observation_pump_event_dispatch_a03_20261008.audit
python -m unittest -v research.doom.v39_observation_pump_event_dispatch_a03_20261008.test_audit
```

The candidate refuses to overwrite retained output. The independent audit is read-only after `AUDIT.json` exists. The current Issue #59 live threat/recovery allocation remains separate and unassigned.
