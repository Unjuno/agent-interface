# Capture-epoch currentness contract (#2340)

Container-only successor evidence for #2340. This does not claim live GUI capture, IPC latency, model interpretation, or task/effect correctness.

## H/T/D/C/U

- H: current action context requires exact epoch, sequence, scope, and current planner role.
- T: fresh, late old epoch/sequence, future sequence, wrong role, dropped epoch, corrupt sequence, and missing scope.
- D: `work/capture-epoch-contract-2340.py` must classify eight cases with fail-closed missing-field behavior and survive one JSON round-trip.
- C: authored observations only; no live GUI, queue, restart, model, input, or independent effect scorer.
- U: real capture/transport preservation, latency, model use, held-out surface, and task/effect transfer remain unverified.

## Result

Native and `python:3.12-slim` runs emitted:

`PASS_CAPTURE_EPOCH_CONTRACT cases=8 current=1 historical=3 reobserve=1 abstain=3`

This is a transport-admission contract, not live GUI evidence. Historical context never grants current action authority.
