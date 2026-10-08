# V39 pending-loop full-body construction A02

This one-shot synthetic experiment executes the exact frozen nested `wait()` function and complete pending-future loop body from V39. It runs two cases: repeated healthy cover terminals followed by a scripted planner completion, and hard health invalidation during a pending cycle. The production monitor, terminal validator, and cancellation helper remain in the source slice; only planner/process and cover submission boundaries are deterministic fakes. A01's partial result, the A02 wrapper STOP, and A03's preflight refusal are retained as separate records. A02 queues only the cancellation terminal on the invalidation path.

## H / T / D / C / U

- **H:** The full loop drains typed observations while the planner future is pending, renews only after valid cover terminals, stops renewal after a completion poll, and sends cancellation before interrupt transport on hard invalidation.
- **T:** Execute the frozen nested wait and complete pending-loop AST with scripted typed signals, terminals, planner completion, and deterministic transport fakes.
- **D:** Pass only if the healthy path consumes two terminals, renews once between them, and performs no further renewal after completion; the invalidation path cancels the active cover before planner interruption and returns verified-empty release.
- **C:** Synthetic source-slice construction; no live runner, real producer, model service, game, GUI, OS input, or physical key state.
- **U:** No HUD accuracy/cadence, wall-clock bound, useful feedback, recovery efficacy, progress, survival, or task outcome.

Exact source hashes and line/AST anchors are in `FREEZE.json`. Earlier A01–A04 harness STOP evidence for the predecessor experiment remains in its original sibling directories.

## Reproduction

```text
python -m research.doom.v39_observation_pump_full_loop_a02_20261008.candidate
python -m research.doom.v39_observation_pump_full_loop_a02_20261008.audit
python -m unittest -v research.doom.v39_observation_pump_full_loop_a02_20261008.test_audit
```

Candidate outputs are one-shot and refuse overwrite.
