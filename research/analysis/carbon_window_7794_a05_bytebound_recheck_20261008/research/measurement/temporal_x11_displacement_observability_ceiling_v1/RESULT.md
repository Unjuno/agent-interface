# #1351 preformal stop — no scientific disposition

Task: `TEMPORAL-X11-DISPLACEMENT-OBSERVABILITY-CEILING-R1-20260918-013`

**Decision:** `PREFORMAL_STOP_FORMAL_MODE_PRECHECK_BEFORE_FREEZE`

No formal scientific result is claimed.

During preformal audit-coverage validation, the worker generated a disposable `PRECHECK_FORMAL.json` by invoking `runner.py formal` before the source-freeze/ownership-reread boundary. The file was used only to confirm that five copied-output corruption controls were rejected and was then deleted. Nevertheless, this exposed the deterministic formal result shape before the preregistered freeze. Under the experiment's own one-formal-after-freeze discipline, that invalidates this allocation.

The audit-coverage repair itself is retained because it is useful: `audit.py` now checks published correct/unknown/safe-correct counts and rejects the `correct_count` mutation. Science hypotheses, #1344 boundary facts, witness rule and thresholds were not changed.

A distinct successor must freeze this corrected source **before any formal-mode generation** and then run exactly one formal invocation.

`PREFORMAL_STOP.json` SHA-256: `3b19bc04cfefd9af97ba2d81419242662c772aa1e034541030c7744328cc0430`.
