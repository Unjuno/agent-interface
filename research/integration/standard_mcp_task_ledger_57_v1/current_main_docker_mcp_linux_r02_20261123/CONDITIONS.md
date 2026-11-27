# Current-main Docker/Linux MCP worker-entry timing R02

## Frozen baseline

- Main baseline: `a9bb375a09a03ca6129844053cc56910ad96efdf`.
- Prior combined optimized run R01: 86/87 pass; `test_cancelled_transport_keeps_worker_and_receipt_without_replay` missed the exact 2 s worker-entry event. The case and each module passed separately. Preserve this as the red baseline; see R01 raw logs.
- Linux image: `issue57-calc-appserver-r88:local`, image ID `sha256:a3b2b4cd54ca731a86f8d2ba16f1eb833220122c60bfafbdb048e5ad39e50056`; CPython 3.11.2, MCP/Xlib/ViZDoom installed.
- Runtime source: read-only bind mount of this checkout; before test, its runtime tree matched `origin/main` exactly. Container uses `--network none`, `--rm`, and no external GUI/model/provider or WSLc allocation.
- Scope: only test synchronization changes. Production implementation and acceptance timeout remain unchanged.

## Candidate adjustment

The dispatch worker now reports entry through `loop.call_soon_threadsafe(asyncio.Event.set)`. The test waits on that event with `asyncio.wait_for(..., 2)`, preserving the same 2 s bound while avoiding a second `asyncio.to_thread` waiter consuming the same default executor used by `submit`'s worker. The presentation completion notification uses the same loop-safe mechanism and keeps its existing 2 s bound.

## Pass rule

The focused case and complete 87-test public MCP/guarded MCP modules must pass in normal and optimized modes. Preserve all first results; do not expand the two-second deadline or retry a failed full suite as though the first failure did not occur.
