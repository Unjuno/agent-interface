# Temporal ambiguity policy successor (Issue #2436)

A narrow successor to #2204/#984. It compiles typed temporal classifications into fail-closed recovery dispositions.

H/T/D/C/U:
- H: ambiguity, missing lineage, and incomparable clocks must not authorize DONE; retry requires idempotency and generation match.
- T: exercise all six classifications and safe/unsafe retry controls.
- D: deterministic standard-library native and pinned-container tests; no live GUI, model, network, or input.
- C: no evidence about live clock domains, application consumption, task usefulness, or model behavior.
- U: live/model-facing recovery remains open in #2204.
