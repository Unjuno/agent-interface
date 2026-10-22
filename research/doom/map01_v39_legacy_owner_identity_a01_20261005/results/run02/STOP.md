# Run 02 result-collection failure

Disposition: `FAIL_RESULT_COLLECTION_AFTER_CASE_EXECUTION`. The package-root command loaded both projections and executed the six-case matrix, then exited while the post-matrix hash collector looked for `baseline_projection.py` outside `SOURCE/`. It emitted no candidate JSON, so the case outcomes are not retained as a formal result. Stderr and exit are preserved. A local Python 3.14 construction smoke afterward confirmed the repaired collector; run 03 is the new pinned-container execution.
