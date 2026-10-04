# MAP01 v39 cancellation-aware release cause

The versioned owner fix is documented in [`../../MAP01_V14_CANCELLATION_RELEASE_CAUSE.md`](../../MAP01_V14_CANCELLATION_RELEASE_CAUSE.md). C01 retains the exact-main parent RED; C02 retains the versioned candidate PASS. Each has its own freeze, raw stdout, exit receipt, and independent audit.

`SOURCE_MANIFEST.json` binds the current-main parent and additive owner/adapter/session chain, plus the frozen tests and outputs. Regenerate it with `python -B make_source_manifest.py` from this directory.

Scope is owner-thread construction under fake Xlib. The candidate run does not execute the historical `ExecutorV12` worker/finally chain or a MAP01 game allocation.
