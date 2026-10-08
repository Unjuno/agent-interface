# V39 pending-planner observation pump construction probe (A01)

This offline probe asks one narrow question: does the current V39 controller source composition continue dispatching typed observations while its planner future is pending, and then issue a cancellation before consuming a neutral cancelled terminal after policy invalidation?

## Frozen inputs

- Main commit: `08d3283f6d3c61cc6b032c6c9c5a63ec464c07ff`
- Controller: `research/doom/map01_overlap_controller_v39.py`
- Controller Git blob: `3f43c261e2de0b54cc1e83d2a9d53fd984d70f0a`
- Controller SHA-256: `c4004089e82a6e6114ea6a9451fe5e9336da8b10c9f46aa02fcaa36f8a945e95`
- Synthetic ordered event stream: `inputs/events.json`

## Result

`RESULT.json` records a synthetic typed observation being monitored while the fake planner future remains pending, followed by a `cancel` command and a synthetic cancelled terminal whose declared key and button state is empty. No cover was renewed. `AUDIT.json` independently reconstructs the expected record from the frozen source identity and raw event stream and passes all four audit checks.

Reproduce from the repository root with the bundled Python runtime:

```sh
PY=/Users/taka/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3
PKG=research/doom/v39_pending_planner_observation_pump_construction_a01_20261008
$PY -B -m unittest discover -s "$PKG/tests" -v
$PY -B "$PKG/probe.py"
$PY -B "$PKG/audit.py"
```

The probe and audit commands refuse to overwrite output files. The checked-in JSON outputs are deterministic for these frozen inputs.

## Evidence class and limits

This is source-composition construction evidence only. The probe extracts and executes the controller's nested wait dispatcher, pending-planner executor block, and cancellation helper against synthetic event rows. Its fake pool intentionally does not start a worker or invoke `planner.await_turn`; it models a pending future and the ordering around it. Therefore it does **not** establish real thread concurrency, planner latency, live executor transport behavior, a running Doom game, model behavior, GUI or OS input, physical key state, useful feedback, recovery, or task effect. It does not satisfy the live threat-exposure gate in `docs/CURRENT_GOAL.md` or Issue #59.

The next useful experiment, once a valid live allocation and threat exposure exist, is to record monotonic timestamps for observation capture, monitor decision, cancellation send, terminal receipt, and verified release while the real planner is blocked. This package makes no claim that such a live run has happened.
