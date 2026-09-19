# #1257 first outcome — STOPPED_OUTER_EXECUTION_TIMEOUT

The exact frozen primary was invoked once in the disposable container and was not rerun. The outer container execution ceiling of 180,000 ms terminated the command before `runner.py` wrote `ROWS.jsonl` or `SUMMARY.json`. Therefore the 108-case scientific decision is **not evaluable**.

- scientific primary invocations: 1
- reruns / replacements / post-freeze tuning: 0 / 0 / 0
- formal retained rows: 0
- stdout / stderr bytes: 0 / 0
- frozen source rehash: 12/12 exact
- exact #1251 candidate: `24fa033d1bce9fc36d3d628bf4dd454cfeab2441a6c7ac281c80ce82b3c94e9f`
- residual runner/Xvfb/LibreOffice/scorer processes after stop: 0
- excluded construction remains PASS with rows SHA-256 `c80096c320ca1fcb3b2dba697109e1c540720111371aa0b7c72470085880ba5a`.

This is an orchestration stop, not evidence against the actor-attribution hypothesis. The frozen runner accumulates rows in memory and writes both retained result files only after the complete loop, so no partial scientific rows can be recovered from this consumed primary.

The next legitimate experiment is a **fresh allocation** that changes only outer orchestration to bounded immutable batches. It must keep the exact candidate, nine families, A1 target, lowercase token grammar, independent UNO scorer, XTEST injector separation, and 500 ms temporal comparator unchanged.
