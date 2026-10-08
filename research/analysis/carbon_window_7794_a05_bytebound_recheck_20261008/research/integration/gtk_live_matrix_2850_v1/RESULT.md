# Result

Date: 2026-09-20

Decision: `COMPLETED_UNSCORED_GTK_LIVE_MATRIX_PREFLIGHT`

Runtime was local Docker only, with `--network none`, a read-only source
mount, tmpfs runtime, and a fresh output root. Image lineage:
`agent-interface-gtk-live-effect-2850:v1`, based on
`agent-interface-gtk-fixture-v2:2748` plus `python3-xlib_0.33-2`.

The existing `formal_matrix_runner.py` produced:

```text
actual   = SUCCESS,YIELD,YIELD,NONE,PARTIAL,YIELD,YIELD,YIELD
expected = SUCCESS,YIELD,YIELD,NONE,PARTIAL,YIELD,YIELD,YIELD
scorer_matches = true
formal_receipt_order_ok = true (fixed_order)
```

Independent gate outcomes were `USEFUL`, `UNAVAILABLE`, `REFUSED`,
`NO_EFFECT`, `PARTIAL`, `REPAIRED`, `UNKNOWN`, and `CLEANUP_FAILURE`.
Ambiguous delivery had no replay. Stale repair refused the stale dispatch.
Cleanup failure remained classified as cleanup failure rather than success.
All rows reported zero authority grants and zero model/provider calls.

The runner scope is explicitly `live GTK/X11 adapter matrix receipt-emission
preflight; not formal #2606 acceptance`. Completed native rows still expose an
adapter boundary of `partial` with `task_success=null`; therefore this result
does not close #2850. The full negative-control provenance and scorer-boundary
repair remain required.
